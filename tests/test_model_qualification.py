"""M3c harness evidence is synthetic; no test calls an installed model or real gateway."""
import importlib.util
import json
import os
import time
from pathlib import Path
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('provider_qualification',ROOT/'scripts/qualify_model_providers.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)


@pytest.fixture
def upstream():
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            calls.append({'path':self.path,'auth':self.headers.get('Authorization'),
                          'body':self.rfile.read(int(self.headers['Content-Length']))})
            data=json.dumps({'model':'synthetic-endpoint','choices':[{'message':{'content':'{"ok":true}'},'finish_reason':'stop'}],
                             'usage':{'prompt_tokens':4,'completion_tokens':5}}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}/v1',calls
    server.shutdown();server.server_close();thread.join(timeout=3)


@pytest.mark.parametrize('url',[
    'http://example.com/v1','http://localhost/v1','http://127.0.0.1.evil.test/v1',
    'http://user:pass@127.0.0.1/v1','http://127.0.0.1/v1?token=x',
    'http://127.0.0.1/v1#secret','http://127.0.0.1/api',
])
def test_qualification_only_accepts_literal_loopback_without_credentials(url):
    with pytest.raises(ValueError): q.endpoint(url)


def test_auth_gate_blocks_missing_wrong_key_and_unrecognised_routes_before_upstream(upstream):
    url,calls=upstream
    with q.Relay(url,key='sk-synthetic-only') as relay, httpx.Client(trust_env=False) as client:
        for headers in ({},{'Authorization':'Bearer wrong'}):
            response=client.post(relay.base_url+'/chat/completions',json={},headers=headers)
            assert response.status_code==401
        assert relay.forwarded==0 and len(calls)==0 and relay.rejected==2
        assert client.post(relay.base_url+'/arbitrary',json={}).status_code==404
        assert client.post(relay.base_url+'/chat/completions',json={},
            headers={'Authorization':'Bearer sk-synthetic-only'}).status_code==200
        assert relay.forwarded==1 and len(calls)==1
        assert calls[0]['auth'] is None  # gate credential never reaches the model


def test_private_unix_broker_can_complete_model_request_without_tcp_listener(tmp_path,upstream):
    url,calls=upstream; path=str(tmp_path/'model.sock')
    with q.Relay(url,unix_socket=path) as relay:
        settings=q.ModelSettings(base_url=relay.base_url,model='synthetic',timeout_seconds=2,max_tokens=64)
        result=q.smoke(settings,transport=httpx.HTTPTransport(uds=path))
        assert result['status']=='passed' and result['prompt_tokens']==4
        assert len(calls)==1 and relay.forwarded==1
        assert (os.stat(path).st_mode & 0o777)==0o600


def test_egress_refusal_sends_no_request(upstream):
    url,calls=upstream
    settings=q.ModelSettings(base_url=url,model='synthetic',timeout_seconds=1,max_tokens=64,data_allowed='none')
    result=q.smoke(settings)
    assert result['code']=='model_data_class_blocked' and calls==[]


def test_schema_rejection_and_timeout_are_not_automatically_retried():
    settings=q.ModelSettings(base_url='http://127.0.0.1/v1',model='synthetic',timeout_seconds=.01,max_tokens=64)
    calls=[]
    def reject(request):
        calls.append(1)
        return httpx.Response(400,json={'error':'response_format json_schema unsupported'})
    result=q.smoke(settings,transport=httpx.MockTransport(reject))
    assert result['code']=='model_response_format_rejected' and len(calls)==1
    def timeout(request):
        calls.append(1);raise httpx.ReadTimeout('synthetic')
    result=q.smoke(settings,transport=httpx.MockTransport(timeout))
    assert result['code']=='model_timeout' and len(calls)==2


def test_missing_credential_is_blocked_before_http(upstream,monkeypatch):
    url,calls=upstream;monkeypatch.delenv('M3C_MISSING_KEY',raising=False)
    settings=q.ModelSettings(base_url=url,model='synthetic',timeout_seconds=1,max_tokens=64,
        credential_ref='env:M3C_MISSING_KEY',provider_profile_id='qualification')
    result=q.smoke(settings)
    assert result['status']=='failed' and calls==[]


def test_child_environment_excludes_owner_credentials_and_workspace_overrides(tmp_path,monkeypatch):
    for key in ('AWS_SECRET_ACCESS_KEY','OPENAI_API_KEY','POSTGRES_PASSWORD','GEOAGENT_STATE_ROOT','GEOAGENT_INPUT_ROOT'):
        monkeypatch.setenv(key,'owner-private-value')
    settings=q.ModelSettings(base_url='http://127.0.0.1/v1',model='synthetic',timeout_seconds=1,max_tokens=64)
    env=q.environment(tmp_path,settings,'synthetic-gateway-key')
    assert 'owner-private-value' not in json.dumps(env)
    assert env['ENABLE_WRITE_TOOLS']=='false'
    assert env['QUALIFICATION_KEY']=='synthetic-gateway-key'
    assert Path(env['HOME']).is_relative_to(tmp_path)


def test_actual_fixture_pipeline_is_checked_but_never_claimed_real_qualification(tmp_path):
    settings=q.ModelSettings(base_url='http://127.0.0.1:1/v1',model='synthetic',timeout_seconds=1,max_tokens=512)
    plan=json.loads((ROOT/'benchmarks/tasks'/q.TASK/'fixture-plan.json').read_text())
    result=q.workflow(tmp_path/'fixture',settings,fixture_plan=plan,wall_seconds=30,critic_timeout=45)
    assert result['execution']=='passed',result
    assert result['critic']=='complete'
    assert result['executed_operations']==1 and result['data_outputs']==0
    assert result['planning']=='validated' and len(result['checks'])==2
    assert result['status']=='not_qualified' and result['model_planner_called'] is False
    state=json.loads((tmp_path/'fixture/state/model-providers.json').read_text())
    assert state['selected']=='qualification' and state['profiles'][0]['model']=='synthetic'
    from geoagent_harness.platform.model_gateway.catalog import review_timeout_preference
    assert review_timeout_preference(tmp_path/'fixture')['seconds']==45
    (tmp_path/'unused').mkdir()
    assert review_timeout_preference(tmp_path/'unused')['seconds']==15


def test_qualification_cannot_expand_to_database_operations(tmp_path):
    from geoagent_harness.apps.benchmark.worker import work
    (tmp_path/'job.json').write_text(json.dumps({'model_calls':1,'wall_clock_s':1,
        'allow_writes':False,'allowed_skill_ids':['import_csv_to_postgres']}))
    with pytest.raises(ValueError,match='subset'): work(tmp_path)


def test_critic_schema_diagnostics_never_store_model_content_or_unknown_keys(tmp_path,monkeypatch):
    from geoagent_harness.apps.benchmark.worker import BudgetClient
    from geoagent_harness.platform.model_gateway import SharedModelClient
    from geoagent_harness.platform.model_gateway.schemas import ModelResult
    from geoagent_harness.platform.model_gateway.telemetry import phase
    private='synthetic-private-content'
    response={'deterministic_status':'completed','conclusion':'supported','summary':private,
              'findings':[],'limitations':[],private:private}
    monkeypatch.setattr(SharedModelClient,'complete',lambda *a:ModelResult(model='fixture',content=json.dumps(response)))
    settings=q.ModelSettings(base_url='http://127.0.0.1:1/v1',model='fixture',timeout_seconds=1,max_tokens=64)
    client=BudgetClient(settings,None,1,time.monotonic()+3,tmp_path,qualification=True)
    with phase('critic','outcome_review'):
        client.complete(q.ModelRequest(messages=[q.ChatMessage(role='user',content='fixture')]))
    record=json.loads((tmp_path/'calls.json').read_text())['calls'][0]
    assert record['assessment_schema_valid'] is False
    assert {v['field'] for v in record['schema_findings']}=={'limitations','[unexpected field]'}
    assert private not in (tmp_path/'calls.json').read_text()
