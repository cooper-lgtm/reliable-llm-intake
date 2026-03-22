from app.core.enums import JobStatus
from app.db.models import IntakeJob


def test_intake_job_defaults_to_pending():
    job = IntakeJob(
        task_type="resume_intake",
        idempotency_key="abc",
        input_text="hello",
    )

    assert job.status == JobStatus.PENDING
