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


if __name__ == "__main__":
    app()
