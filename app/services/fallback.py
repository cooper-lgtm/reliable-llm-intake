from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
YEARS_PATTERN = re.compile(r"\b(\d+)\s+years?\b", re.IGNORECASE)
NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")


def run_fallback(task_type: str, input_text: str) -> dict:
    if task_type == "resume_intake":
        return _fallback_resume_intake(input_text)
    if task_type == "support_ticket_intake":
        return _fallback_support_ticket_intake(input_text)
    return {}


def _fallback_resume_intake(input_text: str) -> dict:
    result: dict[str, str | int] = {}

    name_match = NAME_PATTERN.search(input_text)
    if name_match:
        result["name"] = name_match.group(1)

    email_match = EMAIL_PATTERN.search(input_text)
    if email_match:
        result["email"] = email_match.group(0)

    years_match = YEARS_PATTERN.search(input_text)
    if years_match:
        result["years_experience"] = int(years_match.group(1))

    return result


def _fallback_support_ticket_intake(input_text: str) -> dict:
    result: dict[str, str] = {}

    name_match = NAME_PATTERN.search(input_text)
    if name_match:
        result["customer_name"] = name_match.group(1)

    stripped = input_text.strip()
    if stripped:
        result["issue_summary"] = stripped[:160]

    lower_text = input_text.lower()
    if "urgent" in lower_text or "sev1" in lower_text or "high priority" in lower_text:
        result["priority"] = "high"
    elif "low priority" in lower_text or "minor" in lower_text:
        result["priority"] = "low"
    elif stripped:
        result["priority"] = "unknown"

    return result
