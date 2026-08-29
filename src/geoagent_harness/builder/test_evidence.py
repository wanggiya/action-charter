"""Storage for isolated Builder candidate-test evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.builder.schemas import (
    BuilderCandidateTestRecord,
)


MAX_BUILDER_TEST_RECORD_BYTES = 250_000


class BuilderCandidateTestEvidenceError(
    RuntimeError
):
    """Raised when Builder test evidence is unsafe."""


def load_builder_candidate_test_record(
    path: Path,
    *,
    evidence_root: Path,
) -> BuilderCandidateTestRecord:
    """Load one bounded test record beneath its root."""

    if evidence_root.is_symlink():
        raise BuilderCandidateTestEvidenceError(
            "Builder test evidence root cannot be a symlink"
        )

    try:
        root = evidence_root.resolve(strict=True)
    except OSError as exc:
        raise BuilderCandidateTestEvidenceError(
            "Builder test evidence root is unavailable"
        ) from exc

    if not root.is_dir():
        raise BuilderCandidateTestEvidenceError(
            "Builder test evidence root must be a directory"
        )

    unresolved = (
        path
        if path.is_absolute()
        else root / path
    )

    if unresolved.is_symlink():
        raise BuilderCandidateTestEvidenceError(
            "Builder test record cannot be a symlink"
        )

    try:
        safe_path = unresolved.resolve(strict=True)
    except OSError as exc:
        raise BuilderCandidateTestEvidenceError(
            "Builder test record does not exist"
        ) from exc

    if not safe_path.is_relative_to(root):
        raise BuilderCandidateTestEvidenceError(
            "Builder test record escaped its evidence root"
        )

    if safe_path.suffix != ".json":
        raise BuilderCandidateTestEvidenceError(
            "Builder test record must be JSON"
        )

    if not safe_path.is_file():
        raise BuilderCandidateTestEvidenceError(
            "Builder test record must be a file"
        )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise BuilderCandidateTestEvidenceError(
            "Builder test record could not be inspected"
        ) from exc

    if size > MAX_BUILDER_TEST_RECORD_BYTES:
        raise BuilderCandidateTestEvidenceError(
            "Builder test record exceeds the size limit"
        )

    try:
        payload: Any = json.loads(
            safe_path.read_text(encoding="utf-8")
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise BuilderCandidateTestEvidenceError(
            "Builder test record is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderCandidateTestEvidenceError(
            "Builder test record must contain an object"
        )

    try:
        return BuilderCandidateTestRecord.model_validate(
            payload
        )
    except ValidationError as exc:
        raise BuilderCandidateTestEvidenceError(
            "Builder test record failed schema validation"
        ) from exc
