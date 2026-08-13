"""Typer command-line interface."""

import json
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from geoagent_harness.agent_manifest import load_agent_manifest

from geoagent_harness.failures import (
    FailureStage,
    failure_from_exception,
)


app = typer.Typer(
    name="geoagent",
    help="Run allowlisted GeoAgent Skill Harness operations.",
    no_args_is_help=True,
)

def _raise_typed_failure(
    exception: BaseException,
    *,
    stage: FailureStage,
) -> NoReturn:
    """Render one redacted typed failure and exit."""

    failure = failure_from_exception(
        exception,
        stage=stage,
    )

    typer.echo(
        (
            f"Error [{failure.code}]: "
            f"{failure.message}"
        ),
        err=True,
    )

    raise typer.Exit(
        code=failure.exit_code
    ) from exception

@app.command("agent-info")
def agent_info_command(
    role: Annotated[
        str, typer.Argument(help="Logical role: planner, executor, or critic.")
    ],
    agents_root: Annotated[
        Path, typer.Option("--agents-root", help="Trusted agent manifest root.")
    ] = Path("/app/agents"),
) -> None:
    """Validate and display a redacted static agent manifest.

    Checkpoint 1 intentionally exits after validation; it does not call Ollama
    or start an agent loop.
    """
    try:
        manifest = load_agent_manifest(role, agents_root)
    except (OSError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "id": manifest.id,
                "model_ref": manifest.model_ref,
                "purpose": manifest.purpose,
                "allowed_tools": manifest.permissions.tools,
                "checkpoint_status": "manifest-valid; role-runtime-implemented",
            },
            separators=(",", ":"),
        )
    )


@app.command("inspect-vector")
def inspect_vector_command(
    path: Annotated[Path, typer.Argument(help="Dataset beneath data/input.")],
    input_root: Annotated[
        Path,
        typer.Option(
            "--input-root",
            help="Trusted input root; intended for deployment configuration/tests.",
        ),
    ] = Path("data/input"),
    pretty: Annotated[
        bool, typer.Option("--pretty", help="Indent the JSON response.")
    ] = False,
) -> None:
    """Inspect an approved vector dataset without executing a shell."""
    from geoagent_harness.skills.inspect_vector.service import (
        InspectVectorError,
        inspect_vector,
    )
    try:
        result = inspect_vector(path=path, input_root=input_root)
    except InspectVectorError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

@app.command("load-vector-to-postgis")
def load_vector_to_postgis_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Vector dataset beneath the approved input root."
        ),
    ],
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved target schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="New target table name."),
    ] = "loaded_vector",
    source_layer: Annotated[
        str | None,
        typer.Option(
            "--layer",
            help="Required when the source has multiple layers.",
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Load one approved vector layer into a new PostGIS table."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.skills.load_vector_to_postgis.service import (
        LoadVectorError,
        load_vector_to_postgis,
    )

    try:
        result = load_vector_to_postgis(
            path=path,
            target_schema=target_schema,
            target_table=target_table,
            source_layer=source_layer,
            settings=load_settings(),
        )
    except (LoadVectorError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

@app.command("validate-postgis-layer")
def validate_postgis_layer_command(
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved PostGIS schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="PostGIS table to validate."),
    ] = "checkpoint3b_sample_points",
    expected_row_count: Annotated[
        int | None,
        typer.Option("--expected-row-count"),
    ] = None,
    expected_srid: Annotated[
        int | None,
        typer.Option("--expected-srid"),
    ] = None,
    expected_geometry_type: Annotated[
        str | None,
        typer.Option("--expected-geometry-type"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Deterministically validate one approved PostGIS layer."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.verifier.postgis import (
        PostGISVerificationError,
        validate_postgis_layer,
    )

    try:
        result = validate_postgis_layer(
            target_schema=target_schema,
            target_table=target_table,
            expected_row_count=expected_row_count,
            expected_srid=expected_srid,
            expected_geometry_type=expected_geometry_type,
            settings=load_settings(),
        )
    except (PostGISVerificationError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if not result.passed:
        raise typer.Exit(code=1)

@app.command("run-vector-postgis-workflow")
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
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.orchestrator.workflow import (
        WorkflowError,
        run_vector_postgis_workflow,
    )

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


@app.command("plan-task")
def plan_task_command(
    original_request: Annotated[
        str,
        typer.Option(
            "--request",
            help="Task request to plan without executing.",
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help="Root containing trusted context files.",
        ),
    ] = Path("."),
    agents_root: Annotated[
        Path,
        typer.Option(
            "--agents-root",
            help="Root containing trusted agent manifests.",
        ),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Create and validate a plan without executing it."""

    from geoagent_harness.context_pack import (
        ContextPackError,
    )
    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )
    from geoagent_harness.planner import (
        PlannerAgentError,
        plan_task,
    )

    try:
        result = plan_task(
            original_request=original_request,
            project_root=project_root,
            agents_root=agents_root,
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.PLANNING,
        )
    except ModelClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except (
        ContextPackError,
        ModelSettingsError,
        PlannerAgentError,
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
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

@app.command("plan-digest")
def plan_digest_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved root containing saved plans.",
        ),
    ] = Path("plans"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Calculate the canonical digest of a validated plan."""

    from geoagent_harness.approvals import (
        ApprovalError,
        load_planner_result,
        plan_sha256,
    )

    try:
        planner_result = load_planner_result(
            path=plan_file,
            plan_root=plan_root,
        )

        payload = {
            "status": "ok",
            "plan_sha256": plan_sha256(
                planner_result.plan
            ),
            "plan_file": plan_file.as_posix(),
        }
    except ApprovalError as exc:
        typer.echo(f"Error: {exc}", err=True)
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

@app.command("approve-plan")
def approve_plan_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Planner result JSON beneath the plan root.",
        ),
    ],
    step_ids: Annotated[
        list[str],
        typer.Option(
            "--step",
            help=(
                "Plan step to approve or deny; "
                "repeat for multiple steps."
            ),
        ),
    ],
    approver: Annotated[
        str,
        typer.Option(
            "--approver",
            help="Human or local operator recording the decision.",
        ),
    ],
    reason: Annotated[
        str,
        typer.Option(
            "--reason",
            help="Reason for the approval decision.",
        ),
    ],
    decision: Annotated[
        str,
        typer.Option(
            "--decision",
            help="Either approved or denied.",
        ),
    ] = "approved",
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    valid_for_minutes: Annotated[
        int | None,
        typer.Option(
            "--valid-for-minutes",
            help=(
                "Optional approval lifetime. "
                "Omit for no expiration."
            ),
        ),
    ] = None,
    corrections: Annotated[
        list[str] | None,
        typer.Option(
            "--correction",
            help=(
                "Human correction; repeat for multiple "
                "corrections."
            ),
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Record an append-only decision for an exact plan."""

    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    from geoagent_harness.approvals import (
        ApprovalError,
        create_approval,
        load_planner_result,
    )

    if decision not in {"approved", "denied"}:
        typer.echo(
            "Error: decision must be approved or denied",
            err=True,
        )
        raise typer.Exit(code=2)

    if (
        valid_for_minutes is not None
        and valid_for_minutes <= 0
    ):
        typer.echo(
            "Error: valid-for-minutes must be positive",
            err=True,
        )
        raise typer.Exit(code=2)

    active_now = datetime.now(timezone.utc)

    expires_at = (
        active_now
        + timedelta(minutes=valid_for_minutes)
        if valid_for_minutes is not None
        else None
    )

    try:
        planner_result = load_planner_result(
            path=plan_file,
            plan_root=plan_root,
        )

        record, path = create_approval(
            planner_result=planner_result,
            step_ids=step_ids,
            decision=decision,
            approver=approver,
            reason=reason,
            approval_root=approval_root,
            project_root=project_root,
            human_corrections=corrections,
            expires_at=expires_at,
            now=active_now,
        )
    except (ApprovalError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "status": "recorded",
                "approval_path": path.as_posix(),
                "approval": record.model_dump(
                    mode="json"
                ),
            },
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )
    
@app.command("verify-plan-approval")
def verify_plan_approval_command(
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
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify approval for every approval-required plan step."""

    from geoagent_harness.approvals import (
        ApprovalError,
        load_approval,
        load_planner_result,
        verify_approval,
    )

    try:
        planner_result = load_planner_result(
            path=plan_file,
            plan_root=plan_root,
        )

        approval = load_approval(
            path=approval_file,
            approval_root=approval_root,
        )

        required_steps = [
            step.step_id
            for step in planner_result.plan.steps
            if step.requires_approval
        ]

        verification = verify_approval(
            approval=approval,
            plan=planner_result.plan,
            required_step_ids=required_steps,
        )
    except ApprovalError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            verification.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not verification.approved:
        raise typer.Exit(code=1)

@app.command("build-execution-envelope")
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

    from geoagent_harness.approvals import (
        ApprovalError,
        load_approval,
        load_planner_result,
    )
    from geoagent_harness.executor import (
        ExecutorPolicyError,
        build_execution_envelope,
    )

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

@app.command("mcp-http-smoke")
def mcp_http_smoke_command(
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Test internal MCP using only health_check."""

    import asyncio

    from geoagent_harness.mcp_client import (
        MCPClientError,
        MCPClientSettingsError,
        MCPReadOnlyClient,
        load_mcp_client_settings,
    )

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
    
@app.command("execute-approved-plan")
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

    from geoagent_harness.approvals import (
        ApprovalError,
    )
    from geoagent_harness.executor import (
        ExecutorPolicyError,
    )
    from geoagent_harness.executor.service import (
        ExecutorServiceError,
        execute_approved_plan,
    )
    from geoagent_harness.mcp_client import (
        MCPClientError,
        MCPClientSettingsError,
    )

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

@app.command("inspect-workflow-state")
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

    from geoagent_harness.mcp_server.settings import (
        load_settings,
    )
    from geoagent_harness.workflow_state import (
        WorkflowStateError,
        load_state,
    )

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


@app.command("assess-workflow-resume")
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

    from geoagent_harness.mcp_server.settings import (
        load_settings,
    )
    from geoagent_harness.workflow_state import (
        WorkflowStateError,
        assess_resume,
        load_state,
    )

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

@app.command("build-critic-evidence")
def build_critic_evidence_command(
    trace_path: Annotated[
        Path,
        typer.Argument(
            help="JSON trace beneath the approved trace root.",
        ),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Markdown report beneath the approved report root.",
        ),
    ],
    trace_root: Annotated[
        Path,
        typer.Option(
            "--trace-root",
            help="Trusted trace directory.",
        ),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option(
            "--report-root",
            help="Trusted report directory.",
        ),
    ] = Path("reports"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Build redacted deterministic evidence for the Critic Agent."""

    from geoagent_harness.critic.evidence import (
        CriticEvidenceError,
        build_critic_evidence,
    )

    try:
        evidence = build_critic_evidence(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
        )
    except CriticEvidenceError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            evidence.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

@app.command("critique-task")
def critique_task_command(
    trace_path: Annotated[
        Path,
        typer.Argument(
            help="JSON trace beneath the approved trace root.",
        ),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Markdown report beneath the approved report root.",
        ),
    ],
    trace_root: Annotated[
        Path,
        typer.Option("--trace-root"),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option("--report-root"),
    ] = Path("reports"),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Critique deterministic workflow evidence using Ollama."""

    from geoagent_harness.critic import (
        CriticAgentError,
        CriticEvidenceError,
        critique_task,
    )
    from geoagent_harness.model import (
        ModelClientError,
        ModelSettingsError,
    )

    try:
        result = critique_task(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
            agents_root=agents_root,
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.CRITIQUE,
        )
    except ModelClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except (
        CriticAgentError,
        CriticEvidenceError,
        ModelSettingsError,
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
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if result.deterministic_status != "validated_success":
        raise typer.Exit(code=1)

@app.command("schema-policies")
def schema_policies_command(
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Display the read-only artifact schema registry."""

    from geoagent_harness.schema_registry import (
        list_schema_policies,
    )

    payload = {
        "schema_version": "1.0",
        "policies": [
            policy.model_dump(mode="json")
            for policy in list_schema_policies()
        ],
        "registry_modified": False,
    }

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


@app.command("assess-schema-compatibility")
def assess_schema_compatibility_command(
    artifact_type: Annotated[
        str,
        typer.Argument(
            help=(
                "Registered artifact type, such as "
                "workflow_trace or workflow_state."
            ),
        ),
    ],
    artifact_version: Annotated[
        str,
        typer.Argument(
            help="Artifact schema version to assess.",
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess schema compatibility without mutation."""

    from geoagent_harness.schema_registry import (
        SchemaRegistryError,
        assess_schema_compatibility,
    )

    try:
        assessment = assess_schema_compatibility(
            artifact_type=artifact_type,
            artifact_version=artifact_version,
        )
    except SchemaRegistryError as exc:
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

    if not assessment.readable:
        raise typer.Exit(code=1)


@app.command("assess-schema-migration")
def assess_schema_migration_command(
    artifact_type: Annotated[
        str,
        typer.Argument(
            help="Registered artifact type.",
        ),
    ],
    artifact_version: Annotated[
        str,
        typer.Argument(
            help="Source schema version to assess.",
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess migration needs without modifying artifacts."""

    from geoagent_harness.schema_registry import (
        SchemaRegistryError,
        assess_migration,
    )

    try:
        assessment = assess_migration(
            artifact_type=artifact_type,
            artifact_version=artifact_version,
        )
    except SchemaRegistryError as exc:
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

    if assessment.manual_review_required:
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
