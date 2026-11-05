import json

import httpx
import pytest

from geoagent_harness.model.catalog import catalog, select, Selection, request_selection, CatalogError
from geoagent_harness.model.settings import load_model_settings
from geoagent_harness.model.diagnostics import inspect_model_configuration


ENV = {'MODEL_NAME': 'old:4b', 'MODEL_BASE_URL': 'http://127.0.0.1:11434/v1'}


def client(calls, *, bad_loaded=False):
    def handle(request):
        calls.append((request.method, request.url.path))
        if request.url.path == '/api/ps' and bad_loaded:
            return httpx.Response(503)
        models = [{'name': 'new:4b', 'size': 100}, {'name': 'old:4b', 'size': 200}]
        return httpx.Response(200, json={'models': models[:1] if request.url.path == '/api/ps' else models})
    return httpx.Client(transport=httpx.MockTransport(handle))


def test_discovery_selection_persists_and_pins_requests(tmp_path, monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    calls = []
    with client(calls) as connection:
        original = catalog(tmp_path, client=connection)
        assert original['count'] == 2 and original['models'][0]['loaded']
        with request_selection(tmp_path):
            assert load_model_settings().model == 'old:4b'
            selected = select(tmp_path, Selection(model='new:4b', expected_revision=0), client=connection)
            assert selected['revision'] == 1
            assert load_model_settings().model == 'old:4b'
        with request_selection(tmp_path):
            assert load_model_settings().model == 'new:4b'
            assert inspect_model_configuration()['status'] == 'configured'
        assert load_model_settings().model == 'old:4b'
        assert catalog(tmp_path, client=connection)['selected_model'] == 'new:4b'
        with pytest.raises(CatalogError, match='changed'):
            select(tmp_path, Selection(model='old:4b', expected_revision=0), client=connection)
        with pytest.raises(CatalogError, match='no longer'):
            select(tmp_path, Selection(model='missing', expected_revision=1), client=connection)
    assert all(method == 'GET' and path in {'/api/tags', '/api/ps'} for method, path in calls)


def test_missing_environment_model_can_be_selected(tmp_path, monkeypatch):
    monkeypatch.delenv('MODEL_NAME', raising=False)
    monkeypatch.setenv('MODEL_BASE_URL', ENV['MODEL_BASE_URL'])
    with client([]) as connection:
        assert catalog(tmp_path, client=connection)['selected_model'] is None
        select(tmp_path, Selection(model='new:4b', expected_revision=0), client=connection)
    with request_selection(tmp_path):
        assert inspect_model_configuration()['model_name_set']
        assert load_model_settings().model == 'new:4b'


def test_loaded_status_optional_and_catalog_errors_do_not_leak(tmp_path):
    with client([], bad_loaded=True) as connection:
        result = catalog(tmp_path, client=connection, environ=ENV)
        assert result['count'] == 2 and result['loaded_status_error']
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(404, text='private-secret'))) as connection:
        with pytest.raises(CatalogError) as failure:
            catalog(tmp_path, client=connection, environ=ENV)
        assert 'private-secret' not in str(failure.value)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b'x' * (1024**2 + 1)))) as connection:
        with pytest.raises(CatalogError, match='budget'):
            catalog(tmp_path, client=connection, environ=ENV)


def test_discovery_never_follows_redirects_or_embedded_credentials(tmp_path):
    calls = []
    with httpx.Client(transport=httpx.MockTransport(lambda r: (calls.append(str(r.url)), httpx.Response(302, headers={'location':'http://private/'}))[1])) as connection:
        with pytest.raises(CatalogError):
            catalog(tmp_path, client=connection, environ=ENV)
    assert len(calls) == 1
    with pytest.raises(CatalogError, match='without URL credentials'):
        catalog(tmp_path, environ={**ENV, 'MODEL_BASE_URL':'http://user:password@localhost/v1'})


def test_reasoning_project_override_persists_and_pins_active_requests(tmp_path,monkeypatch):
    from geoagent_harness.model.catalog import reasoning_preference,select_reasoning,ReasoningSelection
    for key,value in ENV.items():monkeypatch.setenv(key,value)
    monkeypatch.setenv('MODEL_REASONING_EFFORT','high')
    assert reasoning_preference(tmp_path)['effective']=='high'
    with request_selection(tmp_path):
        assert load_model_settings().reasoning_effort=='high'
        saved=select_reasoning(tmp_path,ReasoningSelection(selection='none',expected_revision=0))
        assert saved['effective']=='none' and not saved['model_called']
        with request_selection(tmp_path):assert load_model_settings().reasoning_effort=='high'
    with request_selection(tmp_path):assert load_model_settings().reasoning_effort=='none'
    assert load_model_settings().reasoning_effort=='high'
    with pytest.raises(CatalogError,match='changed'):select_reasoning(tmp_path,ReasoningSelection(selection='low',expected_revision=0))
    select_reasoning(tmp_path,ReasoningSelection(selection='provider',expected_revision=1))
    with request_selection(tmp_path):assert load_model_settings().reasoning_effort is None
    select_reasoning(tmp_path,ReasoningSelection(selection='environment',expected_revision=2))
    with request_selection(tmp_path):assert load_model_settings().reasoning_effort=='high'


def test_project_reasoning_is_sent_by_shared_client(tmp_path,monkeypatch):
    from geoagent_harness.model.catalog import select_reasoning,ReasoningSelection
    from geoagent_harness.model import SharedModelClient
    from geoagent_harness.model.schemas import ModelRequest,ChatMessage
    for key,value in ENV.items():monkeypatch.setenv(key,value)
    monkeypatch.delenv('MODEL_REASONING_EFFORT',raising=False)
    select_reasoning(tmp_path,ReasoningSelection(selection='none',expected_revision=0))
    bodies=[]
    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200,json={'choices':[{'message':{'content':'{}'},'finish_reason':'stop'}]})
    with request_selection(tmp_path):
        SharedModelClient(load_model_settings(),transport=httpx.MockTransport(handle)).complete(ModelRequest(messages=[ChatMessage(role='user',content='Inspect metadata')]))
    assert len(bodies)==1 and bodies[0]['reasoning_effort']=='none'


def test_review_timeout_is_bounded_persistent_and_request_pinned(tmp_path):
    from geoagent_harness.model.catalog import ReviewTimeoutSelection,select_review_timeout,review_timeout_seconds,review_timeout_preference
    from pydantic import ValidationError
    assert review_timeout_seconds(tmp_path)==15
    for value in (0,4,181,True,12.5,'30'):
        with pytest.raises(ValidationError):ReviewTimeoutSelection(seconds=value,expected_revision=0)
    with request_selection(tmp_path):
        select_review_timeout(tmp_path,ReviewTimeoutSelection(seconds=45,expected_revision=0))
        assert review_timeout_seconds(tmp_path)==15
        with pytest.raises(CatalogError,match='changed'):
            select_review_timeout(tmp_path,ReviewTimeoutSelection(seconds=90,expected_revision=0))
    with request_selection(tmp_path):assert review_timeout_seconds(tmp_path)==45
    assert review_timeout_preference(tmp_path)=={'seconds':45,'revision':1,'source':'project'}


def test_review_timeout_http_origin_validation_and_conflict(tmp_path):
    from http.server import ThreadingHTTPServer
    from http.client import HTTPConnection
    from threading import Thread
    from geoagent_harness.interface_api.server import _handler
    from geoagent_harness.model.catalog import review_timeout_preference
    server=ThreadingHTTPServer(('127.0.0.1',0),_handler(tmp_path));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    def post(value,origin=None):
        connection=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        connection.request('POST','/api/v1/models/review-timeout',json.dumps(value),headers)
        response=connection.getresponse();status=response.status;payload=json.loads(response.read());connection.close();return status,payload
    try:
        assert post({'seconds':30,'expected_revision':0},'https://foreign.invalid')[0]==403
        assert review_timeout_preference(tmp_path)['seconds']==15
        assert post({'seconds':181,'expected_revision':0})[0] in {400,422}
        status,value=post({'seconds':30,'expected_revision':0})
        assert status==200 and value['seconds']==30 and not value['execution_performed'] and not value['model_called']
        assert post({'seconds':60,'expected_revision':0})[0]==409
    finally:server.shutdown();server.server_close();thread.join(5)
