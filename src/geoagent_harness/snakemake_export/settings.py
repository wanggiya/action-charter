"""Trusted settings for Snakemake approved replay."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

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


def load_snakemake_replay_settings(
    environ: Mapping[str, str] | None = None,
) -> SnakemakeReplaySettings:
    """Load replay roots from trusted environment values."""

    source = (
        os.environ
        if environ is None
        else environ
    )

    return SnakemakeReplaySettings(
        project_root=Path(
            source.get(
                "GEOAGENT_PROJECT_ROOT",
                ".",
            )
        ),
        agents_root=Path(
            source.get(
                "GEOAGENT_AGENTS_ROOT",
                "agents",
            )
        ),
        recipe_root=Path(
            source.get(
                "GEOAGENT_RECIPE_ROOT",
                "workflow-recipes",
            )
        ),
        approval_root=Path(
            source.get(
                "GEOAGENT_APPROVAL_ROOT",
                "approvals",
            )
        ),
        export_root=Path(
            source.get(
                "GEOAGENT_SNAKEMAKE_EXPORT_ROOT",
                "snakemake-exports",
            )
        ),
    )

