"""Existing approvals CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer


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

    from geoagent_harness.core.policy.approvals import ApprovalError
    from geoagent_harness.task_actions.command_actions import approvals__load_planner_result as load_planner_result, approvals__plan_sha256 as plan_sha256

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

    from geoagent_harness.core.policy.approvals import ApprovalError
    from geoagent_harness.task_actions.command_actions import approvals__create_approval as create_approval, approvals__load_planner_result as load_planner_result

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

    from geoagent_harness.core.policy.approvals import ApprovalError
    from geoagent_harness.task_actions.command_actions import approvals__load_approval as load_approval, approvals__load_planner_result as load_planner_result, approvals__verify_approval as verify_approval

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
