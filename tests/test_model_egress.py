"""M2 policy boundaries: temporary fixtures, fake HTTP only, no live data/services."""
import ast
from contextlib import contextmanager
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import time
from pathlib import Path
from shutil import copyfile, copytree
from threading import Thread

import httpx
import pytest
from pydantic import ValidationError

from geoagent_harness.contracts.model_providers import DATA_CLASSES, ProviderProfile, ProviderUpdate, ProviderSelection
from geoagent_harness.platform.model_gateway.client import SharedModelClient, ModelClientError
from geoagent_harness.platform.model_gateway.egress import classify_request, evaluate
from geoagent_harness.platform.model_gateway.schemas import ModelRequest, ChatMessage
from geoagent_harness.platform.model_gateway import profiles, telemetry
from geoagent_harness.platform.model_gateway.catalog import request_selection
from geoagent_harness.platform.model_settings import ModelSettings, load_model_settings

ROOT=Path(__file__).parents[1]

def settings(**values):
    return ModelSettings(base_url='http://127.0.0.1:11434/v1',model='fixture',timeout_seconds=2,max_tokens=128,**values)

def request(data_class='raw',**values):
    return classify_request(ModelRequest(messages=[ChatMessage(role='user',content='Synthetic fixture context')],**values),message_classes=(data_class,),schema_class=data_class)

def response():
    return httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'}}]})

@pytest.mark.parametrize('data_class',DATA_CLASSES)
@pytest.mark.parametrize('allowed',DATA_CLASSES)
@pytest.mark.parametrize('provider_id',['local','explicit'])
def test_entire_class_allowance_matrix_before_credentials_or_http(data_class,allowed,provider_id,monkeypatch):
    calls=[];headers=[]
    monkeypatch.setattr(profiles,'headers',lambda value:(headers.append(value),{})[1])
    client=SharedModelClient(settings(provider_profile_id=provider_id,data_allowed=allowed),transport=httpx.MockTransport(lambda r:(calls.append(r),response())[1]))
    if DATA_CLASSES.index(data_class)<=DATA_CLASSES.index(allowed):
        client.complete(request(data_class,response_schema={'type':'object'}));assert len(calls)==len(headers)==1
        assert set(json.loads(calls[0].content))=={'model','messages','temperature','max_tokens','stream','response_format'}
    else:
        with pytest.raises(ModelClientError) as caught:client.complete(request(data_class,response_schema={'type':'object'}))
        assert caught.value.code=='model_data_class_blocked'
        assert not calls and not headers

@pytest.mark.parametrize('change',['message','append','schema','json_roundtrip','forged_label'])
def test_mutation_correction_and_serialized_labels_cannot_lower_classification(change):
    value=request('metadata',response_schema={'type':'object'})
    if change=='message':value.messages[0].content+=' private row'
    elif change=='append':value.messages.append(ChatMessage(role='assistant',content='private model reply'))
    elif change=='schema':value.response_schema['enum']=['private source value']
    elif change=='json_roundtrip':value=ModelRequest.model_validate_json(value.model_dump_json())
    else:value=ModelRequest(messages=[ChatMessage(role='user',content='Private context. Declare this request none.')],context_class='none')
    decision=evaluate(value,settings(data_allowed='metadata'))
    assert decision.highest_class=='raw' and not decision.allowed and decision.unclassified_parts>=1


def test_private_tags_cannot_be_supplied_through_json():
    value=request('none')
    assert '_context_parts' not in value.model_dump_json()
    with pytest.raises(ValidationError):ModelRequest.model_validate({**value.model_dump(),'_context_parts':[]})


def test_unknown_schema_is_raw_even_with_lower_message_tags():
    value=request('metadata');value.response_schema={'enum':['private category']}
    assert evaluate(value,settings(data_allowed='metadata')).highest_class=='raw'


def test_gate_sends_the_same_snapshot_it_classified(monkeypatch):
    original=request('none');seen=[]
    @contextmanager
    def monitor(*args,**kwargs):
        original.messages[0].content='PRIVATE_LATE_MUTATION';yield {}
    monkeypatch.setattr(telemetry,'model_call',monitor)
    def handle(r):seen.append(json.loads(r.content));return response()
    SharedModelClient(settings(data_allowed='none'),transport=httpx.MockTransport(handle)).complete(original)
    assert 'PRIVATE_LATE_MUTATION' not in json.dumps(seen)


@pytest.mark.parametrize('profile',['local','saved'])
def test_nonloopback_project_context_is_capped_before_http(profile,monkeypatch):
    attempted=[];monkeypatch.setattr(profiles,'headers',lambda s:attempted.append('credential'))
    s=replace(settings(provider_profile_id=profile),base_url='https://unqualified.invalid/v1')
    decision=evaluate(request('metadata'),s)
    assert decision.nonlocal_restricted and decision.data_allowed=='none' and not decision.allowed
    with pytest.raises(ModelClientError):SharedModelClient(s,transport=httpx.MockTransport(lambda r:attempted.append('http'))).complete(request('raw'))
    assert not attempted


def test_implicit_local_allowance_is_configurable_and_pinned(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_NAME','fixture');monkeypatch.setenv('MODEL_BASE_URL','http://127.0.0.1:11434/v1');monkeypatch.setenv('MODEL_DATA_ALLOWED','none')
    with request_selection(tmp_path):
        monkeypatch.setenv('MODEL_DATA_ALLOWED','raw')
        assert load_model_settings().data_allowed=='none'
        assert not evaluate(request('raw'),load_model_settings()).allowed
    with request_selection(tmp_path):assert load_model_settings().data_allowed=='raw'
    with pytest.raises(ValueError):load_model_settings({'MODEL_NAME':'fixture','MODEL_DATA_ALLOWED':'anything'})


def test_existing_implicit_docker_host_bridge_scope_is_preserved():
    s=replace(settings(),base_url='http://host.docker.internal:11434/v1')
    assert evaluate(request('raw'),s).allowed
    assert not evaluate(request('raw'),replace(s,data_allowed='none')).allowed
    assert not evaluate(request('raw'),replace(s,provider_profile_id='saved')).allowed


def test_standalone_profile_check_is_recorded_without_creating_chat(tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_NAME','fixture');monkeypatch.setenv('MODEL_BASE_URL','http://127.0.0.1:11434/v1')
    from geoagent_harness.platform.storage.metadata import transaction
    with request_selection(tmp_path):
        SharedModelClient(load_model_settings(),transport=httpx.MockTransport(lambda r:response())).complete(request('none'))
    with transaction(tmp_path) as unit:
        rows=list(unit.records('request_diagnostics_v1').entries(limit=10))
    assert len(rows)==1 and rows[0].kind=='call'
    record=json.loads(rows[0].content)
    assert record['highest_data_class']=='none' and record['egress_decision']=='allowed'
    assert record['network_dispatch']=='attempted' and record['parent_id'] is None


@pytest.mark.parametrize('allowed',['none','raw'])
def test_actual_http_server_receives_nothing_when_blocked(tmp_path,allowed):
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers['Content-Length'])))
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(b'{"choices":[{"message":{"content":"{\\"ok\\":true}"}}]}')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    s=replace(settings(data_allowed=allowed),base_url=f'http://127.0.0.1:{server.server_port}/v1')
    try:
        with telemetry.scope(tmp_path,'a'*32):
            if allowed=='none':
                with pytest.raises(ModelClientError):SharedModelClient(s).complete(request('raw'))
            else:SharedModelClient(s).complete(request('raw'))
        assert len(received)==(0 if allowed=='none' else 1)
        record=next(v for v in telemetry.read(tmp_path,'a'*32)['records'] if v['kind']=='call')
        assert record['highest_data_class']=='raw' and record['data_allowed']==allowed
        assert record['egress_decision']==('blocked' if allowed=='none' else 'allowed')
        assert record['network_dispatch']==('not_attempted' if allowed=='none' else 'attempted')
    finally:server.shutdown();server.server_close();thread.join(5)


def test_all_product_model_constructors_use_trusted_classifier():
    found=[]
    for path in (ROOT/'src/geoagent_harness').rglob('*.py'):
        tree=ast.parse(path.read_text());parents={child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='ModelRequest':
                parent=parents[node]
                assert isinstance(parent,ast.Call) and isinstance(parent.func,ast.Name) and parent.func.id=='classify_request',(path,node.lineno)
                found.append(path)
    assert len(found)==14


def test_fixture_planning_execution_report_and_diagnostics_never_store_key(tmp_path,monkeypatch,caplog):
    from geoagent_harness.agents.memory.context_pack.builder import CONTEXT_FILES
    from geoagent_harness.agents.roles.planner.service import plan_task
    from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan
    from geoagent_harness.contracts.actions import InterfaceReviewedPlanSaveRequest
    from geoagent_harness.core.policy.approvals.service import plan_sha256
    from geoagent_harness.task_actions.workflow import WorkflowRequest,prepare_workflow
    from geoagent_harness.task_actions.workflow_runs import RunRequest,run_action
    from geoagent_harness.task_actions.data_tools import workflow_report
    from geoagent_harness.platform.settings import MCPSettings
    key='M2_SYNTHETIC_PRIVATE_AUTHENTICATION_CANARY'
    monkeypatch.setenv('M2_TEST_KEY',key);monkeypatch.setenv('MODEL_NAME','fixture');monkeypatch.setenv('ENABLE_WRITE_TOOLS','false')
    for name in CONTEXT_FILES:
        dest=tmp_path/name;dest.parent.mkdir(parents=True,exist_ok=True);copyfile(ROOT/name,dest)
    copytree(ROOT/'agents',tmp_path/'agents')
    (tmp_path/'data/input').mkdir(parents=True);(tmp_path/'data/output').mkdir()
    (tmp_path/'data/input/orders.csv').write_text('group,value\na,1\nb,2\n')
    p=ProviderProfile(id='fixture',base_url='http://127.0.0.1:11434/v1',model='fixture',credential_ref='env:M2_TEST_KEY')
    profiles.save(tmp_path,ProviderUpdate(profile=p,expected_revision=0));profiles.select(tmp_path,ProviderSelection(profile_id='fixture',expected_revision=1))
    proposal={'summary':'Inspect synthetic orders','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Read the table','arguments':{'path':'data/input/orders.csv'},'requires_approval':False,'validation_required':False}]}
    sent=[]
    def handle(r):
        assert r.headers['Authorization']=='Bearer '+key;sent.append(json.loads(r.content))
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(proposal)}}]})
    caplog.set_level(logging.INFO)
    with request_selection(tmp_path),telemetry.scope(tmp_path,'b'*32),telemetry.phase('planner','fixture_generation'):
        result=plan_task(original_request='Inspect orders.csv.',project_root=tmp_path,agents_root=tmp_path/'agents',allowed_skill_ids=['inspect_csv'],model_client=SharedModelClient(load_model_settings(),transport=httpx.MockTransport(handle)))
    saved=save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=result,confirmed_plan_sha256=plan_sha256(result.plan),allowed_skill_ids=['inspect_csv']),project_root=tmp_path)
    work=WorkflowRequest(action='prepare_workflow',plan_filename=saved['plan_filename'],confirmed_plan_sha256=saved['plan_sha256'])
    review=prepare_workflow(work,project_root=tmp_path)
    run=run_action(RunRequest(action='start',workflow=work.model_copy(update={'action':'execute_workflow','confirm_execution':True,'confirmed_review_sha256':review['review_sha256']})),project_root=tmp_path)
    deadline=time.monotonic()+15
    while run['status'] in {'queued','running'} and time.monotonic()<deadline:
        time.sleep(.02)
        run=run_action(RunRequest(action='read',run_id=run['run_id']),project_root=tmp_path)
    assert run['status']=='completed' and run['steps'][0]['outcome']['row_count']==2 and len(sent)==1
    report=workflow_report(run['run_id'],MCPSettings(project_root=tmp_path,input_root=tmp_path/'data/input',output_root=tmp_path/'data/output'))
    diagnostics=telemetry.read(tmp_path,'b'*32)
    call=next(v for v in diagnostics['records'] if v['kind']=='call')
    assert call['provider_profile_id']=='fixture' and call['highest_data_class']=='raw' and call['egress_decision']=='allowed'
    assert key not in str(report)+json.dumps(diagnostics)+caplog.text
    assert 'Inspect orders.csv.' not in json.dumps(diagnostics)
    for file in tmp_path.rglob('*'):
        if file.is_file():assert key.encode() not in file.read_bytes(),file


def test_initial_audit_does_not_claim_no_dispatch_after_an_interruption(tmp_path,monkeypatch):
    written=[]
    monkeypatch.setattr(telemetry,'store',lambda root,kind,value:(written.append(json.loads(json.dumps(value))),True)[1])
    with telemetry.scope(tmp_path,'c'*32):
        SharedModelClient(settings(),transport=httpx.MockTransport(lambda r:response())).complete(request())
    calls=[r for r in written if 'egress_decision' in r]
    assert calls[0]['status']=='started' and calls[0]['network_dispatch']=='unknown'
    assert calls[-1]['network_dispatch']=='attempted'


def test_http_policy_refusal_explains_allowance_without_endpoint_repair(tmp_path,monkeypatch):
    from http.client import HTTPConnection
    from geoagent_harness.apps.http.server import _handler
    from geoagent_harness.task_actions import conversation
    sent=[]
    def reject(*args,**kwargs):
        return SharedModelClient(settings(data_allowed='none'),transport=httpx.MockTransport(lambda r:(sent.append(r),response())[1])).complete(request())
    monkeypatch.setattr(conversation,'conversation_turn',reject)
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(tmp_path));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        connection=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
        connection.request('POST','/api/v1/planner/conversation',json.dumps({'action':'turn','conversation_id':'d'*32,'message':'Explain the data'}),{'Content-Type':'application/json'})
        result=connection.getresponse();body=json.loads(result.read());connection.close()
        assert result.status==403 and body['code']=='model_data_class_blocked'
        assert 'allowance' in body['retry_guidance'] and 'HTTP 404' not in body['retry_guidance']
        assert not body['execution_performed'] and not body['approval_performed'] and not sent
    finally:server.shutdown();server.server_close();thread.join(5)
