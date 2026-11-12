"""Existing releases CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer


def assess_workflow_release_command(
    release_id: Annotated[
        str,
        typer.Argument(help="Stable release-candidate ID."),
    ],
    trace_file: Annotated[
        Path,
        typer.Argument(help="Workflow trace beneath its approved root."),
    ],
    report_file: Annotated[
        Path,
        typer.Argument(help="Workflow report beneath its approved root."),
    ],
    critic_record_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable CRITIC_RESULT.json beneath its root."
        ),
    ],
    history_file: Annotated[
        Path,
        typer.Argument(help="Operational JSONL beneath its approved root."),
    ],
    trace_root: Annotated[
        Path,
        typer.Option("--trace-root"),
    ] = Path("traces"),
    report_root: Annotated[
        Path,
        typer.Option("--report-root"),
    ] = Path("reports"),
    critic_root: Annotated[
        Path,
        typer.Option("--critic-root"),
    ] = Path("critic-results"),
    history_root: Annotated[
        Path,
        typer.Option("--history-root"),
    ] = Path("operational-history"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    plan_file: Annotated[
        Path | None,
        typer.Option("--plan-file"),
    ] = None,
    plan_root: Annotated[
        Path,
        typer.Option("--plan-root"),
    ] = Path("plans"),
    approval_file: Annotated[
        Path | None,
        typer.Option("--approval-file"),
    ] = None,
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess exact workflow evidence without creating a release."""

    from datetime import timezone

    from geoagent_harness.core.ledger.releases import ReleaseAssessmentError
    from geoagent_harness.task_actions.command_actions import releases__assess_workflow_release_candidate as assess_workflow_release_candidate, releases__authoritative_release_candidate_sha256 as authoritative_release_candidate_sha256

    try:
        candidate = assess_workflow_release_candidate(
            release_id=release_id,
            trace_file=trace_file,
            report_file=report_file,
            critic_record_file=critic_record_file,
            history_file=history_file,
            trace_root=trace_root,
            report_root=report_root,
            critic_root=critic_root,
            history_root=history_root,
            project_root=project_root,
            assessed_at=datetime.now(timezone.utc),
            plan_file=plan_file,
            plan_root=plan_root,
            approval_file=approval_file,
            approval_root=approval_root,
        )
        payload = {
            "candidate_sha256": (
                authoritative_release_candidate_sha256(candidate)
            ),
            "candidate": candidate.model_dump(mode="json"),
        }
    except (
        ReleaseAssessmentError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(None if pretty else (",", ":")),
        )
    )


def create_workflow_release_command(
    release_id: Annotated[
        str,
        typer.Argument(help="Stable authoritative release ID."),
    ],
    trace_file: Annotated[Path, typer.Argument()],
    report_file: Annotated[Path, typer.Argument()],
    critic_record_file: Annotated[Path, typer.Argument()],
    history_file: Annotated[Path, typer.Argument()],
    trace_root: Annotated[
        Path, typer.Option("--trace-root")
    ] = Path("traces"),
    report_root: Annotated[
        Path, typer.Option("--report-root")
    ] = Path("reports"),
    critic_root: Annotated[
        Path, typer.Option("--critic-root")
    ] = Path("critic-results"),
    history_root: Annotated[
        Path, typer.Option("--history-root")
    ] = Path("operational-history"),
    project_root: Annotated[
        Path, typer.Option("--project-root")
    ] = Path("."),
    plan_file: Annotated[
        Path | None, typer.Option("--plan-file")
    ] = None,
    plan_root: Annotated[
        Path, typer.Option("--plan-root")
    ] = Path("plans"),
    approval_file: Annotated[
        Path | None, typer.Option("--approval-file")
    ] = None,
    approval_root: Annotated[
        Path, typer.Option("--approval-root")
    ] = Path("approvals"),
    release_root: Annotated[
        Path, typer.Option("--release-root")
    ] = Path("releases"),
    pretty: Annotated[
        bool, typer.Option("--pretty")
    ] = False,
) -> None:
    """Create one immutable release from reverified workflow evidence."""

    from datetime import timezone

    from geoagent_harness.core.ledger.releases import AuthoritativeReleaseStorageError
    from geoagent_harness.core.ledger.releases import ReleaseAssessmentError
    from geoagent_harness.task_actions.command_actions import releases__assess_workflow_release_candidate as assess_workflow_release_candidate, releases__persist_authoritative_release as persist_authoritative_release

    now = datetime.now(timezone.utc)
    try:
        candidate = assess_workflow_release_candidate(
            release_id=release_id,
            trace_file=trace_file,
            report_file=report_file,
            critic_record_file=critic_record_file,
            history_file=history_file,
            trace_root=trace_root,
            report_root=report_root,
            critic_root=critic_root,
            history_root=history_root,
            project_root=project_root,
            assessed_at=now,
            plan_file=plan_file,
            plan_root=plan_root,
            approval_file=approval_file,
            approval_root=approval_root,
        )
        result = persist_authoritative_release(
            candidate,
            project_root=project_root,
            release_root=release_root,
            released_at=now,
        )
    except (
        ReleaseAssessmentError,
        AuthoritativeReleaseStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(None if pretty else (",", ":")),
        )
    )


def inspect_authoritative_release_command(
    manifest_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable RELEASE.json beneath its approved root."
        ),
    ],
    release_root: Annotated[
        Path,
        typer.Option(
            "--release-root",
            help="Approved immutable release-package root.",
        ),
    ] = Path("releases"),
    pretty: Annotated[
        bool, typer.Option("--pretty")
    ] = False,
) -> None:
    """Independently verify one immutable authoritative release."""

    from geoagent_harness.core.ledger.releases import AuthoritativeReleaseStorageError
    from geoagent_harness.task_actions.command_actions import releases__inspect_authoritative_release as inspect_authoritative_release

    try:
        result = inspect_authoritative_release(
            manifest_file,
            release_root=release_root,
        )
    except (
        AuthoritativeReleaseStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(None if pretty else (",", ":")),
        )
    )
