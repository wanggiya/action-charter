"""Tests for reusable-recipe CLI registration."""

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app


runner = CliRunner()


def command_help(command: str) -> str:
    result = runner.invoke(
        app,
        [
            command,
            "--help",
        ],
    )

    assert result.exit_code == 0

    return unstyle(result.stdout)


def test_save_recipe_is_registered() -> None:
    output = command_help(
        "save-recipe"
    )

    assert "--recipe-root" in output
    assert "--project-root" in output


def test_approve_recipe_is_registered() -> None:
    output = command_help(
        "approve-recipe"
    )

    assert "--step" in output
    assert "--approver" in output
    assert "--reason" in output
    assert "--decision" in output
    assert "--valid-for-minutes" in output


def test_verify_recipe_approval_is_registered() -> None:
    output = command_help(
        "verify-recipe-approval"
    )

    assert "--recipe-root" in output
    assert "--approval-root" in output
    assert "--project-root" in output

