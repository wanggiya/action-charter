"""Existing builder inspection CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer


def inspect_builder_candidate_command(
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Materialized Builder candidate directory "
                "to inspect."
            ),
        ),
    ],
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help=(
                "Approved root containing isolated "
                "Builder candidates."
            ),
        ),
    ] = Path("builder-candidates"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Statically inspect one untrusted Builder candidate."""

    from geoagent_harness.evolution.builder import BuilderCandidateInspectionError
    from geoagent_harness.task_actions.command_actions import builder__inspect_builder_candidate as inspect_builder_candidate

    try:
        result = inspect_builder_candidate(
            candidate_path=candidate_path,
            candidate_root=candidate_root,
        )
    except BuilderCandidateInspectionError as exc:
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


def assess_builder_candidate_tests_command(
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Materialized Builder candidate "
                "directory."
            ),
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Isolated Builder candidate-test "
                "JSON record."
            ),
        ),
    ],
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option(
            "--evidence-root",
            help="Approved Builder test-evidence root.",
        ),
    ] = Path("builder-test-results"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Assess digest-bound isolated Builder tests."""

    from geoagent_harness.evolution.builder import BuilderCandidateTestingError
    from geoagent_harness.task_actions.command_actions import builder__assess_builder_candidate_tests as assess_builder_candidate_tests

    try:
        result = assess_builder_candidate_tests(
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record_path=test_record_file,
            evidence_root=evidence_root,
        )
    except (
        BuilderCandidateTestingError,
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
