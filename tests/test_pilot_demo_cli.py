"""CLI tests for the read-only pilot demonstration readiness boundary."""

from __future__ import annotations

import json
from pathlib import Path

from click.utils import strip_ansi
from typer.testing import CliRunner

from geoagent_harness.cli import app


PROJECT_ROOT = Path(__file__).parents[1]
DEFINITION = Path("demonstrations/checkpoint14f/DEMO.json")
runner = CliRunner()


def test_pilot_demo_readiness_command_is_registered() -> None:
    result = runner.invoke(app, ["assess-pilot-demo-readiness", "--help"])
    output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "without taking any action" in output
    assert "--project-root" in output


def test_cli_reports_fixed_demo_ready() -> None:
    result = runner.invoke(
        app,
        [
            "assess-pilot-demo-readiness",
            str(DEFINITION),
            "--project-root",
            str(PROJECT_ROOT),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["repository_ready"] is True
    assert payload["next_action"] == "propose_workflow"
    assert payload["violations"] == []
    assert payload["model_called"] is False
    assert payload["approval_created"] is False
    assert payload["workflow_executed"] is False
    assert payload["filesystem_modified"] is False
    assert payload["database_modified"] is False
    assert payload["release_created"] is False
    assert payload["snakemake_invoked"] is False


def test_cli_returns_two_for_unsafe_definition() -> None:
    result = runner.invoke(
        app,
        [
            "assess-pilot-demo-readiness",
            "../DEMO.json",
            "--project-root",
            str(PROJECT_ROOT),
        ],
    )

    assert result.exit_code == 2
    assert "Error:" in result.output
