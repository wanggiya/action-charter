"""Existing postgis_rollback CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer


def plan_postgis_rollback_command(
    verification_file: Annotated[Path, typer.Argument(help="Exact 15G verification JSON.")],
    execution_file: Annotated[Path, typer.Option("--execution-file")],
    plan_file: Annotated[Path, typer.Option("--plan-file")],
    verification_root: Annotated[Path, typer.Option("--verification-root")] = Path("postgis-promotion-verifications"),
    execution_root: Annotated[Path, typer.Option("--execution-root")] = Path("postgis-promotion-executions"),
    plan_root: Annotated[Path, typer.Option("--plan-root")] = Path("postgis-promotion-plans"),
    rollback_plan_root: Annotated[Path, typer.Option("--rollback-plan-root")] = Path("postgis-rollback-plans"),
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Create an immutable, non-executing rollback plan."""
    from geoagent_harness.data.databases.postgis.rollback.plan import PostGISRollbackPlanError
    from geoagent_harness.data.databases.postgis.rollback.plan import PostGISRollbackPlanStorageError
    from geoagent_harness.task_actions.command_actions import postgis_rollback_plan__persist_postgis_rollback_plan as persist_postgis_rollback_plan, postgis_rollback_plan__plan_postgis_rollback as plan_postgis_rollback

    try:
        rollback_plan = plan_postgis_rollback(
            plan_file=plan_file, plan_root=plan_root,
            execution_file=execution_file, execution_root=execution_root,
            verification_file=verification_file, verification_root=verification_root,
        )
        result = persist_postgis_rollback_plan(
            rollback_plan, rollback_plan_root=rollback_plan_root
        )
    except (PostGISRollbackPlanError, PostGISRollbackPlanStorageError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))


def record_postgis_rollback_approval_command(
    rollback_plan_file: Annotated[Path, typer.Argument()],
    approver: Annotated[str, typer.Option("--approver")],
    reason: Annotated[str, typer.Option("--reason")],
    decision: Annotated[str, typer.Option("--decision")] = "approved",
    rollback_plan_root: Annotated[Path, typer.Option("--rollback-plan-root")] = Path("postgis-rollback-plans"),
    approval_root: Annotated[Path, typer.Option("--approval-root")] = Path("postgis-rollback-approvals"),
    valid_for_minutes: Annotated[int | None, typer.Option("--valid-for-minutes")] = None,
    corrections: Annotated[list[str] | None, typer.Option("--correction")] = None,
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Record one human decision for an exact rollback plan."""
    from datetime import datetime, timedelta, timezone
    from geoagent_harness.data.databases.postgis.rollback.approval import PostGISRollbackApprovalError
    from geoagent_harness.data.databases.postgis.rollback.approval import PostGISRollbackApprovalStorageError
    from geoagent_harness.task_actions.command_actions import postgis_rollback_approval__create_postgis_rollback_approval as create_postgis_rollback_approval, postgis_rollback_approval__persist_postgis_rollback_approval as persist_postgis_rollback_approval
    if valid_for_minutes is not None and valid_for_minutes < 1:
        typer.echo("Error: valid-for-minutes must be positive",err=True); raise typer.Exit(code=2)
    now=datetime.now(timezone.utc); expires_at=now+timedelta(minutes=valid_for_minutes) if valid_for_minutes else None
    try:
        approval=create_postgis_rollback_approval(rollback_plan_file=rollback_plan_file,rollback_plan_root=rollback_plan_root,decision=decision,approver=approver,reason=reason,human_corrections=corrections,expires_at=expires_at,now=now)
        result=persist_postgis_rollback_approval(approval,approval_root=approval_root)
    except (PostGISRollbackApprovalError,PostGISRollbackApprovalStorageError) as exc:
        typer.echo(f"Error: {exc}",err=True); raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"),indent=2 if pretty else None,separators=None if pretty else (",",":")))


def execute_postgis_rollback_command(
    rollback_plan_file: Annotated[Path, typer.Argument()],
    approval_file: Annotated[Path, typer.Option("--approval-file")],
    confirm_rollback_plan_sha256: Annotated[str, typer.Option("--confirm-rollback-plan-sha256")],
    confirm_approval_sha256: Annotated[str, typer.Option("--confirm-approval-sha256")],
    rollback_plan_root: Annotated[Path, typer.Option("--rollback-plan-root")] = Path("postgis-rollback-plans"),
    approval_root: Annotated[Path, typer.Option("--approval-root")] = Path("postgis-rollback-approvals"),
    execution_root: Annotated[Path, typer.Option("--execution-root")] = Path("postgis-rollback-executions"),
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Execute one exact approved rollback transaction."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.databases.postgis.rollback.execution import PostGISRollbackExecutionError
    from geoagent_harness.data.databases.postgis.rollback.execution import PostGISRollbackExecutionStorageError
    from geoagent_harness.task_actions.command_actions import postgis_rollback_execution__execute_postgis_rollback as execute_postgis_rollback, postgis_rollback_execution__persist_postgis_rollback_execution as persist_postgis_rollback_execution
    try:
        execution=execute_postgis_rollback(rollback_plan_file=rollback_plan_file,rollback_plan_root=rollback_plan_root,approval_file=approval_file,approval_root=approval_root,settings=load_settings(),confirm_rollback_plan_sha256=confirm_rollback_plan_sha256,confirm_approval_sha256=confirm_approval_sha256)
        result=persist_postgis_rollback_execution(execution,execution_root=execution_root)
    except (PostGISRollbackExecutionError,PostGISRollbackExecutionStorageError) as exc:
        typer.echo(f"Error: {exc}",err=True); raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"),indent=2 if pretty else None,separators=None if pretty else (",",":")))


def verify_postgis_rollback_command(
    execution_file: Annotated[Path, typer.Argument(help="Exact 15J rollback execution JSON.")],
    rollback_plan_file: Annotated[Path, typer.Option("--rollback-plan-file")],
    approval_file: Annotated[Path, typer.Option("--approval-file")],
    execution_root: Annotated[Path, typer.Option("--execution-root")] = Path("postgis-rollback-executions"),
    rollback_plan_root: Annotated[Path, typer.Option("--rollback-plan-root")] = Path("postgis-rollback-plans"),
    approval_root: Annotated[Path, typer.Option("--approval-root")] = Path("postgis-rollback-approvals"),
    verification_root: Annotated[Path, typer.Option("--verification-root")] = Path("postgis-rollback-verifications"),
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Independently inspect and record one completed rollback."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.databases.postgis.rollback.verification import PostGISRollbackVerificationError
    from geoagent_harness.data.databases.postgis.rollback.verification import PostGISRollbackVerificationStorageError
    from geoagent_harness.task_actions.command_actions import postgis_rollback_verification__persist_postgis_rollback_verification as persist_postgis_rollback_verification, postgis_rollback_verification__verify_postgis_rollback as verify_postgis_rollback
    try:
        verification = verify_postgis_rollback(
            execution_file=execution_file, execution_root=execution_root,
            rollback_plan_file=rollback_plan_file, rollback_plan_root=rollback_plan_root,
            approval_file=approval_file, approval_root=approval_root, settings=load_settings(),
        )
        saved = persist_postgis_rollback_verification(
            verification, verification_root=verification_root
        )
    except (PostGISRollbackVerificationError, PostGISRollbackVerificationStorageError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(
        {"verification": verification.model_dump(mode="json"), "verification_file": saved.as_posix()},
        indent=2 if pretty else None, separators=None if pretty else (",", ":"),
    ))
