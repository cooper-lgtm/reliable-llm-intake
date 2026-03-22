from sqlalchemy import select

from app.core.enums import JobStatus
from app.db.models import IntakeJob, IntakeJobEvent
from app.db.session import create_session_factory, get_engine, init_db
from app.services.llm_client import FakeLLMClient
from app.services.pipeline import IntakePipeline


def test_pipeline_retries_on_invalid_llm_output_and_then_succeeds(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'pipeline_retry.db'}"
    engine = get_engine(database_url)
    init_db(engine)
    session_factory = create_session_factory(database_url)

    with session_factory() as session:
        job = IntakeJob(
            task_type="resume_intake",
            idempotency_key="retry-1",
            input_text="Alice Doe alice@example.com 5 years at ACME",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        pipeline = IntakePipeline(
            llm_client=FakeLLMClient(
                responses=[
                    '{"name": "Alice"}',
                    '{"name": "Alice", "email": "alice@example.com", "years_experience": 5}',
                ],
            ),
            sleep_func=lambda _: None,
        )

        result = pipeline.run(session, job)
        event_types = session.scalars(
            select(IntakeJobEvent.event_type).where(IntakeJobEvent.job_id == job.id),
        ).all()

    assert result.status == JobStatus.SUCCEEDED
    assert result.attempt_count == 2
    assert result.normalized_output == {
        "name": "Alice",
        "email": "alice@example.com",
        "years_experience": 5,
    }
    assert "validation_failed" in event_types
