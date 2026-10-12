"""CLI parity through the same workflow services used by the interface."""
from pathlib import Path
from typing import Annotated
import json
import typer


def register(app):
    @app.command('inspect-csv')
    def inspect(path: Annotated[str,typer.Argument()], project_root: Annotated[Path,typer.Option('--project-root')]=Path('.'), delimiter: Annotated[str,typer.Option('--delimiter')]=',', preview_rows: Annotated[int,typer.Option('--preview-rows')]=5):
        from .service import inspect_csv
        from geoagent_harness.mcp_server.settings import load_settings
        from geoagent_harness.redaction import redact_value
        try:
            settings=load_settings().model_copy(update={'project_root':project_root.resolve()})
            typer.echo(json.dumps(redact_value(inspect_csv(path,settings,delimiter,preview_rows)),indent=2))
        except (ValueError,OSError) as error:
            typer.echo(f'Error: {error}',err=True);raise typer.Exit(2)

    @app.command('workflow-plan')
    def plan(request_file: Annotated[Path,typer.Argument()], project_root: Annotated[Path,typer.Option('--project-root')]=Path('.'), request: Annotated[str,typer.Option('--request')]='Operator-authored typed workflow'):
        from geoagent_harness.planner.schemas import PlannerResult, WorkflowPlan
        from geoagent_harness.interface_api.workflow import EditRequest,validate_edit
        from geoagent_harness.interface_api.server import InterfaceReviewedPlanSaveRequest,save_interface_reviewed_plan
        try:
            if request_file.stat().st_size>64000:raise ValueError('Workflow request exceeds 64 KiB')
            result=PlannerResult(model='operator-authored',original_request=request,context_references=[],plan=WorkflowPlan.model_validate_json(request_file.read_text()))
            validated=validate_edit(EditRequest(action='validate_plan_edit',planner_result=result),project_root=project_root)
            saved=save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=result,confirmed_plan_sha256=validated['plan_sha256'],allowed_skill_ids=validated['allowed_skill_ids']),project_root=project_root)
            typer.echo(json.dumps({'planner_result':validated,'saved':saved,'human_review_performed':False,'approval_performed':False,'execution_performed':False},indent=2))
        except (ValueError,OSError,RuntimeError) as error:
            typer.echo(f'Error: {error}',err=True);raise typer.Exit(2)

    def call(action,filename,sha,root,**extra):
        from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow,authorize_workflow,execute_workflow
        try:
            result={'prepare_workflow':prepare_workflow,'authorize_workflow':authorize_workflow,'execute_workflow':execute_workflow}[action](WorkflowRequest(action=action,plan_filename=filename,confirmed_plan_sha256=sha,**extra),project_root=root)
            typer.echo(json.dumps(result,indent=2))
        except (ValueError,OSError,RuntimeError) as error:
            typer.echo(f'Error: {error}',err=True);raise typer.Exit(2)

    @app.command('workflow-review')
    def review(filename: Annotated[str,typer.Argument()], plan_sha: Annotated[str,typer.Option('--plan-sha')], project_root: Annotated[Path,typer.Option('--project-root')]=Path('.')):
        call('prepare_workflow',filename,plan_sha,project_root)

    @app.command('workflow-authorize')
    def authorize(filename: Annotated[str,typer.Argument()], plan_sha: Annotated[str,typer.Option('--plan-sha')], review_sha: Annotated[str,typer.Option('--review-sha')], approver: Annotated[str,typer.Option('--approver')], reason: Annotated[str,typer.Option('--reason')], project_root: Annotated[Path,typer.Option('--project-root')]=Path('.')):
        call('authorize_workflow',filename,plan_sha,project_root,confirmed_review_sha256=review_sha,approve_required_steps=True,approver=approver,reason=reason)

    @app.command('workflow-execute')
    def execute(filename: Annotated[str,typer.Argument()], plan_sha: Annotated[str,typer.Option('--plan-sha')], review_sha: Annotated[str,typer.Option('--review-sha')], confirm: Annotated[bool,typer.Option('--confirm-execution')]=False, plan_approval: Annotated[str | None,typer.Option('--plan-approval')]=None, recipe_approval: Annotated[str | None,typer.Option('--recipe-approval')]=None, project_root: Annotated[Path,typer.Option('--project-root')]=Path('.')):
        if not confirm:typer.echo('Error: --confirm-execution is required',err=True);raise typer.Exit(2)
        call('execute_workflow',filename,plan_sha,project_root,confirmed_review_sha256=review_sha,confirm_execution=True,plan_approval_filename=plan_approval,recipe_approval_filename=recipe_approval)
