"""Tests for structured shared-model failure policy."""

from __future__ import annotations

import httpx
import pytest

from geoagent_harness.failures import (
    FailureCategory,
    FailureStage,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.model.client import (
    ModelClientError,
    SharedModelClient,
)
from geoagent_harness.model.schemas import (
    ChatMessage,
    ModelRequest,
)
from geoagent_harness.model.settings import (
    ModelSettings,
)


@pytest.fixture
def settings() -> ModelSettings:
    return ModelSettings(
        base_url="http://ollama.test/v1",
        model="qwen-test",
        timeout_seconds=10,
        max_tokens=128,
    )


@pytest.fixture
def model_request() -> ModelRequest:
    return ModelRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Return a test response.",
            )
        ],
        temperature=0.0,
        json_mode=True,
    )


def classify(
    error: ModelClientError,
):
    return failure_from_exception(
        error,
        stage=FailureStage.MODEL,
    )


def test_model_timeout_is_safe_read_only_retry(
    settings: ModelSettings,
    model_request: ModelRequest,
) -> None:
    def handler(
        http_request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ReadTimeout(
            "timed out",
            request=http_request,
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ModelClientError) as captured:
        client.complete(model_request)

    failure = classify(captured.value)

    assert failure.category == FailureCategory.TIMEOUT
    assert failure.code == "model_timeout"
    assert (
        failure.retry
        == RetryDisposition.SAFE_READ_ONLY
    )
    assert failure.exit_code == 3


def test_model_connection_failure_is_retryable(
    settings: ModelSettings,
    model_request: ModelRequest,
) -> None:
    def handler(
        http_request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "connection refused",
            request=http_request,
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ModelClientError) as captured:
        client.complete(model_request)

    failure = classify(captured.value)

    assert (
        failure.category
        == FailureCategory.DEPENDENCY_UNAVAILABLE
    )
    assert failure.code == "model_unavailable"
    assert (
        failure.retry
        == RetryDisposition.SAFE_READ_ONLY
    )
    assert failure.exit_code == 3


@pytest.mark.parametrize(
    "status_code",
    [401, 403],
)
def test_model_authentication_failure_is_not_retried(
    settings: ModelSettings,
    model_request: ModelRequest,
    status_code: int,
) -> None:
    def handler(
        http_request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code,
            request=http_request,
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ModelClientError) as captured:
        client.complete(model_request)

    failure = classify(captured.value)

    assert (
        failure.category
        == FailureCategory.CONFIGURATION
    )
    assert (
        failure.code
        == "model_authentication_failed"
    )
    assert failure.retry == RetryDisposition.NEVER
    assert failure.exit_code == 2


@pytest.mark.parametrize(
    "status_code",
    [408, 429, 500, 503],
)
def test_temporary_model_http_failure_is_retryable(
    settings: ModelSettings,
    model_request: ModelRequest,
    status_code: int,
) -> None:
    def handler(
        http_request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code,
            request=http_request,
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ModelClientError) as captured:
        client.complete(model_request)

    failure = classify(captured.value)

    assert (
        failure.category
        == FailureCategory.DEPENDENCY_UNAVAILABLE
    )
    assert failure.code == "model_http_unavailable"
    assert (
        failure.retry
        == RetryDisposition.SAFE_READ_ONLY
    )
    assert failure.exit_code == 3


def test_nonretryable_model_http_rejection(
    settings: ModelSettings,
    model_request: ModelRequest,
) -> None:
    def handler(
        http_request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            400,
            request=http_request,
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ModelClientError) as captured:
        client.complete(model_request)

    failure = classify(captured.value)

    assert (
        failure.category
        == FailureCategory.EXTERNAL_RESPONSE_INVALID
    )
    assert failure.code == "model_http_error"
    assert failure.retry == RetryDisposition.NEVER
    assert failure.exit_code == 4


def test_invalid_model_response_is_not_retried(
    settings: ModelSettings,
    model_request: ModelRequest,
) -> None:
    def handler(
        http_request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            request=http_request,
            json={
                "choices": [],
            },
        )

    client = SharedModelClient(
        settings,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ModelClientError) as captured:
        client.complete(model_request)

    failure = classify(captured.value)

    assert (
        failure.category
        == FailureCategory.EXTERNAL_RESPONSE_INVALID
    )
    assert failure.code == "model_invalid_response"
    assert failure.retry == RetryDisposition.NEVER
    assert failure.exit_code == 4