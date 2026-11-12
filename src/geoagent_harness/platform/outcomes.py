"""Existing redacted, byte-bounded outcome projection shared by transports."""
import json
from geoagent_harness.contracts.redaction import redact_value

MAX_INTERFACE_OUTCOME_BYTES = 16_384


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

