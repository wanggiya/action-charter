"""Trusted settings for Snakemake approved replay."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from geoagent_harness.platform.layout import LayoutConfiguration

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)


class SnakemakeReplaySettingsError(ValueError):
    """Raised when replay settings are unsafe."""


class SnakemakeReplaySettings(BaseModel):
    """Trusted roots used by the replay adapter."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    project_root: Path
    agents_root: Path
    recipe_root: Path
    approval_root: Path
    export_root: Path

    @field_validator(
        "project_root",
        "agents_root",
        "recipe_root",
        "approval_root",
        "export_root",
    )
    @classmethod
    def roots_are_not_empty(
        cls,
        value: Path,
    ) -> Path:
        if not value.as_posix().strip():
            raise ValueError(
                "replay roots cannot be empty"
            )

        return value


def _parse_snakemake_replay_settings(layout: LayoutConfiguration) -> SnakemakeReplaySettings:
    """Load replay roots from trusted environment values."""
    return SnakemakeReplaySettings(project_root=layout.project_root, agents_root=layout.agents_root, recipe_root=layout.recipe_root, approval_root=layout.approval_root, export_root=layout.export_root)


def load_snakemake_replay_settings(environ: Mapping[str, str] | None = None) -> SnakemakeReplaySettings:
    """Load approved replay roots from the shared platform layout."""
    from geoagent_harness.platform.configuration import load_configuration
    return load_configuration(environ).replay
