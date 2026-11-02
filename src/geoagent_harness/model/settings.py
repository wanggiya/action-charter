"""Trusted configuration for the shared model endpoint."""

from __future__ import annotations

import os
from contextvars import ContextVar
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

# Set once at the interface request boundary; never mutate process environment.
selected_model: ContextVar[str | None] = ContextVar('selected_model', default=None)
selected_reasoning: ContextVar[str | None] = ContextVar('selected_reasoning', default=None)


class ModelSettingsError(ValueError):
    """Raised when model configuration is missing or unsafe."""


@dataclass(frozen=True)
class ModelSettings:
    """Non-secret settings for one shared model runtime."""

    base_url: str
    model: str
    timeout_seconds: float
    max_tokens: int
    reasoning_effort: str | None = None
    response_format: str = "json_schema"


def load_model_settings(
    environ: Mapping[str, str] | None = None,
) -> ModelSettings:
    """Load model settings from trusted process environment variables."""

    values = os.environ if environ is None else environ

    base_url = values.get(
        "MODEL_BASE_URL",
        "http://host.docker.internal:11434/v1",
    ).strip().rstrip("/")

    model = (selected_model.get() if environ is None else None) or values.get("MODEL_NAME", "").strip()

    if not model:
        raise ModelSettingsError("MODEL_NAME is required")

    parsed = urlparse(base_url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ModelSettingsError(
            "MODEL_BASE_URL must be a valid HTTP or HTTPS URL"
        )

    if not parsed.path.endswith("/v1"):
        raise ModelSettingsError(
            "MODEL_BASE_URL must end with /v1"
        )

    try:
        timeout_seconds = float(
            values.get("MODEL_TIMEOUT_SECONDS", "120")
        )
    except ValueError as exc:
        raise ModelSettingsError(
            "MODEL_TIMEOUT_SECONDS must be numeric"
        ) from exc

    if timeout_seconds <= 0 or timeout_seconds > 600:
        raise ModelSettingsError(
            "MODEL_TIMEOUT_SECONDS must be between 0 and 600"
        )

    try:
        max_tokens = int(values.get("MODEL_MAX_TOKENS", "1024"))
    except ValueError as exc:
        raise ModelSettingsError(
            "MODEL_MAX_TOKENS must be an integer"
        ) from exc

    if max_tokens < 1 or max_tokens > 32768:
        raise ModelSettingsError(
            "MODEL_MAX_TOKENS must be between 1 and 32768"
        )

    reasoning = values.get("MODEL_REASONING_EFFORT", "").strip() or None
    override=selected_reasoning.get() if environ is None else None
    if override and override!='environment':reasoning=None if override=='provider' else override
    if reasoning not in {None, "none", "low", "medium", "high"}:
        raise ModelSettingsError("MODEL_REASONING_EFFORT must be none, low, medium or high")
    response_format = values.get("MODEL_RESPONSE_FORMAT", "json_schema").strip()
    if response_format not in {"json_schema", "json_object"}:
        raise ModelSettingsError("MODEL_RESPONSE_FORMAT must be json_schema or json_object")
    return ModelSettings(
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
        max_tokens=max_tokens,
        reasoning_effort=reasoning,
        response_format=response_format,
    )
