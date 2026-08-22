"""CLI registration tests for Snakemake export."""

from typer.testing import CliRunner

from geoagent_harness.cli import app


runner = CliRunner()


def test_plan_snakemake_export_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "plan-snakemake-export",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "non-executing" in result.stdout
    assert "--recipe-root" in result.stdout
    assert "--approval-root" in result.stdout


def test_export_snakemake_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "export-approved-recipe-snakemake",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "exact approved recipe" in (
        result.stdout
    )
    assert "--export-root" in result.stdout


def test_validate_snakemake_export_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "validate-snakemake-export",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Statically validate" in (
        result.stdout
    )

