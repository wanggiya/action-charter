"""Bounded loading for skill scaffold requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)
from geoagent_harness.skill_scaffolding.schemas import (
    SkillScaffoldRequest,
)


MAX_SKILL_SCAFFOLD_REQUEST_BYTES = 100_000


class SkillScaffoldStorageError(RuntimeError):
    """Raised when a scaffold request cannot be loaded."""


def load_skill_scaffold_request(
    path: Path,
) -> SkillScaffoldRequest:
    """Load one bounded, versioned scaffold request."""

    if not path.is_file():
        raise SkillScaffoldStorageError(
            "skill scaffold request does not exist"
        )

    if path.is_symlink():
        raise SkillScaffoldStorageError(
            "skill scaffold request cannot be a symlink"
        )

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SkillScaffoldStorageError(
            "skill scaffold request could not be inspected"
        ) from exc

    if size > MAX_SKILL_SCAFFOLD_REQUEST_BYTES:
        raise SkillScaffoldStorageError(
            "skill scaffold request exceeds the size limit"
        )

    try:
        payload: Any = json.loads(
            path.read_text(encoding="utf-8")
        )
    except UnicodeDecodeError as exc:
        raise SkillScaffoldStorageError(
            "skill scaffold request is not UTF-8"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SkillScaffoldStorageError(
            "skill scaffold request is not valid JSON"
        ) from exc
    except OSError as exc:
        raise SkillScaffoldStorageError(
            "skill scaffold request could not be read"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillScaffoldStorageError(
            "skill scaffold request must be an object"
        )

    try:
        require_supported_schema(
            payload,
            artifact_type=(
                ArtifactType.SKILL_SCAFFOLD_REQUEST
            ),
        )

        return SkillScaffoldRequest.model_validate(
            payload
        )
    except (
        ValidationError,
        ValueError,
    ) as exc:
        raise SkillScaffoldStorageError(
            "skill scaffold request failed validation"
        ) from exc

