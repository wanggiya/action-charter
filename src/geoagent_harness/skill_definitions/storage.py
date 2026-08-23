"""Bounded storage for declarative skill definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
)


MAX_SKILL_DEFINITION_BYTES = 250_000


class SkillDefinitionStorageError(RuntimeError):
    """Raised when a skill definition is unsafe or invalid."""


def skill_definition_path(
    definition: DeclarativeSkillDefinition,
    *,
    definition_root: Path,
) -> Path:
    """Return the canonical path for one definition."""

    return (
        definition_root.resolve()
        / f"{definition.skill_id}.skill.yaml"
    )


def _safe_definition_path(
    path: Path,
    *,
    definition_root: Path,
) -> Path:
    """Require one skill YAML beneath the trusted root."""

    root = definition_root.resolve()
    resolved = path.resolve()

    if not resolved.is_relative_to(root):
        raise SkillDefinitionStorageError(
            "skill definition path escaped its "
            "trusted root"
        )

    if not resolved.name.endswith(
        ".skill.yaml"
    ):
        raise SkillDefinitionStorageError(
            "skill definition must use the "
            ".skill.yaml suffix"
        )

    return resolved


def load_skill_definition(
    path: Path,
    *,
    definition_root: Path,
) -> DeclarativeSkillDefinition:
    """Load one canonical declarative definition."""

    safe_path = _safe_definition_path(
        path,
        definition_root=definition_root,
    )

    if not safe_path.is_file():
        raise SkillDefinitionStorageError(
            "skill definition does not exist"
        )

    try:
        size = safe_path.stat().st_size
    except OSError as exc:
        raise SkillDefinitionStorageError(
            "skill definition could not be inspected"
        ) from exc

    if size > MAX_SKILL_DEFINITION_BYTES:
        raise SkillDefinitionStorageError(
            "skill definition exceeds the size limit"
        )

    try:
        content = safe_path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise SkillDefinitionStorageError(
            "skill definition is not UTF-8"
        ) from exc
    except OSError as exc:
        raise SkillDefinitionStorageError(
            "skill definition could not be read"
        ) from exc

    try:
        payload: Any = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise SkillDefinitionStorageError(
            "skill definition is not valid YAML"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillDefinitionStorageError(
            "skill definition must be an object"
        )

    try:
        definition = (
            DeclarativeSkillDefinition
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise SkillDefinitionStorageError(
            "skill definition failed schema validation"
        ) from exc

    expected_path = skill_definition_path(
        definition,
        definition_root=definition_root,
    )

    if safe_path != expected_path:
        raise SkillDefinitionStorageError(
            "skill definition filename does not "
            "match its skill ID"
        )

    return definition

