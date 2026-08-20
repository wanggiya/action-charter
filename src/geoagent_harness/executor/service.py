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
    ExecutorRecipeRunResult,
    ExecutorRunResult,
    WorkflowExecutionResult,
)
from geoagent_harness.mcp_client.executor import (
    APPROVED_EXECUTOR_TOOLS,
    APPROVED_RECIPE_TOOL,
    APPROVED_WORKFLOW_TOOL,
    MCPExecutorClient,
)
from geoagent_harness.recipes import (
    RecipeExecutionEnvelope,
    RecipeRunResult,
    build_recipe_execution_envelope,
    load_recipe,
    load_recipe_approval,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)
from geoagent_harness.mcp_client.schemas import (
    MCPToolCallResult,
)
from geoagent_harness.mcp_client.settings import (
    load_mcp_client_settings,
)

from geoagent_harness.recipes.evidence_schemas import (
    PersistedRecipeExecutionResult,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)

from geoagent_harness.recipes.evidence_storage import (
    recipe_run_result_sha256,
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


class ExecutorRecipeClientProtocol(Protocol):
    """Narrow client interface for approved recipe execution."""

    async def execute_approved_recipe(
        self,
        *,
        envelope: RecipeExecutionEnvelope,
        recipe_filename: str,
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
    
async def execute_approved_recipe_via_mcp(
    *,
    recipe_file: Path,
    approval_file: Path,
    recipe_root: Path,
    approval_root: Path,
    project_root: Path,
    agents_root: Path,
    mcp_client: (
        ExecutorRecipeClientProtocol | None
    ) = None,
) -> ExecutorRecipeRunResult:
    """Verify an approved recipe locally and execute it through MCP."""

    manifest = load_agent_manifest(
        "executor",
        agents_root,
    )
    _validate_executor_manifest(manifest)

    recipe = load_recipe(
        recipe_file,
        recipe_root=recipe_root,
    )

    approval = load_recipe_approval(
        approval_file,
        approval_root=approval_root,
    )

    registry = load_skill_registry(
        project_root
    )

    envelope = build_recipe_execution_envelope(
        recipe=recipe,
        approval=approval,
        registry=registry,
    )

    client = mcp_client or MCPExecutorClient(
        load_mcp_client_settings()
    )

    tool_result = await client.execute_approved_recipe(
        envelope=envelope,
        recipe_filename=recipe_file.name,
        approval_filename=approval_file.name,
    )

    if tool_result.tool_name != APPROVED_RECIPE_TOOL:
        raise ExecutorServiceError(
            "MCP returned a result for an unexpected tool"
        )

    try:
        require_supported_schema(
            tool_result.result,
            artifact_type=(
                ArtifactType
                .PERSISTED_RECIPE_EXECUTION_RESULT
            ),
        )

        persisted = (
            PersistedRecipeExecutionResult
            .model_validate(
                tool_result.result
            )
        )
    except (
        ValidationError,
        ValueError,
    ) as exc:
        raise ExecutorServiceError(
            "MCP returned an invalid persisted "
            "recipe result"
        ) from exc

    recipe_result = persisted.run_result
    execution_record = (
        persisted.execution_record
    )
    
    if (
        recipe_run_result_sha256(
            recipe_result
        )
        != execution_record.run_result_sha256
    ):
        raise ExecutorServiceError(
            "MCP recipe result digest conflicts "
            "with its execution record"
        )

    if (
        recipe_result.recipe_id
        != envelope.recipe_id
    ):
        raise ExecutorServiceError(
            "MCP recipe ID does not match the approved recipe"
        )

    if (
        recipe_result.recipe_sha256
        != envelope.recipe_sha256
    ):
        raise ExecutorServiceError(
            "MCP recipe digest does not match the approved recipe"
        )

    if (
        recipe_result.approval_id
        != envelope.approval_id
    ):
        raise ExecutorServiceError(
            "MCP approval ID does not match the approved recipe"
        )

    if (
        recipe_result.final_status
        == "validated_success"
        and not recipe_result.validation_performed
    ):
        raise ExecutorServiceError(
            "MCP recipe success lacks deterministic validation"
        )

    if (
        recipe_result.final_status
        == "validated_success"
        and any(
            (
                step.validation_performed
                and step.status
                != "validated_success"
            )
            or (
                not step.validation_performed
                and step.status
                != "completed"
            )
            for step in recipe_result.step_results
        )
    ):
        raise ExecutorServiceError(
            "MCP recipe success conflicts with a step result"
        )
        
    if (
        recipe_result.final_status
        == "validated_success"
        and recipe_result.failed_step_id
        is not None
    ):
        raise ExecutorServiceError(
            "MCP recipe success identifies a failed step"
        )

    return ExecutorRecipeRunResult(
        recipe_sha256=envelope.recipe_sha256,
        approval_id=envelope.approval_id,
        tool_name=APPROVED_RECIPE_TOOL,
        execution_performed=True,
        recipe=recipe_result,
        execution_record=execution_record,
    )

