# Reliable LLM Intake Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a backend-first sample service that turns unstructured text into validated structured output with explicit job states, retries, fallbacks, and tests.

**Architecture:** A FastAPI API creates intake jobs and persists state in a relational store. A pipeline service orchestrates LLM extraction, schema validation, retry with exponential backoff, and deterministic fallback before storing a terminal result and event history.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy, SQLite for local development, pytest, httpx, a fake LLM provider for tests.

---

### Task 1: Bootstrap the Repository Skeleton

**Files:**
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `tests/test_health.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_health.py -v`
Expected: FAIL because `app.main` or `/health` does not exist yet.

**Step 3: Write minimal implementation**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_health.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md pyproject.toml app/__init__.py app/main.py tests/test_health.py
git commit -m "chore: bootstrap reliable llm intake service"
```

### Task 2: Define Core Enums and Intake Schemas

**Files:**
- Create: `app/core/enums.py`
- Create: `app/core/schemas.py`
- Create: `tests/test_schemas.py`

**Step 1: Write the failing test**

```python
from pydantic import ValidationError
from app.core.schemas import CreateJobRequest

def test_create_job_request_accepts_supported_task_type():
    payload = CreateJobRequest(task_type="resume_intake", input_text="Alice worked at ACME")
    assert payload.task_type == "resume_intake"

def test_create_job_request_rejects_unknown_task_type():
    try:
        CreateJobRequest(task_type="unknown", input_text="x")
        assert False
    except ValidationError:
        assert True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_schemas.py -v`
Expected: FAIL because schemas do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- `JobStatus` enum with `pending`, `running`, `succeeded`, `needs_review`, `failed`
- `TaskType` enum with `resume_intake`, `support_ticket_intake`
- `CreateJobRequest`
- `CreateJobResponse`
- `ResumeIntakeResult`
- `SupportTicketIntakeResult`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_schemas.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/core/enums.py app/core/schemas.py tests/test_schemas.py
git commit -m "feat: add job enums and intake schemas"
```

### Task 3: Add Database Base, Models, and Session Setup

**Files:**
- Create: `app/db/base.py`
- Create: `app/db/models.py`
- Create: `app/db/session.py`
- Create: `tests/test_db_models.py`

**Step 1: Write the failing test**

```python
from app.db.models import IntakeJob
from app.core.enums import JobStatus

def test_intake_job_defaults_to_pending():
    job = IntakeJob(task_type="resume_intake", idempotency_key="abc", input_text="hello")
    assert job.status == JobStatus.PENDING
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_db_models.py -v`
Expected: FAIL because models are missing.

**Step 3: Write minimal implementation**

Implement:
- SQLAlchemy base
- `IntakeJob` model
- `IntakeJobEvent` model
- SQLite session factory for local development and tests

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_db_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/db/base.py app/db/models.py app/db/session.py tests/test_db_models.py
git commit -m "feat: add intake job persistence models"
```

### Task 4: Build the Idempotent Job Creation Service

**Files:**
- Create: `app/services/idempotency.py`
- Create: `tests/test_idempotency.py`

**Step 1: Write the failing test**

```python
def test_duplicate_idempotency_key_returns_existing_job():
    ...
```

Test behavior:
- first request creates a job
- second request with same key and task type returns the same job ID
- second request does not create a duplicate row

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_idempotency.py -v`
Expected: FAIL because service logic is missing.

**Step 3: Write minimal implementation**

Implement a service that:
- looks up existing job by idempotency key and task type
- creates a new job only when no match exists
- records a `job_created` event

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_idempotency.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/idempotency.py tests/test_idempotency.py
git commit -m "feat: add idempotent intake job creation"
```

### Task 5: Implement the LLM Client Contract and Fake Provider

**Files:**
- Create: `app/services/llm_client.py`
- Create: `tests/test_llm_client.py`

**Step 1: Write the failing test**

```python
from app.services.llm_client import FakeLLMClient

def test_fake_client_returns_stubbed_response():
    client = FakeLLMClient(responses=['{"name": "Alice"}'])
    result = client.extract("prompt", "input")
    assert result == '{"name": "Alice"}'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_client.py -v`
Expected: FAIL because client contract is missing.

**Step 3: Write minimal implementation**

Implement:
- `LLMClient` protocol or abstract base
- `FakeLLMClient`
- placeholder real client interface for future provider wiring

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/llm_client.py tests/test_llm_client.py
git commit -m "feat: add llm client abstraction and fake provider"
```

### Task 6: Implement Validation and Repair Helpers

**Files:**
- Create: `app/services/validators.py`
- Create: `app/services/repair.py`
- Create: `tests/test_validation_and_repair.py`

**Step 1: Write the failing test**

```python
def test_validation_rejects_missing_required_fields():
    ...

def test_repair_extracts_json_object_from_wrapped_text():
    ...
```

Test behavior:
- invalid payload raises a structured validation error
- wrapped output such as `"Here is the JSON: {...}"` can be repaired into raw JSON before re-validation

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_validation_and_repair.py -v`
Expected: FAIL because validation and repair utilities do not exist.

**Step 3: Write minimal implementation**

Implement:
- JSON parsing helper
- schema validation helper
- lightweight repair function that extracts the first JSON object

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_validation_and_repair.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/validators.py app/services/repair.py tests/test_validation_and_repair.py
git commit -m "feat: add validation and repair helpers"
```

### Task 7: Implement Pipeline Retry with Exponential Backoff

**Files:**
- Create: `app/services/pipeline.py`
- Create: `tests/test_pipeline_retry.py`

**Step 1: Write the failing test**

```python
def test_pipeline_retries_on_invalid_llm_output_and_then_succeeds():
    ...
```

Test behavior:
- attempt 1 returns invalid output
- attempt 2 returns valid output
- final result is `succeeded`
- attempt count is `2`
- validation failure event is recorded

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_retry.py -v`
Expected: FAIL because pipeline logic is missing.

**Step 3: Write minimal implementation**

Implement pipeline behavior:
- set job to `running`
- call LLM client
- validate output
- back off and retry on transient or validation failure
- record per-attempt events

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline_retry.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/pipeline.py tests/test_pipeline_retry.py
git commit -m "feat: add retrying intake pipeline"
```

### Task 8: Implement Deterministic Fallback and Review State

**Files:**
- Create: `app/services/fallback.py`
- Create: `tests/test_pipeline_fallback.py`

**Step 1: Write the failing test**

```python
def test_pipeline_marks_job_needs_review_when_fallback_is_partial():
    ...
```

Test behavior:
- LLM keeps failing or omits critical fields
- fallback extracts only partial information
- job ends in `needs_review`
- partial normalized output is preserved

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_fallback.py -v`
Expected: FAIL because fallback logic is missing.

**Step 3: Write minimal implementation**

Implement:
- deterministic fallback extractors for `resume_intake` and `support_ticket_intake`
- review decision logic based on missing critical fields or low confidence

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline_fallback.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/fallback.py tests/test_pipeline_fallback.py
git commit -m "feat: add fallback and review state handling"
```

### Task 9: Expose Job Creation and Retrieval APIs

**Files:**
- Create: `app/api/routes_jobs.py`
- Modify: `app/main.py`
- Create: `tests/test_api_jobs.py`

**Step 1: Write the failing test**

```python
def test_create_job_returns_job_id_and_pending_or_terminal_state():
    ...

def test_get_job_returns_normalized_output_and_events():
    ...
```

Test behavior:
- `POST /v1/intake/jobs` accepts task type, input text, and idempotency key
- `GET /v1/intake/jobs/{job_id}` returns status, attempts, result, and event trail

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_jobs.py -v`
Expected: FAIL because routes are not mounted.

**Step 3: Write minimal implementation**

Implement:
- create job route
- get job route
- dependency wiring for db session and pipeline service

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_jobs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/api/routes_jobs.py app/main.py tests/test_api_jobs.py
git commit -m "feat: add intake job api routes"
```

### Task 10: Add a Thin Workflow Trace Layer

**Files:**
- Modify: `app/services/pipeline.py`
- Create: `tests/test_pipeline_trace.py`

**Step 1: Write the failing test**

```python
def test_pipeline_records_ordered_state_transition_trace():
    ...
```

Test behavior:
- pipeline events appear in deterministic order
- trace includes create, start, attempt, validation, fallback, and terminal outcome events

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_trace.py -v`
Expected: FAIL because the ordered trace contract is not enforced.

**Step 3: Write minimal implementation**

Implement:
- event sequencing helper
- stable event ordering contract
- clear event payload structure for debugging and demo output

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline_trace.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/pipeline.py tests/test_pipeline_trace.py
git commit -m "feat: add ordered pipeline trace events"
```

### Task 11: Document Local Run, Sample Inputs, and Portfolio Positioning

**Files:**
- Modify: `README.md`
- Create: `docs/sample-resume-input.txt`
- Create: `docs/sample-ticket-input.txt`
- Create: `docs/sample-job-output.json`

**Step 1: Write the failing test**

There is no automated test for documentation. Instead define manual acceptance:
- README explains problem, architecture, failure handling, and why this is a production-style LLM sample
- sample inputs and output are present and coherent

**Step 2: Run manual review to verify docs are incomplete**

Run: `sed -n '1,220p' README.md`
Expected: missing architecture, setup, and demo explanation

**Step 3: Write minimal implementation**

Add README sections for:
- project purpose
- architecture diagram
- run instructions
- API examples
- failure injection examples
- how this repo maps to AI engineering job requirements

**Step 4: Run manual review to verify docs are complete**

Run: `sed -n '1,260p' README.md`
Expected: clear setup, architecture, examples, and portfolio framing

**Step 5: Commit**

```bash
git add README.md docs/sample-resume-input.txt docs/sample-ticket-input.txt docs/sample-job-output.json
git commit -m "docs: add portfolio framing and sample pipeline artifacts"
```

### Task 12: Run Full Verification

**Files:**
- No file changes required unless fixes are needed

**Step 1: Run the full test suite**

Run: `pytest -v`
Expected: all tests PASS

**Step 2: Run a local API smoke test**

Run: `uvicorn app.main:app --reload`
Expected: server starts locally without import errors

**Step 3: Run a sample intake request**

Run:

```bash
curl -X POST http://127.0.0.1:8000/v1/intake/jobs \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-resume-1' \
  -d '{
    "task_type": "resume_intake",
    "input_text": "Alice Doe is a Python engineer with 5 years of experience..."
  }'
```

Expected: returns a job payload with status and job ID

**Step 4: Fetch the created job**

Run:

```bash
curl http://127.0.0.1:8000/v1/intake/jobs/<job_id>
```

Expected: returns normalized output plus event trace

**Step 5: Commit final verification fixes if needed**

```bash
git add .
git commit -m "test: finalize reliable llm intake verification"
```

