"""Bounded loading and canonical hashing of Builder results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.schemas import (
    BuilderGenerationResult,
)

MAX_BUILDER_GENERATION_BYTES = 1_000_000


class BuilderGenerationStorageError(RuntimeError):
    """Raised when stored Builder output is unsafe or invalid."""


def canonical_builder_generation_json(
    generation: BuilderGenerationResult,
) -> str:
    """Return canonical JSON for one Builder generation."""

    return json.dumps(
        generation.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def builder_generation_sha256(
    generation: BuilderGenerationResult,
) -> str:
    """Digest the complete validated Builder generation."""

    return hashlib.sha256(
        canonical_builder_generation_json(
            generation
        ).encode("utf-8")
    ).hexdigest()


def _safe_generation_path(
    generation_file: Path,
    *,
    generation_root: Path,
) -> Path:
    """Require one direct, non-symlink file beneath its root."""

    if generation_root.is_symlink():
        raise BuilderGenerationStorageError(
            "Builder generation root cannot be a symlink"
        )

    try:
        root = generation_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderGenerationStorageError(
            "Builder generation root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderGenerationStorageError(
            "Builder generation root must be a directory"
        )

    candidate = (
        generation_file
        if generation_file.is_absolute()
        else root / generation_file
    )

    if candidate.is_symlink():
        raise BuilderGenerationStorageError(
            "Builder generation file cannot be a symlink"
        )

    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise BuilderGenerationStorageError(
            "Builder generation file is unavailable"
        ) from exc

    if resolved.parent != root:
        raise BuilderGenerationStorageError(
            "Builder generation file must be directly "
            "beneath the approved root"
        )

    if not resolved.is_file():
        raise BuilderGenerationStorageError(
            "Builder generation path must be a regular file"
        )

    return resolved


def load_builder_generation(
    generation_file: Path,
    *,
    generation_root: Path,
) -> BuilderGenerationResult:
    """Load one bounded, schema-valid Builder generation."""

    safe_path = _safe_generation_path(
        generation_file,
        generation_root=generation_root,
    )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise BuilderGenerationStorageError(
            "Builder generation file metadata is unavailable"
        ) from exc

    if size < 1:
        raise BuilderGenerationStorageError(
            "Builder generation file is empty"
        )

    if size > MAX_BUILDER_GENERATION_BYTES:
        raise BuilderGenerationStorageError(
            "Builder generation file exceeds the size limit"
        )

    try:
        raw = safe_path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise BuilderGenerationStorageError(
            "Builder generation file is not valid UTF-8"
        ) from exc
    except OSError as exc:
        raise BuilderGenerationStorageError(
            "Builder generation file cannot be read"
        ) from exc

    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuilderGenerationStorageError(
            "Builder generation file contains invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderGenerationStorageError(
            "Builder generation must contain one JSON object"
        )

    try:
        generation = BuilderGenerationResult.model_validate(
            payload
        )
    except ValidationError as exc:
        raise BuilderGenerationStorageError(
            "Builder generation failed schema validation"
        ) from exc

    if (
        generation.proposal.task_id
        != generation.request.task_id
    ):
        raise BuilderGenerationStorageError(
            "Builder generation task IDs do not match"
        )

    requested = {
        artifact.path: artifact.kind
        for artifact in generation.request.artifacts
    }
    proposed = {
        artifact.path: artifact.kind
        for artifact in generation.proposal.files
    }

    if proposed != requested:
        raise BuilderGenerationStorageError(
            "Builder generation artifacts do not match"
        )

    return generation

