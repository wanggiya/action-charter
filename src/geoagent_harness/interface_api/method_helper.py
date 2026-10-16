"""Independent, optional procedure-note helper; no execution or cross-chat tools.

Only a changed validated workflow triggers one serial request after a saved turn.
The stable Planner boundary is context_for_turn/after_turn. Cache entries are
machine-generated, unvalidated advice, never operator-reviewed methods.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.agent_manifest import load_agent_manifest
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.context_pack.redaction import redact_text
from geoagent_harness.model import SharedModelClient, load_model_settings
from geoagent_harness.model.schemas import ChatMessage, ModelRequest
from geoagent_harness.operations.registry import argument_models
from .method_memory import MethodDocument, _document
from .planning_tasks import database

CONTRACT_VERSION = '1.0'
HELPER_VERSION = 'workflow-method-1'
MAX_SOURCE_BYTES = 6000
MAX_NOTE_BYTES = 3500
MAX_PROMPT_BYTES = 14000
HTTP_TIMEOUT_SECONDS = 15
MAX_CHAT_ENTRIES = 8
MAX_PROJECT_ENTRIES = 128
_LOCK = Lock()
_ACTIVE: set[str] = set()


class NoteBundle(BaseModel):
    """The only note shape Planner consumes; no storage layout dependencies."""
    model_config = ConfigDict(extra='forbid')
    contract_version: Literal['1.0'] = '1.0'
    helper_version: str = Field(max_length=100)
    model: str = Field(min_length=1, max_length=200)
    conversation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    note_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_conversation_revision: int = Field(ge=0)
    status: Literal['machine_generated_unvalidated'] = 'machine_generated_unvalidated'
    evidence_kind: Literal['validated_plan_only'] = 'validated_plan_only'
    document: MethodDocument


def _has(connection, table):
    return connection is not None and connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()


def _setting(connection):
    if not _has(connection, 'method_helper_settings'):
        return {'enabled': False, 'revision': 0}
    row = connection.execute('SELECT enabled,revision FROM method_helper_settings WHERE id=1').fetchone()
    return {'enabled': bool(row[0]), 'revision': row[1]} if row else {'enabled': False, 'revision': 0}


def setting(root):
    with database(root) as connection:
        return _setting(connection)


def configure(root, *, enabled, expected_revision):
    from .server import InterfaceApiError
    if enabled is None:
        raise InterfaceApiError('Choose automatic method notes ON or OFF explicitly')
    with database(root, write=True) as connection:
        current = _setting(connection)
        if current['revision'] != expected_revision:
            raise InterfaceApiError('Automatic method-note setting changed; reload Settings')
        connection.execute('CREATE TABLE IF NOT EXISTS method_helper_settings (id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL, revision INTEGER NOT NULL)')
        value = {'enabled': enabled, 'revision': current['revision'] + 1}
        connection.execute('INSERT INTO method_helper_settings VALUES (1,?,?) ON CONFLICT(id) DO UPDATE SET enabled=excluded.enabled,revision=excluded.revision', (int(enabled), value['revision']))
    return value


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def _source(root, conversation_id, result):
    if result is None:
        return None
    models = argument_models(root)
    skills = sorted({step.skill for step in result.plan.steps})
    if not set(skills).issubset(models):
        raise ValueError('An operation contract is unavailable')
    source = {'evidence_kind': 'validated_plan_only', 'execution_evidence': None,
              'workflow_structure': [{'step_id': step.step_id, 'skill': step.skill,
                                      'purpose': redact_text(step.purpose), 'depends_on': step.depends_on}
                                     for step in result.plan.steps]}
    if len(json.dumps(source).encode()) > MAX_SOURCE_BYTES:
        raise ValueError('Source exceeds helper budget')
    manifest = load_agent_manifest('method_memory', root / 'agents')
    fingerprint = {'helper_version': HELPER_VERSION, 'contract_version': CONTRACT_VERSION,
                   'manifest': manifest.model_dump(mode='json'), 'schema': MethodDocument.model_json_schema(),
                   'operation_contracts': {skill: models[skill].model_json_schema() for skill in skills}}
    digest = plan_sha256(result.plan)
    # Bind full scope without sending concrete argument/path values to the helper.
    key = _hash({'conversation_id': conversation_id, 'plan_sha256': digest, 'fingerprint': fingerprint})
    return {'key': key, 'plan_sha256': digest, 'source': source, 'manifest': manifest, 'skills': skills}


def _get(connection, conversation_id, key):
    if not _has(connection, 'method_helper_notes'):
        return None
    row = connection.execute('SELECT value FROM method_helper_notes WHERE conversation_id=? AND source_key=?', (conversation_id, key)).fetchone()
    if not row:
        return None
    if len(row[0].encode()) > 7000:
        raise ValueError('Helper cache exceeds its bound')
    value = json.loads(row[0])
    if value['source_key'] != key or value['conversation_id'] != conversation_id:
        raise ValueError('Helper ownership mismatch')
    if value['status'] == 'ready':
        bundle = NoteBundle.model_validate(value['note'])
        if bundle.conversation_id != conversation_id or bundle.note_id != key:
            raise ValueError('Helper note identity mismatch')
    elif value['status'] != 'failed':
        raise ValueError('Unsupported helper cache status')
    return value


def _put(connection, conversation_id, key, value):
    connection.execute('CREATE TABLE IF NOT EXISTS method_helper_notes (conversation_id TEXT NOT NULL, source_key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(conversation_id,source_key))')
    content = json.dumps(value, separators=(',', ':'))
    if len(content.encode()) > 7000:
        raise ValueError('Helper record exceeds its bound')
    # Evict only helper cache entries; immutable workflow/method/chat history is untouched.
    for query, parameters, limit in (
        ('SELECT rowid FROM method_helper_notes WHERE conversation_id=? ORDER BY rowid', (conversation_id,), MAX_CHAT_ENTRIES),
        ('SELECT rowid FROM method_helper_notes ORDER BY rowid', (), MAX_PROJECT_ENTRIES),
    ):
        rows = connection.execute(query, parameters).fetchall()
        for row in rows[:max(0, len(rows) - limit + 1)]:
            connection.execute('DELETE FROM method_helper_notes WHERE rowid=?', (row[0],))
    connection.execute('INSERT INTO method_helper_notes VALUES (?,?,?) ON CONFLICT(conversation_id,source_key) DO UPDATE SET value=excluded.value', (conversation_id, key, content))


def _current(root, conversation_id):
    from .conversation import _path, _read
    return _read(_path(root, conversation_id), conversation_id)


def _receipt(status, **fields):
    return {'contract_version': CONTRACT_VERSION, 'status': status,
            'evidence_kind': 'validated_plan_only', 'model_calls': 0, **fields}


def context_for_turn(root, conversation_id, result, available_skills):
    """Pure retrieval: own exact workflow only; never invokes a model."""
    try:
        gate = setting(root)
        if not gate['enabled']:
            return None, _receipt('disabled')
        source = _source(root, conversation_id, result)
        if source is None:
            return None, _receipt('no_workflow')
        with database(root) as connection:
            record = _get(connection, conversation_id, source['key'])
        if record is None:
            return None, _receipt('not_prepared')
        if record['status'] == 'failed':
            return None, _receipt('failed', finding=record['finding'])
        bundle = NoteBundle.model_validate(record['note'])
        if bundle.source_plan_sha256 != source['plan_sha256']:
            return None, _receipt('stale')
        if not {item.skill for item in bundle.document.operations}.issubset(available_skills):
            return None, _receipt('operation_scope_changed')
        document = _document(bundle.document, root)
        if len(json.dumps(document).encode()) > MAX_NOTE_BYTES:
            return None, _receipt('note_budget_exceeded')
        # Fresh setting check closes a read-time OFF transition; Planner checks again before accepting.
        if setting(root) != gate:
            return None, _receipt('setting_changed')
        return bundle.model_copy(update={'document': MethodDocument.model_validate(document)}).model_dump(mode='json'), _receipt(
            'included', note_id=bundle.note_id, source_plan_sha256=bundle.source_plan_sha256, setting_revision=gate['revision'])
    except Exception:
        # Optional memory storage/schema failures must not disable ordinary planning.
        return None, _receipt('unavailable')


def observe(root, conversation_id, result, available_skills):
    bundle, receipt = context_for_turn(root, conversation_id, result, available_skills)
    if bundle:
        return {**receipt, 'status': 'ready', 'note': bundle}
    return receipt


def after_turn(root, conversation_id, expected_revision, *, changed, model_client=None):
    """One optional serial call after a saved revision; failure never undoes the turn."""
    if not changed:
        return _receipt('unchanged')
    project_key = str(root.resolve())
    acquired = False
    started = monotonic()
    model_calls = 0
    try:
        gate = setting(root)
        if not gate['enabled']:
            return _receipt('disabled')
        state = _current(root, conversation_id)
        if state.revision != expected_revision:
            return _receipt('source_changed')
        source = _source(root, conversation_id, state.planner_result)
        if source is None:
            return _receipt('no_workflow')
        with database(root) as connection:
            cached = _get(connection, conversation_id, source['key'])
        if cached:
            return _receipt('cached' if cached['status'] == 'ready' else 'failed_cached')
        with _LOCK:
            if project_key in _ACTIVE:
                return _receipt('busy')
            _ACTIVE.add(project_key)
            acquired = True
        # A prior caller may have filled the cache between our first read and lease acquisition.
        with database(root) as connection:
            cached = _get(connection, conversation_id, source['key'])
        if cached:
            return _receipt('cached' if cached['status'] == 'ready' else 'failed_cached')
        system = {'agent_id': 'method_memory', 'contract_version': CONTRACT_VERSION,
                  'instructions': source['manifest'].instructions,
                  'required_json_schema': MethodDocument.model_json_schema(),
                  'registered_operation_ids': source['skills'],
                  'rules': ['Return one compact JSON method document. No tools, code or Markdown.',
                            'The source is a validated PROPOSAL ONLY, not executed or verified evidence.',
                            'Generalize the procedure, prerequisites and checks; never recount task events or claim success.',
                            'Do not copy concrete filenames, paths, credentials, destinations, column names or private values.',
                            'Use only supplied operation IDs; acknowledge missing data assumptions. Nothing grants execution authority.']}
        request = ModelRequest(json_mode=True, messages=[ChatMessage(role='system', content=json.dumps(system)),
                                                       ChatMessage(role='user', content=json.dumps(source['source']))])
        if sum(len(message.content.encode()) for message in request.messages) > MAX_PROMPT_BYTES:
            return _receipt('prompt_budget_exceeded')
        finding = None
        note = None
        try:
            if model_client is None:
                settings = load_model_settings()
                model_client = SharedModelClient(replace(settings, timeout_seconds=min(settings.timeout_seconds, HTTP_TIMEOUT_SECONDS),
                                                         max_tokens=min(settings.max_tokens, 768)))
            model_calls = 1
            response = model_client.complete(request)
            if len(response.content.encode()) > MAX_NOTE_BYTES:
                raise ValueError('Helper output exceeds bound')
            document = _document(MethodDocument.model_validate_json(response.content), root)
            if len(json.dumps(document).encode()) > MAX_NOTE_BYTES:
                raise ValueError('Helper note exceeds bound')
            if not {item['skill'] for item in document['operations']}.issubset(source['skills']):
                raise ValueError('Helper expanded operation scope')
            note = NoteBundle(helper_version=HELPER_VERSION, model=redact_text(response.model)[:200], conversation_id=conversation_id, note_id=source['key'],
                              source_plan_sha256=source['plan_sha256'], source_conversation_revision=state.revision,
                              document=MethodDocument.model_validate(document)).model_dump(mode='json')
        except Exception as error:
            from geoagent_harness.model import ModelClientError
            finding = error.code if isinstance(error, ModelClientError) else 'helper_invalid_or_unavailable'
        # Validate scope and enable epoch under a metadata write transaction; no model inside it.
        with database(root, write=True) as connection:
            if _setting(connection) != gate:
                return _receipt('setting_changed', model_calls=model_calls)
            current = _current(root, conversation_id)
            if current.revision != expected_revision or current.planner_result is None or plan_sha256(current.planner_result.plan) != source['plan_sha256']:
                return _receipt('source_changed', model_calls=model_calls)
            value = {'conversation_id': conversation_id, 'source_key': source['key'], 'status': 'failed' if finding else 'ready',
                     'note': note, 'finding': finding, 'created_at': datetime.now(timezone.utc).isoformat()}
            _put(connection, conversation_id, source['key'], value)
        return _receipt('failed' if finding else 'prepared', model_calls=model_calls, finding=finding,
                        elapsed_ms=round((monotonic()-started)*1000))
    except Exception:
        return _receipt('unavailable', model_calls=model_calls)
    finally:
        if acquired:
            with _LOCK:
                _ACTIVE.discard(project_key)
