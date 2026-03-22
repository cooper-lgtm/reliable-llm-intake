from pydantic import BaseModel

from app.core.enums import JobStatus, TaskType


class CreateJobRequest(BaseModel):
    task_type: TaskType
    input_text: str


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class ResumeIntakeResult(BaseModel):
    name: str | None = None
    email: str | None = None
    years_experience: int | None = None


class SupportTicketIntakeResult(BaseModel):
    customer_name: str | None = None
    issue_summary: str | None = None
    priority: str | None = None
