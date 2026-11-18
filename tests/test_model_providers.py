"""M1 uses only synthetic keys, fake servers and temporary project state."""
import json
from pathlib import Path
import httpx
import pytest
from pydantic import ValidationError

from geoagent_harness.contracts.model_providers import ProviderProfile,ProviderUpdate,ProviderSelection,ProviderCheck
from geoagent_harness.platform.model_gateway import profiles
from geoagent_harness.platform.model_gateway.catalog import request_selection,catalog,select,Selection
from geoagent_harness.platform.model_settings import load_model_settings
from geoagent_harness.platform.model_gateway.client import SharedModelClient,ModelClientError
from geoagent_harness.platform.model_gateway.schemas import ModelRequest,ChatMessage
from geoagent_harness.task_actions.model_providers import check_profile

@pytest.fixture
def project(tmp_path,monkeypatch):
    (tmp_path/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(tmp_path/'state')}))
    monkeypatch.setenv('MODEL_NAME','legacy');monkeypatch.setenv('MODEL_BASE_URL','http://127.0.0.1:11434/v1')
    return tmp_path


def install(root,**changes):
    p=ProviderProfile.model_validate({'id':'test','base_url':'http://127.0.0.1:8001/v1','model':'small','data_allowed':'raw',**changes})
    state=profiles.read(root)
    profiles.save(root,ProviderUpdate(profile=p,expected_revision=state.revision))
    state=profiles.read(root)
    profiles.select(root,ProviderSelection(profile_id=p.id,expected_revision=state.revision))
    return profiles.read(root)


def request(**kwargs):return ModelRequest(messages=[ChatMessage(role='user',content='Synthetic test')],**kwargs)

@pytest.mark.parametrize('changes',[{'id':'local'},{'base_url':'http://user:CANARY@localhost/v1'},
    {'base_url':'http://localhost/v1?key=CANARY'},{'base_url':'file:///tmp/key'},
    {'base_url':'http://localhost:abc/v1'},{'credential_ref':'secret:../key'},
    {'credential_ref':'CANARY-ACTUAL-KEY'},{'api_key':'CANARY'},
    {'data_allowed':'anything'},{'limits':{'timeout_s':0}},{'limits':{'max_tokens':True}}])
def test_profile_contract_rejects_unsafe_or_unknown_configuration(changes):
    with pytest.raises(ValidationError):ProviderProfile.model_validate({'id':'test','base_url':'http://localhost/v1',**changes})


def test_save_pin_switch_and_legacy_configuration(project,monkeypatch):
    assert profiles.public_state(project)['selected_profile']=='local'
    assert not (project/'state/model-providers.json').exists()
    install(project)
    with request_selection(project):
        old=load_model_settings();assert old.model=='small' and old.provider_profile_id=='test'
        profiles.select(project,ProviderSelection(profile_id='local',expected_revision=2))
        monkeypatch.setenv('MODEL_NAME','changed')
        assert load_model_settings()==old
        with request_selection(project):assert load_model_settings()==old
    with request_selection(project):assert load_model_settings().model=='changed'
    assert load_model_settings({'MODEL_NAME':'explicit-env','MODEL_BASE_URL':'http://localhost/v1'}).model=='explicit-env'
    with pytest.raises(profiles.ProviderError,match='changed'):
        profiles.select(project,ProviderSelection(profile_id='local',expected_revision=0))


def test_endpoint_authentication_is_private_and_redirects_never_follow(project,monkeypatch,caplog):
    key='SYNTHETIC_M1_KEY_CANARY_123'
    monkeypatch.setenv('M1_TEST_KEY',key)
    install(project,credential_ref='env:M1_TEST_KEY')
    calls=[]
    def handle(r):
        calls.append(r);assert r.headers['Authorization']=='Bearer '+key
        return httpx.Response(302,headers={'Location':'http://outside.invalid/v1'})
    with request_selection(project):
        settings=load_model_settings()
        with pytest.raises(ModelClientError) as failure:SharedModelClient(settings,transport=httpx.MockTransport(handle)).complete(request())
    assert len(calls)==1
    assert key not in str(failure.value) and key not in repr(settings) and key not in caplog.text
    for p in (project/'state').rglob('*'):
        if p.is_file():assert key.encode() not in p.read_bytes()
    assert 'credential_ref' not in json.dumps(profiles.public_state(project))


@pytest.mark.parametrize('field',['model','content','discovery'])
def test_provider_cannot_reflect_authentication_into_results(project,monkeypatch,field):
    key='SYNTHETIC_REFLECTION_KEY_456';monkeypatch.setenv('M1_TEST_KEY',key)
    install(project,credential_ref='env:M1_TEST_KEY')
    if field=='discovery':
        with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[{'id':key}]}))) as client:
            with pytest.raises(Exception) as failure:catalog(project,client=client)
    else:
        body={'model':key if field=='model' else 'small','choices':[{'message':{'content':key if field=='content' else '{}'}}]}
        with request_selection(project):
            with pytest.raises(ModelClientError) as failure:SharedModelClient(load_model_settings(),transport=httpx.MockTransport(lambda r:httpx.Response(200,json=body))).complete(request())
    assert key not in str(failure.value)


def test_missing_secret_bad_secret_links_and_nonlocal_are_blocked_before_http(project,monkeypatch):
    install(project,credential_ref='secret:key')
    calls=[];transport=httpx.MockTransport(lambda r:(calls.append(r),httpx.Response(200))[1])
    def attempt():
        with request_selection(project):SharedModelClient(load_model_settings(),transport=transport).complete(request())
    with pytest.raises(profiles.ProviderError,match='credential'):attempt()
    directory=project/'.secrets';directory.mkdir();(directory/'key').write_text('header\ninjection')
    with pytest.raises(profiles.ProviderError):attempt()
    (directory/'key').unlink();(directory/'target').write_text('SYNTHETIC');(directory/'key').symlink_to(directory/'target')
    with pytest.raises(profiles.ProviderError):attempt()
    profile=ProviderProfile(id='remote',base_url='https://outside.invalid/v1',credential_ref='env:M1_TEST_KEY')
    profiles.save(project,ProviderUpdate(profile=profile,expected_revision=2))
    with pytest.raises(profiles.ProviderError,match='Non-local'):
        profiles.select(project,ProviderSelection(profile_id='remote',expected_revision=3))
    with pytest.raises(profiles.ProviderError,match='Non-local'):
        check_profile(project,ProviderCheck(profile_id='remote',model='small',expected_revision=3),transport=transport)
    assert not calls and profiles.read(project).selected=='test'


def test_compatible_model_discovery_auth_selection_and_pagination_are_bounded(project,monkeypatch):
    monkeypatch.setenv('M1_TEST_KEY','SYNTHETIC')
    install(project,credential_ref='env:M1_TEST_KEY')
    calls=[]
    def handle(r):
        calls.append(r);assert r.url.path=='/v1/models' and r.headers['Authorization']=='Bearer SYNTHETIC'
        return httpx.Response(200,json={'data':[{'id':'small'},{'id':'second'}],'next':'https://outside.invalid/next'})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        value=catalog(project,client=client)
        assert value['count']==2 and value['provider_id']=='test'
        with pytest.raises(Exception):select(project,Selection(model='second',expected_revision=2),client=client)
        with request_selection(project):
            value=select(project,Selection(model='second',expected_revision=2,provider_id='test',provider_revision=2),client=client)
            assert value['selected_model']=='second'
            assert load_model_settings().model=='small'
        with request_selection(project):assert load_model_settings().model=='second'
    assert all(r.url.host=='127.0.0.1' for r in calls)


@pytest.mark.parametrize('supported',['json_object','text'])
def test_explicit_check_negotiates_only_synthetic_requests_and_generation_does_not_retry(project,supported):
    install(project)
    calls=[]
    def handle(r):
        body=json.loads(r.content);calls.append(body)
        mode=body.get('response_format',{}).get('type','text')
        if mode!=supported:return httpx.Response(400,text=mode+' not supported')
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'}}]})
    transport=httpx.MockTransport(handle)
    with request_selection(project):
        with pytest.raises(ModelClientError,match='schema'):SharedModelClient(load_model_settings(),transport=transport).complete(request(response_schema={'type':'object'}))
    assert len(calls)==1
    result=check_profile(project,ProviderCheck(profile_id='test',model='small',expected_revision=2),transport=transport)
    assert result['status']=='compatible' and result['attempts']==(['json_schema','json_object'] if supported=='json_object' else ['json_schema','json_object','text'])
    assert all(b['messages'][0]['content'].startswith('Return only this JSON') for b in calls[1:])
    with request_selection(project):
        assert load_model_settings().response_format==supported
        SharedModelClient(load_model_settings(),transport=transport).complete(request(response_schema={'type':'object'}))
    assert calls[-1].get('response_format')==({'type':'json_object'} if supported=='json_object' else None)


@pytest.mark.parametrize('status',[401,403,429,500])
def test_failed_checks_do_not_fallback_or_record_success(project,status):
    install(project);calls=[]
    transport=httpx.MockTransport(lambda r:(calls.append(r),httpx.Response(status,text='SECRET_ECHO'))[1])
    result=check_profile(project,ProviderCheck(profile_id='test',model='small',expected_revision=2),transport=transport)
    assert result['status']=='unavailable' and len(calls)==1
    assert 'SECRET_ECHO' not in json.dumps(result)
    assert not profiles.read(project).findings


def test_credential_rotation_during_check_does_not_hide_prior_request(project,monkeypatch):
    monkeypatch.setenv('M1_TEST_KEY','SYNTHETIC')
    install(project,credential_ref='env:M1_TEST_KEY')
    calls=[]
    def handle(r):
        calls.append(r);monkeypatch.delenv('M1_TEST_KEY')
        return httpx.Response(400,text='json_schema unsupported')
    result=check_profile(project,ProviderCheck(profile_id='test',model='small',expected_revision=2),transport=httpx.MockTransport(handle))
    assert result['model_called'] and result['code']=='model_credentials_invalid' and len(calls)==1
    assert not profiles.read(project).findings


def test_coarse_allowance_blocks_unclassified_generation_but_synthetic_check_can_run(project):
    install(project,data_allowed='none');calls=[]
    transport=httpx.MockTransport(lambda r:(calls.append(r),httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'}}]}))[1])
    with request_selection(project):
        with pytest.raises(ModelClientError) as error:SharedModelClient(load_model_settings(),transport=transport).complete(request())
    assert error.value.code=='model_data_class_blocked' and not calls
    assert check_profile(project,ProviderCheck(profile_id='test',model='small',expected_revision=2),transport=transport)['status']=='compatible'


def test_failed_check_after_concurrent_edit_reports_call_without_overwriting_config(project):
    install(project)
    def handle(r):
        profiles.select(project,ProviderSelection(profile_id='local',expected_revision=2))
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'}}]})
    result=check_profile(project,ProviderCheck(profile_id='test',model='small',expected_revision=2),transport=httpx.MockTransport(handle))
    assert result['status']=='stale' and result['model_called']
    assert profiles.read(project).selected=='local' and not profiles.read(project).findings


def test_status_blocks_manually_selected_nonlocal_profile_without_network(project):
    from geoagent_harness.platform.model_gateway.diagnostics import inspect_model_configuration
    profile=ProviderProfile(id='remote',base_url='https://outside.invalid/v1',model='small')
    profiles.save(project,ProviderUpdate(profile=profile,expected_revision=0))
    path=project/'state/model-providers.json';value=json.loads(path.read_text());value['selected']='remote';path.write_text(json.dumps(value))
    with request_selection(project):result=inspect_model_configuration()
    assert result['status']=='configuration_blocked' and result['code']=='model_profile_blocked'
    assert not result['model_called'] and not result['connection_tested']


def test_http_and_cli_use_same_configuration_and_reject_foreign_origin(project):
    from http.server import ThreadingHTTPServer
    from http.client import HTTPConnection
    from threading import Thread
    from geoagent_harness.apps.http.server import _handler
    from geoagent_harness.apps.cli.main import app
    from typer.testing import CliRunner
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(project));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    def post(origin=None):
        c=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
        c.request('POST','/api/v1/providers/save',json.dumps({'profile':{'id':'test','base_url':'http://localhost:11434/v1'},'expected_revision':0}),
            {'Content-Type':'application/json',**({'Origin':origin} if origin else {})})
        r=c.getresponse();v=json.loads(r.read());c.close();return r.status,v
    try:
        assert post('https://outside.invalid')[0]==403 and profiles.read(project).revision==0
        status,value=post();assert status==200 and value['revision']==1
        result=CliRunner().invoke(app,['models','profiles','--project-root',str(project)])
        assert result.exit_code==0 and json.loads(result.stdout)==value
    finally:server.shutdown();server.server_close();thread.join(5)
