from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.db.models import IntakeJob, IntakeJobEvent


def create_or_get_job(
    session: Session,
    *,
    task_type: str,
    idempotency_key: str,
    input_text: str,
) -> IntakeJob:
    existing_job = session.scalar(
        select(IntakeJob).where(
            IntakeJob.task_type == task_type,
            IntakeJob.idempotency_key == idempotency_key,
        )
    )
    if existing_job is not None:
        return existing_job

    job = IntakeJob(
        task_type=task_type,
        idempotency_key=idempotency_key,
        input_text=input_text,
        status=JobStatus.PENDING,
    )
    session.add(job)
    session.flush()

    session.add(
        IntakeJobEvent(
            job_id=job.id,
            event_type="job_created",
            event_payload={"task_type": task_type},
        )
    )
    session.commit()
    session.refresh(job)
    return job
