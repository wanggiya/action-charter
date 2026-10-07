"""Configuration and transport failures stay actionable and do not reveal secrets."""
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
import pytest
from geoagent_harness.interface_api.server import _handler
from geoagent_harness.model import ModelClientError, ModelSettingsError
from geoagent_harness.model.diagnostics import inspect_model_configuration, model_failure
from geoagent_harness.failures import FailureCategory, RetryDisposition

@pytest.mark.parametrize('error, code', [
    (ModelSettingsError('MODEL_NAME is required'), 'model_name_missing'),
    (ModelSettingsError('MODEL_BASE_URL must end with /v1'), 'model_endpoint_invalid'),
    (ModelClientError.timeout(), 'model_timeout'),
    (ModelClientError.unavailable(), 'model_unavailable'),
    (ModelClientError.http_status(403), 'model_authentication_failed'),
    (ModelClientError.http_status(429), 'model_http_unavailable'),
    (ModelClientError.http_status(404), 'model_http_error'),
    (ModelClientError.invalid_response(), 'model_invalid_response'),
])
def test_failure_categories_are_specific_and_never_grant_authority(error, code):
    result = model_failure(error)
    assert result['code'] == code
    assert result['retry_guidance'] and result['error']
    assert result['execution_performed'] is result['plan_saved'] is result['approval_performed'] is False


def test_unrecognised_messages_and_codes_do_not_expose_values():
    secret = 'http://user:secret-password@private.example/v1?api_key=secret-token'
    for error in (ModelSettingsError(secret), ModelClientError(secret, code=secret, category=FailureCategory.CONFIGURATION, retry=RetryDisposition.NEVER)):
        result = json.dumps(model_failure(error))
        assert 'secret-password' not in result and 'private.example' not in result and 'secret-token' not in result


def test_configuration_status_inspects_settings_not_connectivity_or_model_quality():
    blocked = inspect_model_configuration({})
    assert blocked['status'] == 'configuration_blocked' and blocked['code'] == 'model_name_missing'
    configured = inspect_model_configuration({'MODEL_NAME':'private-model-name', 'MODEL_BASE_URL':'http://private-host:11434/v1', 'MODEL_TIMEOUT_SECONDS':'300', 'MODEL_MAX_TOKENS':'4096', 'MODEL_API_KEY':'secret-token'})
    assert configured['status'] == 'configured' and configured['timeout_seconds'] == 300
    assert configured['connection_tested'] is configured['model_called'] is configured['execution_performed'] is False
    text = json.dumps(configured)
    assert 'private-model-name' not in text and 'private-host' not in text and 'secret-token' not in text


@pytest.mark.parametrize('error, expected_code', [
    (ModelSettingsError('MODEL_NAME is required'), 'model_name_missing'),
    (ModelClientError.timeout(), 'model_timeout'),
    (ModelClientError.unavailable(), 'model_unavailable'),
])
def test_intent_http_returns_actionable_failure_and_process_configuration(tmp_path, monkeypatch, error, expected_code):
    import geoagent_harness.intent.service as service
    def fail(**_kwargs): raise error
    monkeypatch.setattr(service, 'reason_task_intent', fail)
    monkeypatch.delenv('MODEL_NAME', raising=False)
    server = ThreadingHTTPServer(('127.0.0.1',0), _handler(tmp_path))
    thread = Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        connection = HTTPConnection('127.0.0.1',server.server_port,timeout=3)
        connection.request('POST','/api/v1/intent/reason',body=json.dumps({'action':'reason_task_intent','review_filename':None,'request':'Inspect metadata'}),headers={'Content-Type':'application/json','Origin':'http://localhost:5173'})
        response = connection.getresponse(); result = json.loads(response.read())
        assert response.status == 502 and result['code'] == expected_code
        assert result['retry_guidance'] and result['execution_performed'] is False
        connection.request('GET','/api/v1/model-status')
        response = connection.getresponse(); config = json.loads(response.read())
        assert response.status == 200 and config['status'] == 'configuration_blocked'
        assert config['code'] == 'model_name_missing' and config['model_called'] is False
        connection.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
    assert not (tmp_path/'reviewed-intents').exists()
