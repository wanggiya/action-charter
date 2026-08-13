"""Tests for read-only workflow-state CLI commands."""

import json
from datetime import datetime, timezone
from pathlib import Path

from click import unstyle
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.workflow_state import (
    create_initial_state,
    write_initial_state,
)


runner = CliRunner()

NOW = datetime(
    2026,
    8,
    13,
    16,
    0,
    tzinfo=timezone.utc,
)


def write_state(root: Path) -> Path:
    state = create_initial_state(
        task_id="cli-state-test",
        plan_sha256="a" * 64,
        occurred_at=NOW,
    )

    return write_initial_state(
        state,
        state_root=root,
    )


def test_inspect_command_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "inspect-workflow-state",
            "--help",
        ],
    )

    output = unstyle(result.output)

    assert result.exit_code == 0
    assert "--state-root" in output
    assert "--pretty" in output


def test_assess_command_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "assess-workflow-resume",
            "--help",
        ],
    )

    output = unstyle(result.output)

    assert result.exit_code == 0
    assert "--state-root" in output
    assert "--pretty" in output


def test_inspects_validated_state(
    tmp_path: Path,
) -> None:
    path = write_state(tmp_path)

    result = runner.invoke(
        app,
        [
            "inspect-workflow-state",
            str(path),
            "--state-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0

    payload = json.loads(result.stdout)

    assert payload["task_id"] == "cli-state-test"
    assert payload["current_state"] == "planned"
    assert payload["revision"] == 0


def test_assesses_state_without_modifying_it(
    tmp_path: Path,
) -> None:
    path = write_state(tmp_path)
    before = path.read_bytes()

    result = runner.invoke(
        app,
        [
            "assess-workflow-resume",
            str(path),
            "--state-root",
            str(tmp_path),
        ],
    )

    after = path.read_bytes()

    assert result.exit_code == 0
    assert after == before

    payload = json.loads(result.stdout)

    assert payload["disposition"] == (
        "resume_allowed"
    )
    assert (
        payload["automatic_execution_allowed"]
        is False
    )
    assert payload["state_modified"] is False


def test_rejects_state_outside_root(
    tmp_path: Path,
) -> None:
    approved_root = tmp_path / "approved"
    approved_root.mkdir()

    outside_root = tmp_path / "outside"
    outside_root.mkdir()

    path = write_state(outside_root)

    result = runner.invoke(
        app,
        [
            "inspect-workflow-state",
            str(path),
            "--state-root",
            str(approved_root),
        ],
    )

    assert result.exit_code == 2
    assert "escaped" in result.output