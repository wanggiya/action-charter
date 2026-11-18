"""Controlled client for the shared OpenAI-compatible model endpoint."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError

from geoagent_harness.contracts.failures import FailureCategory, GeoAgentError, RetryDisposition
from geoagent_harness.platform.model_gateway.schemas import ModelRequest, ModelResult
from geoagent_harness.platform.model_settings import ModelSettings


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

        from geoagent_harness.platform.model_gateway.telemetry import model_call
        from geoagent_harness.platform.model_gateway.egress import evaluate
        request=request.model_copy(deep=True)
        decision=evaluate(request,self._settings)
        with model_call(request,self._settings,decision=decision) as record:
            if record is not None:record['network_dispatch']='not_attempted'
            if not decision.allowed:
                raise ModelClientError('Provider data allowance blocks this request',code='model_data_class_blocked',category=FailureCategory.CONFIGURATION,retry=RetryDisposition.NEVER)
            result=self._complete(request,record=record)
            if record is not None:
                record.update(prompt_tokens=result.prompt_tokens,completion_tokens=result.completion_tokens,finish_reason=result.finish_reason,response_format=result.response_format)
            return result

    def _complete(self, request: ModelRequest, *, record=None) -> ModelResult:
        from geoagent_harness.platform.model_gateway.profiles import headers
        auth=headers(self._settings)
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

        if self._settings.reasoning_effort is not None:
            payload["reasoning_effort"] = self._settings.reasoning_effort

        response_format = "text"
        if request.response_schema is not None and self._settings.response_format == "json_schema":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "actioncharter_reply", "schema": request.response_schema},
            }
            response_format = "json_schema"
        elif self._settings.response_format!='text' and (request.json_mode or request.response_schema is not None):
            payload["response_format"] = {
                "type": "json_object",
            }
            response_format = "json_object"

        try:
            with httpx.Client(
                timeout=min(self._settings.timeout_seconds, request.timeout_seconds) if request.timeout_seconds is not None else self._settings.timeout_seconds,
                transport=self._transport,
                headers=auth,follow_redirects=False,trust_env=False,
            ) as client:
                if record is not None:record['network_dispatch']='attempted'
                response = client.post(
                    (
                        f"{self._settings.base_url}"
                        "/chat/completions"
                    ),
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelClientError.timeout() from None
        except httpx.HTTPStatusError as exc:
            if response_format in {'json_schema','json_object'} and exc.response.status_code in {400, 422}:
                detail = exc.response.text[:4096].casefold()
                if "response_format" in detail or "json_schema" in detail or "json_object" in detail or "failed to parse grammar" in detail or ("schema" in detail and any(word in detail for word in ("unsupported", "invalid", "not support"))):
                    raise ModelClientError("Model endpoint rejected schema-constrained output", code="model_response_format_rejected", category=FailureCategory.CONFIGURATION, retry=RetryDisposition.NEVER) from None
            raise ModelClientError.http_status(
                exc.response.status_code
            ) from None
        except httpx.RequestError as exc:
            raise ModelClientError.unavailable() from None

        try:
            body: dict[str, Any] = response.json()
            choice = body["choices"][0]
            content = choice["message"]["content"]
            usage = body.get("usage", {})
            if auth and any(isinstance(v,str) and auth['Authorization'][7:] in v
                    for v in (content,body.get('model'),choice.get('finish_reason'))):
                raise ValueError('Model response contained private authentication material')

            if (
                not isinstance(content, str)
                or not content.strip()
            ):
                raise ValueError(
                    "model content is empty"
                )

            return ModelResult(
                provider='ollama-openai-compatible' if self._settings.listing=='ollama' else 'openai-compatible',
                provider_profile_id=self._settings.provider_profile_id,
                model=str(
                    body.get(
                        "model",
                        self._settings.model,
                    )
                ),
                content=content.strip(),
                response_format=response_format,
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
            raise ModelClientError.invalid_response() from None
