"""Tests for schema-registry CLI commands."""

import json

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app


runner = CliRunner()


def test_schema_policies_command() -> None:
    result = runner.invoke(
        app,
        [
            "schema-policies",
        ],
    )

    assert result.exit_code == 0

    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "1.0"
    assert payload["registry_modified"] is False
    assert payload["policies"]


def test_compatibility_help_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "assess-schema-compatibility",
            "--help",
        ],
    )

    output = unstyle(result.output)

    assert result.exit_code == 0
    assert "artifact_type" in output
    assert "artifact_version" in output
    assert "--pretty" in output


def test_current_version_exits_zero() -> None:
    result = runner.invoke(
        app,
        [
            "assess-schema-compatibility",
            "workflow_trace",
            "1.0",
        ],
    )

    assert result.exit_code == 0

    payload = json.loads(result.stdout)

    assert payload["disposition"] == "current"
    assert payload["readable"] is True
    assert payload["artifact_modified"] is False


def test_future_version_exits_one() -> None:
    result = runner.invoke(
        app,
        [
            "assess-schema-compatibility",
            "workflow_trace",
            "2.0",
        ],
    )

    assert result.exit_code == 1

    payload = json.loads(result.stdout)

    assert payload["disposition"] == (
        "unsupported_future"
    )
    assert payload["readable"] is False


def test_unknown_artifact_exits_two() -> None:
    result = runner.invoke(
        app,
        [
            "assess-schema-compatibility",
            "unknown_artifact",
            "1.0",
        ],
    )

    assert result.exit_code == 2
    assert "unknown artifact type" in result.output


def test_migration_assessment_is_read_only() -> None:
    result = runner.invoke(
        app,
        [
            "assess-schema-migration",
            "workflow_state",
            "2.0",
        ],
    )

    assert result.exit_code == 1

    payload = json.loads(result.stdout)

    assert payload["migration_available"] is False
    assert payload["manual_review_required"] is True
    assert payload["artifact_modified"] is False
    assert payload["migration_performed"] is False
