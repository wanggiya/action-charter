"""Immutable digest-addressed storage for PostGIS rollback plans."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from pydantic import ValidationError

from .schemas import PostGISRollbackPlan, PostGISRollbackPlanStorageResult

ROLLBACK_PLAN_FILE_NAME = "ROLLBACK_PLAN.json"


class PostGISRollbackPlanStorageError(RuntimeError):
    """Raised when rollback plan evidence is unsafe or invalid."""


def canonical_postgis_rollback_plan_json(value: PostGISRollbackPlan) -> str:
    try:
        snapshot = PostGISRollbackPlan.model_validate(value.model_dump(mode="json"))
    except ValidationError as exc:
        raise PostGISRollbackPlanStorageError(
            "rollback plan failed schema validation"
        ) from exc
    return json.dumps(
        snapshot.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False
    ) + "\n"


def postgis_rollback_plan_sha256(value: PostGISRollbackPlan) -> str:
    return hashlib.sha256(canonical_postgis_rollback_plan_json(value).encode()).hexdigest()


def persist_postgis_rollback_plan(
    value: PostGISRollbackPlan, *, rollback_plan_root: Path
) -> PostGISRollbackPlanStorageResult:
    content = canonical_postgis_rollback_plan_json(value)
    digest = hashlib.sha256(content.encode()).hexdigest()
    if rollback_plan_root.is_symlink():
        raise PostGISRollbackPlanStorageError("rollback plan root cannot be a symlink")
    try:
        rollback_plan_root.mkdir(parents=True, exist_ok=True)
        root = rollback_plan_root.resolve(strict=True)
    except OSError as exc:
        raise PostGISRollbackPlanStorageError("rollback plan root is unavailable") from exc
    directory = root / f"{value.rollback_plan_id}.{digest}.postgis-rollback-plan"
    if directory.exists() or directory.is_symlink():
        raise PostGISRollbackPlanStorageError("rollback plan package already exists")
    temporary = Path(tempfile.mkdtemp(prefix=".postgis-rollback-plan-", dir=root))
    staged = temporary / "record"
    try:
        staged.mkdir()
        with (staged / ROLLBACK_PLAN_FILE_NAME).open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(content)
        os.replace(staged, directory)
        temporary.rmdir()
    except OSError as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        raise PostGISRollbackPlanStorageError(
            "rollback plan could not be persisted"
        ) from exc
    final_file = directory / ROLLBACK_PLAN_FILE_NAME
    if hashlib.sha256(final_file.read_bytes()).hexdigest() != digest:
        raise PostGISRollbackPlanStorageError("persisted rollback plan digest changed")
    return PostGISRollbackPlanStorageResult(
        rollback_plan_id=value.rollback_plan_id,
        promotion_plan_id=value.promotion_plan_id,
        execution_id=value.execution_id,
        verification_id=value.verification_id,
        rollback_plan_sha256=digest,
        rollback_plan_directory=directory.as_posix(),
        rollback_plan_file=final_file.as_posix(),
    )


def load_postgis_rollback_plan(
    rollback_plan_file: Path, *, rollback_plan_root: Path
) -> PostGISRollbackPlan:
    try:
        root = rollback_plan_root.resolve(strict=True)
        candidate = (
            rollback_plan_file
            if rollback_plan_file.is_absolute()
            else root / rollback_plan_file
        )
        if (
            rollback_plan_root.is_symlink()
            or candidate.is_symlink()
            or candidate.parent.is_symlink()
        ):
            raise OSError
        safe = candidate.resolve(strict=True)
        if (
            safe.name != ROLLBACK_PLAN_FILE_NAME
            or safe.parent.parent != root
            or not safe.is_file()
        ):
            raise OSError
        raw = safe.read_text(encoding="utf-8")
        value = PostGISRollbackPlan.model_validate_json(raw)
    except (OSError, UnicodeError, ValidationError) as exc:
        raise PostGISRollbackPlanStorageError(
            "rollback plan evidence is unavailable or invalid"
        ) from exc
    canonical = canonical_postgis_rollback_plan_json(value)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    if (
        raw != canonical
        or safe.parent.name
        != f"{value.rollback_plan_id}.{digest}.postgis-rollback-plan"
    ):
        raise PostGISRollbackPlanStorageError("rollback plan package identity is invalid")
    if {item.name for item in safe.parent.iterdir()} != {ROLLBACK_PLAN_FILE_NAME}:
        raise PostGISRollbackPlanStorageError(
            "rollback plan package contains unexpected files"
        )
    return value
