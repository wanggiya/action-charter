"""Existing schemas CLI commands; shared services retain policy and execution."""

import json
from typing import Annotated, NoReturn
import typer


def schema_policies_command(
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Display the read-only artifact schema registry."""

    from geoagent_harness.task_actions.command_actions import schema_registry__list_schema_policies as list_schema_policies

    payload = {
        "schema_version": "1.0",
        "policies": [
            policy.model_dump(mode="json")
            for policy in list_schema_policies()
        ],
        "registry_modified": False,
    }

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


def assess_schema_compatibility_command(
    artifact_type: Annotated[
        str,
        typer.Argument(
            help=(
                "Registered artifact type, such as "
                "workflow_trace or workflow_state."
            ),
        ),
    ],
    artifact_version: Annotated[
        str,
        typer.Argument(
            help="Artifact schema version to assess.",
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess schema compatibility without mutation."""

    from geoagent_harness.contracts.schema_registry import SchemaRegistryError
    from geoagent_harness.task_actions.command_actions import schema_registry__assess_schema_compatibility as assess_schema_compatibility

    try:
        assessment = assess_schema_compatibility(
            artifact_type=artifact_type,
            artifact_version=artifact_version,
        )
    except SchemaRegistryError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            assessment.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not assessment.readable:
        raise typer.Exit(code=1)


def assess_schema_migration_command(
    artifact_type: Annotated[
        str,
        typer.Argument(
            help="Registered artifact type.",
        ),
    ],
    artifact_version: Annotated[
        str,
        typer.Argument(
            help="Source schema version to assess.",
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess migration needs without modifying artifacts."""

    from geoagent_harness.contracts.schema_registry import SchemaRegistryError
    from geoagent_harness.task_actions.command_actions import schema_registry__assess_migration as assess_migration

    try:
        assessment = assess_migration(
            artifact_type=artifact_type,
            artifact_version=artifact_version,
        )
    except SchemaRegistryError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            assessment.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if assessment.manual_review_required:
        raise typer.Exit(code=1)
