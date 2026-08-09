"""Tests for Executor handoff CLI registration."""

from typer.testing import CliRunner

from geoagent_harness.cli import app

runner = CliRunner()


def test_build_execution_envelope_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "build-execution-envelope",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "--plan-root" in result.stdout
    assert "--approval-root" in result.stdout
    assert "--allowed-schemas" in result.stdout