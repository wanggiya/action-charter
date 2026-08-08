"""Tests for Planner Agent CLI registration."""

from typer.testing import CliRunner

from geoagent_harness.cli import app

runner = CliRunner()


def test_plan_task_command_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "plan-task",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "--request" in result.stdout
    assert "--project-root" in result.stdout
    assert "--agents-root" in result.stdout