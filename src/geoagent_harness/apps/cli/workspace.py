"""Resolve CLI artifact defaults once, leaving explicitly supplied roots untouched."""
from functools import wraps
import inspect
from pathlib import Path
from typing import get_type_hints

import typer
# New Typer versions own their Click context; older supported versions share
# click's context. Use the same stack as the installed Typer in either case.
try:
    from typer._click.globals import get_current_context
    from typer._click.core import ParameterSource
except ImportError:
    from click import get_current_context
    from click.core import ParameterSource

from geoagent_harness.platform.workspace import RUNTIME_STORES, WorkspaceError, WorkspaceLayout, runtime_store_path


def workspace_defaults(function):
    signature = inspect.signature(function)
    defaults = {name: parameter.default for name, parameter in signature.parameters.items()
                if isinstance(parameter.default, Path) and str(parameter.default) in RUNTIME_STORES}
    if not defaults:
        return function

    @wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        supplied = set(bound.arguments)
        bound.apply_defaults()
        project = Path(bound.arguments.get('project_root', Path.cwd()))
        context = get_current_context(silent=True)
        try:
            for name, default in defaults.items():
                implicit = (context.get_parameter_source(name) == ParameterSource.DEFAULT
                            if context is not None else name not in supplied)
                if implicit:
                    layout = WorkspaceLayout.load(project)
                    # Preserve the old spelling as well as meaning for unchanged
                    # cwd-based projects. Relocated/explicit project defaults bind
                    # to their actual source project rather than the shell's cwd.
                    if layout.state_root != Path.cwd().resolve():
                        bound.arguments[name] = runtime_store_path(project, str(default))
        except WorkspaceError as error:
            typer.echo(f'Error: {error}', err=True)
            raise typer.Exit(2) from error
        return function(*bound.args, **bound.kwargs)

    # Registered commands in other modules can use postponed annotations. Typer
    # must resolve them in the original module, not this wrapper's globals.
    hints = get_type_hints(function, include_extras=True)
    wrapped.__signature__ = signature.replace(parameters=[
        p.replace(annotation=hints.get(name, p.annotation)) for name, p in signature.parameters.items()])
    return wrapped


class WorkspaceTyper(typer.Typer):
    def command(self, *args, **kwargs):
        register = super().command(*args, **kwargs)
        def decorate(function):
            callback = workspace_defaults(function)
            command_name = args[0] if args else function.__name__.replace('_', '-')
            # Migration/startup own their lifetime; auditing them would mutate the
            # state that offline migration is checking or span an entire server.
            if command_name not in {'workspace-migrate', 'workspace-verify', 'workspace-rollback',
                                     'project-identity',
                                     'serve-interface-api', 'chat', 'agent-info', 'recipe-template-catalog'}:
                from geoagent_harness.core.execution.actions import task_entrypoint
                callback = task_entrypoint(callback, trigger='cli', audit=command_name not in {'planning-tasks', 'planning-conversation-read', 'operations', 'library-inventory', 'saved-library-scans', 'search-library-functions', 'plan-task', 'builder-propose', 'critique-task'})
            return register(callback)
        return decorate


def register_workspace_commands(app):
    def emit(callback):
        import json
        try: typer.echo(json.dumps(callback(), indent=2))
        except (WorkspaceError, OSError, ValueError) as error:
            typer.echo(f'Error: {error}', err=True)
            raise typer.Exit(2) from error

    @app.command('project-identity')
    def identity(project_root: Path = typer.Option(Path('.'), '--project-root'),
                 initialize: bool = typer.Option(False, '--initialize'),
                 rebind: bool = typer.Option(False, '--rebind'),
                 offline: bool = typer.Option(False, '--offline')):
        """Read identity; opt in or verify a filesystem rename explicitly offline."""
        from geoagent_harness.platform import project_identity
        def checked():
            if initialize and rebind:
                raise WorkspaceError('Choose either --initialize or --rebind')
            action = project_identity.initialize if initialize else project_identity.rebind if rebind else None
            return action(project_root, offline=offline) if action else project_identity.status(project_root)
        emit(checked)

    @app.command('workspace-migrate')
    def migrate(destination: Path = typer.Argument(),
                project_root: Path = typer.Option(Path('.'), '--project-root'),
                apply: bool = typer.Option(False, '--apply'),
                offline: bool = typer.Option(False, '--offline'),
                archive_legacy: bool = typer.Option(False, '--archive-legacy')):
        """Preview by default; --apply --offline copies/verifies and changes config.

        --archive-legacy moves old roots into the verified workspace backup, deleting nothing.
        Stop all launcher/CLI/worker processes first. No workflow is run or authorized.
        """
        from geoagent_harness.platform.workspace_migration import migrate as action
        emit(lambda: action(project_root, destination, apply=apply, offline=offline,
                            archive_legacy=archive_legacy))

    @app.command('workspace-verify')
    def verify(project_root: Path = typer.Option(Path('.'), '--project-root')):
        """Verify migration inventory/hashes and report remaining legacy roots."""
        from geoagent_harness.platform.workspace_migration import verify as action
        emit(lambda: action(project_root))

    @app.command('workspace-rollback')
    def rollback(project_root: Path = typer.Option(Path('.'), '--project-root'),
                 offline: bool = typer.Option(False, '--offline'),
                 confirm: bool = typer.Option(False, '--confirm-rollback')):
        """Restore prior config/archived roots only when no post-copy state changed."""
        from geoagent_harness.platform.workspace_migration import rollback as action
        def checked():
            if not confirm: raise WorkspaceError('Explicit --confirm-rollback is required')
            return action(project_root, offline=offline)
        emit(checked)
