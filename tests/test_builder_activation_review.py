"""Tests for Builder activation-review decisions."""

from __future__ import annotations

import json
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.builder import (
    BuilderActivationReviewDecision,
    BuilderActivationReviewError,
    builder_promotion_verification_sha256,
    create_builder_activation_review_decision,
    persist_builder_promotion_verification,
)
from tests.test_builder_promotion_verification_storage import (
    prepared_verification,
)


DECIDED_AT = datetime(
    2026,
    9,
    1,
    12,
    0,
    tzinfo=timezone.utc,
)


def prepared_persisted_verification(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = prepared_verification(
        tmp_path
    )

    persisted = (
        persist_builder_promotion_verification(
            prepared["verification"],
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
        )
    )

    return {
        **prepared,
        "verification_file": Path(
            persisted.verification_file
        ),
        "verification_sha256": (
            persisted.verification_sha256
        ),
    }


def create_decision(
    prepared: dict[str, object],
    *,
    decision: str = "approved",
    decided_at: datetime = DECIDED_AT,
) -> BuilderActivationReviewDecision:
    return create_builder_activation_review_decision(
        verification_file=prepared[
            "verification_file"
        ],
        verification_root=prepared[
            "verification_root"
        ],
        promotion_root=prepared[
            "promotion_root"
        ],
        plan_root=prepared["plan_root"],
        decision_id="activation-review-v1",
        reviewer_id="operator@example.com",
        decided_at=decided_at,
        decision=decision,
        rationale=(
            "Reviewed the exact immutable verification "
            "evidence and promoted bundle."
        ),
    )


def test_approves_exact_verified_bundle(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_verification(
        tmp_path
    )
    verification = prepared["verification"]

    result = create_decision(prepared)

    assert result.decision == "approved"
    assert result.task_id == verification.task_id
    assert (
        result.verification_sha256
        == prepared["verification_sha256"]
    )
    assert result.verification_sha256 == (
        builder_promotion_verification_sha256(
            verification
        )
    )
    assert (
        result.promotion_plan_sha256
        == verification.promotion_plan_sha256
    )
    assert (
        result.candidate_tree_sha256
        == verification.candidate_tree_sha256
    )
    assert (
        result.promotion_directory
        == verification.promotion_directory
    )
    assert result.reviewed_paths == sorted(
        verification.verified_paths
    )

    assert result.human_review_performed is True
    assert (
        result.verification_evidence_verified
        is True
    )
    assert result.bundle_reverified is True
    assert result.approval_granted is True
    assert (
        result.activation_planning_authorized
        is True
    )

    assert result.activation_performed is False
    assert result.files_copied is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is True
    assert result.execution_performed is False


def test_records_rejected_activation_review(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_verification(
        tmp_path
    )

    result = create_decision(
        prepared,
        decision="rejected",
    )

    assert result.decision == "rejected"
    assert result.approval_granted is False
    assert (
        result.activation_planning_authorized
        is False
    )
    assert result.human_review_performed is True
    assert result.bundle_reverified is True
    assert result.activation_performed is False
    assert result.implementation_trusted is False


def test_rejects_changed_bundle_after_verification(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_verification(
        tmp_path
    )
    verification = prepared["verification"]

    promoted_file = (
        Path(verification.promotion_directory)
        / "files"
        / verification.verified_paths[0]
    )
    promoted_file.write_text(
        '"""Changed before activation review."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationReviewError,
        match="could not reverify",
    ):
        create_decision(prepared)


def test_rejects_noncanonical_verification_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_verification(
        tmp_path
    )
    verification_file = Path(
        prepared["verification_file"]
    )

    payload = json.loads(
        verification_file.read_text(
            encoding="utf-8"
        )
    )
    verification_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationReviewError,
        match="persisted evidence",
    ):
        create_decision(prepared)


def test_rejects_naive_decision_timestamp(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_verification(
        tmp_path
    )

    with pytest.raises(
        BuilderActivationReviewError,
        match="failed validation",
    ):
        create_decision(
            prepared,
            decided_at=datetime(
                2026,
                9,
                1,
                12,
                0,
            ),
        )


def test_schema_rejects_inconsistent_approval(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_verification(
        tmp_path
    )
    decision = create_decision(prepared)
    payload = decision.model_dump(mode="json")
    payload["approval_granted"] = False

    with pytest.raises(
        ValidationError,
        match="approval conflicts",
    ):
        BuilderActivationReviewDecision.model_validate(
            payload
        )


def test_schema_rejects_unsorted_reviewed_paths(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_verification(
        tmp_path
    )
    decision = create_decision(prepared)
    payload = decision.model_dump(mode="json")
    payload["reviewed_paths"] = list(
        reversed(payload["reviewed_paths"])
    )

    with pytest.raises(
        ValidationError,
        match="must be sorted",
    ):
        BuilderActivationReviewDecision.model_validate(
            payload
        )
