"""Tests for append-only operational event storage."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from geoagent_harness.operational_history import (
    AgentRole,
    OperationalEventType,
    OperationalHistoryError,
    OperationalIdentity,
    append_operational_event,
    append_operational_events,
    build_operational_timeline,
    create_operational_identity,
    create_operational_event,
    load_operational_events,
    operational_event_sha256,
)


NOW = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)


def test_creates_unique_operational_identities() -> None:
    first = create_operational_identity(
        agent_id=AgentRole.PLANNER,
    )
    second = create_operational_identity(
        agent_id=AgentRole.PLANNER,
    )

    assert first.agent_instance_id != second.agent_instance_id
    assert first.agent_run_id != second.agent_run_id
    assert first.task_id != second.task_id
    assert first.correlation_id != second.correlation_id


def test_preserves_shared_identity_scope_and_parent() -> None:
    active_identity = create_operational_identity(
        agent_id=AgentRole.EXECUTOR,
        task_id="shared-task",
        correlation_id="shared-correlation",
        parent_run_id="planner-run-1",
    )

    assert active_identity.task_id == "shared-task"
    assert active_identity.correlation_id == "shared-correlation"
    assert active_identity.parent_run_id == "planner-run-1"


def identity(
    *,
    role: AgentRole = AgentRole.PLANNER,
    run_id: str = "planner-run-1",
    parent_run_id: str | None = None,
) -> OperationalIdentity:
    return OperationalIdentity(
        agent_id=role,
        agent_instance_id=f"{role.value}-instance-1",
        agent_run_id=run_id,
        task_id="operational-history-test",
        correlation_id="correlation-1",
        parent_run_id=parent_run_id,
    )


def complete_planner_history(
    root: Path,
):
    active_identity = identity()
    started = create_operational_event(
        identity=active_identity,
        event_type=OperationalEventType.RUN_STARTED,
        event_id="event-planner-started",
        occurred_at=NOW,
    )
    completed = create_operational_event(
        identity=active_identity,
        event_type=OperationalEventType.RUN_COMPLETED,
        previous_event=started,
        event_id="event-planner-completed",
        occurred_at=NOW + timedelta(seconds=2),
        artifact_digests={"plan": "a" * 64},
    )
    path = append_operational_event(
        started,
        event_root=root,
    )
    append_operational_event(
        completed,
        event_root=root,
    )
    return path, started, completed


def test_appends_and_loads_hash_chained_events(
    tmp_path: Path,
) -> None:
    path, started, completed = complete_planner_history(
        tmp_path
    )

    loaded = load_operational_events(
        path,
        event_root=tmp_path,
    )

    assert loaded == [started, completed]
    assert completed.previous_event_sha256 == (
        operational_event_sha256(started)
    )
    assert path.stat().st_mode & 0o777 == 0o644


def test_rejects_tampered_hash_chain(
    tmp_path: Path,
) -> None:
    path, _, _ = complete_planner_history(tmp_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["status"] = "tampered"
    lines[0] = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(
        OperationalHistoryError,
        match="hash chain",
    ):
        load_operational_events(
            path,
            event_root=tmp_path,
        )


def test_rejects_future_event_schema(
    tmp_path: Path,
) -> None:
    path, _, _ = complete_planner_history(tmp_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["schema_version"] = "2.0"
    lines[0] = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(
        OperationalHistoryError,
        match="failed validation",
    ):
        load_operational_events(
            path,
            event_root=tmp_path,
        )


def test_rejects_duplicate_event_id(
    tmp_path: Path,
) -> None:
    active_identity = identity()
    event = create_operational_event(
        identity=active_identity,
        event_type=OperationalEventType.RUN_STARTED,
        event_id="event-duplicate",
        occurred_at=NOW,
    )
    append_operational_event(event, event_root=tmp_path)

    with pytest.raises(
        OperationalHistoryError,
        match="unique",
    ):
        append_operational_event(event, event_root=tmp_path)


def test_appends_complete_run_as_one_batch(
    tmp_path: Path,
) -> None:
    active_identity = identity()
    started = create_operational_event(
        identity=active_identity,
        event_type=OperationalEventType.RUN_STARTED,
        event_id="event-batch-started",
        occurred_at=NOW,
    )
    completed = create_operational_event(
        identity=active_identity,
        event_type=OperationalEventType.RUN_COMPLETED,
        previous_event=started,
        event_id="event-batch-completed",
        occurred_at=NOW + timedelta(seconds=1),
    )

    path = append_operational_events(
        [started, completed],
        event_root=tmp_path,
    )

    assert load_operational_events(
        path,
        event_root=tmp_path,
    ) == [started, completed]


def test_rejects_event_after_terminal_state() -> None:
    active_identity = identity()
    started = create_operational_event(
        identity=active_identity,
        event_type=OperationalEventType.RUN_STARTED,
        occurred_at=NOW,
    )
    completed = create_operational_event(
        identity=active_identity,
        event_type=OperationalEventType.RUN_COMPLETED,
        previous_event=started,
        occurred_at=NOW + timedelta(seconds=1),
    )

    with pytest.raises(
        OperationalHistoryError,
        match="terminal",
    ):
        create_operational_event(
            identity=active_identity,
            event_type=OperationalEventType.EVIDENCE_PERSISTED,
            previous_event=completed,
            occurred_at=NOW + timedelta(seconds=2),
        )


def test_builds_correlated_parent_child_timeline(
    tmp_path: Path,
) -> None:
    path, _, _ = complete_planner_history(tmp_path)
    executor_identity = identity(
        role=AgentRole.EXECUTOR,
        run_id="executor-run-1",
        parent_run_id="planner-run-1",
    )
    executor_started = create_operational_event(
        identity=executor_identity,
        event_type=OperationalEventType.RUN_STARTED,
        event_id="event-executor-started",
        occurred_at=NOW + timedelta(seconds=3),
    )
    executor_completed = create_operational_event(
        identity=executor_identity,
        event_type=OperationalEventType.RUN_COMPLETED,
        previous_event=executor_started,
        event_id="event-executor-completed",
        occurred_at=NOW + timedelta(seconds=4),
    )
    append_operational_event(
        executor_started,
        event_root=tmp_path,
    )
    append_operational_event(
        executor_completed,
        event_root=tmp_path,
    )

    events = load_operational_events(
        path,
        event_root=tmp_path,
    )
    timeline = build_operational_timeline(events)

    assert timeline.event_count == 4
    assert timeline.agent_ids == [
        AgentRole.EXECUTOR,
        AgentRole.PLANNER,
    ]
    assert timeline.failed_run_ids == []
    assert timeline.history_validated is True


def test_rejects_missing_parent_run(
    tmp_path: Path,
) -> None:
    child = create_operational_event(
        identity=identity(
            role=AgentRole.CRITIC,
            run_id="critic-run-1",
            parent_run_id="missing-run",
        ),
        event_type=OperationalEventType.RUN_STARTED,
        occurred_at=NOW,
    )

    with pytest.raises(
        OperationalHistoryError,
        match="parent agent run",
    ):
        append_operational_event(child, event_root=tmp_path)


def test_rejects_symlinked_log(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.jsonl"
    outside.write_text("", encoding="utf-8")
    root = tmp_path / "history"
    root.mkdir()
    linked = root / "correlation-1.events.jsonl"
    linked.symlink_to(outside)

    event = create_operational_event(
        identity=identity(),
        event_type=OperationalEventType.RUN_STARTED,
        occurred_at=NOW,
    )

    with pytest.raises(
        OperationalHistoryError,
        match="symlink",
    ):
        append_operational_event(event, event_root=root)
