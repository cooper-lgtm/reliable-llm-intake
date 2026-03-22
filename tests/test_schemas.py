from pydantic import ValidationError

from app.core.schemas import CreateJobRequest


def test_create_job_request_accepts_supported_task_type():
    payload = CreateJobRequest(
        task_type="resume_intake",
        input_text="Alice worked at ACME",
    )

    assert payload.task_type == "resume_intake"


def test_create_job_request_rejects_unknown_task_type():
    try:
        CreateJobRequest(task_type="unknown", input_text="x")
        assert False
    except ValidationError:
        assert True
