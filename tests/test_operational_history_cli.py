"""Offline CLI tests for correlated operational history."""

import json
from datetime import datetime, timezone
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.operational_history import (
    AgentRole,
    OperationalEventType,
    OperationalIdentity,
    append_operational_events,
    create_operational_event,
)


runner = CliRunner()
NOW = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)


def test_cli_inspects_validated_timeline(
    tmp_path: Path,
) -> None:
    identity = OperationalIdentity(
        agent_id=AgentRole.PLANNER,
        agent_instance_id="planner-instance-1",
        agent_run_id="planner-run-1",
        task_id="cli-history-test",
        correlation_id="cli-correlation-1",
    )
    started = create_operational_event(
        identity=identity,
        event_type=OperationalEventType.RUN_STARTED,
        event_id="cli-event-1",
        occurred_at=NOW,
    )
    completed = create_operational_event(
        identity=identity,
        event_type=OperationalEventType.RUN_COMPLETED,
        previous_event=started,
        event_id="cli-event-2",
        occurred_at=NOW,
    )
    event_file = append_operational_events(
        [started, completed],
        event_root=tmp_path,
    )

    result = runner.invoke(
        app,
        [
            "inspect-operational-history",
            str(event_file),
            "--event-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["event_count"] == 2
    assert payload["history_validated"] is True
    assert payload["private_reasoning_recorded"] is False


def test_cli_rejects_history_outside_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "events"
    root.mkdir()
    outside = tmp_path / "outside.events.jsonl"
    outside.write_text("{}\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "inspect-operational-history",
            str(outside),
            "--event-root",
            str(root),
        ],
    )

    assert result.exit_code == 2
    assert "escaped" in result.output
