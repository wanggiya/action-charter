"""Loading and validation for the trusted skill registry."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from geoagent_harness.skill_registry.schemas import (
    SkillRegistry,
)

from typing import Any


MAX_SKILL_REGISTRY_BYTES = 250_000


class SkillRegistryError(RuntimeError):
    """Raised when the trusted skill registry is invalid."""


def skill_registry_path(
    project_root: Path,
) -> Path:
    """Return the one approved skill-registry path."""

    root = project_root.resolve()

    return (
        root
        / "context"
        / "SKILLS_INDEX.yaml"
    ).resolve()


def parse_skill_registry(
    content: str,
) -> SkillRegistry:
    """Parse and validate trusted skill-registry YAML."""

    try:
        payload: Any = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise SkillRegistryError(
            "trusted skill registry is not valid YAML"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillRegistryError(
            "trusted skill registry must be an object"
        )

    try:
        return SkillRegistry.model_validate(payload)
    except ValidationError as exc:
        raise SkillRegistryError(
            "trusted skill registry failed schema validation"
        ) from exc

def load_skill_registry(
    project_root: Path = Path("."),
) -> SkillRegistry:
    """Load the fixed trusted skill registry."""

    path = skill_registry_path(project_root)

    if not path.is_file():
        raise SkillRegistryError(
            "trusted skill registry does not exist"
        )

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SkillRegistryError(
            "trusted skill registry could not be inspected"
        ) from exc

    if size > MAX_SKILL_REGISTRY_BYTES:
        raise SkillRegistryError(
            "trusted skill registry exceeds the size limit"
        )

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SkillRegistryError(
            "trusted skill registry is not UTF-8"
        ) from exc
    except OSError as exc:
        raise SkillRegistryError(
            "trusted skill registry could not be read"
        ) from exc

    return parse_skill_registry(text)
