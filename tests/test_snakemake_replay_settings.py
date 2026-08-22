"""Tests for trusted Snakemake replay settings."""

from pathlib import Path

import pytest

from geoagent_harness.snakemake_export import (
    SnakemakeReplayConfiguration,
    SnakemakeReplaySettingsError,
    load_snakemake_replay_settings,
)


def test_replay_settings_load_trusted_roots() -> None:
    settings = load_snakemake_replay_settings(
        {
            "GEOAGENT_PROJECT_ROOT": "/workspace",
            "GEOAGENT_AGENTS_ROOT": "/app/agents",
            "GEOAGENT_RECIPE_ROOT": (
                "/workspace/workflow-recipes"
            ),
            "GEOAGENT_APPROVAL_ROOT": (
                "/workspace/approvals"
            ),
            "GEOAGENT_SNAKEMAKE_EXPORT_ROOT": (
                "/workspace/snakemake-exports"
            ),
        }
    )

    assert settings.project_root == Path(
        "/workspace"
    )
    assert settings.agents_root == Path(
        "/app/agents"
    )
    assert settings.export_root == Path(
        "/workspace/snakemake-exports"
    )


def test_configuration_rejects_step_outside_scope() -> None:
    with pytest.raises(
        ValueError,
        match="inside the topological scope",
    ):
        SnakemakeReplayConfiguration(
            recipe_id="test",
            recipe_sha256="a" * 64,
            approval_id="approval",
            recipe_filename="recipe.json",
            approval_filename="approval.json",
            approved_step_ids=["step_3"],
            topological_step_ids=[
                "step_1",
                "step_2",
            ],
            replay_entrypoint=(
                "geoagent_harness.snakemake_export."
                "replay:run_approved_recipe_replay"
            ),
        )

