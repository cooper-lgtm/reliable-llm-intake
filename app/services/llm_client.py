from collections.abc import Sequence
from typing import Protocol


class LLMClient(Protocol):
    def extract(self, prompt: str, input_text: str) -> str:
        """Return raw model output for the given prompt and input."""


class FakeLLMClient:
    def __init__(self, responses: Sequence[str]):
        self._responses = list(responses)

    def extract(self, prompt: str, input_text: str) -> str:
        if not self._responses:
            raise RuntimeError("No fake LLM responses configured.")
        return self._responses.pop(0)


class PlaceholderLLMClient:
    def extract(self, prompt: str, input_text: str) -> str:
        raise NotImplementedError("Wire a real LLM provider here.")
