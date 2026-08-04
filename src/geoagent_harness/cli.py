"""Typer command-line interface."""

import json
from pathlib import Path
from typing import Annotated

import typer

from geoagent_harness.agent_manifest import load_agent_manifest


app = typer.Typer(
    name="geoagent",
    help="Run allowlisted GeoAgent Skill Harness operations.",
    no_args_is_help=True,
)


@app.command("agent-info")
def agent_info_command(
    role: Annotated[
        str, typer.Argument(help="Logical role: planner, executor, or critic.")
    ],
    agents_root: Annotated[
        Path, typer.Option("--agents-root", help="Trusted agent manifest root.")
    ] = Path("/app/agents"),
) -> None:
    """Validate and display a redacted static agent manifest.

    Checkpoint 1 intentionally exits after validation; it does not call Ollama
    or start an agent loop.
    """
    try:
        manifest = load_agent_manifest(role, agents_root)
    except (OSError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            {
                "id": manifest.id,
                "model_ref": manifest.model_ref,
                "purpose": manifest.purpose,
                "allowed_tools": manifest.permissions.tools,
                "checkpoint_status": "manifest-valid; agent-loop-not-implemented",
            },
            separators=(",", ":"),
        )
    )


@app.command("inspect-vector")
def inspect_vector_command(
    path: Annotated[Path, typer.Argument(help="Dataset beneath data/input.")],
    input_root: Annotated[
        Path,
        typer.Option(
            "--input-root",
            help="Trusted input root; intended for deployment configuration/tests.",
        ),
    ] = Path("data/input"),
    pretty: Annotated[
        bool, typer.Option("--pretty", help="Indent the JSON response.")
    ] = False,
) -> None:
    """Inspect an approved vector dataset without executing a shell."""
    from geoagent_harness.skills.inspect_vector.service import (
        InspectVectorError,
        inspect_vector,
    )
    try:
        result = inspect_vector(path=path, input_root=input_root)
    except InspectVectorError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

@app.command("load-vector-to-postgis")
def load_vector_to_postgis_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Vector dataset beneath the approved input root."
        ),
    ],
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved target schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="New target table name."),
    ] = "loaded_vector",
    source_layer: Annotated[
        str | None,
        typer.Option(
            "--layer",
            help="Required when the source has multiple layers.",
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Load one approved vector layer into a new PostGIS table."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.skills.load_vector_to_postgis.service import (
        LoadVectorError,
        load_vector_to_postgis,
    )

    try:
        result = load_vector_to_postgis(
            path=path,
            target_schema=target_schema,
            target_table=target_table,
            source_layer=source_layer,
            settings=load_settings(),
        )
    except (LoadVectorError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

@app.command("validate-postgis-layer")
def validate_postgis_layer_command(
    target_schema: Annotated[
        str,
        typer.Option("--schema", help="Approved PostGIS schema."),
    ] = "agent_sandbox",
    target_table: Annotated[
        str,
        typer.Option("--table", help="PostGIS table to validate."),
    ] = "checkpoint3b_sample_points",
    expected_row_count: Annotated[
        int | None,
        typer.Option("--expected-row-count"),
    ] = None,
    expected_srid: Annotated[
        int | None,
        typer.Option("--expected-srid"),
    ] = None,
    expected_geometry_type: Annotated[
        str | None,
        typer.Option("--expected-geometry-type"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty", help="Indent the JSON response."),
    ] = False,
) -> None:
    """Deterministically validate one approved PostGIS layer."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.verifier.postgis import (
        PostGISVerificationError,
        validate_postgis_layer,
    )

    try:
        result = validate_postgis_layer(
            target_schema=target_schema,
            target_table=target_table,
            expected_row_count=expected_row_count,
            expected_srid=expected_srid,
            expected_geometry_type=expected_geometry_type,
            settings=load_settings(),
        )
    except (PostGISVerificationError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if not result.passed:
        raise typer.Exit(code=1)

@app.command("run-vector-postgis-workflow")
def run_vector_postgis_workflow_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Vector dataset beneath the approved input root."
        ),
    ],
    target_table: Annotated[
        str,
        typer.Option(
            "--table",
            help="New PostGIS target table.",
        ),
    ],
    target_schema: Annotated[
        str,
        typer.Option(
            "--schema",
            help="Approved PostGIS schema.",
        ),
    ] = "agent_sandbox",
    source_layer: Annotated[
        str | None,
        typer.Option(
            "--layer",
            help="Required for multi-layer datasets.",
        ),
    ] = None,
    original_request: Annotated[
        str,
        typer.Option(
            "--request",
            help="Original task request stored in redacted form.",
        ),
    ] = "Load and validate an approved vector dataset.",
    task_id: Annotated[
        str | None,
        typer.Option(
            "--task-id",
            help="Optional lowercase reproducible task ID.",
        ),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Run the complete validated vector-to-PostGIS workflow."""
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.orchestrator.workflow import (
        WorkflowError,
        run_vector_postgis_workflow,
    )

    try:
        result = run_vector_postgis_workflow(
            path=path,
            source_layer=source_layer,
            target_schema=target_schema,
            target_table=target_table,
            original_request=original_request,
            task_id=task_id,
            settings=load_settings(),
        )
    except (WorkflowError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )

    if result.final_status != "validated_success":
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
