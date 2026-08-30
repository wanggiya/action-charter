"""Atomic promotion of approved Builder files into an immutable bundle."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from geoagent_harness.builder.promotion_plan import (
    BuilderPromotionPlanError,
    plan_builder_promotion,
)
from geoagent_harness.builder.promotion_plan_storage import (
    BuilderPromotionPlanStorageError,
    builder_promotion_plan_sha256,
    load_builder_promotion_plan,
)
from geoagent_harness.builder.schemas import (
    BuilderPromotionPlan,
    BuilderPromotionResult,
)


PROMOTION_MANIFEST_NAME = "PROMOTION.json"
PROMOTED_FILES_DIRECTORY = "files"


class BuilderPromotionError(RuntimeError):
    """Raised when immutable Builder promotion is unsafe."""


def _file_sha256(path: Path) -> str:
    """Hash one regular file without executing it."""

    try:
        return hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderPromotionError(
            "Builder promotion file could not be read"
        ) from exc


def _promotion_root_path(
    promotion_root: Path,
) -> Path:
    """Create and resolve one non-symlinked promotion root."""

    if promotion_root.is_symlink():
        raise BuilderPromotionError(
            "Builder promotion root cannot be a symlink"
        )

    try:
        promotion_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = promotion_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionError(
            "Builder promotion root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPromotionError(
            "Builder promotion root must be a directory"
        )

    return root


def _project_root_path(
    project_root: Path,
) -> Path:
    """Resolve the trusted project root without changing it."""

    if project_root.is_symlink():
        raise BuilderPromotionError(
            "Builder project root cannot be a symlink"
        )

    try:
        root = project_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionError(
            "Builder project root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPromotionError(
            "Builder project root must be a directory"
        )

    return root


def _candidate_path(
    plan: BuilderPromotionPlan,
) -> Path:
    """Resolve the exact candidate recorded in the plan."""

    unresolved = Path(plan.candidate_path)

    if unresolved.is_symlink():
        raise BuilderPromotionError(
            "Builder promotion candidate "
            "cannot be a symlink"
        )

    try:
        candidate = unresolved.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionError(
            "Builder promotion candidate is unavailable"
        ) from exc

    if not candidate.is_dir():
        raise BuilderPromotionError(
            "Builder promotion candidate "
            "must be a directory"
        )

    return candidate


def _source_path(
    candidate: Path,
    relative_path: str,
) -> Path:
    """Resolve one approved source beneath its candidate."""

    unresolved = candidate / relative_path

    if unresolved.is_symlink():
        raise BuilderPromotionError(
            "Builder promotion source "
            "cannot be a symlink"
        )

    try:
        source = unresolved.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionError(
            "Builder promotion source is unavailable"
        ) from exc

    if (
        candidate not in source.parents
        or not source.is_file()
    ):
        raise BuilderPromotionError(
            "Builder promotion source escaped "
            "its candidate"
        )

    return source


def _bundle_destination(
    files_root: Path,
    destination_path: str,
) -> Path:
    """Resolve one staged path beneath the new bundle."""

    unresolved = files_root / destination_path

    if unresolved.is_symlink():
        raise BuilderPromotionError(
            "Builder promotion destination "
            "cannot be a symlink"
        )

    destination = unresolved.resolve()

    if files_root.resolve() not in destination.parents:
        raise BuilderPromotionError(
            "Builder promotion destination "
            "escaped its bundle"
        )

    return destination


def _canonical_manifest_json(
    payload: dict[str, Any],
) -> str:
    """Serialize the immutable promotion manifest."""

    return (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def _manifest_payload(
    plan: BuilderPromotionPlan,
    *,
    promotion_plan_sha256: str,
) -> dict[str, Any]:
    """Build a data-only manifest for the promoted bundle."""

    return {
        "schema_version": "1.0",
        "task_id": plan.task_id,
        "decision_id": plan.decision_id,
        "review_package_sha256": (
            plan.review_package_sha256
        ),
        "decision_sha256": plan.decision_sha256,
        "generation_sha256": plan.generation_sha256,
        "candidate_tree_sha256": (
            plan.candidate_tree_sha256
        ),
        "promotion_plan_sha256": (
            promotion_plan_sha256
        ),
        "files": [
            {
                "kind": item.kind,
                "source_path": item.source_path,
                "destination_path": (
                    item.destination_path
                ),
                "sha256": item.sha256,
            }
            for item in plan.files
        ],
        "bundle_promoted": True,
        "files_copied": True,
        "post_promotion_verified": False,
        "activation_performed": False,
        "registry_modified": False,
        "implementation_trusted": False,
        "promotion_performed": True,
        "execution_performed": False,
    }


def promote_builder_candidate(
    plan_file: Path,
    *,
    plan_root: Path,
    decision_root: Path,
    review_root: Path,
    candidate_root: Path,
    project_root: Path,
    promotion_root: Path,
    confirm_decision_id: str,
    confirm_plan_sha256: str,
) -> BuilderPromotionResult:
    """Promote exact approved bytes as one immutable bundle."""

    try:
        plan = load_builder_promotion_plan(
            plan_file,
            plan_root=plan_root,
        )
    except BuilderPromotionPlanStorageError as exc:
        raise BuilderPromotionError(
            "Builder promotion plan could not be loaded"
        ) from exc

    promotion_plan_sha256 = (
        builder_promotion_plan_sha256(plan)
    )

    if confirm_decision_id != plan.decision_id:
        raise BuilderPromotionError(
            "Builder decision confirmation "
            "does not match"
        )

    if (
        confirm_plan_sha256
        != promotion_plan_sha256
    ):
        raise BuilderPromotionError(
            "Builder promotion-plan confirmation "
            "does not match"
        )

    project = _project_root_path(project_root)

    try:
        current_plan = plan_builder_promotion(
            decision_file=Path(
                plan.decision_file
            ),
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project,
        )
    except BuilderPromotionPlanError as exc:
        raise BuilderPromotionError(
            "Builder promotion inputs could not "
            "be reverified"
        ) from exc

    if current_plan != plan:
        raise BuilderPromotionError(
            "Builder promotion plan changed "
            "before promotion"
        )

    candidate = _candidate_path(plan)
    root = _promotion_root_path(promotion_root)

    promotion_directory = (
        root
        / (
            f"{plan.task_id}."
            f"{promotion_plan_sha256}.promotion"
        )
    )

    if (
        promotion_directory.exists()
        or promotion_directory.is_symlink()
    ):
        raise BuilderPromotionError(
            "Builder promotion bundle already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-promotion-",
            dir=root,
        )
    )
    staged_bundle = temporary_root / "bundle"
    staged_files = (
        staged_bundle
        / PROMOTED_FILES_DIRECTORY
    )
    staged_manifest = (
        staged_bundle
        / PROMOTION_MANIFEST_NAME
    )

    promoted_paths: list[str] = []

    try:
        staged_files.mkdir(parents=True)

        for item in plan.files:
            source = _source_path(
                candidate,
                item.source_path,
            )

            if _file_sha256(source) != item.sha256:
                raise BuilderPromotionError(
                    "Builder promotion source "
                    "digest changed"
                )

            destination = _bundle_destination(
                staged_files,
                item.destination_path,
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with (
                source.open("rb") as source_handle,
                destination.open("xb") as destination_handle,
            ):
                shutil.copyfileobj(
                    source_handle,
                    destination_handle,
                )

            if (
                _file_sha256(destination)
                != item.sha256
            ):
                raise BuilderPromotionError(
                    "Staged Builder promotion "
                    "digest changed"
                )

            promoted_paths.append(
                item.destination_path
            )

        manifest_payload = _manifest_payload(
            plan,
            promotion_plan_sha256=(
                promotion_plan_sha256
            ),
        )

        with staged_manifest.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                _canonical_manifest_json(
                    manifest_payload
                )
            )

        try:
            current_plan_after = (
                plan_builder_promotion(
                    decision_file=Path(
                        plan.decision_file
                    ),
                    decision_root=decision_root,
                    review_root=review_root,
                    candidate_root=candidate_root,
                    project_root=project,
                )
            )
        except BuilderPromotionPlanError as exc:
            raise BuilderPromotionError(
                "Builder promotion inputs could not "
                "be reverified after staging"
            ) from exc

        if current_plan_after != plan:
            raise BuilderPromotionError(
                "Builder promotion inputs changed "
                "during staging"
            )

        for item in plan.files:
            staged_file = _bundle_destination(
                staged_files,
                item.destination_path,
            )

            if (
                _file_sha256(staged_file)
                != item.sha256
            ):
                raise BuilderPromotionError(
                    "Staged Builder promotion changed "
                    "before finalization"
                )

        if (
            promotion_directory.exists()
            or promotion_directory.is_symlink()
        ):
            raise BuilderPromotionError(
                "Builder promotion destination "
                "changed before finalization"
            )

        os.replace(
            staged_bundle,
            promotion_directory,
        )
        temporary_root.rmdir()
    except (
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        shutil.rmtree(
            temporary_root,
            ignore_errors=True,
        )

        if isinstance(
            exc,
            BuilderPromotionError,
        ):
            raise

        raise BuilderPromotionError(
            "Builder promotion bundle "
            "could not be created"
        ) from exc

    final_manifest = (
        promotion_directory
        / PROMOTION_MANIFEST_NAME
    )

    return BuilderPromotionResult(
        task_id=plan.task_id,
        decision_id=plan.decision_id,
        promotion_plan_sha256=(
            promotion_plan_sha256
        ),
        candidate_tree_sha256=(
            plan.candidate_tree_sha256
        ),
        promotion_directory=(
            promotion_directory.as_posix()
        ),
        promotion_manifest=(
            final_manifest.as_posix()
        ),
        promoted_paths=promoted_paths,
    )
