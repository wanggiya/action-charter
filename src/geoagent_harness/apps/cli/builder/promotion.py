"""Existing builder promotion CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer


def plan_builder_promotion_command(
    decision_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder DECISION.json file.",
        ),
    ],
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help="Approved Builder decision root.",
        ),
    ] = Path("builder-decisions"),
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "non-writing destination assessment."
            ),
        ),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Plan exact approved Builder writes without performing them."""

    from geoagent_harness.evolution.builder import BuilderPromotionPlanError
    from geoagent_harness.task_actions.command_actions import builder__plan_builder_promotion as plan_builder_promotion

    try:
        result = plan_builder_promotion(
            decision_file=decision_file,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )
    except (
        BuilderPromotionPlanError,
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


def create_builder_promotion_plan_command(
    decision_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder DECISION.json file.",
        ),
    ],
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help="Approved Builder decision root.",
        ),
    ] = Path("builder-decisions"),
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "non-writing destination assessment."
            ),
        ),
    ] = Path("."),
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Immutable Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Create an immutable, reverified Builder promotion plan."""

    from geoagent_harness.evolution.builder import BuilderPromotionPlanError
    from geoagent_harness.evolution.builder import BuilderPromotionPlanStorageError
    from geoagent_harness.task_actions.command_actions import builder__persist_builder_promotion_plan as persist_builder_promotion_plan, builder__plan_builder_promotion as plan_builder_promotion

    try:
        plan = plan_builder_promotion(
            decision_file=decision_file,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )

        result = persist_builder_promotion_plan(
            plan,
            plan_root=plan_root,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
        )
    except (
        BuilderPromotionPlanError,
        BuilderPromotionPlanStorageError,
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


def promote_builder_candidate_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder PLAN.json file.",
        ),
    ],
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help="Approved Builder decision root.",
        ),
    ] = Path("builder-decisions"),
    review_root: Annotated[
        Path,
        typer.Option(
            "--review-root",
            help="Approved Builder review-package root.",
        ),
    ] = Path("builder-reviews"),
    candidate_root: Annotated[
        Path,
        typer.Option(
            "--candidate-root",
            help="Approved Builder candidate root.",
        ),
    ] = Path("builder-candidates"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "destination-state reverification."
            ),
        ),
    ] = Path("."),
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Immutable promoted Builder-bundle root.",
        ),
    ] = Path("builder-promotions"),
    confirm_decision_id: Annotated[
        str,
        typer.Option(
            "--confirm-decision-id",
            help=(
                "Exact approved decision ID that the "
                "operator authorizes for promotion."
            ),
        ),
    ] = "",
    confirm_plan_sha256: Annotated[
        str,
        typer.Option(
            "--confirm-plan-sha256",
            help=(
                "Exact persisted promotion-plan SHA-256 "
                "that the operator authorizes."
            ),
        ),
    ] = "",
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Atomically promote approved files into an immutable bundle."""

    from geoagent_harness.evolution.builder import BuilderPromotionError
    from geoagent_harness.task_actions.command_actions import builder__promote_builder_candidate as promote_builder_candidate

    if not confirm_decision_id:
        typer.echo(
            "Error: --confirm-decision-id is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not confirm_plan_sha256:
        typer.echo(
            "Error: --confirm-plan-sha256 is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        result = promote_builder_candidate(
            plan_file=plan_file,
            plan_root=plan_root,
            decision_root=decision_root,
            review_root=review_root,
            candidate_root=candidate_root,
            project_root=project_root,
            promotion_root=promotion_root,
            confirm_decision_id=(
                confirm_decision_id
            ),
            confirm_plan_sha256=(
                confirm_plan_sha256
            ),
        )
    except (
        BuilderPromotionError,
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


def verify_builder_promotion_command(
    promotion_directory: Annotated[
        Path,
        typer.Argument(
            help=(
                "Promoted Builder bundle directory."
            ),
        ),
    ],
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder PLAN.json file.",
        ),
    ],
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Approved promoted Builder-bundle root.",
        ),
    ] = Path("builder-promotions"),
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Independently verify one promoted bundle read-only."""

    from geoagent_harness.evolution.builder import BuilderPromotionVerificationError
    from geoagent_harness.task_actions.command_actions import builder__verify_builder_promotion_bundle as verify_builder_promotion_bundle

    try:
        result = verify_builder_promotion_bundle(
            promotion_directory,
            promotion_root=promotion_root,
            plan_file=plan_file,
            plan_root=plan_root,
        )
    except (
        BuilderPromotionVerificationError,
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


def create_builder_promotion_verification_command(
    promotion_directory: Annotated[
        Path,
        typer.Argument(
            help="Immutable promoted Builder bundle.",
        ),
    ],
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder PLAN.json file.",
        ),
    ],
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Approved Builder promotion root.",
        ),
    ] = Path("builder-promotions"),
    plan_root: Annotated[
        Path,
        typer.Option(
            "--plan-root",
            help="Approved Builder promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    verification_root: Annotated[
        Path,
        typer.Option(
            "--verification-root",
            help=(
                "Root for immutable Builder "
                "verification evidence."
            ),
        ),
    ] = Path("builder-promotion-verifications"),
    pretty: Annotated[
        bool,
        typer.Option(
            "--pretty",
            help="Indent the JSON response.",
        ),
    ] = False,
) -> None:
    """Verify a promoted bundle and persist exact evidence."""

    from geoagent_harness.evolution.builder import BuilderPromotionVerificationError
    from geoagent_harness.evolution.builder import BuilderPromotionVerificationStorageError
    from geoagent_harness.task_actions.command_actions import builder__persist_builder_promotion_verification as persist_builder_promotion_verification, builder__verify_builder_promotion_bundle as verify_builder_promotion_bundle

    try:
        verification = (
            verify_builder_promotion_bundle(
                promotion_directory=(
                    promotion_directory
                ),
                promotion_root=promotion_root,
                plan_file=plan_file,
                plan_root=plan_root,
            )
        )

        result = (
            persist_builder_promotion_verification(
                verification,
                verification_root=(
                    verification_root
                ),
                promotion_root=promotion_root,
                plan_root=plan_root,
            )
        )
    except (
        BuilderPromotionVerificationError,
        BuilderPromotionVerificationStorageError,
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
