"""Bounded task evidence with a checked hash chain and derived context."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from geoagent_harness.context_pack.redaction import redact_value

TASK_ID = re.compile(r"task-[a-z0-9][a-z0-9_-]{0,63}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
EVENT_FILE = re.compile(r"([0-9]{6})\.([a-f0-9]{64})\.json\Z")
EVENT_TYPES = frozenset({
    "request", "clarification", "selection", "decision", "outcome", "failure", "artifact_reference",
})
MAX_EVENTS = 200
MAX_EVENT_BYTES = 16384
MAX_CONTEXT_EVENTS = 20
MAX_CONTEXT_CHARACTERS = 12000
MAX_TASK_INVENTORY = 50


class TaskHistoryError(RuntimeError):
    """Task evidence is invalid, unsafe or outside its limits."""


def _canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _task_dir(root: Path, task_id: str, *, create: bool = False) -> Path:
    if not TASK_ID.fullmatch(task_id):
        raise TaskHistoryError("task ID is invalid")
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise TaskHistoryError("task history root is unsafe")
    if create:
        root.mkdir(parents=True, exist_ok=True)
    task = root / task_id
    if task.is_symlink() or (task.exists() and not task.is_dir()):
        raise TaskHistoryError("task directory is unsafe")
    if create:
        task.mkdir(mode=0o700, exist_ok=True)
    return task


def _read_events(task: Path, task_id: str) -> list[dict[str, Any]]:
    if not task.exists():
        return []
    paths = sorted(task.iterdir(), key=lambda path: path.name)
    if len(paths) > MAX_EVENTS + 1:
        raise TaskHistoryError("task history exceeds its limit")
    events: list[dict[str, Any]] = []
    previous: str | None = None
    for path in paths:
        if path.name == ".lock":
            if path.is_symlink() or not path.is_file():
                raise TaskHistoryError("task lock is unsafe")
            continue
        match = EVENT_FILE.fullmatch(path.name)
        if not match or path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_EVENT_BYTES:
            raise TaskHistoryError("task event artifact is unsafe")
        raw = path.read_bytes()
        if _digest(raw) != match.group(2):
            raise TaskHistoryError("task event digest mismatch")
        try:
            event = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise TaskHistoryError("task event is invalid") from exc
        if not isinstance(event, dict) or _canonical(event) != raw:
            raise TaskHistoryError("task event is not canonical")
        sequence = len(events) + 1
        if (int(match.group(1)) != sequence or event.get("schema_version") != "1.0"
                or event.get("task_id") != task_id or event.get("sequence") != sequence
                or event.get("previous_sha256") != previous or event.get("event_type") not in EVENT_TYPES
                or not isinstance(event.get("occurred_at"), str)
                or not isinstance(event.get("payload"), dict)):
            raise TaskHistoryError("task event chain is invalid")
        try:
            timestamp = datetime.fromisoformat(event["occurred_at"])
        except ValueError as exc:
            raise TaskHistoryError("task event timestamp is invalid") from exc
        payload = event["payload"]
        if timestamp.tzinfo is None or not isinstance(payload.get("summary"), str) or not payload["summary"]:
            raise TaskHistoryError("task event fields are invalid")
        if (set(payload) != {"summary", "details", "status", "artifact_path", "artifact_sha256"}
                or not isinstance(payload["details"], str)
                or (payload["status"] is not None and not isinstance(payload["status"], str))):
            raise TaskHistoryError("task payload contains unsupported fields")
        events.append(event)
        previous = match.group(2)
    return events


def load_task_events(*, root: Path, task_id: str) -> list[dict[str, Any]]:
    """Read and verify the complete bounded chain, without changing it."""

    return _read_events(_task_dir(root, task_id), task_id)


def append_task_event(
    *, root: Path, task_id: str, event_type: str, summary: str,
    details: str = "", status: str | None = None, artifact_path: str | None = None,
    artifact_sha256: str | None = None, occurred_at: datetime | None = None,
    require_existing: bool = False,
) -> dict[str, Any]:
    """Append one secret-redacted event after rechecking the full chain."""

    if event_type not in EVENT_TYPES or not isinstance(summary, str) or not summary.strip() or len(summary) > 1000 or not isinstance(details, str) or len(details) > 8000:
        raise TaskHistoryError("task event fields are invalid")
    if status is not None and (not isinstance(status, str) or len(status) > 80):
        raise TaskHistoryError("task status is invalid")
    if (artifact_path is None) != (artifact_sha256 is None):
        raise TaskHistoryError("artifact path and digest are required together")
    if artifact_path is not None:
        path = Path(artifact_path)
        if (not artifact_path or len(artifact_path) > 240 or path.is_absolute()
                or any(part in (".", "..") for part in path.parts)
                or not DIGEST.fullmatch(artifact_sha256 or "")):
            raise TaskHistoryError("artifact reference is invalid")
    timestamp = occurred_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise TaskHistoryError("task timestamp must include a timezone")
    if require_existing and not _task_dir(root, task_id).is_dir():
        raise TaskHistoryError("task history does not exist")
    task = _task_dir(root, task_id, create=True)
    lock_path = task / ".lock"
    if lock_path.is_symlink():
        raise TaskHistoryError("task lock is unsafe")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, "r+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            events = _read_events(task, task_id)
            if require_existing and not events:
                raise TaskHistoryError("task history does not exist")
            if len(events) >= MAX_EVENTS:
                raise TaskHistoryError("task history exceeds its limit")
            previous = _digest(_canonical(events[-1])) if events else None
            payload = redact_value({
                "summary": summary, "details": details, "status": status,
                "artifact_path": artifact_path, "artifact_sha256": artifact_sha256,
            })
            event = {
                "schema_version": "1.0", "task_id": task_id, "sequence": len(events) + 1,
                "event_type": event_type, "occurred_at": timestamp.isoformat(),
                "previous_sha256": previous, "payload": payload,
            }
            data = _canonical(event)
            if len(data) > MAX_EVENT_BYTES:
                raise TaskHistoryError("task event exceeds its size limit")
            name = f"{event['sequence']:06d}.{_digest(data)}.json"
            fd = os.open(task / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            directory_fd = os.open(task, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            return {"event": event, "reference": {"path": f"{task_id}/{name}", "sha256": _digest(data)}}
    except OSError as exc:
        raise TaskHistoryError("task event could not be stored") from exc


def build_task_context(*, root: Path, task_id: str) -> dict[str, Any]:
    """Derive a stable bounded context with exact event references; no model call."""

    events = load_task_events(root=root, task_id=task_id)
    return _context_from_events(events, task_id)


def _context_from_events(events: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    # Preserve the original request when recent task traffic exceeds the cap.
    selected = events if len(events) <= MAX_CONTEXT_EVENTS else [events[0], *events[-(MAX_CONTEXT_EVENTS - 1):]]
    excerpts = []
    for event in selected:
        payload = event["payload"]
        summary = payload["summary"]
        if not isinstance(summary, str):
            raise TaskHistoryError("task summary is invalid")
        raw = _canonical(event)
        excerpts.append({
            "sequence": event["sequence"], "event_type": event["event_type"],
            "summary": summary, "status": payload["status"],
            "source": {"path": f"{task_id}/{event['sequence']:06d}.{_digest(raw)}.json", "sha256": _digest(raw)},
        })
    while excerpts and len(json.dumps(excerpts, ensure_ascii=False)) > MAX_CONTEXT_CHARACTERS:
        excerpts.pop(0)
    package = {
        "schema_version": "1.0", "task_id": task_id,
        "event_count": len(events), "selected_count": len(excerpts),
        "truncated": len(excerpts) < len(events), "excerpts": excerpts,
        "model_called": False, "execution_performed": False,
    }
    return {**package, "context_sha256": _digest(_canonical(package))}


def inspect_task_inventory(*, root: Path) -> dict[str, Any]:
    """List recent checked task histories without modifying or resuming them."""

    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise TaskHistoryError("task history root is unsafe")
    paths = [] if not root.exists() else [path for path in root.iterdir() if TASK_ID.fullmatch(path.name)]
    if len(paths) > 500:
        raise TaskHistoryError("task directory inventory exceeds its limit")
    paths.sort(key=lambda path: (path.lstat().st_mtime_ns, path.name), reverse=True)
    tasks = []
    findings = []
    for path in paths[:MAX_TASK_INVENTORY]:
        try:
            events = load_task_events(root=root, task_id=path.name)
            if not events:
                continue
            context = _context_from_events(events, path.name)
        except (TaskHistoryError, OSError, ValueError):
            findings.append({"task_id": path.name, "finding": "Task history failed independent chain verification"})
            continue
        tasks.append({
            "task_id": path.name, "summary": events[0]["payload"]["summary"],
            "event_count": len(events), "updated_at": events[-1]["occurred_at"],
            "latest_event_type": events[-1]["event_type"],
            "context_sha256": context["context_sha256"],
        })
    return {
        "schema_version": "1.0", "tasks": tasks, "findings": findings,
        "truncated": len(paths) > MAX_TASK_INVENTORY,
        "execution_performed": False, "approval_recorded": False,
    }


ARTIFACT_ROOTS = frozenset({"plans", "approvals", "workflow-recipes", "recipe-runs", "recipe-evidence", "traces", "reports", "critic-results"})
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024


def _artifact_bytes(project_root: Path, relative: str) -> bytes:
    """Read bounded evidence through no-follow directory descriptors."""
    parts = relative.split("/")
    if (len(parts) < 2 or parts[0] not in ARTIFACT_ROOTS
            or any(part in {"", ".", ".."} for part in parts) or "\\" in relative):
        raise TaskHistoryError("artifact path is outside evidence roots")
    import stat
    descriptor = os.open(project_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        with os.fdopen(file_descriptor, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_ARTIFACT_BYTES:
                raise TaskHistoryError("artifact is not bounded regular evidence")
            raw = source.read(MAX_ARTIFACT_BYTES + 1)
            after = os.fstat(source.fileno())
            if len(raw) > MAX_ARTIFACT_BYTES or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise TaskHistoryError("artifact changed during inspection")
            return raw
    finally:
        os.close(descriptor)


def inspect_task_artifacts(*, root: Path, task_id: str, project_root: Path) -> dict[str, Any]:
    """Verify recorded byte identities only; history claims grant no authority."""
    events = load_task_events(root=root, task_id=task_id)
    if not events:
        raise TaskHistoryError("task history does not exist")
    links = []
    for event in events:
        payload = event["payload"]
        path, expected = payload["artifact_path"], payload["artifact_sha256"]
        if path is None and expected is None:
            continue
        status, reason = "unavailable", "Recorded reference is invalid or outside supported evidence roots"
        if isinstance(path, str) and isinstance(expected, str) and DIGEST.fullmatch(expected):
            try:
                observed = _digest(_artifact_bytes(project_root, path))
                status = "matched" if observed == expected else "mismatch"
                reason = "Exact recorded bytes match" if status == "matched" else "Stored bytes differ from the recorded digest"
            except FileNotFoundError:
                reason = "Recorded evidence file is missing"
            except (OSError, TaskHistoryError):
                reason = "Recorded evidence could not be safely inspected"
        links.append({"sequence": event["sequence"], "artifact_path": path,
                      "recorded_sha256": expected, "status": status, "reason": reason})
    return {"schema_version": "1.0", "task_id": task_id, "links": links,
            "link_count": len(links), "byte_identity_only": True,
            "semantic_relationship_verified": False, "approval_recorded": False,
            "execution_performed": False, "model_called": False}


def attach_task_artifact(*, root: Path, task_id: str | None, project_root: Path,
                         artifact_path: str) -> dict[str, Any]:
    """Link a completed save without claiming the save failed if history fails."""
    if task_id is None:
        return {"status": "not_requested", "reason": "No active task selected"}
    try:
        if not load_task_events(root=root, task_id=task_id):
            raise TaskHistoryError("existing task required")
        digest = _digest(_artifact_bytes(project_root, artifact_path))
        append_task_event(root=root, task_id=task_id, event_type="artifact_reference",
                          summary="Stored evidence reference", artifact_path=artifact_path,
                          artifact_sha256=digest, require_existing=True)
        return {"status": "recorded", "task_id": task_id, "artifact_path": artifact_path,
                "artifact_sha256": digest}
    except (OSError, TaskHistoryError):
        return {"status": "failed", "reason": "Artifact operation succeeded, but its task reference could not be recorded"}


def record_task_attempt_state(*, root: Path, task_id: str | None, attempt_sha256: str,
                              state: str) -> bool:
    """Record an attempt-state note, never a success claim or mutable-file digest."""
    if task_id is None:
        return True
    if state not in {"running", "failed", "interrupted"} or not DIGEST.fullmatch(attempt_sha256):
        return False
    details = f"Attempt {attempt_sha256}; state {state}. Inspect durable progress and outputs. No retry or approval is granted."
    try:
        events = load_task_events(root=root, task_id=task_id)
        if not events:
            return False
        if any(event["payload"]["details"] == details for event in events):
            return True
        append_task_event(root=root, task_id=task_id,
                          event_type="selection" if state == "running" else "failure",
                          summary=f"Execution attempt {state}", details=details, status=state,
                          require_existing=True)
        return True
    except (OSError, TaskHistoryError):
        return False
