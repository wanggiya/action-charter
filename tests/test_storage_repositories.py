"""P0-5 local adapter contracts; disposable projects, no model or live database."""
import ast
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from shutil import copyfile
import sqlite3
from threading import Barrier

import pytest

from geoagent_harness.platform.storage.contracts import RepositoryError
from geoagent_harness.platform.storage.provider import repositories, using_repository_provider
from geoagent_harness.platform.storage.provider import LocalRepositories
from geoagent_harness.task_actions import planning_tasks
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.task_actions.conversation import Conversation
from geoagent_harness.platform.workspace import WorkspaceLayout

SOURCE = Path(__file__).parents[1]
CHAT = 'c' * 32


@pytest.fixture(params=[False, True], ids=['legacy', 'relocated'])
def project(tmp_path, request):
    (tmp_path / 'context').mkdir()
    copyfile(SOURCE / 'context/SKILLS_INDEX.yaml', tmp_path / 'context/SKILLS_INDEX.yaml')
    if request.param:
        (tmp_path / 'actioncharter.workspace.json').write_text(json.dumps({
            'version': 1, 'state_root': str(tmp_path.parent / (tmp_path.name + '-state'))}))
    return tmp_path


def test_empty_read_does_not_create_storage(project):
    directory = WorkspaceLayout.load(project).planning_directory()
    with repositories(project).transaction() as unit:
        assert unit is None
    assert not directory.exists()


def test_all_metadata_records_and_settings_roll_back_together(project):
    repo = repositories(project)
    with pytest.raises(RuntimeError, match='fixture abort'):
        with repo.transaction(write=True) as unit:
            unit.records('conversations').put(CHAT, '{"conversation_id":"'+CHAT+'"}')
            unit.records('memories').put(CHAT, '{"task_id":"'+CHAT+'"}')
            unit.records('inspection_submissions_v1').put('s', '{"status":"processing"}')
            unit.records('chat_history_blobs_v1').put('sha', '{"plan":1}')
            unit.records('chat_history_v1').put('entry', '{"revision":1}', owner=CHAT)
            unit.records('dataset_views_v1').put(CHAT+':groups', '{"view":"groups"}')
            unit.save_setting('method_memory_settings', 1, 1)
            raise RuntimeError('fixture abort')
    with repo.transaction() as unit:
        for table in ['conversations','memories','inspection_submissions_v1',
                      'chat_history_blobs_v1','chat_history_v1','dataset_views_v1']:
            assert unit.records(table).entries() == []
        assert unit.setting('method_memory_settings') is None


def test_existing_schema_and_exact_encoded_json_survive_updates(project):
    with planning_tasks.database(project, write=True) as db:
        db.execute('INSERT INTO conversations VALUES (?,?)', (CHAT, '{"conversation_id":"'+CHAT+'","label":"old"}'))
        db.execute('INSERT INTO conversations VALUES (?,?)', ('d'*32, '{"conversation_id":"'+'d'*32+'"}'))
    encoded = '{"conversation_id":"'+CHAT+'","label":"北 / South","revision":2}'
    with repositories(project).transaction(write=True) as unit:
        unit.records('conversations').put(CHAT, encoded)
    with planning_tasks.database(project) as db:
        assert db.execute('SELECT value FROM conversations WHERE id=?',(CHAT,)).fetchone()[0] == encoded
        assert [row[0] for row in db.execute('SELECT id FROM conversations ORDER BY rowid DESC')] == ['d'*32,CHAT]
    with repositories(project).transaction() as unit:
        assert [row.key for row in unit.records('conversations').entries()] == ['d'*32, CHAT]
        assert unit.records('conversations').get(CHAT) == encoded


def test_read_only_and_closed_collection_names(project):
    with repositories(project).transaction(write=True) as unit:
        unit.records('conversations').put(CHAT, '{}')
    with repositories(project).transaction() as unit:
        for action in [lambda: unit.records('conversations').put(CHAT,'changed'),
                       lambda: unit.records('conversations').delete(CHAT),
                       lambda: unit.save_setting('model_selection','fixture',1),
                       lambda: unit.records('conversations; DROP TABLE tasks'),
                       lambda: unit.records('approvals'),
                       lambda: unit.setting('write_policy')]:
            with pytest.raises(RepositoryError): action()
        assert unit.records('conversations').get(CHAT) == '{}'


def test_owner_filter_cannot_retarget_an_existing_record(project):
    with repositories(project).transaction(write=True) as unit:
        unit.records('chat_history_v1').put('entry','{}',owner=CHAT)
    with pytest.raises(RepositoryError, match='provenance'):
        with repositories(project).transaction(write=True) as unit:
            unit.records('chat_history_v1').put('entry','different',owner='d'*32)
    with repositories(project).transaction() as unit:
        assert unit.records('chat_history_v1').count(owner=CHAT) == 1
        assert unit.records('chat_history_v1').entries(owner='d'*32) == []


def test_revision_check_serializes_competing_chat_writes(project):
    state = Conversation(conversation_id=CHAT,revision=1).model_dump(mode='json')
    planning_tasks.write_turn(project,state,expected_revision=0,expected_task_revision=0)
    barrier=Barrier(2)
    def change(label):
        updated={**state,'revision':2,'task_title':label}
        barrier.wait()
        try:
            planning_tasks.write_turn(project,updated,expected_revision=1,expected_task_revision=1)
            return 'saved'
        except InterfaceApiError as error:
            assert 'changed' in str(error)
            return 'stale'
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(change,['first','second'])) == ['saved','stale']
    assert planning_tasks.conversation_record(project, CHAT)['revision'] == 2
    assert planning_tasks.task_record(project, CHAT)['revision'] == 2


def test_same_submission_claim_has_one_winner(project):
    barrier=Barrier(2)
    def claim(_):
        barrier.wait()
        with repositories(project).transaction(write=True) as unit:
            store=unit.records('inspection_submissions_v1')
            if store.get('submission') is not None:
                return False
            store.put('submission','{"status":"processing"}')
            return True
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(claim,range(2))) == [False,True]


def test_read_transaction_is_a_coherent_snapshot(project):
    with repositories(project).transaction(write=True) as unit:
        unit.records('conversations').put(CHAT,'old')
    db_path=WorkspaceLayout.load(project).planning_directory()/'tasks.sqlite3'
    with sqlite3.connect(db_path) as db: db.execute('PRAGMA journal_mode=WAL')
    with repositories(project).transaction() as unit:
        assert unit.records('conversations').get(CHAT) == 'old'
        def update():
            with repositories(project).transaction(write=True) as writer:
                writer.records('conversations').put(CHAT,'new')
        with ThreadPoolExecutor(max_workers=1) as worker:
            worker.submit(update).result(timeout=10)
        assert unit.records('conversations').get(CHAT) == 'old'
    with repositories(project).transaction() as unit:
        assert unit.records('conversations').get(CHAT) == 'new'


def test_mutable_run_bytes_atomic_failure_and_immutable_plan_gate(project, monkeypatch):
    from geoagent_harness.platform.storage import files
    store=repositories(project).runs();store.ensure()
    name='a'*32+'.json'
    content='{"run_id": "'+'a'*32+'", "status": "completed", "label": "北"}'
    store.replace(name,content)
    assert (store.directory/name).read_text() == content
    assert store.read(name)['status'] == 'completed'
    def fail(*args):raise OSError('fixture interrupted before rename')
    with monkeypatch.context() as patch:
        patch.setattr(files.os,'replace',fail)
        with pytest.raises(OSError):store.replace(name,'{"status":"new"}')
    assert (store.directory/name).read_text() == content
    assert not list(store.directory.glob('*.tmp'))
    assert store.names(order='recent',limit=1) == [name]
    with pytest.raises(RepositoryError,match='Immutable'):
        repositories(project).documents('plans').replace('planner-plan.'+'a'*64+'.json','{}')


@pytest.mark.parametrize('kind',['traversal','symlink','hardlink','oversize','fifo'])
def test_unsafe_file_records_reject_without_overwriting(project, kind):
    store=repositories(project).runs();store.ensure();target=store.directory/('a'*32+'.json')
    outside=project/'outside.json';outside.write_text('{"untouched":true}')
    name=target.name
    if kind=='traversal':name='../outside.json'
    elif kind=='symlink':target.symlink_to(outside)
    elif kind=='hardlink':target.hardlink_to(outside)
    elif kind=='fifo':
        import os
        os.mkfifo(target)
    else:target.write_text('x'*512001)
    with pytest.raises(RepositoryError):store.read(name)
    assert outside.read_text() == '{"untouched":true}'


def test_provider_override_is_scoped_and_actions_use_only_interfaces(project):
    observed=[]
    class NoSqlTransaction:
        def __init__(self,unit):self.unit=unit
        def records(self,collection):observed.append(collection);return self.unit.records(collection)
        def setting(self,name):return self.unit.setting(name)
    class Alternate:
        def __init__(self,root):self.local=LocalRepositories(root);self.project_root=root
        def transaction(self,*,write=False):
            from contextlib import contextmanager
            @contextmanager
            def transaction():
                with self.local.transaction(write=write) as unit:
                    yield NoSqlTransaction(unit) if unit else None
            return transaction()
    with using_repository_provider(Alternate):
        state=Conversation(conversation_id=CHAT,revision=1).model_dump(mode='json')
        planning_tasks.write_turn(project,state,expected_revision=0,expected_task_revision=0)
        assert planning_tasks.conversation_record(project,CHAT)['revision']==1
    assert isinstance(repositories(project),LocalRepositories)
    assert {'conversations','memories'}.issubset(observed)


def test_repository_boundary_owns_sql_instead_of_shared_actions():
    files=list((SOURCE/'src/geoagent_harness/task_actions').glob('*.py'))
    files += [SOURCE/'src/geoagent_harness'/name for name in ['platform/model_gateway/catalog.py','platform/model_gateway/telemetry.py','data/tabular/dataset_views.py','agents/roles/planner/acquisition.py']]
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            assert not (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in {'execute','executemany'}), (path.name,node.lineno)
    for path in (SOURCE/'src/geoagent_harness/storage').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom):
                assert not (node.module or '').startswith(('geoagent_harness.task_actions','geoagent_harness.interface_api','geoagent_harness.cli'))


def test_provider_reaches_saved_plans_and_background_run_worker(project, monkeypatch):
    """Instrument the real local adapter, including copied background context."""
    import time
    from geoagent_harness.core.policy.approvals.service import plan_sha256
    from geoagent_harness.contracts.planning import PlannerResult
    from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan
    from geoagent_harness.contracts.actions import InterfaceReviewedPlanSaveRequest
    from geoagent_harness.task_actions.workflow import prepare_workflow, WorkflowRequest
    from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action
    monkeypatch.chdir(project)
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','false')
    (project/'data/input').mkdir(parents=True)
    (project/'data/output').mkdir()
    (project/'data/input/orders.csv').write_text('region,amount\nNorth,10\nSouth,20\n')
    observed=[]
    class Tap:
        def __init__(self,store,label):self.store,self.label=store,label
        def __getattr__(self,name):
            value=getattr(self.store,name)
            if not callable(value):return value
            def call(*args,**kwargs):
                observed.append(self.label+'.'+name)
                return value(*args,**kwargs)
            return call
    class Tracing(LocalRepositories):
        def runs(self,**kwargs):return Tap(super().runs(**kwargs),'runs')
        def documents(self,store,**kwargs):return Tap(super().documents(store,**kwargs),store)
    with using_repository_provider(Tracing):
        proposal=PlannerResult(agent_id='planner',model='fixture',original_request='Inspect orders.csv',
            context_references=[],warnings=[],plan={'summary':'Repository worker fixture','steps':[{
                'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect the temporary input',
                'arguments':{'path':'data/input/orders.csv'},'requires_approval':False,'validation_required':False}]})
        saved=save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',
            planner_result=proposal,confirmed_plan_sha256=plan_sha256(proposal.plan),allowed_skill_ids=['inspect_csv']),project_root=project)
        request=WorkflowRequest(action='prepare_workflow',plan_filename=saved['plan_filename'],confirmed_plan_sha256=saved['plan_sha256'])
        review=prepare_workflow(request,project_root=project)
        workflow=request.model_copy(update={'action':'execute_workflow','confirm_execution':True,
            'confirmed_review_sha256':review['review_sha256']})
        run=run_action(RunRequest(action='start',workflow=workflow),project_root=project,background=True)
        until=time.monotonic()+15
        while time.monotonic()<until:
            run=run_action(RunRequest(action='read',run_id=run['run_id']),project_root=project)
            if run['status'] in {'failed','cancelled','interrupted'}:pytest.fail(str(run.get('finding')))
            if run['status']=='completed' and run.get('successful_recipe',{}).get('status')!='pending':break
            time.sleep(.02)
        assert run['status']=='completed'
        assert run['steps'][0]['outcome']['row_count']==2
    assert {'plans.create','plans.load','runs.ensure','runs.replace','runs.read'}.issubset(observed)
