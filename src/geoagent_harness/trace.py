"""Structured, secret-redacted workflow traces."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.failures import FailureRecord
from geoagent_harness.redaction import (
    redact_text,
    redact_value,
)

_TASK_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")

class TraceError(RuntimeError):
    """Raised when a trace cannot be safely written."""


class TraceTimestamps(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime
    finished_at: datetime


class WorkflowTrace(BaseModel):
    """Complete structured execution record."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    task_id: str
    original_request: str

    context_references: list[str]
    selected_skills: list[str]
    
    plan_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    approval_id: str | None = None
    approved_step_ids: list[str] = Field(
        default_factory=list
    )

    tool_arguments: dict[str, dict[str, Any]]
    tool_results: dict[str, Any]
    validation_results: dict[str, Any] | None
    failure: FailureRecord | None = None

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