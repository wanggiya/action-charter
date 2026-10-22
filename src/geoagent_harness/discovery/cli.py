"""Explicit local discovery through the same bounded worker as the interface."""
import json
from pathlib import Path
import typer


def register(app):
    @app.command('submit-inspection')
    def submit(message:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root'),
               execute:bool=typer.Option(False,'--execute'),conversation_id:str|None=typer.Option(None,'--conversation-id'),
               submission_id:str|None=typer.Option(None,'--submission-id'),revision:int=typer.Option(0,'--revision')):
        """Prepare an exact 1–4 dataset inspection; --execute runs permitted reads only."""
        import uuid
        from geoagent_harness.interface_api.inspection_planning import plan_for_request
        from geoagent_harness.interface_api.planner_submission import SubmissionRequest,submission_action
        from geoagent_harness.interface_api.conversation import TurnRequest
        from geoagent_harness.interface_api.server import InterfaceApiError
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
        from geoagent_harness.interface_api.server import InterfaceApiError
        try:
            result=discover_dataset(project_root,path,delimiter)
            typer.echo(json.dumps(result,indent=2,allow_nan=False))
        except (ValueError,OSError,InterfaceApiError):
            typer.echo('Error: discovery failed; check format, source changes and documented budgets. Nothing was written to the dataset.',err=True)
            raise typer.Exit(2)
