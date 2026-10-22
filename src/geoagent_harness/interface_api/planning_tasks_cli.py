"""Non-model task controls through the shared conversation coordinator."""
from pathlib import Path
import json
import typer


def register(app):
    def emit(action, conversation_id, root, **fields):
        from .conversation import TurnRequest, conversation_turn
        from .server import InterfaceApiError
        from geoagent_harness.planner.agent import PlannerAgentError
        from geoagent_harness.context_pack.builder import ContextPackError
        from geoagent_harness.model import ModelClientError, ModelSettingsError
        try:
            request = TurnRequest(action=action, conversation_id=conversation_id, **fields)
            typer.echo(json.dumps(conversation_turn(request, project_root=root), indent=2))
        except (ValueError, OSError, InterfaceApiError, ModelClientError, ModelSettingsError, PlannerAgentError, ContextPackError) as error:
            from geoagent_harness.context_pack.redaction import redact_text
            typer.echo('Error: ' + redact_text(str(error))[:1000], err=True)
            raise typer.Exit(2)

    @app.command('planning-tasks')
    def inventory(project_root: Path = typer.Option(Path('.'), '--project-root')):
        emit('list_tasks', '0' * 32, project_root)

    @app.command('planning-conversation-read')
    def read(conversation_id: str = typer.Argument(), project_root: Path = typer.Option(Path('.'), '--project-root')):
        emit('read', conversation_id, project_root)

    @app.command('outcome-recommendations')
    def recommendation_setting(conversation_id:str=typer.Argument(),enabled:bool=typer.Option(...,'--enabled/--disabled'),
                    expected_revision:int=typer.Option(...,'--expected-revision'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        """Set this chat's evidence-ranking preference; no inference or execution."""
        emit('configure_recommendations',conversation_id,project_root,expected_revision=expected_revision,recommendations_enabled=enabled)

    @app.command('reset-outcome-recommendations')
    def reset_recommendations(conversation_id:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root')):
        """Forget derived own-chat ranking evidence, preserving runs and authority."""
        import re
        if not re.fullmatch(r'[a-f0-9]{32}', conversation_id):
            raise typer.BadParameter('Invalid conversation identity')
        from geoagent_harness.planner.outcome_recommendations import reset
        reset(project_root, conversation_id)
        typer.echo('Derived ranking evidence reset. Durable runs preserved.')

    @app.command('capability-acquisition')
    def acquisition(conversation_id:str=typer.Argument(),enabled:bool=typer.Option(...,'--enabled/--disabled'),
                    expected_revision:int=typer.Option(...,'--expected-revision'),project_root:Path=typer.Option(Path('.'),'--project-root')):
        """Set this conversation's candidate-preparation switch; no model or execution."""
        emit('configure_acquisition',conversation_id,project_root,expected_revision=expected_revision,acquisition_enabled=enabled)

    @app.command('capability-attempts')
    def attempts(conversation_id:str=typer.Argument(),project_root:Path=typer.Option(Path('.'),'--project-root')):
        from geoagent_harness.capabilities.service import attempts as history
        try:typer.echo(json.dumps(history(project_root,conversation_id),indent=2))
        except (ValueError,OSError) as error:
            typer.echo('Error: capability evidence is unavailable or invalid',err=True);raise typer.Exit(2) from error

    @app.command('install-chat-capability')
    def install_capability(conversation_id:str=typer.Argument(),candidate_sha:str=typer.Option(...,'--candidate-sha'),
                           confirm:bool=typer.Option(False,'--confirm-install'),expected_revision:int=typer.Option(...,'--expected-revision'),
                           project_root:Path=typer.Option(Path('.'),'--project-root')):
        """Retest/install the exact chat candidate; no workflow authorization or execution."""
        if not confirm:
            typer.echo('Error: explicit --confirm-install is required',err=True);raise typer.Exit(2)
        emit('install_capability',conversation_id,project_root,expected_revision=expected_revision,confirmed_candidate_sha256=candidate_sha)

    @app.command('planning-task-bind-plan')
    def bind(conversation_id: str = typer.Argument(), task_id: str = typer.Argument(),
             plan_file: Path = typer.Option(..., '--plan-file'),
             expected_revision: int = typer.Option(..., '--expected-revision'),
             expected_task_revision: int = typer.Option(..., '--expected-task-revision'),
             project_root: Path = typer.Option(Path('.'), '--project-root')):
        if plan_file.is_symlink() or not plan_file.is_file() or plan_file.stat().st_size > 64000:
            typer.echo('Error: choose a regular bounded PlannerResult JSON file', err=True)
            raise typer.Exit(2)
        try:
            result = json.loads(plan_file.read_text())
        except (ValueError, OSError):
            typer.echo('Error: invalid PlannerResult JSON file', err=True)
            raise typer.Exit(2)
        emit('bind_task_plan', conversation_id, project_root, task_id=task_id, current_plan=result,
             expected_revision=expected_revision, expected_task_revision=expected_task_revision)

    @app.command('planning-conversation-bind-plan')
    def bind_conversation(conversation_id: str = typer.Argument(), plan_file: Path = typer.Option(..., '--plan-file'),
                          expected_revision: int = typer.Option(..., '--expected-revision'),
                          project_root: Path = typer.Option(Path('.'), '--project-root')):
        bind(conversation_id, conversation_id, plan_file, expected_revision, expected_revision, project_root)

    @app.command('planning-conversation-turn')
    def turn(request_file: Path = typer.Option(..., '--request-file'),
             project_root: Path = typer.Option(Path('.'), '--project-root')):
        from .conversation import TurnRequest
        if request_file.is_symlink() or not request_file.is_file() or request_file.stat().st_size > 64000:
            typer.echo('Error: choose a regular bounded conversation request JSON file', err=True)
            raise typer.Exit(2)
        try:
            request = TurnRequest.model_validate_json(request_file.read_text())
            if request.action != 'turn':
                raise ValueError('Expected a turn request')
        except (ValueError, OSError):
            typer.echo('Error: invalid conversation turn request', err=True)
            raise typer.Exit(2)
        fields = request.model_dump(exclude={'action','conversation_id'})
        emit('turn', request.conversation_id, project_root, **fields)

    @app.command('planning-submit')
    def submit(request_file: Path = typer.Option(..., '--request-file'),
               project_root: Path = typer.Option(Path('.'), '--project-root')):
        """Submit a typed turn with explicit inspection intent, or read its receipt."""
        from .planner_submission import SubmissionRequest, submission_action
        from .server import InterfaceApiError
        from geoagent_harness.planner.agent import PlannerAgentError
        from geoagent_harness.context_pack.builder import ContextPackError
        from geoagent_harness.model import ModelClientError, ModelSettingsError
        if request_file.is_symlink() or not request_file.is_file() or request_file.stat().st_size > 64000:
            raise typer.BadParameter('Choose a regular submission request JSON file under 64 KB')
        try:
            request = SubmissionRequest.model_validate_json(request_file.read_text())
            typer.echo(json.dumps(submission_action(request, project_root=project_root), indent=2))
        except (ValueError, OSError, InterfaceApiError, PlannerAgentError, ContextPackError, ModelClientError, ModelSettingsError) as error:
            from geoagent_harness.context_pack.redaction import redact_text
            typer.echo('Error: ' + redact_text(str(error))[:1000], err=True)
            raise typer.Exit(2)
