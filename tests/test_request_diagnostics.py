"""Request telemetry preserves failures, privacy, bounds and execution boundaries."""
import json
import httpx
import pytest
from geoagent_harness.platform.model_gateway.client import SharedModelClient, ModelClientError
from geoagent_harness.platform.model_settings import ModelSettings
from geoagent_harness.platform.model_gateway.schemas import ModelRequest, ChatMessage
from geoagent_harness.platform.model_gateway import telemetry as d

ID='a'*32
@pytest.fixture
def model_request():return ModelRequest(messages=[ChatMessage(role='user',content='private patient input must not be logged')],response_schema={'type':'object'})
def client(handler):return SharedModelClient(ModelSettings(base_url='http://localhost:11434/v1',model='fixture',timeout_seconds=2,max_tokens=100),transport=httpx.MockTransport(handler))
def response():return httpx.Response(200,json={'model':'fixture','choices':[{'message':{'content':'{"private_result":"do not log"}'},'finish_reason':'stop'}],'usage':{'prompt_tokens':11,'completion_tokens':7}})

def test_success_tokens_phase_and_private_content_excluded(tmp_path,model_request):
    with d.scope(tmp_path,ID,'b'*32):
        with d.phase('critic','outcome'):client(lambda r:response()).complete(model_request)
    result=d.read(tmp_path,ID);encoded=json.dumps(result)
    assert 'private patient' not in encoded and 'private_result' not in encoded and 'do not log' not in encoded
    call=next(r for r in result['records'] if r['kind']=='call')
    assert (call['role'],call['phase'],call['prompt_tokens'],call['completion_tokens'])==('critic','outcome',11,7)
    assert call['status']=='completed' and call['resources']['samples']>=2
    assert call['resources']['model_rss_bytes'] is None and call['resources']['gpu_vram_bytes'] is None
    assert result['reported_prompt_tokens']==11 and not result['execution_performed']
    assert d.read(tmp_path,'c'*32)['records']==[]

def test_timeout_is_durable_unknown_tokens_and_exactly_one_call(tmp_path,model_request):
    calls=[]
    def timeout(r):calls.append(r);raise httpx.ReadTimeout('sensitive detail',request=r)
    with pytest.raises(ModelClientError):
        with d.scope(tmp_path,ID):client(timeout).complete(model_request)
    result=d.read(tmp_path,ID)
    assert len(calls)==1 and len(result['records'])==2
    assert all(r['error_code']=='model_timeout' for r in result['records'])
    assert result['reported_prompt_tokens'] is None and not result['token_usage_complete']
    assert 'sensitive detail' not in json.dumps(result)

def test_invalid_model_output_and_later_schema_failure_distinguished(tmp_path,model_request):
    with pytest.raises(ModelClientError):
        with d.scope(tmp_path,ID):client(lambda r:httpx.Response(200,json={})).complete(model_request)
    assert d.read(tmp_path,ID)['records'][0]['error_code']=='model_invalid_response'
    with pytest.raises(ValueError):
        with d.scope(tmp_path,ID):
            client(lambda r:response()).complete(model_request)
            raise ValueError('invalid plan schema: private property value')
    result=d.read(tmp_path,ID)
    assert result['records'][1]['error_code']=='planner_invalid_schema'
    assert 'private property' not in json.dumps(result)

def test_nested_submission_scope_and_interruption(tmp_path):
    with d.scope(tmp_path,ID,'b'*32):
        with d.scope(tmp_path,ID):pass
    assert len(d.read(tmp_path,ID)['records'])==1
    value={'id':'d'*32,'conversation_id':ID,'status':'started','owner_pid':99999999,'owner_start_ticks':'never','error_code':None}
    assert d.store(tmp_path,'turn',value)
    r=d.read(tmp_path,ID)['records'][0]
    assert r['status']=='interrupted' and r['error_code']=='process_interrupted'

def test_retention_and_storage_failure_do_not_execute_or_change_model_reply(tmp_path,model_request,monkeypatch):
    monkeypatch.setattr(d,'MAX_RECORDS',2)
    for _ in range(4):
        with d.scope(tmp_path,ID):client(lambda r:response()).complete(model_request)
    records=d.read(tmp_path,ID)['records']
    assert sum(r['kind']=='turn' for r in records)==2 and sum(r['kind']=='call' for r in records)==2
    monkeypatch.setattr(d,'store',lambda *a,**k:False)
    with d.scope(tmp_path,ID):assert client(lambda r:response()).complete(model_request).prompt_tokens==11
    with pytest.raises(Exception):d.read(tmp_path,'../unsafe')


def test_nested_different_chat_is_never_attributed_to_parent(tmp_path,model_request):
    with d.scope(tmp_path,ID):
        with d.scope(tmp_path,'c'*32):client(lambda r:response()).complete(model_request)
    assert len(d.read(tmp_path,ID)['records'])==1
    assert len(d.read(tmp_path,'c'*32)['records'])==2


def test_advisory_revision_is_not_labelled_deterministic_policy_rejection(tmp_path):
    inner=ValueError('Executor work-order review requests correction: private model content')
    outer=RuntimeError('Planner plan failed deterministic policy after one correction attempt');outer.__cause__=inner
    with pytest.raises(RuntimeError):
        with d.scope(tmp_path,ID):raise outer
    result=d.read(tmp_path,ID)
    assert result['records'][0]['error_code']=='planner_review_needs_revision'
    assert 'private model' not in json.dumps(result)


def test_diagnostics_http_read_and_review_failure_contract(tmp_path,monkeypatch):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from geoagent_harness.apps.http.server import _handler
    from geoagent_harness.task_actions import conversation
    from geoagent_harness.agents.roles.planner.agent import PlannerAgentError
    with d.scope(tmp_path,ID):pass
    def fail(*a,**kw):
        raise PlannerAgentError('Planner plan failed deterministic policy after one correction attempt',findings=['Role requested revision'],correction_attempted=True) from ValueError('Executor work-order review requests correction: use valid inputs')
    monkeypatch.setattr(conversation,'conversation_turn',fail)
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(tmp_path));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        c=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
        def post(path,payload):
            c.request('POST',path,json.dumps(payload),{'Content-Type':'application/json','Origin':'http://localhost:5173'})
            response=c.getresponse();return response.status,json.loads(response.read())
        status,result=post('/api/v1/planner/diagnostics',{'conversation_id':ID})
        assert status==200 and result['records'] and not result['execution_performed']
        assert post('/api/v1/planner/diagnostics',{'conversation_id':'../unsafe'})[0]==400
        status,result=post('/api/v1/planner/conversation',{'action':'turn','conversation_id':ID,'message':'Inspect metadata'})
        assert status==422 and result['code']=='planner_review_needs_revision'
        assert not result['execution_performed'] and not result['approval_performed']
    finally:server.shutdown();server.server_close();thread.join(timeout=2)



def test_configuration_failure_and_unknown_memory_are_not_invented(tmp_path,monkeypatch):
    from geoagent_harness.platform.model_settings import ModelSettingsError
    monkeypatch.setattr(d,'resources',lambda:{'api_rss_bytes':None,'system_available_bytes':None})
    with pytest.raises(ModelSettingsError):
        with d.scope(tmp_path,ID):raise ModelSettingsError('MODEL_NAME is required')
    r=d.read(tmp_path,ID)['records'][0]
    assert r['error_code']=='model_name_missing' and r['resources']['api_rss_sampled_peak_bytes'] is None
    value={'id':'d'*32,'conversation_id':ID,'status':'started','owner_pid':__import__('os').getpid(),'owner_start_ticks':None,'error_code':None}
    d.store(tmp_path,'turn',value)
    assert d.read(tmp_path,ID)['records'][0]['status']=='started'
