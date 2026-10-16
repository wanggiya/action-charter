"""Optional method agent: explicit sources, private versions and no authority."""
import json
from pathlib import Path
from shutil import copytree
from threading import Event, Thread

import pytest
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.agent_manifest import load_agent_manifest
from geoagent_harness.interface_api import method_memory as service
from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.model.schemas import ModelResult

CHAT = 'a' * 32
OTHER = 'b' * 32
REPO = Path(__file__).parents[1]
DOC = {'title':'Inspect a CSV table','purpose':'Inspect structure before transforming a table.',
       'inputs':['An operator-selected CSV table'], 'prerequisites':['A supported encoding'],
       'operations':[{'skill':'inspect_csv','guidance':'Inspect row count and column names.'}],
       'checks':['Confirm expected columns are present.'], 'limitations':['No data validity guarantee.']}


class Model:
    def __init__(self, document=None):
        self.document = DOC if document is None else document
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return ModelResult(model='fixture', content=json.dumps(self.document))


@pytest.fixture
def project(tmp_path):
    for name in ('agents','context'):
        copytree(REPO/name, tmp_path/name)
    # A saved private chat, without model calls or execution.
    from geoagent_harness.interface_api.conversation import Conversation, Entry, _path, _write
    _write(_path(tmp_path, CHAT), Conversation(conversation_id=CHAT, revision=1,
        messages=[Entry(role='user',content='Inspect structure. password=do-not-send'), Entry(role='assistant',content='Return row count and column names.')]))
    _write(_path(tmp_path, OTHER), Conversation(conversation_id=OTHER, revision=1,
        messages=[Entry(role='user',content='OTHER CHAT PRIVATE SENTINEL')]))
    return tmp_path


def act(root, action, client=None, **fields):
    return service.method_action(service.MethodRequest(action=action, **fields), project_root=root, model_client=client)


def enable(root):
    current = act(root,'state')
    return act(root,'enable',enabled=True,expected_setting_revision=current['revision'])


def sources():
    return {'conversation_id':CHAT,'expected_revision':1,'message_indices':[0]}


def save(root, **fields):
    return act(root,'save',**{**sources(),'document':DOC,'reviewed':True,**fields})['method']


def test_default_off_no_model_and_enable_does_not_generate(project):
    model = Model()
    assert act(project,'state')['enabled'] is False
    assert not (project/'planner-workspace').exists()
    with pytest.raises(InterfaceApiError, match='OFF'):
        act(project,'generate',model,**sources())
    assert model.requests == []
    assert enable(project)['enabled']
    assert model.requests == []
    assert act(project,'list',conversation_id=CHAT)['methods'] == []


def test_manifest_has_no_tools_or_permissions(project):
    manifest=load_agent_manifest('method_memory', project/'agents')
    assert not any(manifest.permissions.model_dump().values())
    path=project/'agents/method_memory/manifest.yaml'
    path.write_text(path.read_text().replace('tools: []','tools: [execute]'))
    with pytest.raises(ValueError,match='cannot grant'):
        load_agent_manifest('method_memory', project/'agents')


def test_one_generation_selected_sources_redacted_no_auto_save(project):
    enable(project)
    model=Model()
    proposal=act(project,'generate',model,**sources())
    assert len(model.requests)==proposal['model_calls']==1
    prompt='\n'.join(message.content for message in model.requests[0].messages)
    assert 'do-not-send' not in prompt and 'OTHER CHAT' not in prompt
    payload=json.loads(model.requests[0].messages[1].content)
    assert [item['index'] for item in payload['messages']]==[0]
    assert payload['workflow_structure'] is None
    assert proposal['status']=='unvalidated_proposal'
    assert proposal['source']['conversation_revision']==1
    assert not proposal['approval_performed'] and not proposal['execution_performed']
    assert act(project,'list',conversation_id=CHAT)['methods']==[]
    assert not (project/'data/output').exists()


@pytest.mark.parametrize('fields,match',[
    ({'message_indices':[]},'Select at least'),
    ({'message_indices':[-1]},'valid, distinct'),
    ({'message_indices':[2]},'valid, distinct'),
    ({'message_indices':[0,0]},'valid, distinct'),
    ({'expected_revision':0},'Conversation changed'),
    ({'include_workflow':True},'no validated workflow'),
])
def test_source_guards_fail_before_model(project,fields,match):
    enable(project);model=Model()
    with pytest.raises(InterfaceApiError,match=match):
        act(project,'generate',model,**{**sources(),**fields})
    assert model.requests==[]


def test_rejects_invalid_or_unregistered_model_output_without_retry(project):
    enable(project)
    for value in ({'title':'bad'}, {**DOC,'operations':[{'skill':'eval','guidance':'Run anything'}]}):
        model=Model(value)
        with pytest.raises(InterfaceApiError):
            act(project,'generate',model,**sources())
        assert len(model.requests)==1
    assert act(project,'list',conversation_id=CHAT)['methods']==[]


def test_save_versions_isolated_delete_and_off_gate(project):
    enable(project)
    with pytest.raises(InterfaceApiError,match='Review'):
        save(project,reviewed=False)
    record=save(project)
    assert record['revision']==1 and record['status']=='operator_reviewed_unvalidated'
    assert act(project,'list',conversation_id=OTHER)['methods']==[]
    with pytest.raises(InterfaceApiError,match='does not belong'):
        service.method_for_planner(project,OTHER,record['method_id'])
    updated=save(project,method_id=record['method_id'],expected_method_revision=1,document={**DOC,'title':'Updated CSV inspection'})
    assert updated['revision']==2 and updated['versions'][0]['document']['title']==DOC['title']
    with pytest.raises(InterfaceApiError,match='changed'):
        save(project,method_id=record['method_id'],expected_method_revision=1)
    current=act(project,'state')
    act(project,'enable',enabled=False,expected_setting_revision=current['revision'])
    assert len(act(project,'list',conversation_id=CHAT)['methods'])==1
    with pytest.raises(InterfaceApiError,match='OFF'):
        service.method_for_planner(project,CHAT,record['method_id'])
    with pytest.raises(InterfaceApiError,match='OFF'):
        save(project)
    with pytest.raises(InterfaceApiError,match='unavailable'):
        act(project,'delete',conversation_id=OTHER,method_id=record['method_id'],expected_method_revision=2)
    act(project,'delete',conversation_id=CHAT,method_id=record['method_id'],expected_method_revision=2)
    assert act(project,'list',conversation_id=CHAT)['methods']==[]


def test_off_on_during_generation_discards_result_and_duplicate_is_blocked(project):
    enable(project);started=Event();finish=Event();errors=[]
    class Slow(Model):
        def complete(self,request):
            started.set();assert finish.wait(5);return super().complete(request)
    def run():
        try:act(project,'generate',Slow(),**sources())
        except Exception as error:errors.append(error)
    worker=Thread(target=run);worker.start();assert started.wait(5)
    try:
        with pytest.raises(InterfaceApiError,match='already running'):
            act(project,'generate',Model(),**sources())
        current=act(project,'state')
        act(project,'enable',enabled=False,expected_setting_revision=current['revision'])
        enable(project)
    finally:
        finish.set();worker.join(5)
    assert len(errors)==1 and 'discarded' in str(errors[0])
    assert not service.ACTIVE


def test_cli_uses_same_setting_and_storage(project,tmp_path):
    runner=CliRunner()
    state=runner.invoke(app,['method-memory','--project-root',str(project)])
    assert state.exit_code==0 and json.loads(state.stdout)['enabled'] is False
    request=tmp_path/'request.json';request.write_text(json.dumps({'action':'enable','enabled':True,'expected_setting_revision':0}))
    result=runner.invoke(app,['method-memory','--project-root',str(project),'--request-file',str(request)])
    assert result.exit_code==0 and act(project,'state')['enabled']
    request.write_text(json.dumps({'action':'save',**sources(),'document':DOC,'reviewed':True}))
    result=runner.invoke(app,['method-memory','--project-root',str(project),'--request-file',str(request)])
    assert result.exit_code==0 and len(act(project,'list',conversation_id=CHAT)['methods'])==1


def test_planner_only_includes_explicit_current_chat_method_and_off_blocks(project):
    enable(project);record=save(project)
    class Planner(Model):
        def complete(self,request):
            self.requests.append(request)
            return ModelResult(model='fixture',content=json.dumps({'message':'Which CSV table should I inspect?','plan':None}))
    client=Planner()
    result=conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,expected_revision=1,
        message='Help choose an inspection method',method_id=record['method_id'],use_history=False),project_root=project,model_client=client)
    payload=json.loads(client.requests[0].messages[1].content)
    assert payload['selected_method_suggestion']['document']['title']==DOC['title']
    assert result['context_usage']['selected_method_id']==record['method_id']
    assert not result['approval_performed'] and not result['execution_performed']
    client=Planner()
    conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,expected_revision=2,message='No method requested',use_history=False),project_root=project,model_client=client)
    assert json.loads(client.requests[0].messages[1].content)['selected_method_suggestion'] is None
    current=act(project,'state');act(project,'enable',enabled=False,expected_setting_revision=current['revision'])
    with pytest.raises(InterfaceApiError,match='OFF'):
        conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,expected_revision=3,message='Use it',method_id=record['method_id']),project_root=project,model_client=Planner())


def test_workflow_sources_omit_arguments_and_concrete_bindings(project):
    from geoagent_harness.interface_api.conversation import Conversation, _path, _write
    from geoagent_harness.planner.schemas import PlannerResult
    state=Conversation.model_validate_json(_path(project,CHAT).read_text())
    state.planner_result=PlannerResult.model_validate({'model':'fixture','original_request':'Inspect confidential source',
        'context_references':[], 'plan':{'summary':'Inspect','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect the selected table',
        'arguments':{'path':'data/input/confidential.csv'},'requires_approval':False,'validation_required':False}]}})
    _write(_path(project,CHAT),state)
    enable(project);model=Model()
    act(project,'generate',model,**{**sources(),'message_indices':[],'include_workflow':True})
    prompt=json.loads(model.requests[0].messages[1].content)
    assert prompt['messages']==[] and prompt['workflow_structure'][0]['skill']=='inspect_csv'
    assert 'confidential' not in json.dumps(prompt) and 'arguments' not in json.dumps(prompt)


def test_method_rejects_concrete_paths_and_source_budget_without_model(project):
    enable(project)
    with pytest.raises(InterfaceApiError,match='abstract input'):
        save(project,document={**DOC,'inputs':['data/input/private.csv']})
    from geoagent_harness.interface_api.conversation import Conversation, Entry, _path, _write
    _write(_path(project,CHAT),Conversation(conversation_id=CHAT,revision=1,messages=[Entry(role='user',content='x'*8000),Entry(role='assistant',content='y'*8000)]))
    model=Model()
    with pytest.raises(InterfaceApiError,match='12 KB'):
        act(project,'generate',model,**{**sources(),'message_indices':[0,1]})
    assert not model.requests


def test_setting_cas_and_symlink_guard(project,tmp_path):
    enable(project)
    with pytest.raises(InterfaceApiError,match='setting changed'):
        act(project,'enable',enabled=False,expected_setting_revision=0)
    target=tmp_path/'elsewhere';target.mkdir()
    unsafe=tmp_path/'unsafe';unsafe.mkdir();(unsafe/'planner-workspace').symlink_to(target,target_is_directory=True)
    with pytest.raises(InterfaceApiError,match='unsafe'):
        act(unsafe,'state')


def test_method_http_uses_origin_guard_and_returns_safe_model_failure(project,monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from geoagent_harness.interface_api.server import _handler
    from geoagent_harness.model import ModelClientError
    class Unavailable:
        def complete(self,request):raise ModelClientError.timeout()
    monkeypatch.setattr(service,'SharedModelClient',lambda settings:Unavailable())
    monkeypatch.setattr(service,'load_model_settings',lambda:None)
    http=ThreadingHTTPServer(('127.0.0.1',0),_handler(project));thread=Thread(target=http.serve_forever,daemon=True);thread.start()
    def post(payload,origin=None):
        client=HTTPConnection('127.0.0.1',http.server_port)
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        client.request('POST','/api/v1/method-memory',json.dumps(payload),headers)
        response=client.getresponse();result=response.status,json.loads(response.read());client.close();return result
    try:
        assert post({'action':'enable','enabled':True},'https://untrusted.invalid')[0]==403
        assert not act(project,'state')['enabled']
        assert post({'action':'enable','enabled':True})[0]==200
        status,body=post({'action':'generate',**sources()})
        assert status==503 and body['code']=='model_timeout'
        assert not body['approval_performed'] and not body['execution_performed']
        status,body=post({'action':'generate',**sources(),'foreign_chat_ids':[OTHER]})
        assert status==400 and not body['execution_performed']
    finally:http.shutdown();http.server_close();thread.join(5)


def test_cli_method_inclusion_uses_shared_planner(project,tmp_path,monkeypatch):
    enable(project);record=save(project)
    import geoagent_harness.interface_api.conversation as conversation
    class Planner(Model):
        def complete(self,request):
            self.requests.append(request)
            return ModelResult(model='fixture',content=json.dumps({'message':'Please select the input table.','plan':None}))
    client=Planner();monkeypatch.setattr(conversation,'SharedModelClient',lambda settings:client)
    monkeypatch.setattr(conversation,'load_model_settings',lambda:None)
    request=tmp_path/'turn.json';request.write_text(json.dumps({'action':'turn','conversation_id':CHAT,'expected_revision':1,
        'message':'Use my selected method as advice only','method_id':record['method_id']}))
    result=CliRunner().invoke(app,['planning-conversation-turn','--project-root',str(project),'--request-file',str(request)])
    assert result.exit_code==0,result.output
    assert json.loads(result.stdout)['context_usage']['selected_method_id']==record['method_id']
    assert json.loads(client.requests[0].messages[1].content)['selected_method_suggestion']['method_id']==record['method_id']


def test_changed_sources_during_generation_discard_result(project):
    enable(project)
    class Changing(Model):
        def complete(self,request):
            from geoagent_harness.interface_api.conversation import Conversation, _path, _write
            path=_path(project,CHAT);state=Conversation.model_validate_json(path.read_text());state.revision+=1
            _write(path,state)
            return super().complete(request)
    model=Changing()
    with pytest.raises(InterfaceApiError,match='Conversation changed'):
        act(project,'generate',model,**sources())
    assert len(model.requests)==1 and act(project,'list',conversation_id=CHAT)['methods']==[]


def test_off_on_cycle_during_method_assisted_planning_discards_reply(project):
    enable(project);record=save(project)
    class Changing(Model):
        def complete(self,request):
            current=act(project,'state');act(project,'enable',enabled=False,expected_setting_revision=current['revision']);enable(project)
            return ModelResult(model='fixture',content=json.dumps({'message':'Do not accept this stale reply.','plan':None}))
    with pytest.raises(InterfaceApiError,match='setting changed'):
        conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,expected_revision=1,message='Use the selected method',method_id=record['method_id']),project_root=project,model_client=Changing())
    state=conversation_turn(TurnRequest(action='read',conversation_id=CHAT),project_root=project)
    assert state['revision']==1 and all(entry['content']!='Do not accept this stale reply.' for entry in state['messages'])


def test_per_chat_record_bound_keeps_list_responses_bounded(project,monkeypatch):
    enable(project);monkeypatch.setattr(service,'MAX_METHODS_PER_CHAT',1)
    record=save(project)
    with pytest.raises(InterfaceApiError,match='eight records'):
        save(project)
    updated=save(project,method_id=record['method_id'],expected_method_revision=1)
    assert updated['revision']==2
    assert len(json.dumps(act(project,'list',conversation_id=CHAT)).encode())<2_000_000
