"""Existing history CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from geoagent_harness.core.ledger.task_history.service import TaskHistoryError
from geoagent_harness.task_actions.command_actions import task_history_service__history_directory as runtime_history_directory
from typing import Annotated, NoReturn
import typer
from geoagent_harness.task_actions.command_actions import workspace__runtime_store_path as runtime_store_path


def record_task_event_command(
    task_id: Annotated[str, typer.Argument(help="Task identity, beginning with task-.")],
    event_type: Annotated[str, typer.Option("--event-type", help="request, clarification, selection, decision, outcome, failure or artifact_reference.")],
    summary: Annotated[str, typer.Option("--summary", help="Short event statement; secrets are redacted before storage.")],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
    artifact_path: Annotated[str | None, typer.Option("--artifact-path")] = None,
    artifact_sha256: Annotated[str | None, typer.Option("--artifact-sha256")] = None,
) -> None:
    """Append one governed task event without approving or executing work."""

    from geoagent_harness.core.ledger.task_history import TaskHistoryError
    from geoagent_harness.task_actions.command_actions import task_history__append_task_event as append_task_event

    try:
        result = append_task_event(
            root=runtime_history_directory(project_root), task_id=task_id,
            event_type=event_type, summary=summary, artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
        )
        typer.echo(json.dumps(result, indent=2))
    except (TaskHistoryError, OSError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def build_task_context_command(
    task_id: Annotated[str, typer.Argument(help="Task identity, beginning with task-.")],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Inspect a deterministic bounded task context without model use."""

    from geoagent_harness.core.ledger.task_history import TaskHistoryError
    from geoagent_harness.task_actions.command_actions import task_history__build_task_context as build_task_context

    try:
        result = build_task_context(root=runtime_history_directory(project_root), task_id=task_id)
        typer.echo(json.dumps(result, indent=2))
    except (TaskHistoryError, OSError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def retrieve_task_context_command(
    query: Annotated[str, typer.Option("--query")],
    task_ids: Annotated[list[str], typer.Option("--task-id", help="Repeat for each explicitly selected history, at most five.")],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Retrieve unreviewed context candidates without calling a model or executing."""
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    from geoagent_harness.task_actions.command_actions import context_retrieval__retrieve_task_context as retrieve_task_context
    try:
        result = retrieve_task_context(root=runtime_history_directory(project_root), query=query, task_ids=task_ids)
        typer.echo(json.dumps(result, indent=2))
    except (ContextRetrievalError,TaskHistoryError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def review_task_context_command(
    query: Annotated[str, typer.Option("--query")],
    task_ids: Annotated[list[str], typer.Option("--task-id")],
    confirmed_context_sha256: Annotated[str, typer.Option("--confirmed-context-sha256")],
    reviewer: Annotated[str, typer.Option("--reviewer")],
    reason: Annotated[str, typer.Option("--reason")],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Confirm exact context for reasoning only, never approve work."""
    from geoagent_harness.agents.memory.context_retrieval import ContextReviewError
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    from geoagent_harness.task_actions.command_actions import context_retrieval__save_reviewed_context as save_reviewed_context
    try:
        result = save_reviewed_context(history_root=runtime_history_directory(project_root),
            review_root=runtime_store_path(project_root, "reviewed-contexts"), query=query, task_ids=task_ids,
            confirmed_context_sha256=confirmed_context_sha256, reviewer=reviewer, reason=reason)
        typer.echo(json.dumps(result, indent=2))
    except (ContextReviewError, ContextRetrievalError, TaskHistoryError, OSError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def inspect_reviewed_context_command(
    filename: Annotated[str, typer.Argument()],
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    from geoagent_harness.agents.memory.context_retrieval import ContextReviewError
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    from geoagent_harness.task_actions.command_actions import context_retrieval__load_reviewed_context as load_reviewed_context
    try:
        typer.echo(json.dumps(load_reviewed_context(review_root=runtime_store_path(project_root, "reviewed-contexts"),
            history_root=runtime_history_directory(project_root), filename=filename), indent=2))
    except (ContextReviewError, ContextRetrievalError, TaskHistoryError, OSError, ValueError, KeyError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def list_reviewed_context_command(
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """List source-checked saved context and intent reviews without inference."""
    from geoagent_harness.task_actions.command_actions import intent_inventory__reviewed_context_inventory as reviewed_context_inventory
    try:
        typer.echo(json.dumps(reviewed_context_inventory(project_root=project_root), indent=2))
    except (OSError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def record_gis_operational_history_command(
    trace_path: Annotated[
        Path,
        typer.Argument(
            help="Validated workflow trace JSON file.",
        ),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(
            help="Validated workflow Markdown report.",
        ),
    ],
    task_id: Annotated[
        str,
        typer.Option(
            "--task-id",
            help="Exact task identity observed by the caller.",
        ),
    ],
    correlation_id: Annotated[
        str,
        typer.Option(
            "--correlation-id",
            help="Correlation identity shared across agent runs.",
        ),
    ],
    agent_instance_id: Annotated[
        str,
        typer.Option(
            "--agent-instance-id",
            help="Identity of the observed GIS service instance.",
        ),
    ],
    agent_run_id: Annotated[
        str,
        typer.Option(
            "--agent-run-id",
            help="Unique identity of the observed GIS invocation.",
        ),
    ],
    parent_run_id: Annotated[
        str | None,
        typer.Option(
            "--parent-run-id",
            help="Optional parent Executor run identity.",
        ),
    ] = None,
    trace_root: Annotated[
        Path,
        typer.Option("--trace-root"),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option("--report-root"),
    ] = Path("reports"),
    event_root: Annotated[
        Path,
        typer.Option("--event-root"),
    ] = Path("operational-history"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Derive one GIS run history from verified evidence."""

    from geoagent_harness.core.ledger.operational_history import AgentRole, OperationalIdentity
    from geoagent_harness.core.ledger.operational_history import OperationalHistoryError
    from geoagent_harness.task_actions.command_actions import operational_history__build_operational_timeline as build_operational_timeline, operational_history__load_operational_events as load_operational_events, operational_history__operational_event_log_path as operational_event_log_path, operational_history__record_gis_workflow_history as record_gis_workflow_history

    try:
        identity = OperationalIdentity(
            agent_id=AgentRole.GIS,
            agent_instance_id=agent_instance_id,
            agent_run_id=agent_run_id,
            task_id=task_id,
            correlation_id=correlation_id,
            parent_run_id=parent_run_id,
        )
        recorded = record_gis_workflow_history(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
            event_root=event_root,
            identity=identity,
        )
        event_file = operational_event_log_path(
            event_root=event_root,
            correlation_id=correlation_id,
        )
        all_events = load_operational_events(
            event_file,
            event_root=event_root,
        )
        timeline = build_operational_timeline(
            all_events
        )
    except (
        OperationalHistoryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "status": "recorded",
                "event_file": event_file.as_posix(),
                "recorded_event_count": len(recorded),
                "timeline": timeline.model_dump(mode="json"),
            },
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )


def inspect_operational_history_command(
    event_file: Annotated[
        Path,
        typer.Argument(
            help="Correlation-scoped operational event JSONL file.",
        ),
    ],
    event_root: Annotated[
        Path,
        typer.Option(
            "--event-root",
            help="Approved operational-history root.",
        ),
    ] = Path("operational-history"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate and display one correlated event timeline."""

    from geoagent_harness.core.ledger.operational_history import OperationalHistoryError
    from geoagent_harness.task_actions.command_actions import operational_history__build_operational_timeline as build_operational_timeline, operational_history__load_operational_events as load_operational_events

    try:
        events = load_operational_events(
            event_file,
            event_root=event_root,
        )
        timeline = build_operational_timeline(events)
    except (
        OperationalHistoryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            timeline.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )
