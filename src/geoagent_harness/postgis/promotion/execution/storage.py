"""Immutable digest-addressed PostGIS promotion execution evidence."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from pydantic import ValidationError

from .schemas import PostGISPromotionExecutionResult, PostGISPromotionExecutionStorageResult

EXECUTION_FILE_NAME = "EXECUTION.json"


class PostGISPromotionExecutionStorageError(RuntimeError):
    pass


def canonical_postgis_promotion_execution_json(result: PostGISPromotionExecutionResult) -> str:
    try:
        snapshot = PostGISPromotionExecutionResult.model_validate(result.model_dump(mode="json"))
    except ValidationError as exc:
        raise PostGISPromotionExecutionStorageError("promotion execution failed schema validation") from exc
    return json.dumps(snapshot.model_dump(mode="json"), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def postgis_promotion_execution_sha256(result: PostGISPromotionExecutionResult) -> str:
    return hashlib.sha256(canonical_postgis_promotion_execution_json(result).encode()).hexdigest()


def persist_postgis_promotion_execution(result: PostGISPromotionExecutionResult, *, execution_root: Path) -> PostGISPromotionExecutionStorageResult:
    content = canonical_postgis_promotion_execution_json(result)
    digest = hashlib.sha256(content.encode()).hexdigest()
    if execution_root.is_symlink():
        raise PostGISPromotionExecutionStorageError("promotion execution root cannot be a symlink")
    try:
        execution_root.mkdir(parents=True, exist_ok=True)
        root = execution_root.resolve(strict=True)
    except OSError as exc:
        raise PostGISPromotionExecutionStorageError("promotion execution root is unavailable") from exc
    directory = root / f"{result.execution_id}.{digest}.postgis-promotion-execution"
    if directory.exists() or directory.is_symlink():
        raise PostGISPromotionExecutionStorageError("promotion execution package already exists")
    temporary = Path(tempfile.mkdtemp(prefix=".postgis-execution-", dir=root))
    staged = temporary / "record"
    try:
        staged.mkdir()
        with (staged / EXECUTION_FILE_NAME).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(staged, directory)
        temporary.rmdir()
    except OSError as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        raise PostGISPromotionExecutionStorageError("promotion execution could not be persisted") from exc
    final_file = directory / EXECUTION_FILE_NAME
    if hashlib.sha256(final_file.read_bytes()).hexdigest() != digest:
        raise PostGISPromotionExecutionStorageError("persisted promotion execution digest changed")
    return PostGISPromotionExecutionStorageResult(
        execution_id=result.execution_id, plan_id=result.plan_id,
        plan_sha256=result.plan_sha256, approval_id=result.approval_id,
        approval_sha256=result.approval_sha256, execution_sha256=digest,
        execution_directory=directory.as_posix(), execution_file=final_file.as_posix(),
    )


def load_postgis_promotion_execution(execution_file: Path, *, execution_root: Path) -> PostGISPromotionExecutionResult:
    try:
        root = execution_root.resolve(strict=True)
        candidate = execution_file if execution_file.is_absolute() else root / execution_file
        if execution_root.is_symlink() or candidate.is_symlink() or candidate.parent.is_symlink():
            raise OSError
        safe = candidate.resolve(strict=True)
        if safe.name != EXECUTION_FILE_NAME or safe.parent.parent != root or not safe.is_file():
            raise OSError
        raw = safe.read_text(encoding="utf-8")
        result = PostGISPromotionExecutionResult.model_validate_json(raw)
    except (OSError, UnicodeError, ValidationError) as exc:
        raise PostGISPromotionExecutionStorageError("promotion execution evidence is unavailable or invalid") from exc
    canonical = canonical_postgis_promotion_execution_json(result)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    if raw != canonical or safe.parent.name != f"{result.execution_id}.{digest}.postgis-promotion-execution":
        raise PostGISPromotionExecutionStorageError("promotion execution package identity is invalid")
    if {item.name for item in safe.parent.iterdir()} != {EXECUTION_FILE_NAME}:
        raise PostGISPromotionExecutionStorageError("promotion execution package contains unexpected files")
    return result
