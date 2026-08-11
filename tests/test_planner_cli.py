"""Tests for Planner Agent CLI registration."""

from click import unstyle
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
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--request" in output
    assert "--project-root" in output
    assert "--agents-root" in output