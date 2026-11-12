"""Bounded Ollama discovery and project-local selection; no generation or pulls."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
import re

import httpx
from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.platform.model_settings import load_model_settings
from geoagent_harness.platform.configuration import selected_model, selected_reasoning
from contextvars import ContextVar
from typing import Literal
_selection_root=ContextVar('model_selection_root',default=None)


class CatalogError(ValueError):
    pass


class Selection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    model: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$')
    expected_revision: int = Field(ge=0)


def preference(root):
    from geoagent_harness.platform.storage.metadata import transaction
    with transaction(root) as unit:
        row = unit.setting('model_selection') if unit else None
        return row if row else {'model': None, 'revision': 0}


@contextmanager
def request_selection(root):
    """Pin selection across all model calls/corrections in this request."""
    from pathlib import Path
    key=str(Path(root).resolve())
    if _selection_root.get()==key:yield;return
    token=selected_model.set(preference(root)['model'])
    reasoning_token=selected_reasoning.set(reasoning_preference(root)['selection'])
    review_token=_review_timeout.set(review_timeout_preference(root)['seconds'])
    root_token=_selection_root.set(key)
    try:yield
    finally:
        selected_model.reset(token);selected_reasoning.reset(reasoning_token);_review_timeout.reset(review_token);_selection_root.reset(root_token)


def native_url(environ=None):
    values = dict(os.environ if environ is None else environ)
    # Discovery must work before a model has been selected.
    values['MODEL_NAME'] = 'discovery-placeholder'
    base = load_model_settings(values).base_url
    from urllib.parse import urlsplit
    parsed = urlsplit(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise CatalogError('Model discovery requires an endpoint without URL credentials or query parameters')
    return base[:-3]


def _get(client, url):
    try:
        with client.stream('GET', url) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content) > 1024 * 1024:
                    raise CatalogError('Model catalog exceeds its response budget')
        value = json.loads(content)
        if not isinstance(value, dict) or not isinstance(value.get('models'), list) or len(value['models']) > 256:
            raise CatalogError('Invalid model catalog')
        return value['models']
    except (httpx.HTTPError, ValueError) as error:
        if isinstance(error, CatalogError):
            raise
        raise CatalogError('Ollama model list is unavailable. Check the configured service; nothing was generated or downloaded.') from error


def catalog(root, *, client=None, environ=None):
    base = native_url(environ)
    if client is None:
        with httpx.Client(timeout=3, follow_redirects=False, trust_env=False) as connection:
            return catalog(root, client=connection, environ=environ)
    available = _get(client, base + '/api/tags')
    loaded_error = None
    try:
        loaded = _get(client, base + '/api/ps')
        running = {item.get('name', item.get('model')) for item in loaded if isinstance(item, dict)}
    except CatalogError:
        running = set()
        loaded_error = 'Loaded-model status unavailable'
    entries = []
    for item in available:
        if not isinstance(item, dict):
            raise CatalogError('Invalid model catalog entry')
        name = item.get('name', item.get('model'))
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', name):
            raise CatalogError('Invalid model name in catalog')
        size = item.get('size')
        entries.append({'name': name, 'size_bytes': size if type(size) is int and size >= 0 else None,
                        'loaded': name in running, 'compatibility': 'untested'})
    saved = preference(root)
    env = os.environ if environ is None else environ
    effective = saved['model'] or env.get('MODEL_NAME', '').strip() or None
    return {'models': entries, 'count': len(entries), 'selected_model': effective,
            'selection_source': 'project' if saved['model'] else 'environment',
            'revision': saved['revision'], 'selected_available': any(e['name'] == effective for e in entries),
            'review_timeout':review_timeout_preference(root),'reasoning':reasoning_preference(root,environ=environ),'loaded_status_error': loaded_error, 'model_called': False, 'execution_performed': False}


def select(root, request, *, client=None, environ=None):
    current = catalog(root, client=client, environ=environ)
    if not any(item['name'] == request.model for item in current['models']):
        raise CatalogError('Selected model is no longer in the available catalog. Refresh the list.')
    from geoagent_harness.platform.storage.metadata import transaction as database
    with database(root, write=True) as connection:
        row = connection.setting('model_selection')
        revision = row['revision'] if row else 0
        if revision != request.expected_revision:
            raise CatalogError('Model selection changed. Refresh before applying.')
        connection.save_setting('model_selection', request.model, revision + 1)
    return {**current, 'selected_model': request.model, 'selection_source': 'project',
            'revision': revision + 1, 'selected_available': True}


class ReasoningSelection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    selection:Literal['environment','provider','none','low','medium','high']
    expected_revision:int=Field(ge=0)


def reasoning_preference(root,*,environ=None):
    from geoagent_harness.platform.storage.metadata import transaction as database
    selection='environment';revision=0
    with database(root) as connection:
        row=connection.setting('model_reasoning_selection') if connection else None
        if row:selection,revision=row['selection'],row['revision']
    values=os.environ if environ is None else environ
    effective=(values.get('MODEL_REASONING_EFFORT','').strip() or None) if selection=='environment' else None if selection=='provider' else selection
    if effective not in {None,'none','low','medium','high'}:raise CatalogError('Invalid reasoning configuration')
    return {'selection':selection,'effective':effective,'revision':revision,'source':'environment' if selection=='environment' else 'project'}


def select_reasoning(root,request):
    from geoagent_harness.platform.storage.metadata import transaction as database
    with database(root,write=True) as connection:
        row=connection.setting('model_reasoning_selection');revision=row['revision'] if row else 0
        if revision!=request.expected_revision:raise CatalogError('Reasoning selection changed. Refresh before applying.')
        connection.save_setting('model_reasoning_selection',request.selection,revision+1)
    return {**reasoning_preference(root),'model_called':False,'execution_performed':False}

# Standalone post-run review budget; independent of planning and coordinated reports.
_review_timeout = ContextVar('outcome_review_timeout', default=None)

class ReviewTimeoutSelection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    seconds:int=Field(ge=5,le=180,strict=True)
    expected_revision:int=Field(ge=0)


def review_timeout_preference(root):
    from geoagent_harness.platform.storage.metadata import transaction as database
    with database(root) as connection:
        row=connection.setting('outcome_review_settings') if connection else None
        if row:return {**row,'source':'project'}
    return {'seconds':15,'revision':0,'source':'default'}


def review_timeout_seconds(root):
    from pathlib import Path
    if _selection_root.get()==str(Path(root).resolve()) and _review_timeout.get() is not None:
        return _review_timeout.get()
    return review_timeout_preference(root)['seconds']


def select_review_timeout(root,request):
    from geoagent_harness.platform.storage.metadata import transaction as database
    with database(root,write=True) as connection:
        row=connection.setting('outcome_review_settings');revision=row['revision'] if row else 0
        if revision!=request.expected_revision:raise CatalogError('Review timeout changed. Refresh before applying.')
        connection.save_setting('outcome_review_settings',request.seconds,revision+1)
    return {**review_timeout_preference(root),'model_called':False,'execution_performed':False}
