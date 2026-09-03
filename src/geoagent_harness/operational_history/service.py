"""Append-only storage and deterministic operational timelines."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from geoagent_harness.redaction import redact_value
from geoagent_harness.schema_registry import (
    ArtifactType,
    SchemaVersionError,
    require_supported_schema,
)
from geoagent_harness.operational_history.schemas import (
    AgentRole,
    OperationalEvent,
    OperationalEventType,
    OperationalIdentity,
    OperationalTimeline,
)


MAX_EVENT_LOG_BYTES = 5_000_000
MAX_EVENT_LINE_BYTES = 32_768


class OperationalHistoryError(RuntimeError):
    """Raised when operational history is unsafe or inconsistent."""


def create_operational_identity(
    *,
    agent_id: AgentRole,
    task_id: str | None = None,
    correlation_id: str | None = None,
    agent_instance_id: str | None = None,
    agent_run_id: str | None = None,
    parent_run_id: str | None = None,
) -> OperationalIdentity:
    """Create unique bounded IDs while preserving caller correlation."""

    return OperationalIdentity(
        agent_id=agent_id,
        agent_instance_id=(
            agent_instance_id
            or f"{agent_id.value}-instance-{uuid4().hex}"
        ),
        agent_run_id=(
            agent_run_id
            or f"{agent_id.value}-run-{uuid4().hex}"
        ),
        task_id=task_id or f"task-{uuid4().hex}",
        correlation_id=(
            correlation_id
            or f"correlation-{uuid4().hex}"
        ),
        parent_run_id=parent_run_id,
    )


def canonical_operational_event_json(
    event: OperationalEvent,
) -> str:
    """Return the canonical single-line representation of an event."""

    return json.dumps(
        event.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def operational_event_sha256(
    event: OperationalEvent,
) -> str:
    """Hash one complete validated event."""

    return hashlib.sha256(
        canonical_operational_event_json(event).encode(
            "utf-8"
        )
    ).hexdigest()


def create_operational_event(
    *,
    identity: OperationalIdentity,
    event_type: OperationalEventType,
    previous_event: OperationalEvent | None = None,
    occurred_at: datetime | None = None,
    event_id: str | None = None,
    status: str | None = None,
    recipe_id: str | None = None,
    skill_id: str | None = None,
    tool_name: str | None = None,
    policy_decision: str | None = None,
    failure_code: str | None = None,
    artifact_digests: dict[str, str] | None = None,
    evidence_references: list[str] | None = None,
    versions: dict[str, str] | None = None,
    facts: dict[
        str,
        str | int | float | bool | None,
    ] | None = None,
) -> OperationalEvent:
    """Create the next immutable event for one exact run."""

    if previous_event is not None:
        if previous_event.identity != identity:
            raise OperationalHistoryError(
                "previous event belongs to a different agent run"
            )
        if previous_event.event_type in {
            OperationalEventType.RUN_COMPLETED,
            OperationalEventType.RUN_FAILED,
        }:
            raise OperationalHistoryError(
                "a terminal agent run cannot receive more events"
            )

    sequence = (
        0
        if previous_event is None
        else previous_event.sequence + 1
    )
    predecessor = (
        None
        if previous_event is None
        else operational_event_sha256(previous_event)
    )

    return OperationalEvent(
        event_id=(
            event_id
            or f"event-{uuid4().hex}"
        ),
        sequence=sequence,
        identity=identity,
        event_type=event_type,
        occurred_at=(
            occurred_at
            or datetime.now(timezone.utc)
        ),
        status=status,
        recipe_id=recipe_id,
        skill_id=skill_id,
        tool_name=tool_name,
        policy_decision=policy_decision,
        failure_code=failure_code,
        artifact_digests=(artifact_digests or {}),
        evidence_references=(evidence_references or []),
        versions=(versions or {}),
        facts=(facts or {}),
        previous_event_sha256=predecessor,
    )


def _history_root_path(event_root: Path) -> Path:
    if event_root.is_symlink():
        raise OperationalHistoryError(
            "operational-history root cannot be a symlink"
        )

    try:
        event_root.mkdir(parents=True, exist_ok=True)
        root = event_root.resolve(strict=True)
    except OSError as exc:
        raise OperationalHistoryError(
            "operational-history root is unavailable"
        ) from exc

    if not root.is_dir():
        raise OperationalHistoryError(
            "operational-history root must be a directory"
        )

    return root


def operational_event_log_path(
    *,
    event_root: Path,
    correlation_id: str,
) -> Path:
    """Resolve one correlation log directly beneath its root."""

    try:
        OperationalIdentity(
            agent_id=AgentRole.HARNESS,
            agent_instance_id="path-validation",
            agent_run_id="path-validation",
            task_id="path-validation",
            correlation_id=correlation_id,
        )
    except ValidationError as exc:
        raise OperationalHistoryError(
            "operational correlation ID is unsafe"
        ) from exc

    root = event_root.resolve()
    unresolved = (
        root / f"{correlation_id}.events.jsonl"
    )

    if unresolved.is_symlink():
        raise OperationalHistoryError(
            "operational event log cannot be a symlink"
        )

    candidate = unresolved.resolve()

    if candidate.parent != root:
        raise OperationalHistoryError(
            "operational event log escaped its approved root"
        )

    return candidate


def _parse_event_lines(
    raw: bytes,
) -> list[OperationalEvent]:
    if len(raw) > MAX_EVENT_LOG_BYTES:
        raise OperationalHistoryError(
            "operational event log exceeds the size limit"
        )
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        raise OperationalHistoryError(
            "operational event log has an incomplete final line"
        )

    events: list[OperationalEvent] = []

    for line_number, line in enumerate(
        raw.splitlines(),
        start=1,
    ):
        if not line or len(line) > MAX_EVENT_LINE_BYTES:
            raise OperationalHistoryError(
                "operational event line is empty or oversized"
            )
        try:
            payload: Any = json.loads(
                line.decode("utf-8")
            )
            if not isinstance(payload, dict):
                raise OperationalHistoryError(
                    "operational event line must contain an object"
                )
            require_supported_schema(
                payload,
                artifact_type=ArtifactType.OPERATIONAL_EVENT,
            )
            events.append(
                OperationalEvent.model_validate(payload)
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            SchemaVersionError,
            ValidationError,
        ) as exc:
            raise OperationalHistoryError(
                "operational event line failed validation "
                f"at line {line_number}"
            ) from exc

    _validate_event_history(events)
    return events


def _validate_event_history(
    events: list[OperationalEvent],
) -> None:
    event_ids: set[str] = set()
    latest_by_run: dict[str, OperationalEvent] = {}
    identities: dict[str, OperationalIdentity] = {}

    for event in events:
        if event.event_id in event_ids:
            raise OperationalHistoryError(
                "operational event IDs must be unique"
            )
        event_ids.add(event.event_id)

        run_id = event.identity.agent_run_id
        previous = latest_by_run.get(run_id)

        if run_id in identities and identities[run_id] != (
            event.identity
        ):
            raise OperationalHistoryError(
                "agent-run identity changed within history"
            )

        if previous is None:
            if event.sequence != 0:
                raise OperationalHistoryError(
                    "agent-run sequence must begin at zero"
                )
        else:
            if previous.event_type in {
                OperationalEventType.RUN_COMPLETED,
                OperationalEventType.RUN_FAILED,
            }:
                raise OperationalHistoryError(
                    "terminal agent run has later events"
                )
            if event.sequence != previous.sequence + 1:
                raise OperationalHistoryError(
                    "agent-run sequences must be contiguous"
                )
            if event.occurred_at < previous.occurred_at:
                raise OperationalHistoryError(
                    "agent-run timestamps must be monotonic"
                )
            if event.previous_event_sha256 != (
                operational_event_sha256(previous)
            ):
                raise OperationalHistoryError(
                    "operational event hash chain is invalid"
                )

        identities[run_id] = event.identity
        latest_by_run[run_id] = event

    known_runs = set(identities)
    for identity in identities.values():
        if (
            identity.parent_run_id is not None
            and identity.parent_run_id not in known_runs
        ):
            raise OperationalHistoryError(
                "parent agent run is missing from history"
            )


def append_operational_event(
    event: OperationalEvent,
    *,
    event_root: Path,
) -> Path:
    """Append one canonical event after locked history validation."""

    return append_operational_events(
        [event],
        event_root=event_root,
    )


def append_operational_events(
    events: list[OperationalEvent],
    *,
    event_root: Path,
) -> Path:
    """Append one complete event batch under a single file lock."""

    if not events:
        raise OperationalHistoryError(
            "operational event batch cannot be empty"
        )

    correlation_ids = {
        event.identity.correlation_id
        for event in events
    }
    task_ids = {
        event.identity.task_id
        for event in events
    }

    if len(correlation_ids) != 1 or len(task_ids) != 1:
        raise OperationalHistoryError(
            "operational event batch contains mixed identities"
        )

    root = _history_root_path(event_root)
    path = operational_event_log_path(
        event_root=root,
        correlation_id=next(iter(correlation_ids)),
    )

    if path.is_symlink():
        raise OperationalHistoryError(
            "operational event log cannot be a symlink"
        )

    try:
        with path.open("a+b") as stream:
            os.fchmod(stream.fileno(), 0o644)
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            stream.seek(0)
            existing = _parse_event_lines(stream.read())

            combined = [*existing, *events]
            _validate_event_history(combined)

            for previous in existing:
                if previous.identity.correlation_id != (
                    events[0].identity.correlation_id
                ):
                    raise OperationalHistoryError(
                        "event correlation does not match its log"
                    )
                if previous.identity.task_id != (
                    events[0].identity.task_id
                ):
                    raise OperationalHistoryError(
                        "event task identity does not match its log"
                    )

            lines: list[bytes] = []
            for event in events:
                original_payload = event.model_dump(mode="json")
                payload = redact_value(original_payload)
                if payload != original_payload:
                    raise OperationalHistoryError(
                        "operational event contains content requiring "
                        "redaction"
                    )
                line = (
                    json.dumps(
                        payload,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                    + "\n"
                ).encode("utf-8")
                if len(line) > MAX_EVENT_LINE_BYTES:
                    raise OperationalHistoryError(
                        "operational event line exceeds the size limit"
                    )
                lines.append(line)

            block = b"".join(lines)
            if stream.tell() + len(block) > MAX_EVENT_LOG_BYTES:
                raise OperationalHistoryError(
                    "operational event log exceeds the size limit"
                )

            stream.seek(0, os.SEEK_END)
            stream.write(block)
            stream.flush()
            os.fsync(stream.fileno())
    except OperationalHistoryError:
        raise
    except OSError as exc:
        raise OperationalHistoryError(
            "operational event could not be appended"
        ) from exc

    return path


def load_operational_events(
    path: Path,
    *,
    event_root: Path,
) -> list[OperationalEvent]:
    """Load one bounded, non-symlinked JSONL event history."""

    if event_root.is_symlink():
        raise OperationalHistoryError(
            "operational-history root cannot be a symlink"
        )
    try:
        root = event_root.resolve(strict=True)
    except OSError as exc:
        raise OperationalHistoryError(
            "operational-history root is unavailable"
        ) from exc
    if not root.is_dir():
        raise OperationalHistoryError(
            "operational-history root must be a directory"
        )

    candidate = path if path.is_absolute() else root / path
    if candidate.is_symlink():
        raise OperationalHistoryError(
            "operational event log cannot be a symlink"
        )
    try:
        safe_path = candidate.resolve(strict=True)
    except OSError as exc:
        raise OperationalHistoryError(
            "operational event log is unavailable"
        ) from exc

    if safe_path.parent != root or not safe_path.is_file():
        raise OperationalHistoryError(
            "operational event log escaped its approved root"
        )
    if not safe_path.name.endswith(".events.jsonl"):
        raise OperationalHistoryError(
            "operational event log has an invalid filename"
        )

    try:
        events = _parse_event_lines(safe_path.read_bytes())
    except OSError as exc:
        raise OperationalHistoryError(
            "operational event log could not be read"
        ) from exc

    if not events:
        raise OperationalHistoryError(
            "operational event log is empty"
        )

    correlation_id = events[0].identity.correlation_id
    expected_path = operational_event_log_path(
        event_root=root,
        correlation_id=correlation_id,
    )
    if safe_path != expected_path:
        raise OperationalHistoryError(
            "operational event filename does not match correlation"
        )

    task_id = events[0].identity.task_id
    if any(
        event.identity.correlation_id != correlation_id
        or event.identity.task_id != task_id
        for event in events
    ):
        raise OperationalHistoryError(
            "operational history contains mixed identities"
        )

    return events


def build_operational_timeline(
    events: list[OperationalEvent],
) -> OperationalTimeline:
    """Build a stable chronological view from validated events."""

    if not events:
        raise OperationalHistoryError(
            "operational timeline requires events"
        )
    _validate_event_history(events)

    task_ids = {
        event.identity.task_id for event in events
    }
    correlation_ids = {
        event.identity.correlation_id for event in events
    }
    if len(task_ids) != 1 or len(correlation_ids) != 1:
        raise OperationalHistoryError(
            "operational timeline identities do not match"
        )

    ordered = sorted(
        events,
        key=lambda event: (
            event.occurred_at,
            event.identity.agent_run_id,
            event.sequence,
            event.event_id,
        ),
    )
    roles = sorted(
        {event.identity.agent_id for event in events},
        key=lambda role: role.value,
    )
    run_ids = sorted(
        {event.identity.agent_run_id for event in events}
    )
    failed_run_ids = sorted(
        {
            event.identity.agent_run_id
            for event in events
            if event.event_type
            == OperationalEventType.RUN_FAILED
        }
    )

    return OperationalTimeline(
        task_id=next(iter(task_ids)),
        correlation_id=next(iter(correlation_ids)),
        agent_ids=roles,
        agent_run_ids=run_ids,
        started_at=ordered[0].occurred_at,
        finished_at=ordered[-1].occurred_at,
        events=ordered,
        event_count=len(ordered),
        failed_run_ids=failed_run_ids,
    )
