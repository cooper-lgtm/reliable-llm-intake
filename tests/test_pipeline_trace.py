from app.db.session import create_session_factory, get_engine, init_db
from app.services.idempotency import create_or_get_job
from app.services.llm_client import FakeLLMClient
from app.services.pipeline import IntakePipeline, build_ordered_trace


def test_pipeline_records_ordered_state_transition_trace(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'pipeline_trace.db'}"
    engine = get_engine(database_url)
    init_db(engine)
    session_factory = create_session_factory(database_url)

    with session_factory() as session:
        job = create_or_get_job(
            session,
            task_type="resume_intake",
            idempotency_key="trace-1",
            input_text="Alice Doe can be reached at alice@example.com and worked at ACME.",
        )
        pipeline = IntakePipeline(
            llm_client=FakeLLMClient(
                responses=[
                    '{"name": "Alice"}',
                    '{"name": "Alice"}',
                ],
            ),
            sleep_func=lambda _: None,
        )

        pipeline.run(session, job)
        trace = build_ordered_trace(session, job.id)

    assert [entry["sequence"] for entry in trace] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert [entry["event_type"] for entry in trace] == [
        "job_created",
        "pipeline_started",
        "llm_attempt_started",
        "validation_failed",
        "llm_attempt_started",
        "validation_failed",
        "fallback_used",
        "job_needs_review",
    ]
    assert trace[3]["payload"]["attempt"] == 1
    assert trace[5]["payload"]["attempt"] == 2
