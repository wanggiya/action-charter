"""Create a sanitized graph from one exact validated workflow trace."""

from __future__ import annotations

import json
import os
import re
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
MAX_PROJECTED_OPERATIONS = 20
_SAFE_OPERATION_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


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

    operation_names = list(dict.fromkeys([*trace.tool_arguments, *trace.tool_results]))
    if (
        any(name.casefold() == "snakemake" for name in trace.versions)
        and not any("snakemake" in name.casefold() for name in operation_names)
    ):
        operation_names.insert(0, "snakemake")
    if len(operation_names) > MAX_PROJECTED_OPERATIONS:
        raise InterfaceProjectionError("workflow operation count exceeds the projection limit")

    operation_nodes: list[InterfaceNode] = []
    for index, operation_name in enumerate(operation_names, start=1):
        safe_name = operation_name if _SAFE_OPERATION_NAME.fullmatch(operation_name) else None
        title = safe_name.replace("_", " ").replace("-", " ").title() if safe_name else f"Recorded tool {index}"
        engine_recorded = operation_name == "snakemake" and "snakemake" in {
            name.casefold() for name in trace.versions
        }
        call_recorded = operation_name in trace.tool_arguments or engine_recorded
        result_recorded = operation_name in trace.tool_results or engine_recorded
        operation_failed = trace.failure is not None and index == len(operation_names)
        operation_nodes.append(InterfaceNode(
            id=f"tool-{index}",
            title=title[:80],
            subtitle="Recorded governed operation",
            kind="tool",
            category="tool",
            group="execution",
            x=840 + ((index - 1) * 240),
            y=360,
            status="failed" if operation_failed else ("complete" if result_recorded else "pending"),
            authority="Typed tool contract",
            performedBy="MCP tool boundary",
            evidence=evidence_name,
            details=InterfaceNodeDetails(
                summary="This node represents one recorded tool operation. Arguments and result payloads remain excluded.",
                observedFacts=[fact("Call recorded", call_recorded), fact("Result recorded", result_recorded), fact("Recorded order", index)],
            ),
        ))

    validation_x = 840 + (max(1, len(operation_nodes)) * 240)
    evidence_x = validation_x + 245

    nodes = [InterfaceNode(id="request", title="Submit request", subtitle="Redacted governed intent", kind="input", category="input", group="intake", x=60, y=70, status="complete", authority="Operator input", performedBy="User", evidence=evidence_name, details=InterfaceNodeDetails(summary="A validated request entered the governed workflow. Its text remains redacted.", observedFacts=[fact("Selected skills", len(trace.selected_skills))]))]
    if trace.context_references:
        nodes.append(InterfaceNode(id="input-data", title="Referenced input data", subtitle="Bounded context boundary", kind="data", category="input", group="intake", x=60, y=260, status="complete", authority="Read-only input boundary", performedBy="Input boundary", evidence=evidence_name, details=InterfaceNodeDetails(summary="The Planner received bounded input references. Paths and payloads remain excluded.", observedFacts=[fact("Context references", len(trace.context_references)), fact("Path exposure", "None")])))
    if trace.plan_sha256:
        nodes.append(InterfaceNode(id="planner", title="Create plan", subtitle="Digest-bound proposal", kind="agent", category="planning", group="planning", x=330, y=70, status=plan, authority="Proposal only", performedBy="Planner agent", evidence="plan digest", details=InterfaceNodeDetails(summary="The Planner could inspect bounded inputs and propose work, but could not execute it.", observedFacts=[fact("Plan recorded", True), fact("Digest algorithm", "SHA-256"), fact("Input references", len(trace.context_references))], evidencePreviews=[plan_preview])))
    if trace.approval_id:
        nodes.append(InterfaceNode(id="approval", title="Record approval", subtitle="Reviewed operator decision", kind="approval", category="approval", group="governance", x=585, y=70, status=approval, authority="Operator only", performedBy="Human operator", evidence="approval record", details=InterfaceNodeDetails(summary="The projection reports approval presence without exposing the approval identifier.", observedFacts=[fact("Approval recorded", True), fact("Approved steps", len(trace.approved_step_ids))], evidencePreviews=[approval_preview])))
    if operation_nodes or trace.failure:
        nodes.append(InterfaceNode(id="executor", title="Execute plan", subtitle="Exact approved scope", kind="agent", category="execution", group="execution", x=840, y=70, status=tools, authority="Execution envelope", performedBy="Executor agent", evidence=evidence_name, details=InterfaceNodeDetails(summary="The Executor remained limited to the recorded approved workflow envelope.", observedFacts=[fact("Recorded operations", len(operation_names)), fact("Failure recorded", bool(trace.failure))], **common_time)))
    nodes.extend(operation_nodes)
    if trace.validation_results is not None:
        nodes.append(InterfaceNode(id="validation", title="Validate result", subtitle="Recorded deterministic result", kind="policy", category="validation", group="assurance", x=validation_x, y=360, status=validation, authority="Deterministic", performedBy="Validator", evidence=evidence_name, details=InterfaceNodeDetails(summary="Validation status is derived from the validated trace rather than an executor claim.", observedFacts=[fact("Validation present", True), fact("Final status", trace.final_status)], findings=([f"{trace.failure.stage.value}: {trace.failure.code}"] if trace.failure else []), evidencePreviews=[validation_preview])))
    projected_previews = [trace_preview]
    if trace.plan_sha256:
        projected_previews.append(plan_preview)
    if trace.approval_id:
        projected_previews.append(approval_preview)
    if trace.validation_results is not None:
        projected_previews.append(validation_preview)
    projected_previews.extend(artifact_previews)
    nodes.append(InterfaceNode(id="evidence", title="Record evidence", subtitle="Sanitized projection source", kind="evidence", category="evidence", group="assurance", x=evidence_x, y=360, status=final, authority="Read-only", performedBy="Evidence service", evidence=evidence_name, details=InterfaceNodeDetails(summary="This node identifies the sanitized trace projection without exposing artifact paths or payloads.", observedFacts=[fact("Artifacts recorded", len(trace.artifacts)), fact("Warnings recorded", len(trace.warnings)), fact("Secrets redacted", trace.secrets_redacted)], evidencePreviews=projected_previews, **common_time)))

    node_ids = {node.id for node in nodes}
    edges: list[InterfaceEdge] = []
    participants = [node_id for node_id in ("request", "planner", "approval", "executor") if node_id in node_ids]
    for start, end in zip(participants, participants[1:]):
        label = {
            ("request", "planner"): "request",
            ("planner", "approval"): "proposal",
            ("approval", "executor"): "approved scope",
        }.get((start, end), "reviewed handoff")
        edges.append(InterfaceEdge.model_validate({"from": start, "to": end, "kind": "control", "label": label}))
    if "input-data" in node_ids:
        input_target = "planner" if "planner" in node_ids else next((node_id for node_id in ("executor", "validation") if node_id in node_ids), "evidence")
        edges.append(InterfaceEdge.model_validate({"from": "input-data", "to": input_target, "kind": "data", "label": "bounded inputs"}))
    previous = "executor" if "executor" in node_ids else participants[-1]
    for index, operation_node in enumerate(operation_nodes):
        edges.append(InterfaceEdge.model_validate({"from": previous, "to": operation_node.id, "kind": "tool" if index == 0 else "data", "label": "bounded call" if index == 0 else "recorded order"}))
        previous = operation_node.id
    if "validation" in node_ids:
        edges.append(InterfaceEdge.model_validate({"from": previous, "to": "validation", "kind": "data", "label": "final result"}))
        previous = "validation"
    edges.append(InterfaceEdge.model_validate({"from": previous, "to": "evidence", "kind": "evidence", "label": "verified record"}))
    return InterfaceWorkflowProjection(
        id=f"trace-{task_id}", title="Validated workflow trace", correlationId=task_id,
        nodes=nodes, edges=edges,
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
