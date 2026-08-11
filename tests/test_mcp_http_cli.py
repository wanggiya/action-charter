"""Tests for MCP HTTP smoke-test CLI registration."""

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app

runner = CliRunner()


def test_mcp_http_smoke_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "mcp-http-smoke",
            "--help",
        ],
    )
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--pretty" in output