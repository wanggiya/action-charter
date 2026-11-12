"""Existing planning CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from geoagent_harness.core.ledger.task_history.service import TaskHistoryError
from typing import Annotated, NoReturn
import typer
from geoagent_harness.contracts.failures import FailureStage
from geoagent_harness.apps.cli.common import _raise_typed_failure


def reason_task_intent_command(
    request: Annotated[str, typer.Option("--request")],
    review_filename: Annotated[str | None, typer.Option("--review-filename", help="Omit to start explicitly without historical context.")] = None,
    clarification_answers: Annotated[list[str] | None, typer.Option("--clarification", help="Repeat for up to five explicit answers; no authority is conferred.")] = None,
    selected_input: Annotated[str | None, typer.Option("--selected-input", help="Optional existing filename or relative path under data/input; checked before inference.")] = None,
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Propose intent with optional reviewed history; never execute."""
    from geoagent_harness.contracts.intent import IntentError
    from geoagent_harness.task_actions.command_actions import intent_service__reason_task_intent as reason_task_intent
    from geoagent_harness.agents.memory.context_retrieval import ContextReviewError
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError
    try:
        result = reason_task_intent(project_root=project_root, review_filename=review_filename, request=request, clarification_answers=clarification_answers, selected_input_path=selected_input)
        typer.echo(json.dumps(result, indent=2))
    except (IntentError, ContextReviewError, ContextRetrievalError, ModelClientError,
            ModelSettingsError, TaskHistoryError, OSError, ValueError, KeyError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def inspect_intent_proposal_command(
    proposal_file: Annotated[Path, typer.Argument()],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    from geoagent_harness.task_actions.command_actions import intent_review__read_intent_file as read_intent_file, intent_review__inspect_intent_for_review as inspect_intent_for_review
    try:
        typer.echo(json.dumps(inspect_intent_for_review(payload=read_intent_file(proposal_file), project_root=project_root), indent=2))
    except (ValueError, TaskHistoryError, OSError, KeyError) as exc:
        typer.echo(f"Error: {exc}", err=True); raise typer.Exit(code=2) from exc


def review_task_intent_command(
    proposal_file: Annotated[Path, typer.Argument()],
    confirmed_intent_sha256: Annotated[str, typer.Option("--confirmed-intent-sha256")],
    reviewer: Annotated[str, typer.Option("--reviewer")],
    reason: Annotated[str, typer.Option("--reason")],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    from geoagent_harness.task_actions.command_actions import intent_review__read_intent_file as read_intent_file, intent_review__save_reviewed_intent as save_reviewed_intent
    try:
        result=save_reviewed_intent(payload=read_intent_file(proposal_file),project_root=project_root,
            confirmed_intent_sha256=confirmed_intent_sha256,reviewer=reviewer,reason=reason)
        typer.echo(json.dumps(result,indent=2))
    except (ValueError, TaskHistoryError, OSError, KeyError) as exc:
        typer.echo(f"Error: {exc}",err=True);raise typer.Exit(code=2) from exc


def inspect_reviewed_intent_command(
    filename: Annotated[str, typer.Argument()],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    from geoagent_harness.task_actions.command_actions import intent_review__load_reviewed_intent as load_reviewed_intent
    try:
        typer.echo(json.dumps(load_reviewed_intent(project_root=project_root,filename=filename),indent=2))
    except (ValueError, OSError, KeyError) as exc:
        typer.echo(f"Error: {exc}",err=True);raise typer.Exit(code=2) from exc


def plan_reviewed_intent_command(
    filename: Annotated[str, typer.Argument()],
    allowed_skill_ids: Annotated[list[str], typer.Option("--allowed-skill")],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Plan one exact reviewed vector inspection; never save or execute."""
    from geoagent_harness.task_actions.command_actions import intent_handoff__plan_reviewed_intent as plan_reviewed_intent
    from geoagent_harness.agents.roles.planner.agent import PlannerAgentError
    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError
    try:
        typer.echo(json.dumps(plan_reviewed_intent(project_root=project_root,filename=filename,
            allowed_skill_ids=allowed_skill_ids),indent=2))
    except (ValueError, OSError, KeyError, PlannerAgentError, ModelClientError, ModelSettingsError) as exc:
        typer.echo(f"Error: {exc}",err=True);raise typer.Exit(code=2) from exc


def save_reviewed_intent_plan_command(
    handoff_file: Annotated[Path, typer.Argument()],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Store the exact reviewed handoff plan, without approval or execution."""
    from geoagent_harness.task_actions.command_actions import intent_review__read_intent_file as read_intent_file
    from geoagent_harness.task_actions.command_actions import intent_handoff__save_reviewed_intent_plan as save_reviewed_intent_plan
    from geoagent_harness.contracts.planning import PlannerResult
    try:
        payload = read_intent_file(handoff_file)
        typer.echo(json.dumps(save_reviewed_intent_plan(project_root=project_root,
            filename=payload['intent_review_filename'],
            planner_result=PlannerResult.model_validate(payload['planner_result']),
            confirmed_plan_sha256=payload['plan_sha256']), indent=2))
    except (ValueError, OSError, KeyError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


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

    from geoagent_harness.agents.memory.context_pack import ContextPackError
    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError
    from geoagent_harness.agents.roles.planner import PlannerAgentError
    from geoagent_harness.task_actions.command_actions import planner__plan_task as plan_task

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
