"""CLI registration tests for Snakemake export."""

from click.utils import strip_ansi
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
    output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "non-executing" in output
    assert "--recipe-root" in output
    assert "--approval-root" in output


def test_export_snakemake_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "export-approved-recipe-snakemake",
            "--help",
        ],
    )
    output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "exact approved recipe" in output
    assert "--export-root" in output


def test_validate_snakemake_export_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "validate-snakemake-export",
            "--help",
        ],
    )
    output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "Statically validate" in output