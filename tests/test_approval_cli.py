"""Tests for approval CLI registration."""

from typer.testing import CliRunner

from geoagent_harness.cli import app

runner = CliRunner()


def test_plan_digest_command_is_registered() -> None:
    result = runner.invoke(
        app,
        ["plan-digest", "--help"],
    )

    assert result.exit_code == 0
    assert "--plan-root" in result.stdout


def test_approve_plan_command_is_registered() -> None:
    result = runner.invoke(
        app,
        ["approve-plan", "--help"],
    )

    assert result.exit_code == 0
    assert "--step" in result.stdout
    assert "--approver" in result.stdout
    assert "--reason" in result.stdout


def test_verify_approval_command_is_registered() -> None:
    result = runner.invoke(
        app,
        ["verify-plan-approval", "--help"],
    )

    assert result.exit_code == 0
    assert "--approval-root" in result.stdout