"""Controlled client for the shared OpenAI-compatible model endpoint."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError

from geoagent_harness.failures import (
    FailureCategory,
    GeoAgentError,
    RetryDisposition,
)
from geoagent_harness.model.schemas import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.model.settings import ModelSettings


class ModelClientError(GeoAgentError):
    """Structured failure from the shared model client."""

    @classmethod
    def timeout(cls) -> ModelClientError:
        return cls(
            "Shared model request timed out",
            code="model_timeout",
            category=FailureCategory.TIMEOUT,
            retry=RetryDisposition.SAFE_READ_ONLY,
        )

    @classmethod
    def unavailable(cls) -> ModelClientError:
        return cls(
            "Shared model endpoint is unavailable",
            code="model_unavailable",
            category=(
                FailureCategory.DEPENDENCY_UNAVAILABLE
            ),
            retry=RetryDisposition.SAFE_READ_ONLY,
        )

    @classmethod
    def http_status(
        cls,
        status_code: int,
    ) -> ModelClientError:
        if status_code in {401, 403}:
            return cls(
                (
                    "Shared model authentication or "
                    "authorization failed"
                ),
                code="model_authentication_failed",
                category=FailureCategory.CONFIGURATION,
                retry=RetryDisposition.NEVER,
            )

        if (
            status_code in {408, 429}
            or status_code >= 500
        ):
            return cls(
                (
                    "Shared model is temporarily unavailable "
                    f"(HTTP {status_code})"
                ),
                code="model_http_unavailable",
                category=(
                    FailureCategory.DEPENDENCY_UNAVAILABLE
                ),
                retry=RetryDisposition.SAFE_READ_ONLY,
            )

        return cls(
            f"Shared model rejected the request "
            f"(HTTP {status_code})",
            code="model_http_error",
            category=(
                FailureCategory.EXTERNAL_RESPONSE_INVALID
            ),
            retry=RetryDisposition.NEVER,
        )

    @classmethod
    def invalid_response(cls) -> ModelClientError:
        return cls(
            "Shared model returned an invalid response",
            code="model_invalid_response",
            category=(
                FailureCategory.EXTERNAL_RESPONSE_INVALID
            ),
            retry=RetryDisposition.NEVER,
        )


class SharedModelClient:
    """Call the configured model without exposing shell or GIS tools."""

    def __init__(
        self,
        settings: ModelSettings,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def complete(self, request: ModelRequest) -> ModelResult:
        """Send a validated, non-streaming chat-completion request."""

        payload = {
            "model": self._settings.model,
            "messages": [
                message.model_dump(mode="json")
                for message in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": self._settings.max_tokens,
            "stream": False,
        }

        if request.json_mode:
            payload["response_format"] = {
                "type": "json_object",
            }

        try:
            with httpx.Client(
                timeout=self._settings.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = client.post(
                    (
                        f"{self._settings.base_url}"
                        "/chat/completions"
                    ),
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelClientError.timeout() from exc
        except httpx.HTTPStatusError as exc:
            raise ModelClientError.http_status(
                exc.response.status_code
            ) from exc
        except httpx.RequestError as exc:
            raise ModelClientError.unavailable() from exc

        try:
            body: dict[str, Any] = response.json()
            choice = body["choices"][0]
            content = choice["message"]["content"]
            usage = body.get("usage", {})

            if (
                not isinstance(content, str)
                or not content.strip()
            ):
                raise ValueError(
                    "model content is empty"
                )

            return ModelResult(
                model=str(
                    body.get(
                        "model",
                        self._settings.model,
                    )
                ),
                content=content.strip(),
                finish_reason=choice.get(
                    "finish_reason"
                ),
                prompt_tokens=usage.get(
                    "prompt_tokens"
                ),
                completion_tokens=usage.get(
                    "completion_tokens"
                ),
            )
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            raise ModelClientError.invalid_response() from exc