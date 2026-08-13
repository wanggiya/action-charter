"""Server-side verification for approved workflow execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.approvals import (
    ApprovalError,
    load_approval,
    load_planner_result,
)
from geoagent_harness.executor import (
    ExecutionEnvelope,
    ExecutorPolicyError,
    build_execution_envelope,
)
from geoagent_harness.mcp_server.settings import (
    MCPSettings,
    load_settings,
)
from geoagent_harness.orchestrator.workflow import (
    WorkflowRunResult,
    run_vector_postgis_workflow,
)
from geoagent_harness.skills.load_vector_to_postgis.service import (
    LoadVectorError,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)


class ApprovedWorkflowError(RuntimeError):
    """Raised when approved execution is not permitted."""


def _record_filename(
    value: str,
    *,
    label: str,
) -> str:
    """Accept only a plain JSON filename."""

    path = Path(value)

    if (
        path.name != value
        or path.suffix != ".json"
        or value in {".json", ".."}
    ):
        raise ApprovedWorkflowError(
            f"{label} must be a plain JSON filename"
        )

    return value


def validate_approved_workflow_request(
    *,
    execution_envelope: dict[str, Any],
    plan_filename: str,
    approval_filename: str,
    settings: MCPSettings,
) -> ExecutionEnvelope:
    """Independently rebuild and compare the execution envelope."""

    safe_plan_filename = _record_filename(
        plan_filename,
        label="plan_filename",
    )
    safe_approval_filename = _record_filename(
        approval_filename,
        label="approval_filename",
    )

    try:
        planner_result = load_planner_result(
            path=(
                settings.plan_root
                / safe_plan_filename
            ),
            plan_root=settings.plan_root,
        )

        approval = load_approval(
            path=(
                settings.approval_root
                / safe_approval_filename
            ),
            approval_root=settings.approval_root,
        )

        expected = build_execution_envelope(
            planner_result=planner_result,
            approval=approval,
            allowed_schemas=set(
                settings.allowed_schemas
            ),
        )
        require_supported_schema(
            execution_envelope,
            artifact_type=(
                ArtifactType.EXECUTION_ENVELOPE
            ),
        )

        supplied = ExecutionEnvelope.model_validate(
            execution_envelope
        )
    except (
        ApprovalError,
        ExecutorPolicyError,
        ValidationError,
        ValueError,
    ) as exc:
        raise ApprovedWorkflowError(
            "approved workflow request failed "
            "server-side verification"
        ) from exc

    if supplied != expected:
        raise ApprovedWorkflowError(
            "execution envelope does not match "
            "the server-verified plan and approval"
        )

    return expected


def run_approved_vector_postgis_workflow(
    *,
    execution_envelope: dict[str, Any],
    plan_filename: str,
    approval_filename: str,
    settings: MCPSettings | None = None,
) -> WorkflowRunResult:
    """Verify approval server-side, then run the fixed workflow."""

    active = settings or load_settings()

    if not active.enable_write_tools:
        raise LoadVectorError(
            "write tools are disabled"
        )

    verified = validate_approved_workflow_request(
        execution_envelope=execution_envelope,
        plan_filename=plan_filename,
        approval_filename=approval_filename,
        settings=active,
    )

    arguments = verified.tool_arguments

    return run_vector_postgis_workflow(
        path=Path(arguments.path),
        source_layer=arguments.source_layer,
        target_schema=arguments.target_schema,
        target_table=arguments.target_table,
        original_request=arguments.original_request,
        task_id=arguments.task_id,
        context_references=(
            arguments.context_references
        ),
        human_corrections=(
            arguments.human_corrections
        ),
        settings=active,
        plan_sha256=verified.plan_sha256,
        approval_id=verified.approval_id,
        approved_step_ids=(
            verified.approved_step_ids
        ),
    )
