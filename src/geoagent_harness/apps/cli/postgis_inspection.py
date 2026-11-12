"""Existing postgis_inspection CLI commands; shared services retain policy and execution."""

import json
from typing import Annotated, NoReturn
import typer


def inspect_postgis_table_command(
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved PostGIS schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="Exact PostGIS table to inspect."),
    ] = "sample_points",
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Inspect bounded metadata for one approved PostGIS table."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionError
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionRequest
    from geoagent_harness.task_actions.command_actions import postgis_inspection__inspect_postgis_table as inspect_postgis_table

    try:
        result = inspect_postgis_table(
            request=PostGISInspectionRequest(
                target_schema=target_schema,
                target_table=target_table,
            ),
            settings=load_settings(),
        )
    except (PostGISInspectionError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))

    if not result.table_exists:
        raise typer.Exit(code=1)


def compare_postgis_tables_command(
    reference_schema: Annotated[
        str,
        typer.Option(
            "--reference-schema",
            help="Approved reference PostGIS schema.",
        ),
    ] = "agent_sandbox",
    reference_table: Annotated[
        str,
        typer.Option(
            "--reference-table",
            help="Exact reference table.",
        ),
    ] = "reference_layer",
    candidate_schema: Annotated[
        str,
        typer.Option(
            "--candidate-schema",
            help="Approved candidate PostGIS schema.",
        ),
    ] = "agent_sandbox",
    candidate_table: Annotated[
        str,
        typer.Option(
            "--candidate-table",
            help="Exact candidate table.",
        ),
    ] = "candidate_layer",
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Compare two approved PostGIS tables without modification."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.data.databases.postgis.comparison import PostGISComparisonError
    from geoagent_harness.data.databases.postgis.comparison import PostGISComparisonRequest
    from geoagent_harness.task_actions.command_actions import postgis_comparison__compare_postgis_tables as compare_postgis_tables
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionError
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionRequest

    try:
        result = compare_postgis_tables(
            request=PostGISComparisonRequest(
                reference=PostGISInspectionRequest(
                    target_schema=reference_schema,
                    target_table=reference_table,
                ),
                candidate=PostGISInspectionRequest(
                    target_schema=candidate_schema,
                    target_table=candidate_table,
                ),
            ),
            settings=load_settings(),
        )
    except (
        PostGISComparisonError,
        PostGISInspectionError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))

    if not result.matches:
        raise typer.Exit(code=1)


def assess_postgis_change_command(
    reference_schema: Annotated[
        str,
        typer.Option("--reference-schema"),
    ] = "agent_sandbox",
    reference_table: Annotated[
        str,
        typer.Option("--reference-table"),
    ] = "reference_layer",
    candidate_schema: Annotated[
        str,
        typer.Option("--candidate-schema"),
    ] = "agent_sandbox",
    candidate_table: Annotated[
        str,
        typer.Option("--candidate-table"),
    ] = "candidate_layer",
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Classify deterministic PostGIS comparison evidence."""
    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.task_actions.command_actions import postgis_change_assessment__assess_postgis_change as assess_postgis_change
    from geoagent_harness.data.databases.postgis.comparison import PostGISComparisonError
    from geoagent_harness.data.databases.postgis.comparison import PostGISComparisonRequest
    from geoagent_harness.task_actions.command_actions import postgis_comparison__compare_postgis_tables as compare_postgis_tables
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionError
    from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionRequest

    try:
        comparison = compare_postgis_tables(
            request=PostGISComparisonRequest(
                reference=PostGISInspectionRequest(
                    target_schema=reference_schema,
                    target_table=reference_table,
                ),
                candidate=PostGISInspectionRequest(
                    target_schema=candidate_schema,
                    target_table=candidate_table,
                ),
            ),
            settings=load_settings(),
        )
        result = assess_postgis_change(comparison)
    except (
        PostGISComparisonError,
        PostGISInspectionError,
        ValueError,
    ) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))

    if not result.compatible:
        raise typer.Exit(code=1)
