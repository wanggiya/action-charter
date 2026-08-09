"""Tests for Executor runtime CLI registration."""

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

    assert result.exit_code == 0
    assert "--plan-root" in result.stdout
    assert "--approval-root" in result.stdout
    assert "--agents-root" in result.stdout
    assert "--allowed-schemas" in result.stdout