from __future__ import annotations

from collections.abc import Callable
from json import JSONDecodeError
from time import sleep

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.core.schemas import ResumeIntakeResult, SupportTicketIntakeResult
from app.db.models import IntakeJob, IntakeJobEvent
from app.services.fallback import run_fallback
from app.services.llm_client import LLMClient
from app.services.validators import parse_json_payload, validate_payload


TASK_SCHEMAS: dict[str, type[BaseModel]] = {
    "resume_intake": ResumeIntakeResult,
    "support_ticket_intake": SupportTicketIntakeResult,
}


class IntakePipeline:
    def __init__(
        self,
        *,
        llm_client: LLMClient,
        max_attempts: int = 2,
        base_backoff_seconds: float = 0.1,
        sleep_func: Callable[[float], None] = sleep,
    ) -> None:
        self.llm_client = llm_client
        self.max_attempts = max_attempts
        self.base_backoff_seconds = base_backoff_seconds
        self.sleep_func = sleep_func

    def run(self, session: Session, job: IntakeJob) -> IntakeJob:
        schema = TASK_SCHEMAS[job.task_type]
        job.status = JobStatus.RUNNING
        self._record_event(session, job, "pipeline_started", {"job_id": job.id})

        last_error: str | None = None
        for attempt in range(1, self.max_attempts + 1):
            job.attempt_count = attempt
            self._record_event(session, job, "llm_attempt_started", {"attempt": attempt})

            try:
                raw_output = self.llm_client.extract(self._build_prompt(job.task_type), job.input_text)
                payload = parse_json_payload(raw_output)
                validated = validate_payload(schema, payload)
            except (ValidationError, ValueError, JSONDecodeError) as exc:
                last_error = str(exc)
                self._record_event(
                    session,
                    job,
                    "validation_failed",
                    {"attempt": attempt, "error": last_error},
                )
                if attempt < self.max_attempts:
                    self.sleep_func(self.base_backoff_seconds * (2 ** (attempt - 1)))
                continue
            except Exception as exc:
                last_error = str(exc)
                self._record_event(
                    session,
                    job,
                    "llm_attempt_failed",
                    {"attempt": attempt, "error": last_error},
                )
                if attempt < self.max_attempts:
                    self.sleep_func(self.base_backoff_seconds * (2 ** (attempt - 1)))
                continue

            job.normalized_output = validated.model_dump()
            job.failure_reason = None
            job.review_required = False
            job.status = JobStatus.SUCCEEDED
            self._record_event(session, job, "job_succeeded", {"attempt": attempt})
            session.commit()
            session.refresh(job)
            return job

        fallback_payload = run_fallback(job.task_type, job.input_text)
        if fallback_payload:
            missing_fields = self._missing_required_fields(schema, fallback_payload)
            job.normalized_output = fallback_payload
            job.failure_reason = last_error
            job.review_required = bool(missing_fields)
            self._record_event(
                session,
                job,
                "fallback_used",
                {"missing_fields": missing_fields},
            )

            if missing_fields:
                job.status = JobStatus.NEEDS_REVIEW
                self._record_event(
                    session,
                    job,
                    "job_needs_review",
                    {"missing_fields": missing_fields},
                )
            else:
                validated = validate_payload(schema, fallback_payload)
                job.normalized_output = validated.model_dump()
                job.status = JobStatus.SUCCEEDED
                self._record_event(session, job, "job_succeeded", {"via": "fallback"})

            session.commit()
            session.refresh(job)
            return job

        job.status = JobStatus.FAILED
        job.failure_reason = last_error
        self._record_event(session, job, "job_failed", {"error": last_error})
        session.commit()
        session.refresh(job)
        return job

    def _build_prompt(self, task_type: str) -> str:
        return f"Extract structured data for task type: {task_type}"

    def _record_event(
        self,
        session: Session,
        job: IntakeJob,
        event_type: str,
        event_payload: dict | None = None,
    ) -> None:
        session.add(
            IntakeJobEvent(
                job_id=job.id,
                event_type=event_type,
                event_payload=event_payload,
            )
        )
        session.flush()

    def _missing_required_fields(
        self,
        schema: type[BaseModel],
        payload: dict,
    ) -> list[str]:
        missing_fields: list[str] = []
        for field_name in schema.model_fields:
            value = payload.get(field_name)
            if value is None or value == "":
                missing_fields.append(field_name)
        return missing_fields
