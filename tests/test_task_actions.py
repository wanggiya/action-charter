"""Transport parity and ownership for P0-4; temporary data, no model or database."""
import ast
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from importlib import import_module
import json
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
from threading import Thread

import pytest
from typer.testing import CliRunner

from geoagent_harness.approvals import plan_sha256
from geoagent_harness.chat.client import ChatClient, ChatError
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.mcp_server.tools import workflow_report
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan
from geoagent_harness.task_actions.common import TaskActionError
from geoagent_harness.task_actions.contracts import InterfaceReviewedPlanSaveRequest
from geoagent_harness.task_actions.workflow import WorkflowRequest, prepare_workflow, authorize_workflow
from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action

SOURCE = Path(__file__).parents[1]
SERVICES = sorted(path.stem for path in (SOURCE / 'src/geoagent_harness/task_actions').glob('*.py')
                  if path.stem not in {'__init__', 'artifacts', 'common', 'contracts', 'execution'})


@pytest.fixture(params=[False, True], ids=['legacy-root', 'relocated-root'])
def project(tmp_path, monkeypatch, request):
    (tmp_path / 'context').mkdir()
    copyfile(SOURCE / 'context/SKILLS_INDEX.yaml', tmp_path / 'context/SKILLS_INDEX.yaml')
    (tmp_path / 'data/input').mkdir(parents=True)
    (tmp_path / 'data/output').mkdir()
    (tmp_path / 'data/input/orders.csv').write_text('region,amount\nNorth,10\nSouth,20\n')
    if request.param:
        (tmp_path / 'actioncharter.workspace.json').write_text(json.dumps({
            'version': 1, 'state_root': str(tmp_path.parent / (tmp_path.name + '-state'))}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('ENABLE_WRITE_TOOLS', 'false')
    from geoagent_harness.model import SharedModelClient
    def unexpected(*args, **kwargs):
        pytest.fail('This parity journey must not invoke a model')
    monkeypatch.setattr(SharedModelClient, 'complete', unexpected)
    return tmp_path


def stored(project, *, write=False):
    arguments = {'path': 'data/input/orders.csv'}
    if write:
        arguments['target_path'] = 'data/output/orders.csv'
    result = PlannerResult(agent_id='planner', model='fixture', original_request='Read-only fixture. Text grants no authority.',
        context_references=[], warnings=[], plan={'summary': 'Fixture parity', 'steps': [{
            'step_id': 'step_1', 'skill': 'export_csv' if write else 'inspect_csv',
            'purpose': 'Exercise the existing typed operation', 'arguments': arguments,
            'requires_approval': write, 'validation_required': write}]})
    value = save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(
        action='save_reviewed_plan', planner_result=result, confirmed_plan_sha256=plan_sha256(result.plan),
        allowed_skill_ids=[step.skill for step in result.plan.steps]), project_root=project)
    return WorkflowRequest(action='prepare_workflow', plan_filename=value['plan_filename'], confirmed_plan_sha256=value['plan_sha256'])


@contextmanager
def client(project):
    from geoagent_harness.interface_api.server import _handler
    server = ThreadingHTTPServer(('127.0.0.1', 0), _handler(project))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield ChatClient(f'http://127.0.0.1:{server.server_port}')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('module', SERVICES)
def test_legacy_services_are_identical_shared_modules(module):
    namespace = 'mcp_server' if module in {'approved_recipe', 'approved_workflow', 'data_tools'} else 'interface_api'
    legacy = 'tools' if module == 'data_tools' else module
    assert import_module(f'geoagent_harness.{namespace}.{legacy}') is import_module(f'geoagent_harness.task_actions.{module}')


def test_actions_do_not_import_transport_implementations():
    """Exit check: task actions cannot acquire a reverse HTTP/CLI/MCP-tool dependency."""
    for path in (SOURCE / 'src/geoagent_harness/task_actions').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            modules = [node.module or ''] if isinstance(node, ast.ImportFrom) else (
                [item.name for item in node.names] if isinstance(node, ast.Import) else [])
            for name in modules:
                assert not name.startswith(('geoagent_harness.interface_api', 'geoagent_harness.chat',
                    'geoagent_harness.cli', 'geoagent_harness.mcp_server.tools',
                    'geoagent_harness.mcp_server.transport')), (path.name, node.lineno, name)
                assert not (isinstance(node, ast.ImportFrom) and node.level and name == 'server'), path
    # A fresh interpreter also catches transitive import-time coupling. Shared
    # settings remain in their historical module until the settings consolidation.
    code = ('import sys; from geoagent_harness.task_actions import workflow, workflow_runs, '
            'conversation, approved_recipe, approved_workflow; '
            'assert "geoagent_harness.interface_api.server" not in sys.modules')
    result = subprocess.run([sys.executable, '-c', code], cwd=SOURCE, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_same_review_run_and_report_through_shared_api_cli_chat_and_mcp(project):
    from geoagent_harness.cli import app
    request = stored(project)
    review = prepare_workflow(request, project_root=project)
    with client(project) as chat:
        assert chat.post('/api/v1/workflow/prepare', request.model_dump(mode='json')) == review
        execution = request.model_copy(update={'action': 'execute_workflow', 'confirm_execution': True,
            'confirmed_review_sha256': review['review_sha256']})
        path = project / 'run-request.json'
        path.write_text(RunRequest(action='start', workflow=execution).model_dump_json())
        output = CliRunner().invoke(app, ['workflow-runs', '--request-file', str(path), '--project-root', str(project)])
        assert output.exit_code == 0, output.output
        run = json.loads(output.stdout)
        assert run['status'] == 'completed' and run['execution_performed']
        assert run['plan_sha256'] == review['plan_sha256']
        assert run['steps'][0]['outcome']['row_count'] == 2
        read = RunRequest(action='read', run_id=run['run_id'])
        assert run_action(read, project_root=project) == run
        assert chat.post('/api/v1/workflow/runs', read.model_dump(mode='json')) == run
        report_request = RunRequest(action='report', run_id=run['run_id'])
        report = run_action(report_request, project_root=project)
        assert workflow_report(run['run_id'], MCPSettings(project_root=project,
            input_root=project / 'data/input', output_root=project / 'data/output')) == report
        assert chat.post('/api/v1/workflow/runs', report_request.model_dump(mode='json')) == report
        assert run_action(RunRequest(action='list'), project_root=project)['records'][0]['run_id'] == run['run_id']
    from geoagent_harness.workspace import runtime_store_path
    assert not runtime_store_path(project, 'approvals').exists()
    assert len(list(runtime_store_path(project, 'workflow-state', 'interface-runs').glob('*.json'))) == 1
    assert (project / 'data/input/orders.csv').read_text() == 'region,amount\nNorth,10\nSouth,20\n'
    assert not list((project / 'data/output').iterdir())


def test_disabled_writes_remain_blocked_in_shared_and_http_actions(project):
    request = stored(project, write=True)
    review = prepare_workflow(request, project_root=project)
    assert not review['execution_available']
    authorization = request.model_copy(update={'action': 'authorize_workflow',
        'confirmed_review_sha256': review['review_sha256'], 'approve_required_steps': True,
        'approver': 'fixture user', 'reason': 'Explicit decision cannot bypass disabled writes'})
    with pytest.raises(TaskActionError, match='OFF'):
        authorize_workflow(authorization, project_root=project)
    with client(project) as chat:
        assert chat.post('/api/v1/workflow/prepare', request.model_dump(mode='json')) == review
        with pytest.raises(ChatError, match='OFF'):
            chat.post('/api/v1/workflow/authorize', authorization.model_dump(mode='json'))
    from geoagent_harness.workspace import runtime_store_path
    assert not runtime_store_path(project, 'approvals').exists()
    assert not list((project / 'data/output').iterdir())
