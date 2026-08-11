"""Tests for deterministic Executor CLI registration."""

from click import unstyle
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
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--plan-root" in output
    assert "--approval-root" in output
    assert "--allowed-schemas" in output