"""Existing workflows CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer
from geoagent_harness.contracts.failures import FailureStage
from geoagent_harness.apps.cli.common import _raise_typed_failure


def run_vector_postgis_workflow_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Vector dataset beneath the approved input root."
        ),
    ],
    target_table: Annotated[
        str,
        typer.Option(
            "--table",
            help="New PostGIS target table.",
        ),
    ],
    target_schema: Annotated[
        str,
        typer.Option(
            "--schema",
            help="Approved PostGIS schema.",
        ),
    ] = "agent_sandbox",
    source_layer: Annotated[
        str | None,
        typer.Option(
            "--layer",
            help="Required for multi-layer datasets.",
        ),
    ] = None,
    original_request: Annotated[
        str,
        typer.Option(
            "--request",
            help="Original task request stored in redacted form.",
        ),
    ] = "Load and validate an approved vector dataset.",
    task_id: Annotated[
        str | None,
        typer.Option(
            "--task-id",
            help="Optional lowercase reproducible task ID.",
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Run the complete validated vector-to-PostGIS workflow."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.agents.runtime.orchestrator.workflow import WorkflowError
    from geoagent_harness.task_actions.command_actions import orchestrator_workflow__run_vector_postgis_workflow as run_vector_postgis_workflow

    try:
        result = run_vector_postgis_workflow(
            path=path,
            source_layer=source_layer,
            target_schema=target_schema,
            target_table=target_table,
            original_request=original_request,
            task_id=task_id,
            settings=load_settings(),
        )
    except (WorkflowError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if result.final_status != "validated_success":
        raise typer.Exit(code=1)


def build_execution_envelope_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Approval JSON beneath the approval root.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    allowed_schemas: Annotated[
        str,
        typer.Option(
            "--allowed-schemas",
            help="Comma-separated approved PostGIS schemas.",
        ),
    ] = "agent_sandbox",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Build an approved envelope without executing it."""

    from geoagent_harness.core.policy.approvals import ApprovalError
    from geoagent_harness.task_actions.command_actions import approvals__load_approval as load_approval, approvals__load_planner_result as load_planner_result
    from geoagent_harness.agents.roles.executor import ExecutorPolicyError
    from geoagent_harness.task_actions.command_actions import executor__build_execution_envelope as build_execution_envelope

    schemas = {
        value.strip()
        for value in allowed_schemas.split(",")
        if value.strip()
    }

    if not schemas:
        typer.echo(
            "Error: at least one allowed schema is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
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
            allowed_schemas=schemas,
        )
    except (
        ApprovalError,
        ExecutorPolicyError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            envelope.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def mcp_http_smoke_command(
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Test internal MCP using only health_check."""

    import asyncio

    from geoagent_harness.platform.internal_mcp import MCPClientError, MCPReadOnlyClient
    from geoagent_harness.platform.internal_mcp import MCPClientSettingsError, load_mcp_client_settings

    async def run_smoke() -> dict:
        client = MCPReadOnlyClient(
            load_mcp_client_settings()
        )

        available_tools = await client.list_tools()

        health = await client.call_tool(
            "health_check"
        )

        return {
            "status": "ok",
            "transport": "streamable-http",
            "available_tools": available_tools,
            "called_tool": health.tool_name,
            "health": health.result,
        }

    try:
        payload = asyncio.run(run_smoke())
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except MCPClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except MCPClientSettingsError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def execute_approved_plan_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Approval JSON beneath the approval root.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    allowed_schemas: Annotated[
        str,
        typer.Option("--allowed-schemas"),
    ] = "agent_sandbox",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Execute one exact approved plan through MCP."""

    import asyncio

    from geoagent_harness.core.policy.approvals import ApprovalError
    from geoagent_harness.agents.roles.executor import ExecutorPolicyError
    from geoagent_harness.agents.roles.executor.service import ExecutorServiceError
    from geoagent_harness.task_actions.command_actions import executor_service__execute_approved_plan as execute_approved_plan
    from geoagent_harness.platform.internal_mcp import MCPClientError
    from geoagent_harness.platform.internal_mcp import MCPClientSettingsError

    schemas = {
        value.strip()
        for value in allowed_schemas.split(",")
        if value.strip()
    }

    if not schemas:
        typer.echo(
            "Error: at least one allowed schema is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        result = asyncio.run(
            execute_approved_plan(
                plan_file=plan_file,
                approval_file=approval_file,
                plan_root=plan_root,
                approval_root=approval_root,
                agents_root=agents_root,
                allowed_schemas=schemas,
            )
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.EXECUTION,
        )
    except MCPClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except (
        ApprovalError,
        ExecutorPolicyError,
        ExecutorServiceError,
        MCPClientSettingsError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if (
        result.workflow.final_status
        != "validated_success"
    ):
        raise typer.Exit(code=1)


def inspect_workflow_state_command(
    state_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "State JSON file beneath the trusted "
                "workflow-state root."
            ),
        ),
    ],
    state_root: Annotated[
        Path | None,
        typer.Option(
            "--state-root",
            help=(
                "Trusted workflow-state directory. "
                "Defaults to GEOAGENT_STATE_ROOT."
            ),
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Load and display validated workflow state."""

    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.core.ledger.workflow_state import WorkflowStateError
    from geoagent_harness.task_actions.command_actions import workflow_state__load_state as load_state

    active_root = (
        state_root
        if state_root is not None
        else load_settings().state_root
    )

    try:
        state = load_state(
            state_file,
            state_root=active_root,
        )
    except (
        WorkflowStateError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            state.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def assess_workflow_resume_command(
    state_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "State JSON file beneath the trusted "
                "workflow-state root."
            ),
        ),
    ],
    state_root: Annotated[
        Path | None,
        typer.Option(
            "--state-root",
            help=(
                "Trusted workflow-state directory. "
                "Defaults to GEOAGENT_STATE_ROOT."
            ),
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess safe continuation without modifying state."""

    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.core.ledger.workflow_state import WorkflowStateError
    from geoagent_harness.task_actions.command_actions import workflow_state__assess_resume as assess_resume, workflow_state__load_state as load_state

    active_root = (
        state_root
        if state_root is not None
        else load_settings().state_root
    )

    try:
        state = load_state(
            state_file,
            state_root=active_root,
        )

        assessment = assess_resume(state)
    except (
        WorkflowStateError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            assessment.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )
