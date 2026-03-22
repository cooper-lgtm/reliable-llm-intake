from app.services.llm_client import FakeLLMClient


def test_fake_client_returns_stubbed_response():
    client = FakeLLMClient(responses=['{"name": "Alice"}'])

    result = client.extract("prompt", "input")

    assert result == '{"name": "Alice"}'
