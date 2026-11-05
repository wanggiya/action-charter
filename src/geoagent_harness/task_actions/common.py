"""Transport-independent errors, project identity and bounded result projection."""
from __future__ import annotations
import json
from pathlib import Path
from geoagent_harness.redaction import redact_value

MAX_INTERFACE_OUTCOME_BYTES = 16_384


class InterfaceApiError(RuntimeError):
    """Raised when the bounded interface API cannot fulfill a request."""


def _trusted_root(project_root: Path) -> Path:
    try:
        resolved = project_root.resolve(strict=True)
    except OSError as exc:
        raise InterfaceApiError("trusted project root is unavailable") from exc
    if not resolved.is_dir():
        raise InterfaceApiError("trusted project root must be a directory")
    return resolved


def _bounded_outcome(value: object) -> object:
    """Return a redacted bounded result projection for interface inspection."""

    projected = redact_value(value)
    encoded = json.dumps(projected, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    limit = 128000 if isinstance(projected, dict) and isinstance(projected.get('table_analysis'), dict) else MAX_INTERFACE_OUTCOME_BYTES
    if len(encoded) > limit:
        return {
            "outcome_available": True,
            "projection_truncated": True,
            "message": "Outcome is too large for the interface projection; inspect durable evidence.",
        }
    return projected

# Preserve the historical exception identity for all callers.
TaskActionError = InterfaceApiError
