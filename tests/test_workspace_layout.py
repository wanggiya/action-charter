"""Workspace relocation preserves identities and refuses silent loss of planning state."""
import json
import sqlite3

import pytest

from tests.test_task_agents import project
from geoagent_harness.workspace import WorkspaceLayout, WorkspaceError, CONFIG_NAME
from geoagent_harness.interface_api.planning_tasks import database
from geoagent_harness.interface_api.server import InterfaceApiError


def configure(root, state):
    (root / CONFIG_NAME).write_text(json.dumps({'version': 1, 'state_root': str(state)}))


def test_legacy_paths_and_reads_do_not_create_state(tmp_path):
    layout = WorkspaceLayout.load(tmp_path)
    assert layout.runtime_path('plans') == tmp_path / 'plans'
    with database(tmp_path) as connection:
        assert connection is None
    assert list(tmp_path.iterdir()) == []


def test_new_project_uses_external_database_and_read_is_side_effect_free(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    state = tmp_path / 'private-state'
    configure(project, state)
    with database(project) as connection:
        assert connection is None
    assert not state.exists()
    with database(project, write=True) as connection:
        connection.execute('INSERT INTO conversations VALUES (?, ?)', ('a'*32, '{"revision":1}'))
    with database(project) as connection:
        assert connection.execute('SELECT value FROM conversations').fetchone()[0] == '{"revision":1}'
    assert (state / 'planner-workspace/tasks.sqlite3').exists()
    assert not (project / 'planner-workspace').exists()
    assert state.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize('state', ['../escape', 'data/state', 'src/state', '.secrets/state', '.git/state', '.local/state', 'planner-workspace/state'])
def test_overlapping_or_traversing_state_rejected(tmp_path, state):
    configure(tmp_path, state)
    with pytest.raises(WorkspaceError): WorkspaceLayout.load(tmp_path)


def test_symlink_components_and_unknown_stores_rejected(tmp_path):
    target = tmp_path / 'target'; target.mkdir()
    (tmp_path / 'link').symlink_to(target, target_is_directory=True)
    configure(tmp_path, 'link/state')
    with pytest.raises(WorkspaceError, match='symbolic'): WorkspaceLayout.load(tmp_path)
    (tmp_path / CONFIG_NAME).unlink()
    with pytest.raises(WorkspaceError): WorkspaceLayout.load(tmp_path).runtime_path('../data')


@pytest.mark.parametrize('config', [{}, {'version': True, 'state_root': 'state'}, {'version': 2, 'state_root': 'state'}, {'version': 1, 'state_root': ''}, {'version': 1, 'state_root': 'state', 'extra': True}])
def test_invalid_configuration_rejected(tmp_path, config):
    (tmp_path / CONFIG_NAME).write_text(json.dumps(config))
    with pytest.raises(WorkspaceError): WorkspaceLayout.load(tmp_path)


def test_existing_state_requires_offline_copy_and_remains_byte_identical(tmp_path):
    with database(tmp_path, write=True) as connection:
        connection.execute('INSERT INTO conversations VALUES (?, ?)', ('a'*32, '{"plan_sha256":"unchanged"}'))
    legacy = tmp_path / 'planner-workspace/tasks.sqlite3'
    before = legacy.read_bytes()
    configure(tmp_path, 'state')
    for write in (False, True):
        with pytest.raises(InterfaceApiError, match='not been migrated'):
            with database(tmp_path, write=write): pass
    assert legacy.read_bytes() == before and not (tmp_path / 'state').exists()
    destination = tmp_path / 'state/planner-workspace'; destination.mkdir(parents=True)
    # Test-only offline SQLite backup, not a file copy of a running database.
    with sqlite3.connect(legacy) as source, sqlite3.connect(destination / 'tasks.sqlite3') as copied:
        source.backup(copied)
    with database(tmp_path) as connection:
        assert connection.execute('SELECT value FROM conversations').fetchone()[0] == '{"plan_sha256":"unchanged"}'
    assert legacy.read_bytes() == before


def test_existing_task_chat_model_and_diagnostics_flows_use_same_workspace(project, monkeypatch):
    # Run the real conversation coordinator with a fixture model, never Ollama.
    from tests.test_planner_conversation import Client
    from geoagent_harness.interface_api.conversation import conversation_turn, TurnRequest
    from geoagent_harness.model.telemetry import read
    configure(project, 'state')
    monkeypatch.setenv('MODEL_NAME', 'fixture')
    reply = {'message':'Proposed', 'plan': {'summary':'Inspect', 'steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect', 'arguments':{'path':'sample_orders.csv'}}]}}
    state = conversation_turn(TurnRequest(action='turn', conversation_id='a'*32, message='Inspect sample_orders.csv.'), project_root=project, model_client=Client(reply))
    saved = conversation_turn(TurnRequest(action='read', conversation_id='a'*32), project_root=project)
    assert saved['planner_result']['plan_sha256'] == state['planner_result']['plan_sha256']
    assert not saved['execution_performed'] and not saved['approval_performed']
    assert read(project, 'a'*32)['records']
    assert (project / 'state/planner-workspace/tasks.sqlite3').exists()
    assert not (project / 'planner-workspace').exists()


def _inspect(root):
    from geoagent_harness.interface_api.planner_submission import submission_action,SubmissionRequest
    from geoagent_harness.interface_api.conversation import TurnRequest
    class NoModel:
        def complete(self,*args):raise AssertionError('Metadata proposal must not invoke a model')
    return submission_action(SubmissionRequest(action='submit',submission_id='d'*32,conversation_id='c'*32,
        inspect_on_send=True,turn=TurnRequest(action='turn',conversation_id='c'*32,
        message='Run a new read-only inspection of sample_orders.csv')),project_root=root,model_client=NoModel(),background=False)


def test_relocated_chat_plan_run_history_and_no_replay(project,tmp_path_factory):
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    from geoagent_harness.interface_api.chat_history import history_action,HistoryRequest
    from geoagent_harness.interface_api.planner_submission import submission_action,SubmissionRequest
    state=tmp_path_factory.mktemp('external-state');configure(project,state)
    result=_inspect(project);record=result['run'];assert record['status']=='completed'
    digest=record['plan_sha256']
    assert (state/'planner-conversations').is_dir()
    assert (state/'plans'/record['plan_filename']).exists()
    assert (state/'workflow-state/interface-runs'/(record['run_id']+'.json')).exists()
    assert not (project/'plans').exists() and not (project/'planner-conversations').exists()
    restored=conversation_turn(TurnRequest(action='read',conversation_id='c'*32),project_root=project)
    assert restored['planner_result']['plan_sha256']==digest
    from geoagent_harness.interface_api.workflow_runs import run_action,RunRequest
    latest=run_action(RunRequest(action='latest',conversation_id='c'*32,confirmed_plan_sha256=digest),project_root=project)
    assert latest['record']['run_id']==record['run_id'] and not latest['execution_performed']
    inventory=conversation_turn(TurnRequest(action='list',conversation_id='c'*32),project_root=project)
    assert any(c['conversation_id']=='c'*32 for c in inventory['conversations'])
    history=history_action(HistoryRequest(action='list',conversation_id='c'*32),project_root=project)
    assert any(e['id']=='run:'+record['run_id'] for e in history['entries'])
    again=submission_action(SubmissionRequest(action='read',submission_id='d'*32,conversation_id='c'*32),project_root=project)
    assert again['run']['run_id']==record['run_id']
    assert len(list((state/'workflow-state/interface-runs').glob('*.json')))==1
    assert not (project/'approvals').exists() and not list((project/'data/output').iterdir())


def test_offline_copies_preserve_saved_plan_run_bytes_and_history(project,tmp_path_factory):
    import shutil
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    from geoagent_harness.interface_api.workflow_runs import run_action,RunRequest
    original=_inspect(project);run=original['run']
    stores=['planner-conversations','plans','workflow-state','workflow-recipes','inspection-runs']
    before={str(p.relative_to(project)):p.read_bytes() for store in stores for p in (project/store).rglob('*.json')}
    target=tmp_path_factory.mktemp('copied-state')
    for store in stores:shutil.copytree(project/store,target/store)
    (target/'planner-workspace').mkdir()
    with sqlite3.connect(project/'planner-workspace/tasks.sqlite3') as source,sqlite3.connect(target/'planner-workspace/tasks.sqlite3') as copied:source.backup(copied)
    configure(project,target)
    restored=conversation_turn(TurnRequest(action='read',conversation_id='c'*32),project_root=project)
    assert restored['planner_result']['plan_sha256']==run['plan_sha256']
    assert run_action(RunRequest(action='read',run_id=run['run_id']),project_root=project)['status']=='completed'
    assert all((project/name).read_bytes()==data and (target/name).read_bytes()==data for name,data in before.items())


def test_run_recovery_uses_source_project_for_partial_outputs(project,tmp_path_factory):
    from geoagent_harness.interface_api.workflow_runs import _directory,_write,_read
    target=tmp_path_factory.mktemp('isolated-state');configure(project,target)
    (project/'data/output').mkdir(exist_ok=True);(project/'data/output/partial.csv').write_text('x\n1\n')
    directory=_directory(project)
    record={'run_id':'e'*32,'status':'running','steps':[{'step_id':'step_1','skill_id':'export_csv','status':'running','arguments':{'target_path':'data/output/partial.csv'}}],
            'finished_at':None,'finding':None,'failed_step_id':None}
    _write(directory,record)
    recovered=_read(directory,'e'*32,project_root=project)
    assert recovered['status']=='interrupted' and recovered['partial_outputs']
    assert recovered['partial_outputs'][0]['path']=='data/output/partial.csv'
    assert not (target/'data/output').exists()


@pytest.mark.parametrize('store,parts',[('planner-conversations',()),('plans',()),('workflow-state',('interface-runs',))])
def test_missing_relocated_store_does_not_hide_legacy_records(tmp_path,store,parts):
    from geoagent_harness.workspace import runtime_store_path
    legacy=tmp_path.joinpath(store,*parts);legacy.mkdir(parents=True)
    (legacy/'record.json').write_text('{}')
    configure(tmp_path,'new-state')
    with pytest.raises(WorkspaceError,match='migration required'):runtime_store_path(tmp_path,store,*parts)
    assert not (tmp_path/'new-state').exists()


def test_legacy_json_reader_uses_explicit_project_and_rejects_other_root(project,tmp_path_factory):
    from geoagent_harness.interface_api import conversation as c
    state=tmp_path_factory.mktemp('legacy-state');configure(project,state)
    identity='b'*32;path=c._path(project,identity)
    c._write(path,c.Conversation(conversation_id=identity,revision=1,messages=[c.Entry(role='user',content='Legacy saved chat')]))
    assert c.conversation_turn(c.TurnRequest(action='read',conversation_id=identity),project_root=project)['messages'][0]['content']=='Legacy saved chat'
    other=tmp_path_factory.mktemp('other-project')
    with pytest.raises(InterfaceApiError,match='does not belong'):
        c._read(path,identity,project_root=other)


def test_relocated_plan_still_requires_exact_write_authority(project,tmp_path_factory,monkeypatch):
    from geoagent_harness.planner.schemas import PlannerResult,WorkflowPlan,PlanStep
    from tests.test_reusable_recipes_and_runs import execution
    from geoagent_harness.interface_api.workflow_runs import run_action,RunRequest
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    configure(project,tmp_path_factory.mktemp('unapproved-write-state'))
    result=PlannerResult(model='fixture',original_request='Export a fresh CSV',context_references=[],plan=WorkflowPlan(summary='Fresh export',steps=[
        PlanStep(step_id='step_1',skill='export_csv',purpose='Export the selected source',arguments={'path':'data/input/sample_orders.csv','target_path':'data/output/unapproved.csv'},requires_approval=True,validation_required=True)]))
    workflow=execution(project,result,authorize=False)
    from geoagent_harness.interface_api.workflow import execute_workflow
    with pytest.raises(InterfaceApiError,match='approval|authoriz'):
        execute_workflow(workflow,project_root=project)
    denied=run_action(RunRequest(action='start',workflow=workflow),project_root=project,background=False)
    assert denied['status']=='failed' and not denied['execution_performed']
    assert not (project/'data/output/unapproved.csv').exists()
    assert not list((project/'approvals').glob('*.json'))
