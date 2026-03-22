from pydantic import BaseModel

from app.core.enums import JobStatus, TaskType


class CreateJobRequest(BaseModel):
    task_type: TaskType
    input_text: str


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class ResumeIntakeResult(BaseModel):
    name: str
    email: str
    years_experience: int


class SupportTicketIntakeResult(BaseModel):
    customer_name: str
    issue_summary: str
    priority: str
