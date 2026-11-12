"""Existing geoserver CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer


def inspect_geoserver_layer_command(
    workspace: Annotated[str, typer.Option("--workspace", help="Approved GeoServer workspace.")] = "agent_sandbox",
    datastore: Annotated[str, typer.Option("--datastore", help="Approved GeoServer datastore.")] = "postgis",
    layer: Annotated[str, typer.Option("--layer", help="Exact GeoServer layer name.")] = "current_layer",
    pretty: Annotated[bool, typer.Option("--pretty", help="Indent the JSON response.")] = False,
) -> None:
    """Inspect one bounded GeoServer publication target without mutation."""
    from geoagent_harness.data.spatial.geoserver.inspection import GeoServerInspectionError
    from geoagent_harness.data.spatial.geoserver.inspection import GeoServerInspectionRequest
    from geoagent_harness.task_actions.command_actions import geoserver_inspection__inspect_geoserver_layer as inspect_geoserver_layer
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings

    try:
        result = inspect_geoserver_layer(
            request=GeoServerInspectionRequest(workspace=workspace, datastore=datastore, layer=layer),
            settings=load_settings(),
        )
    except (GeoServerInspectionError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2 if pretty else None, separators=None if pretty else (",", ":")))
    if result.status == "not_found":
        raise typer.Exit(code=1)


def plan_geoserver_publication_command(
    plan_id: Annotated[str, typer.Option("--plan-id")],
    workspace: Annotated[str, typer.Option("--workspace")],
    datastore: Annotated[str, typer.Option("--datastore")],
    layer: Annotated[str, typer.Option("--layer")],
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Inspect and plan activation of one existing disabled layer."""
    from geoagent_harness.data.spatial.geoserver.inspection import GeoServerInspectionRequest
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationError
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationPlanRequest
    from geoagent_harness.task_actions.command_actions import geoserver_publication__plan_geoserver_publication as plan_geoserver_publication
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    try:
        result = plan_geoserver_publication(
            request=GeoServerPublicationPlanRequest(
                plan_id=plan_id,
                target=GeoServerInspectionRequest(
                    workspace=workspace, datastore=datastore, layer=layer,
                ),
            ), settings=load_settings(),
        )
    except (GeoServerPublicationError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2 if pretty else None,
                          separators=None if pretty else (",", ":")))


def record_geoserver_publication_approval_command(
    plan_file: Annotated[Path, typer.Argument()],
    approver: Annotated[str, typer.Option("--approver")],
    reason: Annotated[str, typer.Option("--reason")],
    decision: Annotated[str, typer.Option("--decision")] = "approved",
    valid_for_minutes: Annotated[int | None, typer.Option("--valid-for-minutes")] = None,
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Record a human decision bound to one exact publication plan."""
    from datetime import datetime, timedelta, timezone
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationError
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationPlanResult
    from geoagent_harness.task_actions.command_actions import geoserver_publication__create_geoserver_publication_approval as create_geoserver_publication_approval, geoserver_publication__load_json as load_json
    if valid_for_minutes is not None and valid_for_minutes < 1:
        typer.echo("Error: valid-for-minutes must be positive", err=True); raise typer.Exit(code=2)
    now = datetime.now(timezone.utc)
    try:
        plan = load_json(plan_file, GeoServerPublicationPlanResult)
        result = create_geoserver_publication_approval(
            plan_result=plan, decision=decision, approver=approver, reason=reason,
            now=now, expires_at=now + timedelta(minutes=valid_for_minutes) if valid_for_minutes else None,
        )
    except GeoServerPublicationError as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2 if pretty else None,
                          separators=None if pretty else (",", ":")))


def execute_geoserver_publication_command(
    plan_file: Annotated[Path, typer.Argument()],
    approval_file: Annotated[Path, typer.Option("--approval-file")],
    confirm_plan_sha256: Annotated[str, typer.Option("--confirm-plan-sha256")],
    confirm_approval_sha256: Annotated[str, typer.Option("--confirm-approval-sha256")],
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Execute one exact approved GeoServer layer activation."""
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationApproval, GeoServerPublicationPlanResult
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationError
    from geoagent_harness.task_actions.command_actions import geoserver_publication__execute_geoserver_publication as execute_geoserver_publication, geoserver_publication__load_json as load_json
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    try:
        plan = load_json(plan_file, GeoServerPublicationPlanResult)
        approval = load_json(approval_file, GeoServerPublicationApproval)
        result = execute_geoserver_publication(
            plan_result=plan, approval=approval, settings=load_settings(),
            confirm_plan_sha256=confirm_plan_sha256,
            confirm_approval_sha256=confirm_approval_sha256,
        )
    except GeoServerPublicationError as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2 if pretty else None,
                          separators=None if pretty else (",", ":")))
    if result.status != "published":
        raise typer.Exit(code=1)


def verify_geoserver_publication_command(
    execution_file: Annotated[Path, typer.Argument()],
    plan_file: Annotated[Path, typer.Option("--plan-file")],
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Independently inspect one executed GeoServer publication."""
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationError
    from geoagent_harness.data.spatial.geoserver.publication import GeoServerPublicationExecutionResult, GeoServerPublicationPlanResult
    from geoagent_harness.task_actions.command_actions import geoserver_publication__load_json as load_json, geoserver_publication__verify_geoserver_publication as verify_geoserver_publication
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    try:
        plan = load_json(plan_file, GeoServerPublicationPlanResult)
        execution = load_json(execution_file, GeoServerPublicationExecutionResult)
        result = verify_geoserver_publication(
            execution=execution, plan_result=plan, settings=load_settings(),
        )
    except GeoServerPublicationError as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2 if pretty else None,
                          separators=None if pretty else (",", ":")))
    if result.status != "verified":
        raise typer.Exit(code=1)
