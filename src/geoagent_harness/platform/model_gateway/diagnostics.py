"""Safe process-configuration summaries and actionable model failure messages."""
from __future__ import annotations
import os
from collections.abc import Mapping
from geoagent_harness.platform.model_gateway.client import ModelClientError
from geoagent_harness.platform.model_settings import ModelSettingsError, load_model_settings
from geoagent_harness.platform.configuration import selected_model

_SETTINGS = {
    'Non-local profiles remain blocked pending provider qualification': (
        'model_profile_blocked','Provider connection is blocked',
        'Select a loopback provider profile. Non-local profiles remain blocked pending provider qualification.'),
    'Provider configuration is invalid or unavailable': (
        'model_profile_invalid','Provider configuration is unavailable',
        'Check the workspace provider configuration; no connection or execution occurred.'),
    'Model credential is missing or invalid; check its configured reference': (
        'model_credentials_invalid','Model credential is unavailable',
        'Check the selected profile credential reference in the API process. Never paste keys into URLs, chat or profile fields.'),
    'MODEL_NAME is required': (
        'model_name_missing', 'No model selected in the API process',
        'Select an available model in Settings, or set MODEL_NAME in the launch terminal and restart the launcher.'),
    'MODEL_BASE_URL must be a valid HTTP or HTTPS URL': (
        'model_endpoint_invalid', 'Model endpoint configuration is invalid',
        'Use an HTTP(S) MODEL_BASE_URL for the process running the API, then restart it.'),
    'MODEL_BASE_URL must end with /v1': (
        'model_endpoint_invalid', 'Model endpoint must use the compatible /v1 API',
        'Set MODEL_BASE_URL to an OpenAI-compatible endpoint ending in /v1, then restart the launcher.'),
}
_CLIENT = {
    'model_timeout': ('The model request timed out', 'Warm the installed model, check other active model requests and MODEL_TIMEOUT_SECONDS, then retry this reasoning request. No automatic retry is performed.'),
    'model_unavailable': ('The API process cannot reach the model service', 'Check Ollama is running and that MODEL_BASE_URL is reachable from WSL or the container running this API. Restart after changing its environment.'),
    'model_authentication_failed': ('The model service rejected access', 'Check the selected profile and its environment or secret-file credential reference. Never put credentials in the endpoint URL.'),
    'model_data_class_blocked': ('Provider allowance blocks this request', 'Check the required data class and effective provider allowance in request diagnostics. Unclassified or changed context counts as raw. Select a permitted local profile; no model request was sent or automatically retried.'),
    'model_http_unavailable': ('The model service is temporarily unavailable', 'Check the model service logs, load and request limits before retrying this reasoning request.'),
    'model_http_error': ('The model service rejected the request', 'Check the exact installed model name and compatible /v1 endpoint. Inspect Ollama logs for the HTTP rejection; raw response bodies are not exposed here.'),
    'model_invalid_response': ('The model service returned an invalid response', 'Check the endpoint implements OpenAI-compatible chat completions and the installed model supports this request. Nothing was saved or executed.'),
}


def model_failure(error: ModelClientError | ModelSettingsError) -> dict:
    """Use allowlisted descriptions, never raw exception/endpoint/credential text."""
    if isinstance(error, ModelSettingsError):
        code, title, guidance = _SETTINGS.get(str(error), (
            'model_settings_invalid', 'Model settings are invalid',
            'Check MODEL_NAME, MODEL_BASE_URL, MODEL_TIMEOUT_SECONDS (0–600) and MODEL_MAX_TOKENS (1–32768) in the launch terminal, then restart.'))
    else:
        code = error.code if error.code in _CLIENT else 'model_request_failed'
        title, guidance = _CLIENT.get(code, (
            'Model request failed', 'Check the installed model, model service and API-process settings.'))
    return {'error': title, 'code': code, 'retry_guidance': guidance,
            'plan_saved': False, 'approval_performed': False, 'execution_performed': False}


def inspect_model_configuration(environ: Mapping[str, str] | None = None) -> dict:
    """Inspect current API process settings without contacting a model or revealing values."""
    values = os.environ if environ is None else environ
    result = {'schema_version': '1.0', 'status': 'configured',
              'model_name_set': bool(values.get('MODEL_NAME', '').strip() or (selected_model.get() if environ is None else None)),
              'model_base_url_set': bool(values.get('MODEL_BASE_URL', '').strip()),
              'model_called': False, 'connection_tested': False, 'execution_performed': False}
    try:
        settings = load_model_settings(environ)
        from geoagent_harness.platform.model_gateway.profiles import require_local
        require_local(settings)
    except ModelSettingsError as error:
        result.update(status='configuration_blocked', **model_failure(error))
        if str(error)=='MODEL_NAME is required':result['model_name_set']=False
    else:
        from geoagent_harness.platform.model_gateway.egress import allowance
        configured,effective,restricted=allowance(settings)
        result.update(model_name_set=bool(settings.model),model_base_url_set=True,
            provider_profile_id=settings.provider_profile_id,provider_kind=settings.provider_kind,
            provider_location=settings.provider_location,timeout_seconds=settings.timeout_seconds, max_tokens=settings.max_tokens,
            data_allowed=configured,effective_data_allowed=effective,nonlocal_restricted=restricted,egress_policy='context-parts-v1')
    return result
