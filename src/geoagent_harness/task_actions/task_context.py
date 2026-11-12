"""Existing task context coordination, independent of HTTP."""
from __future__ import annotations
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import uuid4
from geoagent_harness.core.ledger.task_history import TaskHistoryError, append_task_event, build_task_context, load_task_events, inspect_task_inventory, inspect_task_artifacts, attach_task_artifact, record_task_attempt_state
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.contracts.interface_requests import (
    InterfaceTaskEventRequest,
)


def record_interface_task_event(
    request: InterfaceTaskEventRequest,
    *,
    project_root: Path,
    task_root: Path | None = None,
) -> dict[str, Any]:
    """Store one explicit task-history event, never an approval decision."""

    root = task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history")
    if request.task_id is None and request.event_type != "request":
        raise InterfaceApiError("a new task must begin with a request event")
    task_id = request.task_id or f"task-{uuid4().hex}"
    stored = append_task_event(
        root=root, task_id=task_id, event_type=request.event_type,
        summary=request.summary, details=request.details, artifact_path=request.artifact_path,
        artifact_sha256=request.artifact_sha256,
        require_existing=request.task_id is not None,
    )
    return {
        "schema_version": "1.0", "status": "recorded_history_only",
        "task_id": task_id, "event_reference": stored["reference"],
        "approval_recorded": False, "execution_performed": False,
    }


def inspect_interface_task_context(
    *, project_root: Path, task_id: str, task_root: Path | None = None,
) -> dict[str, Any]:
    """Recheck one complete task chain and return a cited context preview."""

    root = task_root if task_root is not None else runtime_store_path(_trusted_root(project_root), "task-history")
    if not load_task_events(root=root, task_id=task_id):
        raise TaskHistoryError("task history does not exist")
    return build_task_context(root=root, task_id=task_id)


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
record_interface_task_event = _task_entrypoint(record_interface_task_event)
inspect_interface_task_context = _task_entrypoint(inspect_interface_task_context, audit=False)
