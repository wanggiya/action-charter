"""CLI adapters for the same reusable-recipe and durable-run services as HTTP."""
import json
from pathlib import Path
import typer


def register(app):
    def invoke(kind, request_file, project_root):
        from .workflow_runs import RunRequest,run_action
        from geoagent_harness.recipe_catalog.composition import RecipeRequest,recipe_action
        from .server import InterfaceApiError
        from geoagent_harness.model import ModelClientError,ModelSettingsError
        try:
            if request_file is not None:
                if request_file.is_symlink() or not request_file.is_file() or request_file.stat().st_size>65_536:
                    raise ValueError('Choose a bounded regular JSON request')
                value=json.loads(request_file.read_text())
            else:
                value={'action':'list'}
            if kind=='recipe':
                result=recipe_action(RecipeRequest.model_validate(value),project_root=project_root)
            else:
                # CLI start waits for completion; another terminal may inspect/cancel it.
                result=run_action(RunRequest.model_validate(value),project_root=project_root,background=False)
            typer.echo(json.dumps(result,indent=2))
        except (ValueError,OSError,InterfaceApiError,ModelClientError,ModelSettingsError):
            typer.echo('Request failed typed contracts, model/fixture checks or safe storage. No automatic retry.',err=True)
            raise typer.Exit(2)

    @app.command('reusable-recipes')
    def recipes(request_file:Path|None=typer.Option(None,'--request-file'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        invoke('recipe',request_file,project_root)

    @app.command('workflow-runs')
    def runs(request_file:Path|None=typer.Option(None,'--request-file'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        invoke('run',request_file,project_root)
