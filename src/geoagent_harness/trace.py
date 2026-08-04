"""Structured, secret-redacted workflow traces."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

_TASK_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")

_SECRET_KEYS = frozenset(
    {
        "password",
        "postgres_password",
        "database_url",
        "connection_string",
        "token",
        "api_key",
        "secret",
    }
)

_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|token|api[_-]?key|secret)"
    r"\s*[:=]\s*[^\s,;]+"
)

_DATABASE_URL_PATTERN = re.compile(
    r"(?i)(postgres(?:ql)?(?:\+\w+)?://[^:\s/]+:)"
    r"[^@\s/]+(@)"
)


class TraceError(RuntimeError):
    """Raised when a trace cannot be safely written."""


class TraceTimestamps(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime
    finished_at: datetime


class WorkflowTrace(BaseModel):
    """Complete structured execution record."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    original_request: str

    context_references: list[str]
    selected_skills: list[str]

    tool_arguments: dict[str, dict[str, Any]]
    tool_results: dict[str, Any]
    validation_results: dict[str, Any] | None

    artifacts: list[str]
    warnings: list[str]

    final_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
    ]

    human_corrections: list[str] = Field(
        default_factory=list
    )

    timestamps: TraceTimestamps
    versions: dict[str, str]

    secrets_redacted: bool = True


def validate_task_id(task_id: str) -> str:
    """Validate a task ID before using it as a filename."""
    if not _TASK_ID.fullmatch(task_id):
        raise TraceError(
            "task_id must contain only lowercase letters, "
            "numbers, underscores, or hyphens"
        )

    return task_id


def redact_text(value: str) -> str:
    """Redact common secret forms from free text."""
    redacted = _ASSIGNMENT_PATTERN.sub(
        lambda match: (
            f"{match.group(1)}=[REDACTED]"
        ),
        value,
    )

    return _DATABASE_URL_PATTERN.sub(
        r"\1[REDACTED]\2",
        redacted,
    )


def redact_value(value: Any) -> Any:
    """Recursively redact sensitive structured values."""
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        return [
            redact_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            redact_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}

        for key, item in value.items():
            normalized = str(key).lower()

            if normalized in _SECRET_KEYS:
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_value(item)

        return redacted

    return value


def artifact_path(
    *,
    root: Path,
    task_id: str,
    suffix: str,
) -> Path:
    """Return a safe artifact path under an approved root."""
    validate_task_id(task_id)

    root_resolved = root.resolve()
    candidate = (
        root_resolved / f"{task_id}{suffix}"
    ).resolve()

    if candidate.parent != root_resolved:
        raise TraceError(
            "artifact path escaped the approved root"
        )

    return candidate


def write_trace(
    trace: WorkflowTrace,
    *,
    trace_root: Path,
) -> Path:
    """Write one redacted JSON trace without overwriting."""
    path = artifact_path(
        root=trace_root,
        task_id=trace.task_id,
        suffix=".json",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = redact_value(
        trace.model_dump(mode="json")
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as stream:
            json.dump(
                payload,
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
    except FileExistsError as exc:
        raise TraceError(
            f"trace already exists for task "
            f"{trace.task_id!r}"
        ) from exc

    return path