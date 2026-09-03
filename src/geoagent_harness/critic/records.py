"""Deterministic construction of immutable Critic records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from geoagent_harness.critic.schemas import (
    CriticResult,
    CriticResultRecord,
)
from geoagent_harness.redaction import redact_value


class CriticResultRecordError(RuntimeError):
    """Raised when a Critic result cannot be safely recorded."""


def canonical_critic_result_json(result: CriticResult) -> str:
    """Return canonical secret-redacted Critic-result JSON."""

    original = result.model_dump(mode="json")
    redacted = redact_value(original)
    if redacted != original:
        raise CriticResultRecordError(
            "Critic result contains content requiring redaction"
        )
    return json.dumps(
        original,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def critic_result_sha256(result: CriticResult) -> str:
    """Digest one complete validated Critic result."""

    return hashlib.sha256(
        canonical_critic_result_json(result).encode("utf-8")
    ).hexdigest()


def build_critic_result_record(
    *,
    result: CriticResult,
    recorded_at: datetime,
) -> CriticResultRecord:
    """Bind one validated Critic result without changing status."""

    try:
        return CriticResultRecord(
            task_id=result.task_id,
            deterministic_status=result.deterministic_status,
            critic_result_sha256=critic_result_sha256(result),
            critic_result=result,
            recorded_at=recorded_at,
        )
    except ValueError as exc:
        raise CriticResultRecordError(
            "Critic result record could not be constructed"
        ) from exc
