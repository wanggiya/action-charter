"""Explicit local discovery through the same bounded worker as the interface."""
import json
from pathlib import Path
import typer


def register(app):
    @app.command('discover-inputs')
    def discover(directory:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root')):
        from geoagent_harness.tabular.strategy import discover_inputs
        try:typer.echo(json.dumps(discover_inputs(project_root,directory),indent=2))
        except ValueError as error:typer.echo(str(error),err=True);raise typer.Exit(2)

    @app.command('assess-table')
    def assess(path:str=typer.Argument(),operation:str=typer.Option('profile','--operation'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        from geoagent_harness.tabular.strategy import assess_table
        try:typer.echo(json.dumps(assess_table(project_root,path,operation),indent=2))
        except ValueError as error:typer.echo(str(error),err=True);raise typer.Exit(2)

    @app.command('explore-data')
    def explore(message:str=typer.Argument(),directory:str=typer.Option(...,'--directory'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        from geoagent_harness.tabular.analyst import run_session
        try:typer.echo(json.dumps(run_session(project_root,message,directory),indent=2))
        except ValueError as error:typer.echo(str(error),err=True);raise typer.Exit(2)

    @app.command('profile-dataset')
    def profile_dataset(path:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root'),options:Path|None=typer.Option(None,'--options')):
        """Comprehensive CSV/TSV profiling through the same sandbox contract as MCP and Planner."""
        from geoagent_harness.tabular.dataset_service import profile_dataset as profile
        try:
            if options and options.stat().st_size>16000:raise ValueError('Options exceed 16 KiB')
            value=json.loads(options.read_text()) if options else {}
            typer.echo(json.dumps(profile(project_root,path,value,delimiter='\t' if path.endswith('.tsv') else ','),indent=2,allow_nan=False))
        except (ValueError,OSError) as error:
            typer.echo(str(error),err=True);raise typer.Exit(2)

    @app.command('profile-csv')
    def profile(path: str = typer.Argument(), project_root: Path = typer.Option(Path('.'), '--project-root'),
                options: Path | None = typer.Option(None, '--options')):
        """Full-file profiles, quality/duplicate checks and group summaries using closed JSON options; no dataset writes."""
        from geoagent_harness.tabular.analytical_service import profile_table
        from geoagent_harness.task_actions.common import InterfaceApiError
        try:
            if options and options.stat().st_size > 16000:
                raise ValueError('Options exceed 16 KiB')
            value = json.loads(options.read_text()) if options else {}
            typer.echo(json.dumps(profile_table(project_root, path, value), indent=2, allow_nan=False))
        except (ValueError, OSError, InterfaceApiError) as error:
            typer.echo(f'Error: {error}', err=True)
            raise typer.Exit(2)

    @app.command('submit-inspection')
    def submit(message:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root'),
               execute:bool=typer.Option(False,'--execute'),conversation_id:str|None=typer.Option(None,'--conversation-id'),
               submission_id:str|None=typer.Option(None,'--submission-id'),revision:int=typer.Option(0,'--revision')):
        """Prepare an exact 1–4 dataset inspection; --execute runs permitted reads only."""
        import uuid
        from geoagent_harness.task_actions.inspection_planning import plan_for_request
        from geoagent_harness.task_actions.planner_submission import SubmissionRequest,submission_action
        from geoagent_harness.task_actions.conversation import TurnRequest
        from geoagent_harness.task_actions.common import InterfaceApiError
        try:
            if plan_for_request(message,['inspect_csv','inspect_vector','inspect_raster']) is None:
                raise ValueError('Use an exact supported inspection request')
            chat=conversation_id or uuid.uuid4().hex
            request=SubmissionRequest(action='submit',submission_id=submission_id or uuid.uuid4().hex,
                conversation_id=chat,inspect_on_send=execute,
                turn=TurnRequest(action='turn',conversation_id=chat,expected_revision=revision,message=message))
            result=submission_action(request,project_root=project_root,background=False)
            typer.echo(json.dumps(result,indent=2,allow_nan=False))
        except (ValueError,OSError,InterfaceApiError):
            typer.echo('Error: inspection submission stopped. Check source scope, revision and recorded receipt/run before retrying.',err=True)
            raise typer.Exit(2)

    @app.command('discover-dataset')
    def discover(path:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root'),
                 delimiter:str|None=typer.Option(None,'--delimiter')):
        """Read characteristics and complete identity; no model or write authority."""
        from .service import discover_dataset
        from geoagent_harness.task_actions.common import InterfaceApiError
        try:
            result=discover_dataset(project_root,path,delimiter)
            typer.echo(json.dumps(result,indent=2,allow_nan=False))
        except (ValueError,OSError,InterfaceApiError):
            typer.echo('Error: discovery failed; check format, source changes and documented budgets. Nothing was written to the dataset.',err=True)
            raise typer.Exit(2)
