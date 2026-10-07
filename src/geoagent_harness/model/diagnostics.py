"""Safe process-configuration summaries and actionable model failure messages."""
from __future__ import annotations
import os
from collections.abc import Mapping
from .client import ModelClientError
from .settings import ModelSettingsError, load_model_settings

_SETTINGS = {
    'MODEL_NAME is required': (
        'model_name_missing', 'No model selected in the API process',
        'Set MODEL_NAME in the terminal that launches ActionCharter, then stop and restart that launcher.'),
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
    'model_authentication_failed': ('The model service rejected access', 'Check the endpoint and its access requirements. This client sends no model API key; select a compatible accessible endpoint rather than putting credentials in the URL.'),
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
              'model_name_set': bool(values.get('MODEL_NAME', '').strip()),
              'model_base_url_set': bool(values.get('MODEL_BASE_URL', '').strip()),
              'model_called': False, 'connection_tested': False, 'execution_performed': False}
    try:
        settings = load_model_settings(values)
    except ModelSettingsError as error:
        result.update(status='configuration_blocked', **model_failure(error))
    else:
        result.update(timeout_seconds=settings.timeout_seconds, max_tokens=settings.max_tokens)
    return result
