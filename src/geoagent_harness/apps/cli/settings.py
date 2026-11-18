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


models_app=typer.Typer(help='Manage trusted model profiles; changes grant no execution authority.')


def _models_emit(function):
    try:typer.echo(json.dumps(function(),indent=2))
    except (ValueError,OSError,RuntimeError):
        typer.echo('Model profile action failed; check configuration and refresh its revision.',err=True)
        raise typer.Exit(2) from None


@models_app.command('profiles')
def model_profiles(project_root: Path=typer.Option(Path('.'),'--project-root')):
    from geoagent_harness.task_actions.model_providers import list_profiles
    _models_emit(lambda:list_profiles(project_root))


@models_app.command('save')
def save_model_profile(file: Path,expected_revision:int=typer.Option(...,'--expected-revision'),project_root:Path=typer.Option(Path('.'),'--project-root')):
    from geoagent_harness.task_actions.model_providers import save_profile,ProviderUpdate
    def action():
        if not file.is_file() or file.stat().st_size>65536:raise ValueError()
        return save_profile(project_root,ProviderUpdate(profile=json.loads(file.read_text()),expected_revision=expected_revision))
    _models_emit(action)


@models_app.command('use')
def use_model_profile(profile_id:str,expected_revision:int=typer.Option(...,'--expected-revision'),project_root:Path=typer.Option(Path('.'),'--project-root')):
    from geoagent_harness.task_actions.model_providers import select_profile,ProviderSelection
    _models_emit(lambda:select_profile(project_root,ProviderSelection(profile_id=profile_id,expected_revision=expected_revision)))


@models_app.command('list')
def available_models(project_root:Path=typer.Option(Path('.'),'--project-root')):
    from geoagent_harness.task_actions.model_providers import list_models
    _models_emit(lambda:list_models(project_root))


@models_app.command('select')
def choose_model(model:str,expected_revision:int=typer.Option(...,'--expected-revision'),project_root:Path=typer.Option(Path('.'),'--project-root')):
    from geoagent_harness.task_actions.model_providers import select_model,Selection,list_profiles
    def action():
        state=list_profiles(project_root)
        return select_model(project_root,Selection(model=model,expected_revision=expected_revision,provider_id=state['selected_profile'],provider_revision=state['revision']))
    _models_emit(action)


@models_app.command('check')
def check_model_profile(profile_id:str,model:str,expected_revision:int=typer.Option(...,'--expected-revision'),project_root:Path=typer.Option(Path('.'),'--project-root')):
    from geoagent_harness.task_actions.model_providers import check_profile,ProviderCheck
    _models_emit(lambda:check_profile(project_root,ProviderCheck(profile_id=profile_id,model=model,expected_revision=expected_revision)))
