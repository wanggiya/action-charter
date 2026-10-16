"""Task boundaries, durable cross-chat continuation and transaction safety."""
import json
from pathlib import Path
from shutil import copytree, copyfile

import pytest
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.interface_api import planning_tasks as storage
from geoagent_harness.model.schemas import ModelResult

REPO = Path(__file__).parents[1]
CHAT = 'a' * 32
OTHER = 'b' * 32


@pytest.fixture
def project(tmp_path):
    for name in ('context', 'agents'):
        copytree(REPO / name, tmp_path / name)
    (tmp_path / 'data/input').mkdir(parents=True)
    for name in ('sample_points.geojson', 'sample_orders.csv'):
        copyfile(REPO / 'data/input' / name, tmp_path / 'data/input' / name)
    return tmp_path


class Client:
    def __init__(self, skill=None):
        self.skill = skill
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        plan = None if self.skill is None else {'summary': self.skill, 'steps': [
            {'step_id': 'step_1', 'skill': self.skill, 'purpose': 'Inspect temporary input',
             'arguments': {'path': 'sample_orders.csv' if self.skill == 'inspect_csv' else 'sample_points.geojson'},
             'requires_approval': False, 'validation_required': False}]}
        return ModelResult(model='fixture', content=json.dumps({'message': 'Planning only', 'plan': plan}))


def read(project, chat=CHAT):
    return conversation_turn(TurnRequest(action='read', conversation_id=chat), project_root=project)


def action(project, kind, chat=CHAT, **fields):
    state = read(project, chat)
    return conversation_turn(TurnRequest(action=kind, conversation_id=chat, expected_revision=state['revision'],
        expected_task_revision=state['task_revision'], **fields), project_root=project)


def turn(project, client, chat=CHAT, text='Inspect the selected input', **fields):
    state = read(project, chat)
    return conversation_turn(TurnRequest(action='turn', conversation_id=chat, expected_revision=state['revision'],
        task_id=state['active_task_id'], expected_task_revision=state['task_revision'], message=text, **fields),
        project_root=project, model_client=client)


def test_each_conversation_automatically_owns_one_task_and_memory(project):
    fresh = read(project)
    assert fresh['active_task_id'] == CHAT and fresh['linked_task_ids'] == [CHAT]
    assert fresh['task_message_count'] == 0
    assert storage.task_inventory(project)['tasks'] == []
    first = turn(project, Client('inspect_vector'), text='Inspect vector sample_points.geojson')
    assert first['active_task_id'] == CHAT
    assert not first['context_usage']['opening_message_included']
    assert not first['context_usage']['current_workflow_included']
    assert storage.task_record(project, CHAT)['conversation_ids'] == [CHAT]
    assert first['conversation_memory']['scope'] == 'conversation'
    assert not first['conversation_memory']['cross_conversation_memory']
    assert read(project)['planner_result']['plan_sha256'] == first['planner_result']['plan_sha256']


def test_domain_change_in_same_conversation_retains_memory_and_revises_workflow(project):
    vector = turn(project, Client('inspect_vector'), text='Inspect sample_points.geojson; prefer read-only operations.')
    client = Client('inspect_csv')
    csv = turn(project, client, text='Now replace the workflow with inspection of sample_orders.csv. No writes.')
    prompt = json.loads(client.requests[0].messages[1].content)
    assert prompt['current_plan'] == vector['planner_result']['plan']
    assert 'prefer read-only' in prompt['recent_conversation'][0]['content']
    assert csv['active_task_id'] == vector['active_task_id'] == CHAT
    assert csv['task_message_count'] == 4 and csv['proposal_changed']
    assert csv['context_usage']['opening_message_included']
    assert csv['context_usage']['current_workflow_included']
    assert read(project)['planner_result']['plan']['steps'][0]['skill'] == 'inspect_csv'
    assert len(storage.task_inventory(project)['tasks']) == 1
    assert not csv['approval_performed'] and not csv['execution_performed']


def test_new_conversation_starts_with_private_empty_memory(project):
    first = turn(project, Client('inspect_vector'), text='Inspect sample_points.geojson; vector-only sentinel.')
    assert read(project, OTHER)['planner_result'] is None
    client = Client('inspect_csv')
    second = turn(project, client, chat=OTHER, text='Inspect sample_orders.csv')
    prompt = json.loads(client.requests[0].messages[1].content)
    assert prompt['current_plan'] is None and prompt['recent_conversation'] == []
    assert 'sample_points.geojson' not in client.requests[0].messages[1].content
    assert 'vector-only sentinel' not in client.requests[0].messages[1].content
    assert second['active_task_id'] == OTHER and first['active_task_id'] == CHAT
    assert read(project)['planner_result']['plan']['steps'][0]['skill'] == 'inspect_vector'
    assert len(storage.task_inventory(project)['tasks']) == 2


def test_identical_generated_workflow_reuses_artifact_without_sharing_memory(project):
    from geoagent_harness.interface_api.server import (
        InterfaceGeneratedPlanSaveRequest, InterfaceReviewedPlanSaveRequest, save_interface_reviewed_plan,
    )
    from geoagent_harness.planner.schemas import PlannerResult
    first = turn(project, Client('inspect_vector'), text='Inspect sample_points.geojson, original private wording')
    second = turn(project, Client('inspect_vector'), chat=OTHER, text='Inspect sample_points.geojson, different private wording')
    def request(value, generated=True):
        result = PlannerResult.model_validate({key: value['planner_result'][key] for key in ('agent_id','model','original_request','context_references','plan','warnings')})
        cls = InterfaceGeneratedPlanSaveRequest if generated else InterfaceReviewedPlanSaveRequest
        return cls(action='save_generated_plan' if generated else 'save_reviewed_plan', planner_result=result,
            allowed_skill_ids=['inspect_vector'], confirmed_plan_sha256=value['planner_result']['plan_sha256'])
    saved = save_interface_reviewed_plan(request(first), project_root=project)
    path = project/'plans'/saved['plan_filename']; original_bytes = path.read_bytes()
    reused = save_interface_reviewed_plan(request(second), project_root=project)
    assert reused['status']=='already_stored' and path.read_bytes()==original_bytes
    assert reused['workflow_definition_reused'] and not reused['result_metadata_saved']
    assert not reused['approval_performed'] and not reused['execution_performed']
    assert storage.task_record(project,OTHER)['planner_result']['original_request'].endswith('different private wording')
    assert 'original private wording' not in json.dumps(storage.task_record(project,OTHER)['messages'])
    with pytest.raises(InterfaceApiError, match='exact result'):
        save_interface_reviewed_plan(request(second,False), project_root=project)


def test_cross_chat_task_linking_and_subtask_creation_are_disabled(project):
    turn(project, Client('inspect_vector'))
    before = storage.conversation_record(project, CHAT)
    for kind in ('create_task','select_task'):
        with pytest.raises(InterfaceApiError, match='Each conversation is one task'):
            action(project, kind, chat=OTHER, task_id=CHAT, task_title='Subtask')
    client = Client()
    with pytest.raises(InterfaceApiError, match='cross-chat'):
        conversation_turn(TurnRequest(action='turn',conversation_id=OTHER,task_id=CHAT,message='Use their memory'),project_root=project,model_client=client)
    assert client.requests == []
    assert storage.conversation_record(project, CHAT) == before
    assert storage.conversation_record(project, OTHER) is None


def test_history_off_preserves_private_plan_and_stored_transcript(project):
    first = turn(project, Client('inspect_vector'))
    client = Client()
    state = turn(project, client, use_history=False)
    prompt = json.loads(client.requests[0].messages[1].content)
    assert prompt['recent_conversation'] == [] and prompt['initial_request'] is None
    assert prompt['current_plan'] == first['planner_result']['plan']
    assert state['task_message_count'] == 4 and len(storage.task_record(project, CHAT)['messages']) == 4
    assert state['context_usage']['current_workflow_included']
    assert not state['context_usage']['opening_message_included']
    assert state['context_usage']['included_messages'] == 0


def test_stale_conversation_memory_revision_rejects_before_model_call(project):
    first = turn(project, Client('inspect_vector'))
    turn(project, Client())
    client = Client()
    with pytest.raises(InterfaceApiError, match='digest no longer matches'):
        conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,expected_revision=first['revision'],task_id=CHAT,
            expected_task_revision=first['task_revision'],message='Stale turn'),project_root=project,model_client=client)
    assert client.requests == []


def seed_legacy(project):
    directory = project/'planner-conversations';directory.mkdir(exist_ok=True)
    path=directory/(CHAT+'.json')
    path.write_text(json.dumps({'conversation_id':CHAT,'revision':1,'messages':[{'role':'user','content':'Legacy vector context'},
        {'role':'assistant','content':'Legacy reply'}],'planner_result':None}))
    return path


def test_legacy_adoption_keeps_original_file_bytes_and_all_own_messages(project):
    path=seed_legacy(project);before=path.read_bytes()
    result=turn(project,Client('inspect_csv'),text='Now inspect sample_orders.csv')
    assert path.read_bytes()==before
    assert result['task_message_count']==4 and result['messages'][0]['content']=='Legacy vector context'
    assert all(entry['conversation_id']==CHAT for entry in storage.task_record(project,CHAT)['messages'])


def test_old_shared_task_records_do_not_supply_live_foreign_memory(project):
    from geoagent_harness.interface_api.conversation import Conversation
    shared='f'*32
    own=Conversation(conversation_id=CHAT,revision=1,active_task_id=shared,linked_task_ids=[shared],task_revision=4,
        task_title='Old shared task',messages=[{'role':'user','content':'Own transcript'},{'role':'assistant','content':'Own answer'}])
    archived={'task_id':shared,'title':'Shared','revision':4,'conversation_ids':[CHAT,OTHER],
        'messages':[{'role':'user','content':'Foreign secret context','task_id':shared,'conversation_id':OTHER}],
        'planner_result':None,'selected_skill_ids':[],'allowed_skill_ids':[],'context_usage':None}
    with storage.database(project,write=True) as connection:
        storage._put(connection,'tasks',shared,archived)
        storage._put(connection,'conversations',CHAT,own.model_dump(mode='json'))
    client=Client()
    result=turn(project,client,text='Explain my own work')
    assert result['active_task_id']==CHAT and result['task_message_count']==4
    assert 'Foreign secret context' not in client.requests[0].messages[1].content
    with storage.database(project) as connection:
        assert storage._get(connection,'tasks',shared)==archived | {'messages':[dict(archived['messages'][0],selected_skill_ids=None,plan_skill_ids=None)]}


def test_explicit_workflow_binding_is_validated_and_private(project):
    from geoagent_harness.planner.schemas import PlannerResult
    plan={'summary':'CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False}]}
    base=PlannerResult(model='fixture',original_request='CSV',context_references=[],plan=plan)
    first = turn(project, Client('inspect_vector'))
    client=Client()
    with pytest.raises(InterfaceApiError,match='explicitly bind'):
        turn(project,client,current_plan=base)
    assert client.requests==[]
    bound=action(project,'bind_task_plan',task_id=CHAT,current_plan=base)
    assert bound['planner_result']['plan']['steps'][0]['skill']=='inspect_csv'
    assert bound['context_usage'] == first['context_usage']
    bad=base.model_copy(deep=True);bad.plan.steps[0].arguments['path']='../outside.csv'
    with pytest.raises((InterfaceApiError,ValueError)):
        action(project,'bind_task_plan',task_id=CHAT,current_plan=bad)
    assert read(project)['revision']==bound['revision']
    assert not bound['approval_performed'] and not bound['execution_performed']


def test_failed_atomic_commit_changes_neither_transcript_nor_memory(project,monkeypatch):
    initial=turn(project,Client('inspect_vector'));memory=storage.task_record(project,CHAT)
    original_put=storage._put
    def fail(connection,table,identity,value):
        if table=='conversations':raise InterfaceApiError('Injected storage failure')
        original_put(connection,table,identity,value)
    monkeypatch.setattr(storage,'_put',fail)
    with pytest.raises(InterfaceApiError,match='Injected'):
        turn(project,Client())
    assert read(project)['revision']==initial['revision']
    assert storage.task_record(project,CHAT)==memory


def test_failed_first_adoption_can_retry_without_losing_legacy(project,monkeypatch):
    path=seed_legacy(project);before=path.read_bytes();original_put=storage._put
    def fail(connection,table,identity,value):
        if table=='conversations':raise InterfaceApiError('Injected adoption failure')
        original_put(connection,table,identity,value)
    monkeypatch.setattr(storage,'_put',fail)
    with pytest.raises(InterfaceApiError,match='Injected'):
        turn(project,Client())
    assert read(project)['revision']==1 and storage.task_inventory(project)['tasks']==[]
    assert path.read_bytes()==before
    monkeypatch.setattr(storage,'_put',original_put)
    assert turn(project,Client())['revision']==2


def test_same_chat_concurrent_turn_blocks_but_other_chat_is_independent(project):
    class Interrupted:
        def complete(self,request):
            with pytest.raises(InterfaceApiError,match='digest no longer matches'):
                turn(project,Client())
            assert turn(project,Client(),chat=OTHER)['revision']==1
            raise RuntimeError('fixture interruption')
    with pytest.raises(RuntimeError,match='interruption'):
        turn(project,Interrupted())
    assert read(project)['revision']==0 and read(project,OTHER)['revision']==1
    assert turn(project,Client())['revision']==1


def test_storage_symlinks_reject(project):
    turn(project,Client())
    database=project/'planner-workspace/tasks.sqlite3'
    database.rename(database.with_suffix('.backup'));database.symlink_to(database.with_suffix('.backup'))
    with pytest.raises(InterfaceApiError,match='unsafe'):
        read(project)


def test_cli_reads_same_private_conversation_and_memory(project):
    turn(project,Client('inspect_vector'));runner=CliRunner()
    inventory=runner.invoke(app,['planning-tasks','--project-root',str(project)])
    assert inventory.exit_code==0,inventory.output
    assert json.loads(inventory.output)['tasks'][0]['conversation_ids']==[CHAT]
    response=runner.invoke(app,['planning-conversation-read',CHAT,'--project-root',str(project)])
    assert json.loads(response.output)['active_task_id']==CHAT
    assert json.loads(response.output)['conversation_memory']['cross_conversation_memory'] is False


def test_http_chat_memory_uses_origin_guard_and_disables_shared_link(project):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(project));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        connection=HTTPConnection(*server.server_address)
        payload=json.dumps({'action':'read','conversation_id':CHAT})
        connection.request('POST','/api/v1/planner/conversation',payload,{'Content-Type':'application/json','Origin':'https://foreign.example'})
        response=connection.getresponse();assert response.status==403;response.read()
        connection.request('POST','/api/v1/planner/conversation',payload,{'Content-Type':'application/json'})
        response=connection.getresponse();assert response.status==200
        assert json.loads(response.read())['active_task_id']==CHAT
        connection.request('POST','/api/v1/planner/conversation',json.dumps({'action':'select_task','conversation_id':OTHER,'task_id':CHAT}),{'Content-Type':'application/json'})
        response=connection.getresponse();assert response.status in (400,409,422);response.read()
        from geoagent_harness.planner.schemas import PlannerResult
        from geoagent_harness.approvals import plan_sha256
        plan={'summary':'CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/sample_orders.csv'},'requires_approval':False,'validation_required':False}]}
        result=PlannerResult(model='fixture',original_request='First wording',context_references=[],plan=plan)
        saved_bytes=None
        for wording in ('First wording','Second wording'):
            result.original_request=wording
            payload={'action':'save_generated_plan','planner_result':result.model_dump(mode='json'),
                'confirmed_plan_sha256':plan_sha256(result.plan),'allowed_skill_ids':['inspect_csv']}
            connection.request('POST','/api/v1/plans/save-generated',json.dumps(payload),{'Content-Type':'application/json'})
            response=connection.getresponse();body=json.loads(response.read());assert response.status==200,body
            path=project/'plans'/body['plan_filename']
            if saved_bytes is None:saved_bytes=path.read_bytes()
            else:
                assert body['workflow_definition_reused'] and not body['result_metadata_saved']
                assert path.read_bytes()==saved_bytes
            assert not body['human_review_performed'] and not body['execution_performed']
        connection.close()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
