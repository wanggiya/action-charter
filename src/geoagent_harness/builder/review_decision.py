"""Typed human decisions for immutable Builder reviews."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from geoagent_harness.builder.review_storage import (
    BuilderReviewStorageError,
    load_builder_review_package,
)
from geoagent_harness.builder.schemas import (
    BuilderReviewDecision,
)


class BuilderReviewDecisionError(RuntimeError):
    """Raised when a Builder review decision is invalid."""


def create_builder_review_decision(
    *,
    review_file: Path,
    review_root: Path,
    decision_id: str,
    reviewer_id: str,
    decided_at: datetime,
    decision: Literal["approved", "rejected"],
    approved_paths: list[str],
    rationale: str,
) -> BuilderReviewDecision:
    """Bind one human decision to an exact review digest."""

    try:
        review, review_digest, safe_file = (
            load_builder_review_package(
                review_file,
                review_root=review_root,
            )
        )
    except BuilderReviewStorageError as exc:
        raise BuilderReviewDecisionError(
            "Builder review decision could not "
            "verify its review package"
        ) from exc

    reviewed_paths = sorted(
        review.proposed_destinations
    )
    selected_paths = sorted(approved_paths)

    if len(selected_paths) != len(
        set(selected_paths)
    ):
        raise BuilderReviewDecisionError(
            "Builder approved paths must be unique"
        )

    if not set(selected_paths).issubset(
        set(reviewed_paths)
    ):
        raise BuilderReviewDecisionError(
            "Builder approved paths were not reviewed"
        )

    approval_granted = decision == "approved"

    try:
        return BuilderReviewDecision(
            decision_id=decision_id,
            task_id=review.task_id,
            reviewer_id=reviewer_id,
            decided_at=decided_at,
            decision=decision,
            rationale=rationale,
            review_package_sha256=review_digest,
            review_file=safe_file.as_posix(),
            generation_sha256=(
                review.generation_sha256
            ),
            candidate_tree_sha256=(
                review.candidate_tree_sha256
            ),
            reviewed_paths=reviewed_paths,
            approved_paths=selected_paths,
            approval_granted=approval_granted,
            promotion_planning_authorized=(
                approval_granted
            ),
        )
    except ValueError as exc:
        raise BuilderReviewDecisionError(
            "Builder review decision failed validation"
        ) from exc
