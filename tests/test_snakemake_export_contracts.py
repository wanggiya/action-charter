"""Tests for static Snakemake export contracts."""

import json
from pathlib import Path

from geoagent_harness.snakemake_export import (
    SnakemakeRecipeExportPlan,
    generate_snakemake_recipe_export,
    validate_snakemake_export_contract,
)


DIGEST = "a" * 64


def generated_export(
    tmp_path: Path,
) -> Path:
    plan = SnakemakeRecipeExportPlan(
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

    result = generate_snakemake_recipe_export(
        plan,
        export_root=tmp_path / "exports",
    )

    return Path(result.export_path)


def test_generated_export_passes_contract(
    tmp_path: Path,
) -> None:
    export_path = generated_export(
        tmp_path
    )

    result = validate_snakemake_export_contract(
        export_path
    )

    assert result.passed is True
    assert result.violations == []
    assert result.workflow_executed is False
    assert (
        result.recipe_execution_performed
        is False
    )


def test_changed_snakefile_fails_contract(
    tmp_path: Path,
) -> None:
    export_path = generated_export(
        tmp_path
    )

    snakefile = export_path / "Snakefile"

    snakefile.write_text(
        snakefile.read_text(
            encoding="utf-8"
        )
        + '\nshell: "echo unsafe"\n',
        encoding="utf-8",
    )

    result = validate_snakemake_export_contract(
        export_path
    )

    assert result.passed is False
    assert any(
        (
            "digest conflicts"
            in violation
            or "canonical workflow"
            in violation
            or "shell:" in violation
        )
        for violation in result.violations
    )


def test_changed_configuration_fails_contract(
    tmp_path: Path,
) -> None:
    export_path = generated_export(
        tmp_path
    )

    configuration_path = (
        export_path
        / "geoagent-replay.json"
    )

    configuration = json.loads(
        configuration_path.read_text(
            encoding="utf-8"
        )
    )
    configuration["recipe_sha256"] = (
        "b" * 64
    )

    configuration_path.write_text(
        json.dumps(
            configuration,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = validate_snakemake_export_contract(
        export_path
    )

    assert result.passed is False
    assert any(
        (
            "configuration digest conflicts"
            in violation
            or "conflicts between" in violation
        )
        for violation in result.violations
    )


def test_manifest_cannot_authorize_shell_workflow(
    tmp_path: Path,
) -> None:
    export_path = generated_export(
        tmp_path
    )

    snakefile = export_path / "Snakefile"
    manifest_path = (
        export_path
        / "snakemake-export-manifest.json"
    )

    unsafe = 'shell: "echo unsafe"\n'
    snakefile.write_text(
        unsafe,
        encoding="utf-8",
    )

    import hashlib

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )
    manifest["workflow_sha256"] = (
        hashlib.sha256(
            unsafe.encode("utf-8")
        ).hexdigest()
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = validate_snakemake_export_contract(
        export_path
    )

    assert result.passed is False
    assert any(
        (
            "canonical workflow"
            in violation
            or "shell:" in violation
        )
        for violation in result.violations
    )

