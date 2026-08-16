"""Independent deterministic Executor Agent runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from geoagent_harness.agent_manifest import (
    AgentManifest,
    load_agent_manifest,
)
from geoagent_harness.approvals import (
    load_approval,
    load_planner_result,
)
from geoagent_harness.executor.policy import (
    build_execution_envelope,
)
from geoagent_harness.executor.schemas import (
    ExecutionEnvelope,
    ExecutorRunResult,
    WorkflowExecutionResult,
)
from geoagent_harness.mcp_client.executor import (
    APPROVED_EXECUTOR_TOOLS,
    APPROVED_RECIPE_TOOL,
    APPROVED_WORKFLOW_TOOL,
    MCPExecutorClient,
)
from geoagent_harness.mcp_client.schemas import (
    MCPToolCallResult,
)
from geoagent_harness.mcp_client.settings import (
    load_mcp_client_settings,
)


class ExecutorServiceError(RuntimeError):
    """Raised when approved execution cannot be accepted."""


class ExecutorClientProtocol(Protocol):
    async def execute_approved_workflow(
        self,
        *,
        envelope: ExecutionEnvelope,
        plan_filename: str,
        approval_filename: str,
    ) -> MCPToolCallResult:
        ...


def _validate_executor_manifest(
    manifest: AgentManifest,
) -> None:
    if manifest.id != "executor":
        raise ExecutorServiceError(
            "Executor runtime requires executor manifest"
        )

    allowed = {
        "health_check",
        *APPROVED_EXECUTOR_TOOLS,
    }

    if set(manifest.permissions.tools) != allowed:
        raise ExecutorServiceError(
            "Executor manifest tool allowlist is invalid"
        )

    if manifest.permissions.arbitrary_shell:
        raise ExecutorServiceError(
            "Executor cannot have arbitrary shell access"
        )

    if manifest.permissions.unrestricted_sql:
        raise ExecutorServiceError(
            "Executor cannot have unrestricted SQL access"
        )

    if manifest.permissions.filesystem_write:
        raise ExecutorServiceError(
            "Executor cannot have direct filesystem write access"
        )

    if manifest.permissions.database_write:
        raise ExecutorServiceError(
            "Executor cannot have direct database write access"
        )


async def execute_approved_plan(
    *,
    plan_file: Path,
    approval_file: Path,
    plan_root: Path,
    approval_root: Path,
    agents_root: Path,
    allowed_schemas: set[str] | frozenset[str],
    mcp_client: ExecutorClientProtocol | None = None,
) -> ExecutorRunResult:
    """Verify locally, call MCP, and validate its final result."""

    manifest = load_agent_manifest(
        "executor",
        agents_root,
    )
    _validate_executor_manifest(manifest)

    planner_result = load_planner_result(
        path=plan_file,
        plan_root=plan_root,
    )

    approval = load_approval(
        path=approval_file,
        approval_root=approval_root,
    )

    envelope = build_execution_envelope(
        planner_result=planner_result,
        approval=approval,
        allowed_schemas=allowed_schemas,
    )

    client = mcp_client or MCPExecutorClient(
        load_mcp_client_settings()
    )

    tool_result = await client.execute_approved_workflow(
        envelope=envelope,
        plan_filename=plan_file.name,
        approval_filename=approval_file.name,
    )

    try:
        workflow = WorkflowExecutionResult.model_validate(
            tool_result.result
        )
    except ValidationError as exc:
        raise ExecutorServiceError(
            "MCP returned an invalid workflow result"
        ) from exc

    if (
        workflow.final_status
        == "validated_success"
        and not workflow.validation_passed
    ):
        raise ExecutorServiceError(
            "MCP success conflicts with validation result"
        )

    if (
        workflow.final_status
        != "validated_success"
        and workflow.validation_passed
    ):
        raise ExecutorServiceError(
            "MCP failure conflicts with validation result"
        )

    return ExecutorRunResult(
        plan_sha256=envelope.plan_sha256,
        approval_id=envelope.approval_id,
        tool_name=APPROVED_WORKFLOW_TOOL,
        execution_performed=True,
        workflow=workflow,
    )