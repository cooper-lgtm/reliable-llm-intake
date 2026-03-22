from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class TaskType(str, Enum):
    RESUME_INTAKE = "resume_intake"
    SUPPORT_TICKET_INTAKE = "support_ticket_intake"
