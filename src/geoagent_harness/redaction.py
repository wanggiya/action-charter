"""Shared secret-redaction utilities."""

from __future__ import annotations

import re
from typing import Any


_SECRET_KEYS = frozenset(
    {
        "password",
        "postgres_password",
        "database_url",
        "connection_string",
        "token",
        "api_key",
        "secret",
    }
)

_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b("
    r"(?:postgres_)?password"
    r"|database_url"
    r"|connection_string"
    r"|(?:ollama_)?api[_-]?key"
    r"|(?:access|auth)[_-]?token"
    r"|token"
    r"|secret"
    r")"
    r"\s*[:=]\s*"
    r"[^\s,;]+"
)

_DATABASE_URL_PATTERN = re.compile(
    r"(?i)(postgres(?:ql)?(?:\+\w+)?://[^:\s/]+:)"
    r"[^@\s/]+(@)"
)


def redact_text(value: str) -> str:
    """Redact common secret forms from free text."""
    redacted = _ASSIGNMENT_PATTERN.sub(
        lambda match: (
            f"{match.group(1)}=[REDACTED]"
        ),
        value,
    )

    return _DATABASE_URL_PATTERN.sub(
        r"\1[REDACTED]\2",
        redacted,
    )


def redact_value(value: Any) -> Any:
    """Recursively redact sensitive structured values."""
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        return [
            redact_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            redact_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}

        for key, item in value.items():
            normalized = str(key).lower()

            if normalized in _SECRET_KEYS:
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_value(item)

        return redacted

    return value