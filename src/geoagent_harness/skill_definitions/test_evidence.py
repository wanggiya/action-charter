"""Storage for isolated candidate-test evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import hashlib

from pydantic import ValidationError

from geoagent_harness.skill_definitions.schemas import (
    SkillCandidateTestRecord,
)


MAX_CANDIDATE_TEST_RECORD_BYTES = 250_000


class SkillCandidateTestEvidenceError(
    RuntimeError
):
    """Raised when candidate-test evidence is invalid."""


def candidate_tree_sha256(
    root: Path,
) -> str:
    """Hash every candidate file in stable order."""

    candidate = root.resolve()

    if not candidate.is_dir():
        raise SkillCandidateTestEvidenceError(
            "candidate bundle does not exist"
        )

    digest = hashlib.sha256()

    paths = sorted(
        (
            path
            for path in candidate.rglob("*")
            if path.is_file()
        ),
        key=lambda path: (
            path.relative_to(candidate).as_posix()
        ),
    )

    if not paths:
        raise SkillCandidateTestEvidenceError(
            "candidate bundle contains no files"
        )

    for path in paths:
        if path.is_symlink():
            raise SkillCandidateTestEvidenceError(
                "candidate evidence cannot hash symlinks"
            )

        relative = path.relative_to(
            candidate
        ).as_posix()

        try:
            content = path.read_bytes()
        except OSError as exc:
            raise SkillCandidateTestEvidenceError(
                "candidate file could not be read"
            ) from exc

        digest.update(
            relative.encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")

    return digest.hexdigest()

def load_skill_candidate_test_record(
    path: Path,
    *,
    evidence_root: Path,
) -> SkillCandidateTestRecord:
    """Load one bounded test record beneath its root."""

    root = evidence_root.resolve()
    safe_path = path.resolve()

    if not safe_path.is_relative_to(root):
        raise SkillCandidateTestEvidenceError(
            "candidate test record escaped its "
            "evidence root"
        )

    if safe_path.suffix != ".json":
        raise SkillCandidateTestEvidenceError(
            "candidate test record must be JSON"
        )

    if not safe_path.is_file():
        raise SkillCandidateTestEvidenceError(
            "candidate test record does not exist"
        )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise SkillCandidateTestEvidenceError(
            "candidate test record could not "
            "be inspected"
        ) from exc

    if size > MAX_CANDIDATE_TEST_RECORD_BYTES:
        raise SkillCandidateTestEvidenceError(
            "candidate test record exceeds "
            "the size limit"
        )

    try:
        payload: Any = json.loads(
            safe_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise SkillCandidateTestEvidenceError(
            "candidate test record is not "
            "valid UTF-8 JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillCandidateTestEvidenceError(
            "candidate test record must "
            "contain an object"
        )

    try:
        return (
            SkillCandidateTestRecord
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise SkillCandidateTestEvidenceError(
            "candidate test record failed "
            "schema validation"
        ) from exc

