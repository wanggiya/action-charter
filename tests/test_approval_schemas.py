from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from geoagent_harness.approvals.schemas import (
    ApprovalRecord,
)

NOW = datetime(
    2026,
    8,
    9,
    12,
    0,
    tzinfo=timezone.utc,
)


def valid_record() -> dict:
    return {
        "schema_version": "1.0",
        "approval_id": (
            "approval-20260809t120000z-1234abcd"
        ),
        "plan_sha256": "a" * 64,
        "decision": "approved",
        "step_ids": ["step_2"],
        "approver": "local-user",
        "reason": "Approved controlled table creation.",
        "human_corrections": [],
        "created_at": NOW,
        "expires_at": NOW + timedelta(hours=1),
        "secrets_redacted": True,
    }


def test_valid_approval_record() -> None:
    record = ApprovalRecord.model_validate(
        valid_record()
    )

    assert record.decision == "approved"
    assert record.step_ids == ["step_2"]


def test_invalid_digest_is_rejected() -> None:
    payload = valid_record()
    payload["plan_sha256"] = "not-a-digest"

    with pytest.raises(ValidationError):
        ApprovalRecord.model_validate(payload)


def test_duplicate_steps_are_rejected() -> None:
    payload = valid_record()
    payload["step_ids"] = [
        "step_2",
        "step_2",
    ]

    with pytest.raises(
        ValidationError,
        match="duplicates",
    ):
        ApprovalRecord.model_validate(payload)


def test_expiration_must_follow_creation() -> None:
    payload = valid_record()
    payload["expires_at"] = NOW

    with pytest.raises(
        ValidationError,
        match="later",
    ):
        ApprovalRecord.model_validate(payload)


def test_secrets_redacted_cannot_be_false() -> None:
    payload = valid_record()
    payload["secrets_redacted"] = False

    with pytest.raises(ValidationError):
        ApprovalRecord.model_validate(payload)