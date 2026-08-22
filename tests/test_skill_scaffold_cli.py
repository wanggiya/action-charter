"""CLI tests for skill scaffolding commands."""

from typer.testing import CliRunner

from geoagent_harness.cli import app


runner = CliRunner()


def test_plan_skill_scaffold_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "plan-skill-scaffold",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "without writing files" in (
        result.stdout
    )
    assert "--project-root" in result.stdout


def test_generate_skill_scaffold_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "generate-skill-scaffold",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "isolated" in result.stdout
    assert "--scaffold-root" in result.stdout
    assert "--project-root" in result.stdout


def test_validate_skill_scaffold_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "validate-skill-scaffold",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "without importing or executing" in (
        result.stdout
    )

