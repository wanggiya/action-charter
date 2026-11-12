"""Existing critic CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer
from geoagent_harness.contracts.failures import FailureStage
from geoagent_harness.apps.cli.common import _raise_typed_failure


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

    from geoagent_harness.platform.evidence import CriticEvidenceError
    from geoagent_harness.task_actions.command_actions import critic_evidence__build_critic_evidence as build_critic_evidence

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

    from geoagent_harness.agents.roles.critic import CriticAgentError
    from geoagent_harness.platform.evidence import CriticEvidenceError
    from geoagent_harness.task_actions.command_actions import critic__critique_task as critique_task
    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError

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


def record_critic_result_command(
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
    record_root: Annotated[
        Path,
        typer.Option(
            "--record-root",
            help="Immutable Critic-result package root.",
        ),
    ] = Path("critic-results"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Critique verified evidence and persist a separate result."""

    from datetime import timezone

    from geoagent_harness.agents.roles.critic import CriticAgentError
    from geoagent_harness.platform.evidence import CriticEvidenceError
    from geoagent_harness.platform.storage.critic_records import CriticResultRecordError
    from geoagent_harness.platform.storage.critic_record_storage import CriticResultStorageError
    from geoagent_harness.task_actions.command_actions import critic__build_critic_result_record as build_critic_result_record, critic__critique_task as critique_task, critic__persist_critic_result_record as persist_critic_result_record
    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError

    try:
        result = critique_task(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
            agents_root=agents_root,
        )
        record = build_critic_result_record(
            result=result,
            recorded_at=datetime.now(timezone.utc),
        )
        stored = persist_critic_result_record(
            record,
            record_root=record_root,
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
        CriticResultRecordError,
        CriticResultStorageError,
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
            stored.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None if pretty else (",", ":")
            ),
        )
    )
