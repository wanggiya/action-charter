"""Existing interface CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer


def serve_interface_api_command(
    project_root: Annotated[
        Path,
        typer.Option("--project-root", help="Trusted ActionCharter project root."),
    ] = Path("."),
    host: Annotated[
        str,
        typer.Option("--host", help="Loopback host; only 127.0.0.1 is accepted."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", min=1, max=65535),
    ] = 8765,
) -> None:
    """Serve typed local interface operations with execution disabled by default."""

    from geoagent_harness.interface_api import InterfaceApiError, serve_interface_api

    try:
        serve_interface_api(project_root=project_root, host=host, port=port)
    except (InterfaceApiError, OSError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


def project_interface_workflow_command(
    task_id: Annotated[str, typer.Argument(help="Exact validated workflow task ID.")],
    trace_root: Annotated[Path, typer.Option("--trace-root", help="Approved workflow trace root.")] = Path("traces"),
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Emit a browser-safe, read-only projection of one workflow trace."""

    from geoagent_harness.apps.interface_projection import InterfaceProjectionError, project_workflow_trace

    try:
        projection = project_workflow_trace(task_id=task_id, trace_root=trace_root)
    except InterfaceProjectionError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(
        projection.model_dump(mode="json", by_alias=True),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))


def export_interface_workflows_command(
    trace_root: Annotated[Path, typer.Option("--trace-root", help="Approved workflow trace root.")] = Path("traces"),
    output_root: Annotated[Path, typer.Option("--output-root", help="Local interface runtime-output root.")] = Path("interface/public/runtime"),
    pretty: Annotated[bool, typer.Option("--pretty")] = False,
) -> None:
    """Export a bounded run selector and sanitized workflow projections."""

    from geoagent_harness.apps.interface_projection import InterfaceProjectionError, export_workflow_catalog

    try:
        result = export_workflow_catalog(trace_root=trace_root, output_root=output_root)
    except InterfaceProjectionError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(json.dumps(
        result.model_dump(mode="json"),
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ))
