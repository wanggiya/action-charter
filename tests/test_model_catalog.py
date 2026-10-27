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
