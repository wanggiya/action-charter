"""Secret redaction for context sent to models."""

from __future__ import annotations

import re
from typing import Any

SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key)"
    r"\s*[:=]\s*[^\s,;]+"
)

CREDENTIAL_URL = re.compile(
    r"(?i)\b((?:postgres(?:ql)?|https?|mysql)://)"
    r"[^/\s:@]+:[^@\s/]+@"
)


def redact_text(value: str) -> str:
    """Remove common secret representations from text."""

    value = SECRET_ASSIGNMENT.sub(
        lambda match: (
            f"{match.group(1)}=[REDACTED]"
        ),
        value,
    )

    return CREDENTIAL_URL.sub(
        lambda match: (
            f"{match.group(1)}[REDACTED]@"
        ),
        value,
    )


def redact_value(value: Any) -> Any:
    """Recursively redact strings in JSON-like content."""

    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        return [redact_value(item) for item in value]

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}

        for key, item in value.items():
            if any(
                marker in key.lower()
                for marker in (
                    "password",
                    "passwd",
                    "token",
                    "secret",
                    "api_key",
                    "apikey",
                )
            ):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_value(item)

        return redacted

    return value