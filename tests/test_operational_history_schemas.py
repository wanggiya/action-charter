"""Tests for typed operational identities and events."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from geoagent_harness.operational_history import (
    AgentRole,
    OperationalEvent,
    OperationalEventType,
    OperationalIdentity,
)


NOW = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)


def identity() -> OperationalIdentity:
    return OperationalIdentity(
        agent_id=AgentRole.PLANNER,
        agent_instance_id="planner-instance-1",
        agent_run_id="planner-run-1",
        task_id="operational-history-test",
        correlation_id="correlation-1",
    )


def test_accepts_bounded_run_started_event() -> None:
    event = OperationalEvent(
        event_id="event-1",
        sequence=0,
        identity=identity(),
        event_type=OperationalEventType.RUN_STARTED,
        occurred_at=NOW,
        versions={"harness": "0.1.0"},
        facts={"request_received": True},
    )

    assert event.secrets_redacted is True
    assert event.private_reasoning_recorded is False


def test_rejects_unsafe_identity() -> None:
    with pytest.raises(
        ValidationError,
        match="unsafe characters",
    ):
        OperationalIdentity(
            agent_id=AgentRole.PLANNER,
            agent_instance_id="planner-instance-1",
            agent_run_id="planner-run-1",
            task_id="operational-history-test",
            correlation_id="../escape",
        )


def test_rejects_naive_timestamp() -> None:
    with pytest.raises(
        ValidationError,
        match="timezone",
    ):
        OperationalEvent(
            event_id="event-1",
            sequence=0,
            identity=identity(),
            event_type=OperationalEventType.RUN_STARTED,
            occurred_at=datetime(2026, 9, 3, 12),
        )


def test_rejects_sensitive_fact_name() -> None:
    with pytest.raises(
        ValidationError,
        match="sensitive",
    ):
        OperationalEvent(
            event_id="event-1",
            sequence=0,
            identity=identity(),
            event_type=OperationalEventType.RUN_STARTED,
            occurred_at=NOW,
            facts={"access_token": "not-allowed"},
        )


def test_run_failed_requires_failure_code() -> None:
    with pytest.raises(
        ValidationError,
        match="failure code",
    ):
        OperationalEvent(
            event_id="event-1",
            sequence=1,
            identity=identity(),
            event_type=OperationalEventType.RUN_FAILED,
            occurred_at=NOW,
            previous_event_sha256="a" * 64,
        )


def test_later_event_requires_predecessor_digest() -> None:
    with pytest.raises(
        ValidationError,
        match="predecessor",
    ):
        OperationalEvent(
            event_id="event-2",
            sequence=1,
            identity=identity(),
            event_type=OperationalEventType.INPUT_VALIDATED,
            occurred_at=NOW,
        )
