"""Existing builder activation CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer


def create_builder_activation_review_command(
    verification_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder VERIFICATION.json.",
        ),
    ],
    verification_root: Annotated[
        Path,
        typer.Option(
            "--verification-root",
            help="Approved verification-evidence root.",
        ),
    ] = Path("builder-promotion-verifications"),
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
    decision_root: Annotated[
        Path,
        typer.Option(
            "--decision-root",
            help=(
                "Root for immutable activation-review "
                "decisions."
            ),
        ),
    ] = Path("builder-activation-decisions"),
    decision_id: Annotated[
        str,
        typer.Option(
            "--decision-id",
            help="Unique activation-review decision ID.",
        ),
    ] = "",
    reviewer_id: Annotated[
        str,
        typer.Option(
            "--reviewer-id",
            help="Human reviewer identity.",
        ),
    ] = "",
    decided_at: Annotated[
        str,
        typer.Option(
            "--decided-at",
            help=(
                "Timezone-aware ISO-8601 decision "
                "timestamp."
            ),
        ),
    ] = "",
    decision: Annotated[
        str,
        typer.Option(
            "--decision",
            help="Either approved or rejected.",
        ),
    ] = "rejected",
    rationale: Annotated[
        str,
        typer.Option(
            "--rationale",
            help="Human activation-review rationale.",
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
    """Review and persist one verified Builder bundle."""

    from geoagent_harness.evolution.builder import BuilderActivationReviewDecisionStorageError
    from geoagent_harness.evolution.builder import BuilderActivationReviewError
    from geoagent_harness.task_actions.command_actions import builder__create_builder_activation_review_decision as create_builder_activation_review_decision, builder__persist_builder_activation_review_decision as persist_builder_activation_review_decision

    if not decision_id:
        typer.echo(
            "Error: --decision-id is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not reviewer_id:
        typer.echo(
            "Error: --reviewer-id is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not decided_at:
        typer.echo(
            "Error: --decided-at is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        decision_timestamp = (
            datetime.fromisoformat(decided_at)
        )
    except ValueError as exc:
        typer.echo(
            "Error: --decided-at must be a valid "
            "ISO-8601 timestamp",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    if (
        decision_timestamp.tzinfo is None
        or decision_timestamp.utcoffset() is None
    ):
        typer.echo(
            "Error: --decided-at must include "
            "a timezone",
            err=True,
        )
        raise typer.Exit(code=2)

    if not rationale:
        typer.echo(
            "Error: --rationale is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if decision not in {
        "approved",
        "rejected",
    }:
        typer.echo(
            "Error: --decision must be approved "
            "or rejected",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        review_decision = (
            create_builder_activation_review_decision(
                verification_file=verification_file,
                verification_root=verification_root,
                promotion_root=promotion_root,
                plan_root=plan_root,
                decision_id=decision_id,
                reviewer_id=reviewer_id,
                decided_at=decision_timestamp,
                decision=decision,
                rationale=rationale,
            )
        )

        result = (
            persist_builder_activation_review_decision(
                review_decision,
                decision_root=decision_root,
                verification_root=verification_root,
                promotion_root=promotion_root,
                plan_root=plan_root,
            )
        )
    except (
        BuilderActivationReviewError,
        BuilderActivationReviewDecisionStorageError,
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


def plan_builder_activation_command(
    activation_decision_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Immutable Builder "
                "ACTIVATION_DECISION.json."
            ),
        ),
    ],
    activation_decision_root: Annotated[
        Path,
        typer.Option(
            "--activation-decision-root",
            help="Approved activation-decision root.",
        ),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option(
            "--verification-root",
            help="Approved verification-evidence root.",
        ),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option(
            "--promotion-root",
            help="Approved Builder promotion root.",
        ),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option(
            "--promotion-plan-root",
            help="Approved promotion-plan root.",
        ),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root used only for "
                "destination assessment."
            ),
        ),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan exact Builder activation writes without writing."""

    from geoagent_harness.evolution.builder import BuilderActivationPlanError
    from geoagent_harness.task_actions.command_actions import builder__plan_builder_activation as plan_builder_activation

    try:
        result = plan_builder_activation(
            activation_decision_file=(
                activation_decision_file
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderActivationPlanError,
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


def create_builder_activation_plan_command(
    activation_decision_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Immutable Builder "
                "ACTIVATION_DECISION.json."
            ),
        ),
    ],
    activation_decision_root: Annotated[
        Path,
        typer.Option(
            "--activation-decision-root",
        ),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    activation_plan_root: Annotated[
        Path,
        typer.Option(
            "--activation-plan-root",
            help=(
                "Root for immutable Builder "
                "activation plans."
            ),
        ),
    ] = Path("builder-activation-plans"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Create one immutable reverified activation plan."""

    from geoagent_harness.evolution.builder import BuilderActivationPlanError
    from geoagent_harness.evolution.builder import BuilderActivationPlanStorageError
    from geoagent_harness.task_actions.command_actions import builder__persist_builder_activation_plan as persist_builder_activation_plan, builder__plan_builder_activation as plan_builder_activation

    try:
        plan = plan_builder_activation(
            activation_decision_file=(
                activation_decision_file
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )

        result = persist_builder_activation_plan(
            plan,
            plan_root=activation_plan_root,
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderActivationPlanError,
        BuilderActivationPlanStorageError,
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


def activate_builder_bundle_command(
    plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder ACTIVATION_PLAN.json.",
        ),
    ],
    activation_plan_root: Annotated[
        Path,
        typer.Option(
            "--activation-plan-root",
            help="Approved Builder activation-plan root.",
        ),
    ] = Path("builder-activation-plans"),
    activation_decision_root: Annotated[
        Path,
        typer.Option(
            "--activation-decision-root",
            help=(
                "Approved Builder activation-decision "
                "root."
            ),
        ),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help="Trusted project destination root.",
        ),
    ] = Path("."),
    activation_root: Annotated[
        Path,
        typer.Option(
            "--activation-root",
            help="Immutable Builder activation-evidence root.",
        ),
    ] = Path("builder-activations"),
    confirm_activation_decision_id: Annotated[
        str,
        typer.Option(
            "--confirm-activation-decision-id",
            help=(
                "Exact approved activation-decision ID "
                "authorized by the operator."
            ),
        ),
    ] = "",
    confirm_activation_plan_sha256: Annotated[
        str,
        typer.Option(
            "--confirm-activation-plan-sha256",
            help=(
                "Exact persisted activation-plan SHA-256 "
                "authorized by the operator."
            ),
        ),
    ] = "",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Install exact approved Builder files transactionally."""

    from geoagent_harness.evolution.builder import BuilderActivationError
    from geoagent_harness.task_actions.command_actions import builder__activate_builder_bundle as activate_builder_bundle

    if not confirm_activation_decision_id:
        typer.echo(
            "Error: "
            "--confirm-activation-decision-id "
            "is required",
            err=True,
        )
        raise typer.Exit(code=2)

    if not confirm_activation_plan_sha256:
        typer.echo(
            "Error: "
            "--confirm-activation-plan-sha256 "
            "is required",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        result = activate_builder_bundle(
            plan_file=plan_file,
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
            activation_root=activation_root,
            confirm_activation_decision_id=(
                confirm_activation_decision_id
            ),
            confirm_activation_plan_sha256=(
                confirm_activation_plan_sha256
            ),
        )
    except (
        BuilderActivationError,
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


def verify_builder_activation_command(
    activation_directory: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder activation directory.",
        ),
    ],
    activation_plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder ACTIVATION_PLAN.json.",
        ),
    ],
    activation_root: Annotated[
        Path,
        typer.Option("--activation-root"),
    ] = Path("builder-activations"),
    activation_plan_root: Annotated[
        Path,
        typer.Option("--activation-plan-root"),
    ] = Path("builder-activation-plans"),
    activation_decision_root: Annotated[
        Path,
        typer.Option("--activation-decision-root"),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify exact activated Builder files without execution."""

    from geoagent_harness.evolution.builder import BuilderPostActivationVerificationError
    from geoagent_harness.task_actions.command_actions import builder__verify_builder_activation as verify_builder_activation

    try:
        result = verify_builder_activation(
            activation_directory=(
                activation_directory
            ),
            activation_root=activation_root,
            activation_plan_file=(
                activation_plan_file
            ),
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderPostActivationVerificationError,
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


def create_builder_trust_evidence_command(
    activation_directory: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder activation directory.",
        ),
    ],
    activation_plan_file: Annotated[
        Path,
        typer.Argument(
            help="Immutable Builder ACTIVATION_PLAN.json.",
        ),
    ],
    activation_root: Annotated[
        Path,
        typer.Option("--activation-root"),
    ] = Path("builder-activations"),
    activation_plan_root: Annotated[
        Path,
        typer.Option("--activation-plan-root"),
    ] = Path("builder-activation-plans"),
    activation_decision_root: Annotated[
        Path,
        typer.Option("--activation-decision-root"),
    ] = Path("builder-activation-decisions"),
    verification_root: Annotated[
        Path,
        typer.Option("--verification-root"),
    ] = Path("builder-promotion-verifications"),
    promotion_root: Annotated[
        Path,
        typer.Option("--promotion-root"),
    ] = Path("builder-promotions"),
    promotion_plan_root: Annotated[
        Path,
        typer.Option("--promotion-plan-root"),
    ] = Path("builder-promotion-plans"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    trust_evidence_root: Annotated[
        Path,
        typer.Option(
            "--trust-evidence-root",
            help=(
                "Root for immutable post-activation "
                "trust evidence."
            ),
        ),
    ] = Path(
        "builder-post-activation-verifications"
    ),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Verify activation and persist immutable trust evidence."""

    from geoagent_harness.evolution.builder import BuilderPostActivationVerificationError
    from geoagent_harness.evolution.builder import BuilderPostActivationVerificationStorageError
    from geoagent_harness.task_actions.command_actions import builder__persist_builder_trust_evidence as persist_builder_trust_evidence, builder__verify_builder_activation as verify_builder_activation

    try:
        verification = verify_builder_activation(
            activation_directory=(
                activation_directory
            ),
            activation_root=activation_root,
            activation_plan_file=(
                activation_plan_file
            ),
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )

        result = persist_builder_trust_evidence(
            verification,
            evidence_root=trust_evidence_root,
            activation_root=activation_root,
            activation_plan_root=(
                activation_plan_root
            ),
            activation_decision_root=(
                activation_decision_root
            ),
            verification_root=verification_root,
            promotion_root=promotion_root,
            promotion_plan_root=(
                promotion_plan_root
            ),
            project_root=project_root,
        )
    except (
        BuilderPostActivationVerificationError,
        BuilderPostActivationVerificationStorageError,
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
