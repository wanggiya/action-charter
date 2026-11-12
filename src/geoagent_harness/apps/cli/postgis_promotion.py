"""Existing postgis_promotion CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer


def plan_postgis_promotion_command(
    plan_id: Annotated[str, typer.Option("--plan-id")],
    reference_schema: Annotated[
        str, typer.Option("--reference-schema")
    ] = "agent_sandbox",
    reference_table: Annotated[
        str, typer.Option("--reference-table")
    ] = "reference_layer",
    candidate_schema: Annotated[
        str, typer.Option("--candidate-schema")
    ] = "agent_sandbox",
    candidate_table: Annotated[
        str, typer.Option("--candidate-table")
    ] = "candidate_layer",
    archive_schema: Annotated[
        str, typer.Option("--archive-schema")
    ] = "agent_sandbox",
    archive_table: Annotated[
        str, typer.Option("--archive-table")
    ] = "reference_layer_archive",
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Create a digest-bound promotion plan without executing it."""
    from pydantic import ValidationError

    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.databases.postgis.comparison import PostGISComparisonError
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionError
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionRequest
    from geoagent_harness.data.databases.postgis.promotion.plan import PostGISPromotionPlanError
    from geoagent_harness.data.databases.postgis.promotion.plan import PostGISPromotionPlanRequest
    from geoagent_harness.task_actions.command_actions import postgis_promotion_plan__plan_postgis_promotion as plan_postgis_promotion

    try:
        result = plan_postgis_promotion(
            request=PostGISPromotionPlanRequest(
                plan_id=plan_id,
                reference=PostGISInspectionRequest(
                    target_schema=reference_schema,
                    target_table=reference_table,
                ),
                candidate=PostGISInspectionRequest(
                    target_schema=candidate_schema,
                    target_table=candidate_table,
                ),
                archive=PostGISInspectionRequest(
                    target_schema=archive_schema,
                    target_table=archive_table,
                ),
            ),
            settings=load_settings(),
        )
    except (
        PostGISComparisonError,
        PostGISInspectionError,
        PostGISPromotionPlanError,
        ValidationError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))


def record_postgis_promotion_approval_command(
    plan_file: Annotated[
        Path,
        typer.Argument(help="15D plan-result JSON beneath the approved root."),
    ],
    approver: Annotated[str, typer.Option("--approver")],
    reason: Annotated[str, typer.Option("--reason")],
    decision: Annotated[
        str, typer.Option("--decision")
    ] = "approved",
    plan_root: Annotated[
        Path, typer.Option("--plan-root")
    ] = Path("postgis-promotion-plans"),
    approval_root: Annotated[
        Path, typer.Option("--approval-root")
    ] = Path("postgis-promotion-approvals"),
    valid_for_minutes: Annotated[
        int | None, typer.Option("--valid-for-minutes")
    ] = None,
    corrections: Annotated[
        list[str] | None,
        typer.Option("--correction"),
    ] = None,
    pretty: Annotated[
        bool, typer.Option("--pretty")
    ] = False,
) -> None:
    """Persist a human decision for one exact 15D plan digest."""
    from datetime import datetime, timedelta, timezone

    from geoagent_harness.data.databases.postgis.promotion.approval import PostGISPromotionApprovalError
    from geoagent_harness.data.databases.postgis.promotion.approval import PostGISPromotionApprovalStorageError
    from geoagent_harness.task_actions.command_actions import postgis_promotion_approval__create_postgis_promotion_approval as create_postgis_promotion_approval, postgis_promotion_approval__load_postgis_promotion_plan_result as load_postgis_promotion_plan_result, postgis_promotion_approval__persist_postgis_promotion_approval as persist_postgis_promotion_approval

    if valid_for_minutes is not None and valid_for_minutes < 1:
        typer.echo("Error: valid-for-minutes must be positive", err=True)
        raise typer.Exit(code=2)
    now = datetime.now(timezone.utc)
    expires_at = (
        now + timedelta(minutes=valid_for_minutes)
        if valid_for_minutes is not None
        else None
    )
    try:
        plan_result = load_postgis_promotion_plan_result(
            plan_file,
            plan_root=plan_root,
        )
        approval = create_postgis_promotion_approval(
            plan_result=plan_result,
            decision=decision,
            approver=approver,
            reason=reason,
            human_corrections=corrections,
            expires_at=expires_at,
            now=now,
        )
        result = persist_postgis_promotion_approval(
            approval,
            approval_root=approval_root,
        )
    except (
        PostGISPromotionApprovalError,
        PostGISPromotionApprovalStorageError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))


def execute_postgis_promotion_command(
    plan_file: Annotated[Path, typer.Argument(help="Exact 15D plan-result JSON.")],
    approval_file: Annotated[Path, typer.Option("--approval-file")],
    confirm_plan_sha256: Annotated[str, typer.Option("--confirm-plan-sha256")],
    confirm_approval_sha256: Annotated[str, typer.Option("--confirm-approval-sha256")],
    plan_root: Annotated[Path, typer.Option("--plan-root")] = Path("postgis-promotion-plans"),
    approval_root: Annotated[Path, typer.Option("--approval-root")] = Path("postgis-promotion-approvals"),
    execution_root: Annotated[Path, typer.Option("--execution-root")] = Path("postgis-promotion-executions"),
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Execute and record one exact approved transactional promotion."""
    from geoagent_harness.data.databases.postgis.promotion.execution import PostGISPromotionExecutionError
    from geoagent_harness.data.databases.postgis.promotion.execution import PostGISPromotionExecutionStorageError
    from geoagent_harness.task_actions.command_actions import postgis_promotion_execution__execute_postgis_promotion as execute_postgis_promotion, postgis_promotion_execution__persist_postgis_promotion_execution as persist_postgis_promotion_execution
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings

    try:
        execution = execute_postgis_promotion(
            plan_file=plan_file,
            plan_root=plan_root,
            approval_file=approval_file,
            approval_root=approval_root,
            settings=load_settings(),
            confirm_plan_sha256=confirm_plan_sha256,
            confirm_approval_sha256=confirm_approval_sha256,
        )
        result = persist_postgis_promotion_execution(
            execution,
            execution_root=execution_root,
        )
    except (
        PostGISPromotionExecutionError,
        PostGISPromotionExecutionStorageError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))


def verify_postgis_promotion_command(
    execution_file: Annotated[Path, typer.Argument()],
    plan_file: Annotated[Path, typer.Option("--plan-file")],
    execution_root: Annotated[Path, typer.Option("--execution-root")] = Path("postgis-promotion-executions"),
    plan_root: Annotated[Path, typer.Option("--plan-root")] = Path("postgis-promotion-plans"),
    verification_root: Annotated[Path, typer.Option("--verification-root")] = Path("postgis-promotion-verifications"),
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Independently inspect and record one completed promotion."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.databases.postgis.promotion.verification import PostGISPromotionVerificationError
    from geoagent_harness.data.databases.postgis.promotion.verification import PostGISPromotionVerificationStorageError
    from geoagent_harness.task_actions.command_actions import postgis_promotion_verification__persist_postgis_promotion_verification as persist_postgis_promotion_verification, postgis_promotion_verification__verify_postgis_promotion as verify_postgis_promotion
    try:
        verification = verify_postgis_promotion(
            execution_file=execution_file, execution_root=execution_root,
            plan_file=plan_file, plan_root=plan_root, settings=load_settings(),
        )
        saved = persist_postgis_promotion_verification(
            verification, verification_root=verification_root
        )
    except (PostGISPromotionVerificationError, PostGISPromotionVerificationStorageError) as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=2) from exc
    typer.echo(json.dumps({"verification": verification.model_dump(mode="json"),
                           "verification_file": saved.as_posix()},
                          indent=2 if pretty else None,
                          separators=None if pretty else (",", ":")))
