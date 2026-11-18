"""Optional service controls use fakes here; real-provider captures are separate."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qualification_services_tested',ROOT/'scripts/qualification_services.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
qspec=importlib.util.spec_from_file_location('qualification_runner_tested',ROOT/'scripts/qualify_model_providers.py')
q=importlib.util.module_from_spec(qspec);qspec.loader.exec_module(q)


def test_service_environment_never_inherits_owner_credentials_or_proxy_callbacks(tmp_path,monkeypatch):
    for key in ('OPENAI_API_KEY','AWS_SECRET_ACCESS_KEY','DATABASE_URL','HTTP_PROXY','LITELLM_CALLBACKS','PYTHONPATH'):
        monkeypatch.setenv(key,'private-owner-value')
    env=s.clean_environment(tmp_path)
    assert 'private-owner-value' not in json.dumps(env)
    assert env['HOME']==str(tmp_path) and env['XDG_CACHE_HOME'].startswith(str(tmp_path))
    assert env['PYTHON_DOTENV_DISABLED']=='1' and env['LITELLM_TELEMETRY_DISABLED']=='true'


@pytest.mark.parametrize('url',['http://example.com/v1','http://localhost/v1','http://127.0.0.1/v1?secret=x','http://a:b@127.0.0.1/v1'])
def test_managed_gateway_cannot_choose_remote_or_credential_url(url):
    with pytest.raises(ValueError):s.gateway_configuration(url,'fixture')


def test_config_has_references_only_no_retries_or_callbacks():
    value=s.gateway_configuration('http://127.0.0.1:11434/v1','fixture')
    assert value['general_settings']['master_key']=='os.environ/QUALIFICATION_GATEWAY_KEY'
    assert value['router_settings']=={'num_retries':0,'fallbacks':[]}
    assert value['model_list'][0]['litellm_params']['max_retries']==0
    assert value['litellm_settings']['callbacks']==[] and value['litellm_settings']['turn_off_message_logging']


class Process:
    pid=123456
    def __init__(self):self.returncode=None
    def poll(self):return self.returncode
    def wait(self,timeout=None):self.returncode=0;return 0


@pytest.mark.parametrize('ready',[True,False])
def test_gateway_startup_and_failure_both_stop_only_owned_process(tmp_path,monkeypatch,ready):
    python=tmp_path/'env/bin/python';python.parent.mkdir(parents=True);python.touch()
    (python.parent/'litellm').touch()
    monkeypatch.setattr(s,'free_port',lambda:42000)
    monkeypatch.setattr(s.shutil,'which',lambda _: '/usr/bin/timeout')
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='1.109.1\n'))
    process=Process();started=[];stopped=[]
    def popen(command,**kwargs):started.append((command,kwargs));return process
    monkeypatch.setattr(s.subprocess,'Popen',popen)
    monkeypatch.setattr(s.os,'killpg',lambda pid,sig:stopped.append(pid))
    client=httpx.Client
    monkeypatch.setattr(s.httpx,'Client',lambda **kwargs:client(transport=httpx.MockTransport(lambda r:httpx.Response(200))))
    gateway=s.LiteLLMGateway(python,'http://127.0.0.1:1/v1','fixture',tmp_path/'private',startup_seconds=1 if ready else 0)
    if ready:
        with gateway:
            assert started[0][0][:4]==['timeout','--signal=TERM','--kill-after=3s','420s']
            assert gateway.key not in (gateway.directory/'gateway.json').read_text()
            assert started[0][1]['env']['QUALIFICATION_GATEWAY_KEY']==gateway.key
    else:
        with pytest.raises(RuntimeError):gateway.__enter__()
    gateway.close()
    assert stopped==[process.pid] and gateway.stopped and gateway.log.closed


def test_version_mismatch_never_starts_gateway(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'free_port',lambda:42000)
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='wrong-version'))
    monkeypatch.setattr(s.subprocess,'Popen',lambda *a,**k:pytest.fail('must not start mismatched dependency'))
    with pytest.raises(ValueError,match='version'):s.LiteLLMGateway(tmp_path/'python','http://127.0.0.1/v1','fixture',tmp_path/'run').__enter__()


@pytest.mark.parametrize('managed,kind,count,expected',[
    (True,'no_db_connection',0,True),
    (False,'no_db_connection',0,False),
    (True,'no_db_connection',1,False),
    (True,'invalid_request_error',0,False),
    (True,'auth_error',0,False),
    (True,'no_db_connection',None,False),
])
def test_litellm_400_exception_requires_exact_type_valid_body_managed_runtime_and_no_dispatch(managed,kind,count,expected):
    bodies=[]
    def respond(request):
        body=json.loads(request.content);bodies.append(body)
        assert body['messages'] and body['messages'][0]['role']=='user'
        status=400 if request.headers.get('Authorization') else 401
        return httpx.Response(status,json={'error':{'type':kind}})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result=q.credential_rejection_checks(client,'http://127.0.0.1/v1','fixture',managed=managed,
            upstream_calls=(lambda:count) if count is not None else None)
    assert result['blocked'] is expected and len(bodies)==2


def test_secondary_process_reads_bom_metadata_and_runs_guarded_stop(tmp_path,monkeypatch):
    executable=tmp_path/'ollama.exe';executable.touch()
    models=tmp_path/'models';models.mkdir();directory=tmp_path/'private'
    monkeypatch.setattr(s,'free_port',lambda:41000)
    monkeypatch.setattr(s.subprocess,'check_output',lambda *a,**k:'private-windows-path\n')
    process=Process();calls=[]
    def popen(command,**kwargs):
        calls.append(command)
        (directory/'owned-process.json').write_text(json.dumps({'pid':process.pid,'started_ticks':'1','port':42000,'binary_sha256':'a'*64}),encoding='utf-8-sig')
        return process
    monkeypatch.setattr(s.subprocess,'Popen',popen)
    def stop(command,**kwargs):
        assert command[-2:]==['-Action','Stop'];process.returncode=0
    monkeypatch.setattr(s.subprocess,'run',stop)
    client=httpx.Client
    monkeypatch.setattr(s.httpx,'Client',lambda **kwargs:client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'version':'fixture'}))))
    with s.WindowsOllama(executable,models,directory) as server:
        assert server.base_url=='http://127.0.0.1:42000/v1'
        assert server.provenance['separately_started_process'] is True
        assert server.provenance['new_model_downloads'] is False
        assert calls[0][-2:]==['-Port','0']  # Windows, not Linux, allocates its port.
    assert server.stopped
