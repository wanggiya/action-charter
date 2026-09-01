"""Human review decisions for verified Builder promotions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from geoagent_harness.builder.promotion_verification import (
    BuilderPromotionVerificationError,
    verify_builder_promotion_bundle,
)
from geoagent_harness.builder.promotion_verification_storage import (
    BuilderPromotionVerificationStorageError,
    builder_promotion_verification_sha256,
    load_builder_promotion_verification,
)
from geoagent_harness.builder.schemas import (
    BuilderActivationReviewDecision,
)


class BuilderActivationReviewError(RuntimeError):
    """Raised when activation review cannot be created."""


def _safe_verification_file(
    verification_file: Path,
    *,
    verification_root: Path,
) -> Path:
    try:
        root = verification_root.resolve(
            strict=True
        )
        candidate = (
            verification_file
            if verification_file.is_absolute()
            else root / verification_file
        )
        safe_file = candidate.resolve(
            strict=True
        )
    except OSError as exc:
        raise BuilderActivationReviewError(
            "Builder activation review could not "
            "resolve its verification evidence"
        ) from exc

    if root not in safe_file.parents:
        raise BuilderActivationReviewError(
            "Builder activation-review verification "
            "file escaped its root"
        )

    return safe_file


def create_builder_activation_review_decision(
    *,
    verification_file: Path,
    verification_root: Path,
    promotion_root: Path,
    plan_root: Path,
    decision_id: str,
    reviewer_id: str,
    decided_at: datetime,
    decision: Literal["approved", "rejected"],
    rationale: str,
) -> BuilderActivationReviewDecision:
    """Review one exact verified bundle without activating it."""

    try:
        verification = (
            load_builder_promotion_verification(
                verification_file,
                verification_root=verification_root,
            )
        )
        safe_verification_file = (
            _safe_verification_file(
                verification_file,
                verification_root=(
                    verification_root
                ),
            )
        )
    except BuilderPromotionVerificationStorageError as exc:
        raise BuilderActivationReviewError(
            "Builder activation review could not "
            "verify its persisted evidence"
        ) from exc

    verification_digest = (
        builder_promotion_verification_sha256(
            verification
        )
    )

    try:
        current = verify_builder_promotion_bundle(
            promotion_directory=Path(
                verification.promotion_directory
            ),
            promotion_root=promotion_root,
            plan_file=Path(
                verification.plan_file
            ),
            plan_root=plan_root,
        )
    except BuilderPromotionVerificationError as exc:
        raise BuilderActivationReviewError(
            "Builder activation review could not "
            "reverify its promotion bundle"
        ) from exc

    if current != verification:
        raise BuilderActivationReviewError(
            "Builder activation-review verification "
            "does not match the current bundle"
        )

    approved = decision == "approved"

    try:
        return BuilderActivationReviewDecision(
            decision_id=decision_id,
            task_id=verification.task_id,
            reviewer_id=reviewer_id,
            decided_at=decided_at,
            decision=decision,
            rationale=rationale,
            verification_sha256=(
                verification_digest
            ),
            verification_file=(
                safe_verification_file.as_posix()
            ),
            promotion_plan_sha256=(
                verification.promotion_plan_sha256
            ),
            candidate_tree_sha256=(
                verification.candidate_tree_sha256
            ),
            promotion_directory=(
                verification.promotion_directory
            ),
            reviewed_paths=sorted(
                verification.verified_paths
            ),
            approval_granted=approved,
            activation_planning_authorized=(
                approved
            ),
        )
    except ValueError as exc:
        raise BuilderActivationReviewError(
            "Builder activation-review decision "
            "failed validation"
        ) from exc
