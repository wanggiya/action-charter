"""Existing settings CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer
from geoagent_harness.task_actions.command_actions import agent_manifest__load_agent_manifest as load_agent_manifest


def agent_info_command(
    role: Annotated[
        str, typer.Argument(help="Logical role: planner, executor, critic, or builder.")
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
                "checkpoint_status": "manifest-valid; role-runtime-implemented",
            },
            separators=(",", ":"),
        )
    )


def write_policy_command(
    project_root: Annotated[Path, typer.Option('--project-root')] = Path('.'),
    enabled: Annotated[bool | None, typer.Option('--enabled/--disabled')] = None,
) -> None:
    """Read/change the running API's availability; never authorize or execute."""
    from geoagent_harness.core.policy.write_policy import PolicyUpdate
    from geoagent_harness.task_actions.command_actions import write_policy__snapshot as snapshot, write_policy__update as update
    try:
        state=snapshot(project_root)
        if state is None:
            raise ValueError('No running API session for this project. Start the launcher first. Standalone commands retain explicit startup permissions.')
        if enabled is not None:
            state=update(project_root,PolicyUpdate(enabled=enabled,session_id=state['session_id'],revision=state['revision']))
        typer.echo(json.dumps(state,indent=2))
    except (ValueError,OSError) as exc:
        typer.echo(f'Error: {exc}',err=True)
        raise typer.Exit(code=2) from exc
