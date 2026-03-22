from sqlalchemy import select

from app.db.models import IntakeJob, IntakeJobEvent
from app.db.session import create_session_factory, get_engine, init_db
from app.services.idempotency import create_or_get_job


def test_duplicate_idempotency_key_returns_existing_job(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'idempotency.db'}"
    engine = get_engine(database_url)
    init_db(engine)
    session_factory = create_session_factory(database_url)

    with session_factory() as session:
        first_job = create_or_get_job(
            session,
            task_type="resume_intake",
            idempotency_key="abc",
            input_text="Alice worked at ACME",
        )
        second_job = create_or_get_job(
            session,
            task_type="resume_intake",
            idempotency_key="abc",
            input_text="Alice worked at ACME",
        )

        jobs = session.scalars(select(IntakeJob)).all()
        events = session.scalars(select(IntakeJobEvent)).all()

    assert first_job.id == second_job.id
    assert len(jobs) == 1
    assert [event.event_type for event in events] == ["job_created"]
