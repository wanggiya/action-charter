"""CLI tests for skill scaffolding commands."""

from typer.testing import CliRunner

from geoagent_harness.cli import app

from click.utils import strip_ansi

runner = CliRunner()


def test_plan_skill_scaffold_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "plan-skill-scaffold",
            "--help",
        ],
    )
    output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "without writing files" in (
        output
    )
    assert "--project-root" in output


def test_generate_skill_scaffold_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "generate-skill-scaffold",
            "--help",
        ],
    )
    output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "isolated" in output
    assert "--scaffold-root" in output
    assert "--project-root" in output


def test_validate_skill_scaffold_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "validate-skill-scaffold",
            "--help",
        ],
    )
    output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "without importing or executing" in (
        output
    )

