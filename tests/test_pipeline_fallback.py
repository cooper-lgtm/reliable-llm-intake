from sqlalchemy import select

from app.core.enums import JobStatus
from app.db.models import IntakeJob, IntakeJobEvent
from app.db.session import create_session_factory, get_engine, init_db
from app.services.llm_client import FakeLLMClient
from app.services.pipeline import IntakePipeline


def test_pipeline_marks_job_needs_review_when_fallback_is_partial(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'pipeline_fallback.db'}"
    engine = get_engine(database_url)
    init_db(engine)
    session_factory = create_session_factory(database_url)

    with session_factory() as session:
        job = IntakeJob(
            task_type="resume_intake",
            idempotency_key="fallback-1",
            input_text="Alice Doe can be reached at alice@example.com and worked at ACME.",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        pipeline = IntakePipeline(
            llm_client=FakeLLMClient(
                responses=[
                    '{"name": "Alice"}',
                    '{"name": "Alice"}',
                ],
            ),
            sleep_func=lambda _: None,
        )

        result = pipeline.run(session, job)
        event_types = session.scalars(
            select(IntakeJobEvent.event_type).where(IntakeJobEvent.job_id == job.id),
        ).all()

    assert result.status == JobStatus.NEEDS_REVIEW
    assert result.review_required is True
    assert result.normalized_output == {
        "name": "Alice Doe",
        "email": "alice@example.com",
    }
    assert "fallback_used" in event_types
