import httpx
import pytest

from geoagent_harness.model.client import (
    ModelClientError,
    SharedModelClient,
)
from geoagent_harness.model.schemas import (
    ChatMessage,
    ModelRequest,
)
from geoagent_harness.model.settings import ModelSettings


@pytest.fixture
def settings() -> ModelSettings:
    return ModelSettings(
        base_url="http://ollama.test/v1",
        model="qwen-test",
        timeout_seconds=10,
        max_tokens=256,
    )


def test_model_client_returns_structured_result(
    settings: ModelSettings,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"

        payload = __import__("json").loads(
            request.content.decode("utf-8")
        )

        assert payload["model"] == "qwen-test"
        assert payload["stream"] is False
        
        assert "response_format" not in payload
        
        # assert payload["response_format"] == {
        #     "type": "json_object",
        # }

        return httpx.Response(
            200,
            json={
                "model": "qwen-test",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "GEOAGENT_OLLAMA_OK",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 8,
                    "completion_tokens": 4,
                },
            },
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    result = client.complete(
        ModelRequest(
            messages=[
                ChatMessage(
                    role="user",
                    content="Return the test phrase.",
                )
            ]
        )
    )

    assert result.content == "GEOAGENT_OLLAMA_OK"
    assert result.model == "qwen-test"
    assert result.finish_reason == "stop"
    assert result.prompt_tokens == 8
    assert result.completion_tokens == 4


def test_model_client_rejects_invalid_response(
    settings: ModelSettings,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"unexpected": "response"},
        )
    )

    client = SharedModelClient(
        settings,
        transport=transport,
    )

    with pytest.raises(
        ModelClientError,
        match="invalid response",
    ):
        client.complete(
            ModelRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content="Test",
                    )
                ]
            )
        )


def test_model_client_redacts_connection_details(
    settings: ModelSettings,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "connection string containing sensitive details",
            request=request,
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        ModelClientError,
        match="endpoint is unavailable",
    ) as captured:
        client.complete(
            ModelRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content="Test",
                    )
                ]
            )
        )

    assert "sensitive details" not in str(captured.value)

def test_model_client_sends_json_mode(
    settings: ModelSettings,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = __import__("json").loads(
            request.content.decode("utf-8")
        )

        assert payload["response_format"] == {
            "type": "json_object",
        }

        return httpx.Response(
            200,
            json={
                "model": "qwen-test",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": '{"status":"ok"}',
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    result = client.complete(
        ModelRequest(
            messages=[
                ChatMessage(
                    role="user",
                    content="Return JSON.",
                )
            ],
            json_mode=True,
        )
    )

    assert result.content == '{"status":"ok"}'