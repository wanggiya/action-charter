"""Immutable storage for Builder promotion plans."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.promotion_plan import (
    BuilderPromotionPlanError,
    plan_builder_promotion,
)
from geoagent_harness.builder.schemas import (
    BuilderPromotionPlan,
    BuilderPromotionPlanStorageResult,
)


PLAN_FILE_NAME = "PLAN.json"
MAX_PROMOTION_PLAN_BYTES = 1_000_000


class BuilderPromotionPlanStorageError(
    RuntimeError
):
    """Raised when a Builder promotion plan is unsafe."""


def canonical_builder_promotion_plan_json(
    plan: BuilderPromotionPlan,
) -> str:
    """Return deterministic human-readable plan JSON."""

    return (
        json.dumps(
            plan.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def builder_promotion_plan_sha256(
    plan: BuilderPromotionPlan,
) -> str:
    """Hash the exact persisted plan content."""

    return hashlib.sha256(
        canonical_builder_promotion_plan_json(
            plan
        ).encode("utf-8")
    ).hexdigest()


def _plan_root_path(plan_root: Path) -> Path:
    if plan_root.is_symlink():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan root "
            "cannot be a symlink"
        )

    try:
        plan_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        root = plan_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan root "
            "must be a directory"
        )

    return root

def _safe_plan_file_path(
    plan_file: Path,
    *,
    plan_root: Path,
) -> Path:
    """Resolve one immutable plan file beneath its root."""

    if plan_root.is_symlink():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan root "
            "cannot be a symlink"
        )

    try:
        root = plan_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan root "
            "must be a directory"
        )

    candidate = (
        plan_file
        if plan_file.is_absolute()
        else root / plan_file
    )

    if candidate.is_symlink():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file "
            "cannot be a symlink"
        )

    if candidate.parent.is_symlink():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan directory "
            "cannot be a symlink"
        )

    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file is unavailable"
        ) from exc

    if resolved.name != PLAN_FILE_NAME:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan filename "
            "must be PLAN.json"
        )

    plan_directory = resolved.parent

    if plan_directory.parent != root:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file escaped "
            "its approved root"
        )

    if not plan_directory.is_dir():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan parent "
            "must be a directory"
        )

    if not resolved.is_file():
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan path "
            "must be a regular file"
        )

    return resolved


def load_builder_promotion_plan(
    plan_file: Path,
    *,
    plan_root: Path,
) -> BuilderPromotionPlan:
    """Load one canonical digest-addressed promotion plan."""

    safe_path = _safe_plan_file_path(
        plan_file,
        plan_root=plan_root,
    )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan metadata "
            "is unavailable"
        ) from exc

    if size < 1:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file is empty"
        )

    if size > MAX_PROMOTION_PLAN_BYTES:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file exceeds "
            "the size limit"
        )

    try:
        raw = safe_path.read_text(
            encoding="utf-8"
        )
    except UnicodeError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file "
            "is not valid UTF-8"
        ) from exc
    except OSError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file "
            "could not be read"
        ) from exc

    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file "
            "contains invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderPromotionPlanStorageError(
            "Builder promotion plan must contain "
            "one JSON object"
        )

    try:
        plan = BuilderPromotionPlan.model_validate(
            payload
        )
    except ValidationError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion plan failed "
            "schema validation"
        ) from exc

    canonical = (
        canonical_builder_promotion_plan_json(plan)
    )

    if raw != canonical:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan file "
            "is not canonical"
        )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    expected_directory_name = (
        f"{plan.task_id}."
        f"{digest}.promotion-plan"
    )

    if (
        safe_path.parent.name
        != expected_directory_name
    ):
        raise BuilderPromotionPlanStorageError(
            "Builder promotion-plan directory "
            "does not match its content digest"
        )

    return plan


def persist_builder_promotion_plan(
    plan: BuilderPromotionPlan,
    *,
    plan_root: Path,
    decision_root: Path,
    review_root: Path,
    candidate_root: Path,
    project_root: Path,
) -> BuilderPromotionPlanStorageResult:
    """Persist one freshly reverified non-writing plan."""

    try:
        current_plan = plan_builder_promotion(
            decision_file=Path(
                plan.decision_file
            ),
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )
    except BuilderPromotionPlanError as exc:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion plan could not "
            "be reverified"
        ) from exc

    if current_plan != plan:
        raise BuilderPromotionPlanStorageError(
            "Builder promotion plan changed before "
            "persistence"
        )

    root = _plan_root_path(plan_root)
    content = canonical_builder_promotion_plan_json(
        plan
    )
    digest = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    plan_directory = (
        root
        / (
            f"{plan.task_id}."
            f"{digest}.promotion-plan"
        )
    )

    if (
        plan_directory.exists()
        or plan_directory.is_symlink()
    ):
        raise BuilderPromotionPlanStorageError(
            "Builder promotion plan already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-builder-plan-",
            dir=root,
        )
    )
    staged = temporary_root / "plan"
    staged_file = staged / PLAN_FILE_NAME

    try:
        staged.mkdir()

        with staged_file.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(content)

        if (
            hashlib.sha256(
                staged_file.read_bytes()
            ).hexdigest()
            != digest
        ):
            raise BuilderPromotionPlanStorageError(
                "Builder promotion-plan file digest "
                "is inconsistent"
            )

        current_plan_after = plan_builder_promotion(
            decision_file=Path(
                plan.decision_file
            ),
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )

        if current_plan_after != plan:
            raise BuilderPromotionPlanStorageError(
                "Builder promotion inputs changed during "
                "plan persistence"
            )

        os.replace(
            staged,
            plan_directory,
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
            BuilderPromotionPlanStorageError,
        ):
            raise

        raise BuilderPromotionPlanStorageError(
            "Builder promotion plan could not be persisted"
        ) from exc

    final_file = plan_directory / PLAN_FILE_NAME

    try:
        final_digest = hashlib.sha256(
            final_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise BuilderPromotionPlanStorageError(
            "Persisted Builder promotion plan "
            "could not be verified"
        ) from exc

    if final_digest != digest:
        raise BuilderPromotionPlanStorageError(
            "Persisted Builder promotion-plan "
            "digest changed"
        )

    return BuilderPromotionPlanStorageResult(
        task_id=plan.task_id,
        decision_id=plan.decision_id,
        review_package_sha256=(
            plan.review_package_sha256
        ),
        decision_sha256=plan.decision_sha256,
        candidate_tree_sha256=(
            plan.candidate_tree_sha256
        ),
        promotion_plan_sha256=digest,
        plan_directory=(
            plan_directory.as_posix()
        ),
        plan_file=final_file.as_posix(),
    )
