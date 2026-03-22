import json
from typing import TypeVar

from pydantic import BaseModel


SchemaModel = TypeVar("SchemaModel", bound=BaseModel)


def parse_json_payload(raw_output: str) -> dict:
    payload = json.loads(raw_output)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object.")
    return payload


def validate_payload(schema: type[SchemaModel], payload: dict) -> SchemaModel:
    return schema.model_validate(payload)
