"""Tests for deterministic Snakemake package generation."""

import hashlib
import json
from pathlib import Path

import pytest

from geoagent_harness.snakemake_export import (
    SnakemakeExportGenerationError,
    SnakemakeRecipeExportPlan,
    generate_snakemake_recipe_export,
)


DIGEST = "a" * 64


def export_plan() -> SnakemakeRecipeExportPlan:
    return SnakemakeRecipeExportPlan(
        recipe_id="snakemake-test",
        recipe_sha256=DIGEST,
        approval_id=(
            "recipe-approval-"
            "20260822t000000z-1234abcd"
        ),
        recipe_filename=(
            "snakemake-test."
            f"{DIGEST}.json"
        ),
        approval_filename=(
            "recipe-approval-"
            "20260822t000000z-1234abcd.json"
        ),
        approved_step_ids=["step_2"],
        topological_step_ids=[
            "step_1",
            "step_2",
        ],
    )


def file_sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def test_generator_creates_replay_package(
    tmp_path: Path,
) -> None:
    result = generate_snakemake_recipe_export(
        export_plan(),
        export_root=tmp_path / "exports",
    )

    export_path = Path(result.export_path)

    snakefile = (
        export_path
        / result.workflow_path
    )
    configuration = (
        export_path
        / result.configuration_path
    )
    manifest = (
        export_path
        / result.manifest_path
    )

    assert snakefile.is_file()
    assert configuration.is_file()
    assert manifest.is_file()

    assert (
        file_sha256(snakefile)
        == result.workflow_sha256
    )
    assert (
        file_sha256(configuration)
        == result.configuration_sha256
    )

    assert result.export_performed is True
    assert result.workflow_executed is False
    assert (
        result.recipe_execution_performed
        is False
    )


def test_snakefile_has_no_shell_rule(
    tmp_path: Path,
) -> None:
    result = generate_snakemake_recipe_export(
        export_plan(),
        export_root=tmp_path / "exports",
    )

    snakefile = (
        Path(result.export_path)
        / result.workflow_path
    )

    content = snakefile.read_text(
        encoding="utf-8"
    )

    assert "shell:" not in content
    assert "subprocess" not in content
    assert "os.system" not in content
    assert "run_approved_recipe_replay" in content


def test_configuration_preserves_exact_identity(
    tmp_path: Path,
) -> None:
    plan = export_plan()

    result = generate_snakemake_recipe_export(
        plan,
        export_root=tmp_path / "exports",
    )

    configuration = json.loads(
        (
            Path(result.export_path)
            / result.configuration_path
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        configuration["recipe_sha256"]
        == plan.recipe_sha256
    )
    assert (
        configuration["approval_id"]
        == plan.approval_id
    )
    assert (
        configuration["approved_step_ids"]
        == ["step_2"]
    )
    assert (
        configuration[
            "recipe_execution_performed"
        ]
        is False
    )


def test_same_export_is_not_overwritten(
    tmp_path: Path,
) -> None:
    root = tmp_path / "exports"
    plan = export_plan()

    generate_snakemake_recipe_export(
        plan,
        export_root=root,
    )

    with pytest.raises(
        SnakemakeExportGenerationError,
        match="already exists",
    ):
        generate_snakemake_recipe_export(
            plan,
            export_root=root,
        )

