"""Immutable digest-addressed storage for Critic results."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.critic.records import critic_result_sha256
from geoagent_harness.critic.schemas import (
    CriticResultRecord,
    CriticResultStorageResult,
)
from geoagent_harness.redaction import redact_value
from geoagent_harness.schema_registry import (
    ArtifactType,
    SchemaVersionError,
    require_supported_schema,
)


RECORD_FILE_NAME = "CRITIC_RESULT.json"
MAX_CRITIC_RECORD_BYTES = 1_000_000


class CriticResultStorageError(RuntimeError):
    """Raised when Critic-result storage is unsafe or invalid."""


def canonical_critic_result_record_json(
    record: CriticResultRecord,
) -> str:
    """Return canonical human-readable persisted record JSON."""

    original = record.model_dump(mode="json")
    redacted = redact_value(original)
    if redacted != original:
        raise CriticResultStorageError(
            "Critic record contains content requiring redaction"
        )
    return (
        json.dumps(
            original,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def critic_result_record_sha256(
    record: CriticResultRecord,
) -> str:
    """Digest the exact canonical persisted representation."""

    return hashlib.sha256(
        canonical_critic_result_record_json(record).encode("utf-8")
    ).hexdigest()


def _record_root_path(record_root: Path) -> Path:
    if record_root.is_symlink():
        raise CriticResultStorageError(
            "Critic-result root cannot be a symlink"
        )
    try:
        record_root.mkdir(parents=True, exist_ok=True)
        root = record_root.resolve(strict=True)
    except OSError as exc:
        raise CriticResultStorageError(
            "Critic-result root is unavailable"
        ) from exc
    if not root.is_dir():
        raise CriticResultStorageError(
            "Critic-result root must be a directory"
        )
    return root


def persist_critic_result_record(
    record: CriticResultRecord,
    *,
    record_root: Path,
) -> CriticResultStorageResult:
    """Atomically persist one write-once Critic-result package."""

    if critic_result_sha256(record.critic_result) != (
        record.critic_result_sha256
    ):
        raise CriticResultStorageError(
            "Critic-result digest does not match its record"
        )

    root = _record_root_path(record_root)
    content = canonical_critic_result_record_json(record)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    directory = root / f"{record.task_id}.{digest}.critic-result"
    if directory.exists() or directory.is_symlink():
        raise CriticResultStorageError(
            "Critic-result package already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(prefix=".geoagent-critic-", dir=root)
    )
    staged = temporary_root / "record"
    staged_file = staged / RECORD_FILE_NAME
    try:
        staged.mkdir()
        with staged_file.open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(content)
        if hashlib.sha256(staged_file.read_bytes()).hexdigest() != digest:
            raise CriticResultStorageError(
                "Staged Critic-result digest is inconsistent"
            )
        os.replace(staged, directory)
        temporary_root.rmdir()
    except (OSError, RuntimeError, ValueError) as exc:
        shutil.rmtree(temporary_root, ignore_errors=True)
        if isinstance(exc, CriticResultStorageError):
            raise
        raise CriticResultStorageError(
            "Critic-result package could not be persisted"
        ) from exc

    final_file = directory / RECORD_FILE_NAME
    try:
        final_digest = hashlib.sha256(final_file.read_bytes()).hexdigest()
    except OSError as exc:
        raise CriticResultStorageError(
            "Persisted Critic-result package could not be verified"
        ) from exc
    if final_digest != digest:
        raise CriticResultStorageError(
            "Persisted Critic-result digest changed"
        )

    return CriticResultStorageResult(
        task_id=record.task_id,
        deterministic_status=record.deterministic_status,
        critic_result_sha256=record.critic_result_sha256,
        critic_record_sha256=digest,
        record_directory=directory.as_posix(),
        record_file=final_file.as_posix(),
    )


def load_critic_result_record(
    record_file: Path,
    *,
    record_root: Path,
) -> CriticResultRecord:
    """Securely load one canonical digest-addressed Critic record."""

    if record_root.is_symlink():
        raise CriticResultStorageError(
            "Critic-result root cannot be a symlink"
        )
    try:
        root = record_root.resolve(strict=True)
    except OSError as exc:
        raise CriticResultStorageError(
            "Critic-result root is unavailable"
        ) from exc
    if not root.is_dir():
        raise CriticResultStorageError(
            "Critic-result root must be a directory"
        )

    candidate = (
        record_file if record_file.is_absolute() else root / record_file
    )
    if candidate.is_symlink() or candidate.parent.is_symlink():
        raise CriticResultStorageError(
            "Critic-result path cannot contain a symlink"
        )
    try:
        safe_file = candidate.resolve(strict=True)
    except OSError as exc:
        raise CriticResultStorageError(
            "Critic-result file is unavailable"
        ) from exc
    directory = safe_file.parent
    if (
        directory.parent != root
        or safe_file.name != RECORD_FILE_NAME
        or not safe_file.is_file()
    ):
        raise CriticResultStorageError(
            "Critic-result file escaped its approved package"
        )
    try:
        size = safe_file.stat().st_size
        raw = safe_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CriticResultStorageError(
            "Critic-result file could not be read"
        ) from exc
    if size < 1 or size > MAX_CRITIC_RECORD_BYTES:
        raise CriticResultStorageError(
            "Critic-result file has an invalid size"
        )
    try:
        payload: Any = json.loads(raw)
        if not isinstance(payload, dict):
            raise CriticResultStorageError(
                "Critic-result file must contain an object"
            )
        require_supported_schema(
            payload,
            artifact_type=ArtifactType.CRITIC_RESULT_RECORD,
        )
        record = CriticResultRecord.model_validate(payload)
    except (
        json.JSONDecodeError,
        SchemaVersionError,
        ValidationError,
    ) as exc:
        raise CriticResultStorageError(
            "Critic-result file failed schema validation"
        ) from exc

    canonical = canonical_critic_result_record_json(record)
    if raw != canonical:
        raise CriticResultStorageError(
            "Critic-result file is not canonical"
        )
    digest = critic_result_record_sha256(record)
    expected_directory = f"{record.task_id}.{digest}.critic-result"
    if directory.name != expected_directory:
        raise CriticResultStorageError(
            "Critic-result directory identity is invalid"
        )
    if critic_result_sha256(record.critic_result) != (
        record.critic_result_sha256
    ):
        raise CriticResultStorageError(
            "Critic-result content digest is invalid"
        )
    if set(path.name for path in directory.iterdir()) != {
        RECORD_FILE_NAME
    }:
        raise CriticResultStorageError(
            "Critic-result package contains unexpected files"
        )
    return record
