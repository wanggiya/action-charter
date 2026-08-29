"""Read-only promotion planning for approved Builder files."""

from __future__ import annotations

import hashlib
from pathlib import Path

from geoagent_harness.builder.inspection import (
    BuilderCandidateInspectionError,
    inspect_builder_candidate,
)
from geoagent_harness.builder.review_decision_storage import (
    BuilderReviewDecisionStorageError,
    load_builder_review_decision,
)
from geoagent_harness.builder.review_storage import (
    BuilderReviewStorageError,
    load_builder_review_package,
)
from geoagent_harness.builder.schemas import (
    BuilderPromotionFile,
    BuilderPromotionPlan,
)
from geoagent_harness.skill_definitions import (
    candidate_tree_sha256,
)


class BuilderPromotionPlanError(RuntimeError):
    """Raised when Builder promotion cannot be planned."""


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderPromotionPlanError(
            "Builder promotion source could not be read"
        ) from exc


def _project_root_path(
    project_root: Path,
) -> Path:
    if project_root.is_symlink():
        raise BuilderPromotionPlanError(
            "Builder promotion project root "
            "cannot be a symlink"
        )

    try:
        root = project_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionPlanError(
            "Builder promotion project root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPromotionPlanError(
            "Builder promotion project root "
            "must be a directory"
        )

    return root


def plan_builder_promotion(
    *,
    decision_file: Path,
    decision_root: Path,
    review_root: Path,
    candidate_root: Path,
    project_root: Path,
) -> BuilderPromotionPlan:
    """Plan exact approved writes without performing them."""

    try:
        decision, decision_digest, safe_decision = (
            load_builder_review_decision(
                decision_file,
                decision_root=decision_root,
            )
        )
        review, review_digest, safe_review = (
            load_builder_review_package(
                Path(decision.review_file),
                review_root=review_root,
            )
        )
        inspection = inspect_builder_candidate(
            candidate_path=Path(
                review.candidate_path
            ),
            candidate_root=candidate_root,
        )
    except (
        BuilderCandidateInspectionError,
        BuilderReviewDecisionStorageError,
        BuilderReviewStorageError,
    ) as exc:
        raise BuilderPromotionPlanError(
            "Builder promotion inputs could not "
            "be verified"
        ) from exc

    if (
        decision.decision != "approved"
        or not decision.approval_granted
        or not decision.promotion_planning_authorized
    ):
        raise BuilderPromotionPlanError(
            "Builder decision does not authorize "
            "promotion planning"
        )

    if (
        decision.review_package_sha256
        != review_digest
    ):
        raise BuilderPromotionPlanError(
            "Builder decision does not match review digest"
        )

    if (
        decision.task_id != review.task_id
        or decision.generation_sha256
        != review.generation_sha256
        or decision.candidate_tree_sha256
        != review.candidate_tree_sha256
    ):
        raise BuilderPromotionPlanError(
            "Builder decision identities do not "
            "match review"
        )

    if (
        inspection.task_id != review.task_id
        or inspection.generation_sha256
        != review.generation_sha256
        or inspection.candidate_tree_sha256
        != review.candidate_tree_sha256
    ):
        raise BuilderPromotionPlanError(
            "Builder candidate identities do not "
            "match review"
        )

    approved_paths = sorted(
        decision.approved_paths
    )

    if not approved_paths:
        raise BuilderPromotionPlanError(
            "Builder decision approved no files"
        )

    if not set(approved_paths).issubset(
        set(review.proposed_destinations)
    ):
        raise BuilderPromotionPlanError(
            "Builder decision contains unreviewed paths"
        )

    manifest_files = {
        file.path: file
        for file in review.candidate_manifest.files
    }
    candidate = Path(
        inspection.candidate_path
    )
    root = _project_root_path(project_root)
    files: list[BuilderPromotionFile] = []

    for relative_path in approved_paths:
        manifest_file = manifest_files.get(
            relative_path
        )

        if manifest_file is None:
            raise BuilderPromotionPlanError(
                "Approved Builder path is absent "
                "from candidate manifest"
            )

        unresolved_source = (
            candidate / relative_path
        )

        if unresolved_source.is_symlink():
            raise BuilderPromotionPlanError(
                "Builder promotion source cannot "
                "be a symlink"
            )

        try:
            source = unresolved_source.resolve(
                strict=True
            )
        except OSError as exc:
            raise BuilderPromotionPlanError(
                "Builder promotion source is missing"
            ) from exc

        if (
            candidate not in source.parents
            or not source.is_file()
        ):
            raise BuilderPromotionPlanError(
                "Builder promotion source escaped "
                "the candidate"
            )

        source_digest = _file_sha256(source)

        if (
            source_digest
            != manifest_file.content_sha256
        ):
            raise BuilderPromotionPlanError(
                "Builder promotion source digest "
                "does not match manifest"
            )

        unresolved_destination = (
            root / relative_path
        )

        if unresolved_destination.is_symlink():
            raise BuilderPromotionPlanError(
                "Builder promotion destination "
                "cannot be a symlink"
            )

        destination = (
            unresolved_destination.resolve()
        )

        if root not in destination.parents:
            raise BuilderPromotionPlanError(
                "Builder promotion destination "
                "escaped project root"
            )

        if destination.exists():
            raise BuilderPromotionPlanError(
                "Builder promotion destination "
                "already exists"
            )

        files.append(
            BuilderPromotionFile(
                kind=manifest_file.kind,
                source_path=(
                    source.relative_to(
                        candidate
                    ).as_posix()
                ),
                destination_path=(
                    destination.relative_to(
                        root
                    ).as_posix()
                ),
                sha256=source_digest,
            )
        )

    try:
        digest_after = candidate_tree_sha256(
            candidate
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise BuilderPromotionPlanError(
            "Builder candidate could not be rehashed"
        ) from exc

    if (
        digest_after
        != inspection.candidate_tree_sha256
    ):
        raise BuilderPromotionPlanError(
            "Builder candidate changed during "
            "promotion planning"
        )

    return BuilderPromotionPlan(
        task_id=review.task_id,
        decision_id=decision.decision_id,
        reviewer_id=decision.reviewer_id,
        review_package_sha256=review_digest,
        decision_sha256=decision_digest,
        generation_sha256=(
            review.generation_sha256
        ),
        candidate_tree_sha256=(
            review.candidate_tree_sha256
        ),
        candidate_path=candidate.as_posix(),
        project_root=root.as_posix(),
        review_file=safe_review.as_posix(),
        decision_file=safe_decision.as_posix(),
        files=files,
    )
