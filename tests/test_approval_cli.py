"""Tests for approval CLI registration."""

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app

runner = CliRunner()


def test_plan_digest_command_is_registered() -> None:
    result = runner.invoke(
        app,
        ["plan-digest", "--help"],
    )
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--plan-root" in output


def test_approve_plan_command_is_registered() -> None:
    result = runner.invoke(
        app,
        ["approve-plan", "--help"],
    )
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--step" in output
    assert "--approver" in output
    assert "--reason" in output


def test_verify_approval_command_is_registered() -> None:
    result = runner.invoke(
        app,
        ["verify-plan-approval", "--help"],
    )
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--approval-root" in output