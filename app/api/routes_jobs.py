from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.core.schemas import CreateJobRequest, CreateJobResponse
from app.db.models import IntakeJob, IntakeJobEvent
from app.db.session import get_db_session
from app.services.idempotency import create_or_get_job
from app.services.llm_client import PlaceholderLLMClient
from app.services.pipeline import IntakePipeline


router = APIRouter(prefix="/v1/intake/jobs", tags=["intake-jobs"])


class JobEventResponse(BaseModel):
    event_type: str
    event_payload: dict[str, Any] | None = None


class JobDetailResponse(BaseModel):
    job_id: str
    status: JobStatus
    attempts: int
    result: dict[str, Any] | None = None
    events: list[JobEventResponse]


def get_pipeline() -> IntakePipeline:
    return IntakePipeline(llm_client=PlaceholderLLMClient())


@router.post("", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    request: CreateJobRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    session: Session = Depends(get_db_session),
    pipeline: IntakePipeline = Depends(get_pipeline),
) -> CreateJobResponse:
    job = create_or_get_job(
        session,
        task_type=request.task_type.value,
        idempotency_key=idempotency_key,
        input_text=request.input_text,
    )

    if job.status == JobStatus.PENDING and job.attempt_count == 0:
        job = pipeline.run(session, job)

    return CreateJobResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(
    job_id: str,
    session: Session = Depends(get_db_session),
) -> JobDetailResponse:
    job = session.get(IntakeJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    events = session.scalars(
        select(IntakeJobEvent).where(IntakeJobEvent.job_id == job_id).order_by(IntakeJobEvent.created_at),
    ).all()

    return JobDetailResponse(
        job_id=job.id,
        status=job.status,
        attempts=job.attempt_count,
        result=job.normalized_output,
        events=[
            JobEventResponse(event_type=event.event_type, event_payload=event.event_payload)
            for event in events
        ],
    )
