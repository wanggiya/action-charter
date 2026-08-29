"""Secure read-only loading of Builder request files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.schemas import (
    BuilderRequest,
)

MAX_BUILDER_REQUEST_BYTES = 65_536


class BuilderRequestLoadError(ValueError):
    """Raised when a Builder request file is unsafe or invalid."""


def load_builder_request(
    request_file: Path,
    *,
    request_root: Path,
) -> BuilderRequest:
    """Load one bounded request beneath an approved root."""

    if request_root.is_symlink():
        raise BuilderRequestLoadError(
            "Builder request root cannot be a symlink"
        )

    try:
        resolved_root = request_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderRequestLoadError(
            "Builder request root is unavailable"
        ) from exc

    if not resolved_root.is_dir():
        raise BuilderRequestLoadError(
            "Builder request root must be a directory"
        )

    candidate = (
        request_file
        if request_file.is_absolute()
        else resolved_root / request_file
    )

    if candidate.is_symlink():
        raise BuilderRequestLoadError(
            "Builder request file cannot be a symlink"
        )

    try:
        resolved_file = candidate.resolve(strict=True)
    except OSError as exc:
        raise BuilderRequestLoadError(
            "Builder request file is unavailable"
        ) from exc

    if resolved_file.parent != resolved_root:
        raise BuilderRequestLoadError(
            "Builder request file must be directly "
            "beneath the approved root"
        )

    if not resolved_file.is_file():
        raise BuilderRequestLoadError(
            "Builder request path must be a regular file"
        )

    try:
        size = resolved_file.stat().st_size
    except OSError as exc:
        raise BuilderRequestLoadError(
            "Builder request file metadata is unavailable"
        ) from exc

    if size < 1:
        raise BuilderRequestLoadError(
            "Builder request file is empty"
        )

    if size > MAX_BUILDER_REQUEST_BYTES:
        raise BuilderRequestLoadError(
            "Builder request file exceeds the size limit"
        )

    try:
        raw = resolved_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise BuilderRequestLoadError(
            "Builder request file cannot be read"
        ) from exc

    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BuilderRequestLoadError(
            "Builder request file contains invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderRequestLoadError(
            "Builder request must contain one JSON object"
        )

    try:
        return BuilderRequest.model_validate(payload)
    except ValidationError as exc:
        raise BuilderRequestLoadError(
            "Builder request does not match the required schema"
        ) from exc

