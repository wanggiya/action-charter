"""Controlled client for the shared OpenAI-compatible model endpoint."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError

from geoagent_harness.model.schemas import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.model.settings import ModelSettings


class ModelClientError(RuntimeError):
    """Raised when the shared model cannot return a valid response."""


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
                    f"{self._settings.base_url}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ModelClientError(
                "Shared model request timed out"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ModelClientError(
                f"Shared model returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise ModelClientError(
                "Shared model endpoint is unavailable"
            ) from exc

        try:
            body: dict[str, Any] = response.json()
            choice = body["choices"][0]
            content = choice["message"]["content"]
            usage = body.get("usage", {})

            if not isinstance(content, str) or not content.strip():
                raise ValueError("model content is empty")

            return ModelResult(
                model=str(body.get("model", self._settings.model)),
                content=content.strip(),
                finish_reason=choice.get("finish_reason"),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
            )
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            ValidationError,
        ) as exc:
            raise ModelClientError(
                "Shared model returned an invalid response"
            ) from exc