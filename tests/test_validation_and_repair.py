import pytest
from pydantic import ValidationError

from app.core.schemas import ResumeIntakeResult
from app.services.repair import extract_first_json_object
from app.services.validators import parse_json_payload, validate_payload


def test_validation_rejects_missing_required_fields():
    payload = parse_json_payload('{"name": "Alice"}')

    with pytest.raises(ValidationError):
        validate_payload(ResumeIntakeResult, payload)


def test_repair_extracts_json_object_from_wrapped_text():
    repaired = extract_first_json_object(
        'Here is the JSON: {"name": "Alice", "email": "alice@example.com", "years_experience": 5}',
    )

    result = validate_payload(ResumeIntakeResult, parse_json_payload(repaired))

    assert result.name == "Alice"
