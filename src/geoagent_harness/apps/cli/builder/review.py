"""Existing builder review CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer
from geoagent_harness.contracts.failures import FailureStage
from geoagent_harness.apps.cli.common import _raise_typed_failure


def builder_propose_command(
    request_file: Annotated[
        Path,
        typer.Option(
            "--request-file",
            help="Read-only Builder request JSON file.",
        ),
    ],
    request_root: Annotated[
        Path,
        typer.Option(
            "--request-root",
            help="Approved Builder request root.",
        ),
    ] = Path("builder-requests"),
    agents_root: Annotated[
        Path,
        typer.Option(
            "--agents-root",
            help="Trusted agent manifest root.",
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
    """Generate one validated proposal without writing files."""

    from geoagent_harness.evolution.builder import BuilderAgentError
    from geoagent_harness.evolution.builder import BuilderRequestLoadError
    from geoagent_harness.task_actions.command_actions import builder__load_builder_request as load_builder_request, builder__propose_builder_candidate as propose_builder_candidate
    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError

    try:
        request = load_builder_request(
            request_file,
            request_root=request_root,
        )
        result = propose_builder_candidate(
            request=request,
            agents_root=agents_root,
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except ModelClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MODEL,
        )
    except (
        BuilderAgentError,
        BuilderRequestLoadError,
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


def materialize_builder_proposal_command(
    generation_file: Annotated[
        Path,
        typer.Option(
            "--generation-file",
            help=(
                "Operator-saved Builder generation "
                "result JSON."
            ),
        ),
    ],
    generation_root: Annotated[
        Path,
        typer.Option(
            "--generation-root",
            help="Approved Builder generation root.",
        ),
    ] = Path("builder-generations"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help=(
                "Root for isolated untrusted "
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
    """Materialize one proposal outside the Builder container."""

    from geoagent_harness.evolution.builder import BuilderMaterializationError
    from geoagent_harness.task_actions.command_actions import builder__materialize_builder_proposal as materialize_builder_proposal

    try:
        result = materialize_builder_proposal(
            generation_file=generation_file,
            generation_root=generation_root,
            candidate_root=candidate_root,
        )
    except (
        BuilderMaterializationError,
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


def create_builder_review_package_command(
    generation_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Operator-saved Builder generation "
                "result JSON."
            ),
        ),
    ],
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
    generation_root: Annotated[
        Path,
        typer.Option(
            "--generation-root",
            help="Approved Builder generation root.",
        ),
    ] = Path("builder-generations"),
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
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help=(
                "Root for immutable Builder "
                "human-review packages."
            ),
        ),
    ] = Path("builder-reviews"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Assemble and persist one immutable review package."""

    from geoagent_harness.evolution.builder import BuilderReviewError
    from geoagent_harness.evolution.builder import BuilderReviewStorageError
    from geoagent_harness.task_actions.command_actions import builder__assemble_builder_review_package as assemble_builder_review_package, builder__persist_builder_review_package as persist_builder_review_package

    try:
        review = assemble_builder_review_package(
            generation_file=generation_file,
            generation_root=generation_root,
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record_path=test_record_file,
            evidence_root=evidence_root,
        )
        result = persist_builder_review_package(
            review,
            review_root=review_root,
        )
    except (
        BuilderReviewError,
        BuilderReviewStorageError,
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


def record_builder_review_decision_command(
    review_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder REVIEW.json file.",
        ),
    ],
    decision_id: Annotated[
        str,
        typer.Option(
            "--decision-id",
            help="Unique human decision identifier.",
        ),
    ],
    reviewer_id: Annotated[
        str,
        typer.Option(
            "--reviewer-id",
            help="Identity of the human reviewer.",
        ),
    ],
    decided_at: Annotated[
        str,
        typer.Option(
            "--decided-at",
            help=(
                "Timezone-aware ISO-8601 decision "
                "timestamp."
            ),
        ),
    ],
    decision: Annotated[
        str,
        typer.Option(
            "--decision",
            help="Either approved or rejected.",
        ),
    ],
    rationale: Annotated[
        str,
        typer.Option(
            "--rationale",
            help="Human explanation for the decision.",
        ),
    ],
    approved_paths: Annotated[
        list[str] | None,
        typer.Option(
            "--approved-path",
            help=(
                "Exact reviewed path approved for later "
                "promotion planning; repeat as needed."
            ),
        ),
    ] = None,
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help=(
                "Root for immutable Builder "
                "human-decision records."
            ),
        ),
    ] = Path("builder-decisions"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Record one human decision without promoting files."""

    from datetime import datetime

    from geoagent_harness.evolution.builder import BuilderReviewDecisionError
    from geoagent_harness.evolution.builder import BuilderReviewDecisionStorageError
    from geoagent_harness.task_actions.command_actions import builder__create_builder_review_decision as create_builder_review_decision, builder__persist_builder_review_decision as persist_builder_review_decision

    try:
        normalized_timestamp = (
            decided_at[:-1] + "+00:00"
            if decided_at.endswith("Z")
            else decided_at
        )
        parsed_timestamp = datetime.fromisoformat(
            normalized_timestamp
        )

        if decision not in {
            "approved",
            "rejected",
        }:
            raise ValueError(
                "decision must be approved or rejected"
            )

        review_decision = (
            create_builder_review_decision(
                review_file=review_file,
                review_root=review_root,
                decision_id=decision_id,
                reviewer_id=reviewer_id,
                decided_at=parsed_timestamp,
                decision=decision,
                approved_paths=(
                    []
                    if approved_paths is None
                    else approved_paths
                ),
                rationale=rationale,
            )
        )

        result = persist_builder_review_decision(
            review_decision,
            decision_root=decision_root,
            review_root=review_root,
        )
    except (
        BuilderReviewDecisionError,
        BuilderReviewDecisionStorageError,
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
