from collections.abc import Generator

from fastapi.testclient import TestClient

from app.api.routes_jobs import get_pipeline
from app.db.session import create_session_factory, get_db_session, get_engine, init_db
from app.main import app
from app.services.llm_client import FakeLLMClient
from app.services.pipeline import IntakePipeline


def _override_db(session_factory) -> Generator:
    def dependency():
        with session_factory() as session:
            yield session

    return dependency


def _build_client(tmp_path, responses: list[str]) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'api_jobs.db'}"
    engine = get_engine(database_url)
    init_db(engine)
    session_factory = create_session_factory(database_url)

    app.dependency_overrides[get_db_session] = _override_db(session_factory)
    app.dependency_overrides[get_pipeline] = lambda: IntakePipeline(
        llm_client=FakeLLMClient(responses=responses),
        sleep_func=lambda _: None,
    )
    return TestClient(app)


def test_create_job_returns_job_id_and_pending_or_terminal_state(tmp_path):
    client = _build_client(
        tmp_path,
        ['{"name": "Alice Doe", "email": "alice@example.com", "years_experience": 5}'],
    )

    try:
        response = client.post(
            "/v1/intake/jobs",
            headers={"Idempotency-Key": "api-create-1"},
            json={
                "task_type": "resume_intake",
                "input_text": "Alice Doe alice@example.com 5 years at ACME",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert "job_id" in body
    assert body["status"] in {"pending", "succeeded", "needs_review", "failed"}


def test_get_job_returns_normalized_output_and_events(tmp_path):
    client = _build_client(
        tmp_path,
        ['{"name": "Alice Doe", "email": "alice@example.com", "years_experience": 5}'],
    )

    try:
        create_response = client.post(
            "/v1/intake/jobs",
            headers={"Idempotency-Key": "api-get-1"},
            json={
                "task_type": "resume_intake",
                "input_text": "Alice Doe alice@example.com 5 years at ACME",
            },
        )
        job_id = create_response.json()["job_id"]
        response = client.get(f"/v1/intake/jobs/{job_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["attempts"] == 1
    assert body["result"] == {
        "name": "Alice Doe",
        "email": "alice@example.com",
        "years_experience": 5,
    }
    assert [event["event_type"] for event in body["events"]] == [
        "job_created",
        "pipeline_started",
        "llm_attempt_started",
        "job_succeeded",
    ]
