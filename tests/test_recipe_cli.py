"""Tests for reusable-recipe CLI registration."""

from click import unstyle
from typer.testing import CliRunner
from typer.main import get_command

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

def test_run_approved_recipe_is_registered() -> None:
    output = command_help(
        "run-approved-recipe"
    )

    assert "--recipe-root" in output
    assert "--approval-root" in output
    assert "--project-root" in output
    assert "--pretty" in output

def test_execute_approved_recipe_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "execute-approved-recipe",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Execute one exact approved recipe" in (
        result.stdout
    )

    root_command = get_command(app)

    assert hasattr(root_command, "commands")

    command = root_command.commands[
        "execute-approved-recipe"
    ]

    parameter_names = {
        parameter.name
        for parameter in command.params
    }

    assert {
        "recipe_file",
        "approval_file",
        "recipe_root",
        "approval_root",
        "project_root",
        "agents_root",
        "pretty",
    } <= parameter_names
    
def test_compile_recipe_proposal_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "compile-recipe-proposal",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert (
        "Compile a safe proposal without "
        "saving or executing"
        in result.stdout
    )
    assert "--proposal-root" in result.stdout
    assert "--project-root" in result.stdout


def test_propose_recipe_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "propose-recipe",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert (
        "Generate a non-executable recipe proposal"
        in result.stdout
    )
    assert "--agents-root" in result.stdout
    assert "--pretty" in result.stdout

def test_propose_and_compile_recipe_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "propose-and-compile-recipe",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert (
        "Generate and compile without saving "
        "or executing"
        in result.stdout
    )
    assert "--project-root" in result.stdout
    assert "--agents-root" in result.stdout
    
