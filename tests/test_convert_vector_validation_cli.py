"""CLI registration tests for conversion validation."""

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app


runner = CliRunner()


def test_validation_command_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "validate-vector-conversion",
            "--help",
        ],
    )

    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--input-root" in output
    assert "--output-root" in output
    assert "--source-layer" in output
    assert "--target-layer" in output
    assert "--extent-tolerance" in output
