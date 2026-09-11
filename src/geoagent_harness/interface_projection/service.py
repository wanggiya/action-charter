"""Create a sanitized graph from one exact validated workflow trace."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from geoagent_harness.trace import TraceError, WorkflowTrace, validate_task_id

from .schemas import InterfaceEdge, InterfaceNode, InterfaceWorkflowProjection

MAX_TRACE_BYTES = 1_000_000


class InterfaceProjectionError(RuntimeError):
    """Raised when a browser-safe projection cannot be produced."""


def _load_trace(task_id: str, trace_root: Path) -> WorkflowTrace:
    try:
        validate_task_id(task_id)
        if trace_root.is_symlink():
            raise InterfaceProjectionError("trace root cannot be a symlink")
        root = trace_root.resolve(strict=True)
        if not root.is_dir():
            raise InterfaceProjectionError("trace root must be a directory")
        path = root / f"{task_id}.json"
        if path.is_symlink():
            raise InterfaceProjectionError("trace file cannot be a symlink")
        resolved = path.resolve(strict=True)
        if resolved.parent != root or not resolved.is_file():
            raise InterfaceProjectionError("trace file is outside the approved root")
        if resolved.stat().st_size > MAX_TRACE_BYTES:
            raise InterfaceProjectionError("trace file exceeds the projection limit")
        trace = WorkflowTrace.model_validate_json(resolved.read_text(encoding="utf-8"))
    except InterfaceProjectionError:
        raise
    except (OSError, TraceError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise InterfaceProjectionError("validated workflow trace could not be loaded") from exc
    if trace.task_id != task_id or not trace.secrets_redacted:
        raise InterfaceProjectionError("workflow trace identity or redaction claim is invalid")
    return trace


def project_workflow_trace(*, task_id: str, trace_root: Path) -> InterfaceWorkflowProjection:
    """Project one allowlisted trace identity without exposing trace payloads."""

    trace = _load_trace(task_id, trace_root)
    failed = trace.final_status != "validated_success"
    approval = "approved" if trace.approval_id else "pending"
    plan = "complete" if trace.plan_sha256 else "pending"
    tools = "failed" if trace.failure else ("complete" if trace.tool_results else "pending")
    validation = "verified" if trace.final_status == "validated_success" else "failed"
    final = "failed" if failed else "verified"
    evidence_name = f"{task_id}.json"

    nodes = [
        InterfaceNode(id="request", title="Spatial request", subtitle="Redacted operator request", kind="input", x=60, y=250, status="complete", authority="Operator input", evidence=evidence_name),
        InterfaceNode(id="planner", title="Planner", subtitle="Digest-bound proposal", kind="agent", x=300, y=105, status=plan, authority="Proposal only", evidence="plan digest"),
        InterfaceNode(id="policy", title="Policy gate", subtitle="Deterministic checks", kind="policy", x=300, y=390, status=final, authority="No model authority", evidence=evidence_name),
        InterfaceNode(id="approval", title="Human approval", subtitle="Recorded operator decision", kind="approval", x=555, y=250, status=approval, authority="Operator only", evidence="approval record"),
        InterfaceNode(id="executor", title="Executor", subtitle="Exact approved scope", kind="agent", x=805, y=105, status=tools, authority="Execution envelope", evidence=evidence_name),
        InterfaceNode(id="mcp", title="Tool boundary", subtitle="Recorded tool calls", kind="tool", x=805, y=390, status=tools, authority="Fixed tools only", evidence=evidence_name),
        InterfaceNode(id="validation", title="Validation", subtitle="Recorded deterministic result", kind="policy", x=1060, y=250, status=validation, authority="Deterministic", evidence=evidence_name),
        InterfaceNode(id="evidence", title="Trace evidence", subtitle="Sanitized projection source", kind="evidence", x=1305, y=250, status=final, authority="Read-only", evidence=evidence_name),
    ]
    pairs = [("request", "planner"), ("request", "policy"), ("planner", "approval"), ("policy", "approval"), ("approval", "executor"), ("approval", "mcp"), ("executor", "validation"), ("mcp", "validation"), ("validation", "evidence")]
    return InterfaceWorkflowProjection(
        id=f"trace-{task_id}", title="Validated workflow trace", correlationId=task_id,
        nodes=nodes, edges=[InterfaceEdge.model_validate({"from": start, "to": end}) for start, end in pairs],
    )
