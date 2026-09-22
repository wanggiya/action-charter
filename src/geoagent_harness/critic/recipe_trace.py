"""Deterministic, non-writing recipe-run to WorkflowTrace adaptation."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from typing import Any

from geoagent_harness.recipes.evidence_schemas import RecipeRunEvidence
from geoagent_harness.recipes.schemas import RecipeApprovalRecord, WorkflowRecipe
from geoagent_harness.redaction import redact_text, redact_value
from pathlib import Path

from geoagent_harness.trace import TraceTimestamps, WorkflowTrace, artifact_path


class RecipeTraceAdapterError(RuntimeError):
    """Raised when recipe evidence cannot truthfully become a trace."""


def canonical_recipe_trace_json(trace: WorkflowTrace) -> str:
    """Return the stable JSON identity reviewed by the operator."""

    return json.dumps(
        trace.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )


def recipe_trace_sha256(trace: WorkflowTrace) -> str:
    return hashlib.sha256(canonical_recipe_trace_json(trace).encode()).hexdigest()


def _task_id(recipe_id: str, evidence_sha256: str) -> str:
    safe = re.sub(r"[^a-z0-9_-]", "-", recipe_id.lower()).strip("-_")
    safe = safe[:48] or "recipe"
    return f"recipe-{safe}-{evidence_sha256[:12]}"


def build_recipe_trace_candidate(
    *,
    recipe: WorkflowRecipe,
    approval: RecipeApprovalRecord,
    evidence: RecipeRunEvidence,
    evidence_sha256: str,
    progress: dict[str, Any],
    context_references: list[str],
) -> WorkflowTrace:
    """Create a schema-valid trace only when all source identities agree."""

    if recipe.recipe_id != evidence.recipe_id:
        raise RecipeTraceAdapterError("recipe and evidence identities do not match")
    if approval.recipe_sha256 != evidence.recipe_sha256:
        raise RecipeTraceAdapterError("approval and evidence recipe digests do not match")
    if approval.approval_id != evidence.approval_id or approval.decision != "approved":
        raise RecipeTraceAdapterError("approved authority does not match recipe evidence")
    if progress.get("recipe_id") != evidence.recipe_id:
        raise RecipeTraceAdapterError("durable progress has no matching recipe identity")
    if progress.get("recipe_sha256") != evidence.recipe_sha256:
        raise RecipeTraceAdapterError("durable progress has no matching recipe digest")
    if progress.get("status") != evidence.final_status:
        raise RecipeTraceAdapterError("durable progress status conflicts with recipe evidence")
    try:
        started_at = datetime.fromisoformat(str(progress["started_at"]).replace("Z", "+00:00"))
        finished_at = datetime.fromisoformat(str(progress["finished_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise RecipeTraceAdapterError("durable execution timestamps are unavailable") from exc
    if started_at.tzinfo is None or finished_at.tzinfo is None or finished_at < started_at:
        raise RecipeTraceAdapterError("durable execution timestamps are invalid")

    recipe_steps = {step.step_id: step for step in recipe.steps}
    result_steps = {step.step_id: step for step in evidence.run_result.step_results}
    if set(recipe_steps) != set(result_steps):
        raise RecipeTraceAdapterError("recipe steps and run-result steps do not match")

    validation_checks: list[dict[str, Any]] = []
    validation_warnings: list[str] = []
    for step in evidence.run_result.step_results:
        result = step.validation_result
        if not isinstance(result, dict):
            continue
        checks = result.get("checks", [])
        if isinstance(checks, list):
            validation_checks.extend(
                {**redact_value(check), "step_id": step.step_id}
                for check in checks if isinstance(check, dict)
            )
        warnings = result.get("warnings", [])
        if isinstance(warnings, list):
            validation_warnings.extend(redact_text(str(item)) for item in warnings)

    validation_passed = evidence.final_status == "validated_success"
    return WorkflowTrace(
        task_id=_task_id(evidence.recipe_id, evidence_sha256),
        original_request=redact_text(recipe.original_request),
        context_references=[redact_text(item) for item in context_references],
        selected_skills=[step.skill_id for step in recipe.steps],
        recipe_sha256=evidence.recipe_sha256,
        approval_id=evidence.approval_id,
        approved_step_ids=list(approval.step_ids),
        tool_arguments={
            step_id: redact_value(step.arguments)
            for step_id, step in recipe_steps.items()
        },
        tool_results={
            step_id: redact_value(step.execution.result)
            for step_id, step in result_steps.items()
        },
        validation_results={
            "validation_kind": "recipe",
            "passed": validation_passed,
            "checks": validation_checks,
            "warnings": validation_warnings,
            "step_count": len(result_steps),
            "validated_step_count": sum(step.validation_performed for step in result_steps.values()),
        },
        artifacts=[artifact.path for artifact in evidence.artifacts],
        warnings=[redact_text(item) for item in [*evidence.warnings, *evidence.run_result.warnings]],
        final_status=evidence.final_status,
        human_corrections=[redact_text(item) for item in approval.human_corrections],
        timestamps=TraceTimestamps(started_at=started_at, finished_at=finished_at),
        versions={key: redact_text(value) for key, value in evidence.skill_versions.items()},
        secrets_redacted=True,
    )


def render_recipe_trace_report(trace: WorkflowTrace) -> str:
    """Render the minimum deterministic report required by Critic evidence."""

    digest = recipe_trace_sha256(trace)
    return "\n".join([
        f"# Workflow Trace: {trace.task_id}",
        "",
        "## Outcome",
        "",
        f"- Final status: `{trace.final_status}`",
        f"- Approval ID: `{trace.approval_id}`",
        f"- Recipe SHA-256: `{trace.recipe_sha256}`",
        f"- Trace candidate SHA-256: `{digest}`",
        "- Generated deterministically from immutable recipe-run evidence.",
        "- No model was called and no Critic result or release was created.",
        "- Secrets redacted: `true`",
        "",
    ])


def persist_recipe_trace_candidate(
    *,
    trace: WorkflowTrace,
    confirmed_trace_sha256: str,
    trace_root: Path,
    report_root: Path,
) -> tuple[Path, Path, str, str]:
    """Immutably store an exactly reviewed trace and deterministic report."""

    digest = recipe_trace_sha256(trace)
    if digest != confirmed_trace_sha256:
        raise RecipeTraceAdapterError("reviewed trace digest no longer matches")
    if trace_root.exists() and trace_root.is_symlink():
        raise RecipeTraceAdapterError("trace root cannot be a symlink")
    if report_root.exists() and report_root.is_symlink():
        raise RecipeTraceAdapterError("report root cannot be a symlink")
    trace_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)
    trace_path = artifact_path(root=trace_root, task_id=trace.task_id, suffix=".json")
    report_path = artifact_path(root=report_root, task_id=trace.task_id, suffix=".md")
    if trace_path.exists() or report_path.exists():
        raise RecipeTraceAdapterError("adapted trace or report already exists")

    trace_text = json.dumps(trace.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    report_text = render_recipe_trace_report(trace)
    trace_created = False
    try:
        with trace_path.open("x", encoding="utf-8") as stream:
            stream.write(trace_text)
            stream.flush()
            os.fsync(stream.fileno())
        trace_created = True
        with report_path.open("x", encoding="utf-8") as stream:
            stream.write(report_text)
            stream.flush()
            os.fsync(stream.fileno())
    except (FileExistsError, OSError) as exc:
        if trace_created:
            trace_path.unlink(missing_ok=True)
        raise RecipeTraceAdapterError("adapted trace evidence could not be stored atomically") from exc

    report_sha256 = hashlib.sha256(report_text.encode()).hexdigest()
    return trace_path, report_path, digest, report_sha256
