"""Read-only activation planning for verified Builder bundles."""

from __future__ import annotations

import hashlib
from pathlib import Path

from geoagent_harness.builder.activation_review_storage import (
    BuilderActivationReviewDecisionStorageError,
    load_builder_activation_review_decision,
)
from geoagent_harness.builder.promotion_verification import (
    BuilderPromotionVerificationError,
    load_builder_promotion_manifest,
    verify_builder_promotion_bundle,
)
from geoagent_harness.builder.promotion_verification_storage import (
    BuilderPromotionVerificationStorageError,
    builder_promotion_verification_sha256,
    load_builder_promotion_verification,
)
from geoagent_harness.builder.schemas import (
    BuilderActivationFile,
    BuilderActivationPlan,
)


class BuilderActivationPlanError(RuntimeError):
    """Raised when Builder activation cannot be planned."""


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderActivationPlanError(
            "Builder activation source could not be read"
        ) from exc


def _project_root_path(
    project_root: Path,
) -> Path:
    if project_root.is_symlink():
        raise BuilderActivationPlanError(
            "Builder activation project root "
            "cannot be a symlink"
        )

    try:
        root = project_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderActivationPlanError(
            "Builder activation project root "
            "is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderActivationPlanError(
            "Builder activation project root "
            "must be a directory"
        )

    return root


def plan_builder_activation(
    *,
    activation_decision_file: Path,
    activation_decision_root: Path,
    verification_root: Path,
    promotion_root: Path,
    promotion_plan_root: Path,
    project_root: Path,
) -> BuilderActivationPlan:
    """Plan exact trusted writes without performing them."""

    try:
        (
            decision,
            decision_digest,
            safe_decision_file,
        ) = load_builder_activation_review_decision(
            activation_decision_file,
            decision_root=activation_decision_root,
        )

        verification = (
            load_builder_promotion_verification(
                Path(decision.verification_file),
                verification_root=verification_root,
            )
        )
    except (
        BuilderActivationReviewDecisionStorageError,
        BuilderPromotionVerificationStorageError,
    ) as exc:
        raise BuilderActivationPlanError(
            "Builder activation inputs could not "
            "be verified"
        ) from exc

    if (
        decision.decision != "approved"
        or not decision.approval_granted
        or not decision.activation_planning_authorized
    ):
        raise BuilderActivationPlanError(
            "Builder activation decision does not "
            "authorize activation planning"
        )

    verification_digest = (
        builder_promotion_verification_sha256(
            verification
        )
    )

    if (
        decision.verification_sha256
        != verification_digest
    ):
        raise BuilderActivationPlanError(
            "Builder activation decision does not "
            "match verification digest"
        )

    if (
        decision.task_id != verification.task_id
        or decision.promotion_plan_sha256
        != verification.promotion_plan_sha256
        or decision.candidate_tree_sha256
        != verification.candidate_tree_sha256
    ):
        raise BuilderActivationPlanError(
            "Builder activation identities do not "
            "match verification evidence"
        )

    if (
        decision.promotion_directory
        != verification.promotion_directory
    ):
        raise BuilderActivationPlanError(
            "Builder activation promotion directory "
            "does not match verification evidence"
        )

    reviewed_paths = sorted(
        decision.reviewed_paths
    )
    verified_paths = sorted(
        verification.verified_paths
    )

    if reviewed_paths != verified_paths:
        raise BuilderActivationPlanError(
            "Builder activation reviewed paths do not "
            "match verified bundle paths"
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
            plan_root=promotion_plan_root,
        )
    except BuilderPromotionVerificationError as exc:
        raise BuilderActivationPlanError(
            "Builder activation bundle could not "
            "be reverified"
        ) from exc

    if current != verification:
        raise BuilderActivationPlanError(
            "Builder activation verification does not "
            "match the current bundle"
        )

    root = _project_root_path(
        project_root
    )
    promotion_directory = Path(
        verification.promotion_directory
    )

    try:
        (
            manifest,
            safe_promotion_directory,
            _,
        ) = load_builder_promotion_manifest(
            promotion_directory,
            promotion_root=promotion_root,
        )
    except BuilderPromotionVerificationError as exc:
        raise BuilderActivationPlanError(
            "Builder activation manifest could not "
            "be loaded"
        ) from exc

    if (
        safe_promotion_directory
        != promotion_directory
    ):
        raise BuilderActivationPlanError(
            "Builder activation promotion path "
            "does not match verified bundle"
        )

    if (
        manifest.task_id != verification.task_id
        or manifest.decision_id
        != verification.decision_id
        or manifest.promotion_plan_sha256
        != verification.promotion_plan_sha256
        or manifest.candidate_tree_sha256
        != verification.candidate_tree_sha256
    ):
        raise BuilderActivationPlanError(
            "Builder activation manifest identities "
            "do not match verification evidence"
        )

    manifest_files = {
        item.destination_path: item
        for item in manifest.files
    }

    files: list[BuilderActivationFile] = []

    for relative_path in verified_paths:
        manifest_file = manifest_files.get(
            relative_path
        )

        if manifest_file is None:
            raise BuilderActivationPlanError(
                "Builder activation path is absent "
                "from promotion manifest"
            )

        unresolved_source = (
            promotion_directory
            / "files"
            / relative_path
        )

        if unresolved_source.is_symlink():
            raise BuilderActivationPlanError(
                "Builder activation source cannot "
                "be a symlink"
            )

        try:
            source = unresolved_source.resolve(
                strict=True
            )
        except OSError as exc:
            raise BuilderActivationPlanError(
                "Builder activation source is missing"
            ) from exc

        if (
            promotion_directory
            not in source.parents
            or not source.is_file()
        ):
            raise BuilderActivationPlanError(
                "Builder activation source escaped "
                "the promotion bundle"
            )

        source_digest = _file_sha256(source)

        if source_digest != manifest_file.sha256:
            raise BuilderActivationPlanError(
                "Builder activation source digest "
                "does not match promotion manifest"
            )

        unresolved_destination = (
            root / relative_path
        )

        if unresolved_destination.is_symlink():
            raise BuilderActivationPlanError(
                "Builder activation destination "
                "cannot be a symlink"
            )

        destination = (
            unresolved_destination.resolve()
        )

        if root not in destination.parents:
            raise BuilderActivationPlanError(
                "Builder activation destination "
                "escaped project root"
            )

        if destination.exists():
            raise BuilderActivationPlanError(
                "Builder activation destination "
                "already exists"
            )

        files.append(
            BuilderActivationFile(
                kind=manifest_file.kind,
                source_path=(
                    source.relative_to(
                        promotion_directory
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
        current_after = (
            verify_builder_promotion_bundle(
                promotion_directory=(
                    promotion_directory
                ),
                promotion_root=promotion_root,
                plan_file=Path(
                    verification.plan_file
                ),
                plan_root=promotion_plan_root,
            )
        )
    except BuilderPromotionVerificationError as exc:
        raise BuilderActivationPlanError(
            "Builder activation bundle changed "
            "during planning"
        ) from exc

    if current_after != verification:
        raise BuilderActivationPlanError(
            "Builder activation verification changed "
            "during planning"
        )

    try:
        safe_verification_file = Path(
            decision.verification_file
        ).resolve(strict=True)
    except OSError as exc:
        raise BuilderActivationPlanError(
            "Builder activation verification file "
            "is unavailable"
        ) from exc

    return BuilderActivationPlan(
        task_id=decision.task_id,
        activation_decision_id=(
            decision.decision_id
        ),
        reviewer_id=decision.reviewer_id,
        verification_sha256=(
            verification_digest
        ),
        activation_decision_sha256=(
            decision_digest
        ),
        promotion_plan_sha256=(
            verification.promotion_plan_sha256
        ),
        candidate_tree_sha256=(
            verification.candidate_tree_sha256
        ),
        promotion_directory=(
            promotion_directory.as_posix()
        ),
        project_root=root.as_posix(),
        verification_file=(
            safe_verification_file.as_posix()
        ),
        activation_decision_file=(
            safe_decision_file.as_posix()
        ),
        files=files,
    )
