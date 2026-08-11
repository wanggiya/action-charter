"""Tests for Executor runtime CLI registration."""

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app

runner = CliRunner()


def test_execute_approved_plan_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "execute-approved-plan",
            "--help",
        ],
    )
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--plan-root" in output
    assert "--approval-root" in output
    assert "--agents-root" in output
    assert "--allowed-schemas" in output