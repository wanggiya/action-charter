"""Create a sanitized graph from one exact validated workflow trace."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from geoagent_harness.trace import TraceError, WorkflowTrace, validate_task_id

from .schemas import (
    InterfaceEdge,
    InterfaceEvidencePreview,
    InterfaceNode,
    InterfaceNodeDetails,
    InterfaceObservedFact,
    InterfaceProjectionExportResult,
    InterfaceWorkflowCatalog,
    InterfaceWorkflowProjection,
    InterfaceWorkflowSummary,
)

MAX_TRACE_BYTES = 1_000_000
MAX_CATALOG_WORKFLOWS = 50


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
    duration_ms = max(0, int((trace.timestamps.finished_at - trace.timestamps.started_at).total_seconds() * 1000))
    common_time = {
        "startedAt": trace.timestamps.started_at,
        "finishedAt": trace.timestamps.finished_at,
        "durationMs": duration_ms,
    }
    def fact(label: str, value: object) -> InterfaceObservedFact:
        return InterfaceObservedFact(label=label, value=str(value))

    trace_preview = InterfaceEvidencePreview(
        title="Validated workflow trace",
        category="trace",
        status="verified" if not failed else "failed",
        reference=evidence_name,
        facts=[fact("Final status", trace.final_status), fact("Secrets redacted", trace.secrets_redacted)],
    )
    plan_preview = InterfaceEvidencePreview(
        title="Digest-bound plan",
        category="plan",
        status="recorded" if trace.plan_sha256 else "pending",
        reference="plan digest",
        digest=trace.plan_sha256,
        facts=[fact("Approved steps", len(trace.approved_step_ids))],
    )
    approval_preview = InterfaceEvidencePreview(
        title="Human approval record",
        category="approval",
        status="recorded" if trace.approval_id else "pending",
        reference="approval record",
        facts=[fact("Approval recorded", bool(trace.approval_id)), fact("Approved steps", len(trace.approved_step_ids))],
    )
    validation_preview = InterfaceEvidencePreview(
        title="Deterministic validation",
        category="validation",
        status="verified" if trace.final_status == "validated_success" else "failed",
        reference="validation result",
        facts=[fact("Result recorded", trace.validation_results is not None), fact("Final status", trace.final_status)],
    )
    artifact_previews = [
        InterfaceEvidencePreview(
            title=f"Artifact {index}",
            category="artifact",
            status="recorded",
            reference=Path(artifact).name[:120] or "unnamed artifact",
            facts=[fact("Path exposure", "basename only")],
        )
        for index, artifact in enumerate(trace.artifacts[:4], start=1)
    ]

    nodes = [
        InterfaceNode(id="request", title="Spatial request", subtitle="Redacted operator request", kind="input", x=60, y=250, status="complete", authority="Operator input", evidence=evidence_name, details=InterfaceNodeDetails(summary="A validated request entered the governed workflow. Its text and context remain redacted.", observedFacts=[fact("Context references", len(trace.context_references)), fact("Selected skills", len(trace.selected_skills))])),
        InterfaceNode(id="planner", title="Planner", subtitle="Digest-bound proposal", kind="agent", x=300, y=105, status=plan, authority="Proposal only", evidence="plan digest", details=InterfaceNodeDetails(summary="The Planner could propose bounded work but could not execute it.", observedFacts=[fact("Plan recorded", bool(trace.plan_sha256)), fact("Digest algorithm", "SHA-256")], evidencePreviews=[plan_preview])),
        InterfaceNode(id="policy", title="Policy gate", subtitle="Deterministic checks", kind="policy", x=300, y=390, status=final, authority="No model authority", evidence=evidence_name, details=InterfaceNodeDetails(summary="Deterministic workflow policy produced the recorded final classification.", observedFacts=[fact("Final status", trace.final_status), fact("Model authority", "None")])),
        InterfaceNode(id="approval", title="Human approval", subtitle="Recorded operator decision", kind="approval", x=555, y=250, status=approval, authority="Operator only", evidence="approval record", details=InterfaceNodeDetails(summary="The projection reports approval presence without exposing the approval identifier.", observedFacts=[fact("Approval recorded", bool(trace.approval_id)), fact("Approved steps", len(trace.approved_step_ids))], evidencePreviews=[approval_preview])),
        InterfaceNode(id="executor", title="Executor", subtitle="Exact approved scope", kind="agent", x=805, y=105, status=tools, authority="Execution envelope", evidence=evidence_name, details=InterfaceNodeDetails(summary="The Executor remained limited to the recorded approved workflow envelope.", observedFacts=[fact("Tool operations", len(trace.tool_results)), fact("Failure recorded", bool(trace.failure))], **common_time)),
        InterfaceNode(id="mcp", title="Tool boundary", subtitle="Recorded tool calls", kind="tool", x=805, y=390, status=tools, authority="Fixed tools only", evidence=evidence_name, details=InterfaceNodeDetails(summary="Only aggregate operation facts are projected; arguments and results remain private.", observedFacts=[fact("Tool calls", len(trace.tool_arguments)), fact("Tool results", len(trace.tool_results))])),
        InterfaceNode(id="validation", title="Validation", subtitle="Recorded deterministic result", kind="policy", x=1060, y=250, status=validation, authority="Deterministic", evidence=evidence_name, details=InterfaceNodeDetails(summary="Validation status is derived from the validated trace rather than an executor claim.", observedFacts=[fact("Validation present", trace.validation_results is not None), fact("Final status", trace.final_status)], findings=([f"{trace.failure.stage.value}: {trace.failure.code}"] if trace.failure else []), evidencePreviews=[validation_preview])),
        InterfaceNode(id="evidence", title="Trace evidence", subtitle="Sanitized projection source", kind="evidence", x=1305, y=250, status=final, authority="Read-only", evidence=evidence_name, details=InterfaceNodeDetails(summary="This node identifies the sanitized trace projection without exposing artifact paths or payloads.", observedFacts=[fact("Artifacts recorded", len(trace.artifacts)), fact("Warnings recorded", len(trace.warnings)), fact("Secrets redacted", trace.secrets_redacted)], evidencePreviews=[trace_preview, plan_preview, approval_preview, validation_preview, *artifact_previews], **common_time)),
    ]
    pairs = [("request", "planner"), ("request", "policy"), ("planner", "approval"), ("policy", "approval"), ("approval", "executor"), ("approval", "mcp"), ("executor", "validation"), ("mcp", "validation"), ("validation", "evidence")]
    return InterfaceWorkflowProjection(
        id=f"trace-{task_id}", title="Validated workflow trace", correlationId=task_id,
        nodes=nodes, edges=[InterfaceEdge.model_validate({"from": start, "to": end}) for start, end in pairs],
    )


def _atomic_json(path: Path, value: object) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=".projection-", delete=False) as stream:
            temporary = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        if temporary:
            try:
                Path(temporary).unlink(missing_ok=True)
            except OSError:
                pass
        raise InterfaceProjectionError("interface projection could not be written") from exc


def export_workflow_catalog(*, trace_root: Path, output_root: Path) -> InterfaceProjectionExportResult:
    """Export a capped catalog and sanitized projections from validated traces."""

    try:
        if trace_root.is_symlink():
            raise InterfaceProjectionError("trace root cannot be a symlink")
        source_root = trace_root.resolve(strict=True)
        if not source_root.is_dir():
            raise InterfaceProjectionError("trace root must be a directory")
        candidates = sorted(source_root.glob("*.json"))
    except OSError as exc:
        raise InterfaceProjectionError("trace inventory could not be read") from exc
    if len(candidates) > MAX_CATALOG_WORKFLOWS:
        raise InterfaceProjectionError("trace inventory exceeds the workflow limit")

    projections: list[tuple[WorkflowTrace, InterfaceWorkflowProjection]] = []
    for candidate in candidates:
        if candidate.is_symlink() or candidate.stem != candidate.name[:-5]:
            raise InterfaceProjectionError("trace inventory contains an unsafe entry")
        projection = project_workflow_trace(task_id=candidate.stem, trace_root=source_root)
        projections.append((_load_trace(candidate.stem, source_root), projection))
    projections.sort(key=lambda item: (item[0].timestamps.finished_at, item[0].task_id), reverse=True)

    if output_root.is_symlink():
        raise InterfaceProjectionError("interface output root cannot be a symlink")
    try:
        output_root.mkdir(parents=True, exist_ok=True)
        destination = output_root.resolve(strict=True)
    except OSError as exc:
        raise InterfaceProjectionError("interface output root is unavailable") from exc
    if not destination.is_dir():
        raise InterfaceProjectionError("interface output root must be a directory")

    summaries: list[InterfaceWorkflowSummary] = []
    projection_files: list[str] = []
    for trace, projection in projections:
        file_name = f"{trace.task_id}.json"
        _atomic_json(destination / file_name, projection.model_dump(mode="json", by_alias=True))
        projection_files.append(file_name)
        summaries.append(InterfaceWorkflowSummary(
            taskId=trace.task_id,
            status=trace.final_status,
            finishedAt=trace.timestamps.finished_at,
            projectionPath=f"/runtime/{file_name}",
        ))
    catalog = InterfaceWorkflowCatalog(workflows=summaries)
    _atomic_json(destination / "catalog.json", catalog.model_dump(mode="json", by_alias=True))
    return InterfaceProjectionExportResult(
        workflow_count=len(projection_files),
        projection_files=projection_files,
    )
