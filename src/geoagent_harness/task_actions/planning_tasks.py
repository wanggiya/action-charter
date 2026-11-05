"""Project-local task state. No models, tools, credentials or authority records.

Each conversation owns one private task/memory snapshot. SQLite commits both
records together; legacy JSON and former shared-task records remain preserved.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import re
from geoagent_harness.storage import repositories, RepositoryError
from geoagent_harness.storage.sqlite import connection as sqlite_connection, adapt_legacy

MAX_RECORD_BYTES = 2_000_000
MAX_RECORDS = 128
MAX_DATABASE_BYTES = 64_000_000
# Compatibility for private helpers receiving a raw legacy transaction.
as_transaction = adapt_legacy

IDENTITY = re.compile(r'^[a-f0-9]{32}$')


def _error(message):
    from .common import InterfaceApiError
    return InterfaceApiError(message)


def _identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise _error('Invalid planning task identity')
    return value


@contextmanager
def database(root: Path, *, write=False):
    """Legacy raw-connection API; production actions use transaction()."""
    try:
        with sqlite_connection(root, write=write) as connection:
            yield connection
    except RepositoryError as error:
        raise _error(str(error)) from error


@contextmanager
def transaction(root: Path, *, write=False):
    try:
        with repositories(root).transaction(write=write) as unit:
            yield unit
    except RepositoryError as error:
        raise _error(str(error)) from error


def _get(connection, table, identity):
    _identity(identity)
    if connection is None:
        return None
    raw = adapt_legacy(connection).records(table).get(identity)
    if raw is None:
        return None
    if len(raw.encode()) > MAX_RECORD_BYTES:
        raise _error('Planning task record exceeds its byte bound')
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get('task_id' if table in {'tasks','memories'} else 'conversation_id') != identity:
        raise _error('Planning task record identity changed')
    if table == 'memories' and ((value.get('context_usage') or {}).get('model_request') or {}).get('stage') == 'analytical_exploration':
        # One early analytical writer omitted provenance on its final user/assistant
        # pair. Repair only this known shape, corroborated by the same chat record.
        # Reading projects metadata in memory; it never edits history on disk.
        messages=value.get('messages',[])
        pair=messages[-2:]
        if (value.get('conversation_ids') == [identity] and len(pair)==2
                and [m.get('role') for m in pair]==['user','assistant']
                and all(m.get('task_id') is None and m.get('conversation_id') is None for m in pair)
                and all(m.get('task_id')==identity and m.get('conversation_id')==identity for m in messages[:-2])):
            own=_get(connection,'conversations',identity)
            if (own and own.get('analytical_session') and own.get('revision')==value.get('revision')
                    and own.get('messages')==messages):
                value['messages']=[*messages[:-2],*[dict(m,task_id=identity,conversation_id=identity) for m in pair]]
    if table in {'tasks','memories'}:
        from .conversation import PlanningTaskState
        value = PlanningTaskState.model_validate(value).model_dump(mode='json')
        if any(not IDENTITY.fullmatch(item) for item in value['conversation_ids']) or any(
            item['task_id'] != identity or item['conversation_id'] not in value['conversation_ids'] for item in value['messages']
        ):
            raise _error('Planning task message provenance changed')
    return value


def _put(connection, table, identity, value):
    _identity(identity)
    content = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if len(content.encode()) > MAX_RECORD_BYTES:
        raise _error('Planning task record exceeds its byte bound')
    if _get(connection, table, identity) is None and adapt_legacy(connection).records(table).count() >= MAX_RECORDS:
        raise _error('Planning task storage limit reached')
    adapt_legacy(connection).records(table).put(identity, content)


def conversation_record(root, identity):
    with transaction(root) as connection:
        return _get(connection, 'conversations', identity)


def task_record(root, identity):
    with transaction(root) as connection:
        task = _get(connection, 'memories', identity)
    if task is None:
        raise _error('Planning task is not available in this project')
    return task


def stored_conversations(root):
    with transaction(root) as connection:
        return [] if connection is None else [row.key for row in connection.records('conversations').entries()]


def private_state(state):
    """Project an old record without importing the former shared task's state."""
    state = json.loads(json.dumps(state))
    identity = state['conversation_id']
    title = (state['messages'][0]['content'] if state['messages'] else
             state['task_title'] or 'New conversation')[:160]
    state.update(active_task_id=identity, linked_task_ids=[identity], task_revision=state['revision'],
                 task_title=title)
    state['messages'] = [{**entry, 'task_id': identity, 'conversation_id': identity} for entry in state['messages']]
    return state


def _memory(state):
    return {'task_id': state['conversation_id'], 'title': state['task_title'] or 'New conversation',
            'revision': state['revision'], 'conversation_ids': [state['conversation_id']],
            **{key: state[key] for key in ('messages','planner_result','selected_skill_ids','allowed_skill_ids','context_usage')}}


def task_inventory(root):
    with transaction(root) as connection:
        rows = connection.records('memories').entries() if connection else []
        tasks = [_get(connection, 'memories', row.key) for row in rows]
    return {'tasks': [{'task_id': task['task_id'], 'title': task['title'], 'revision': task['revision'],
                      'conversation_ids': task['conversation_ids'], 'has_plan': task['planner_result'] is not None,
                      'input_paths': sorted({step['arguments'][key] for step in task['planner_result']['plan']['steps'] for key in ('path','right_path') if isinstance(step['arguments'].get(key), str)}) if task['planner_result'] else []}
                     for task in tasks], 'approval_performed': False, 'execution_performed': False}


def change_task(root, state, *, action, task_id=None, title=''):
    if action != 'bind_task_plan' or task_id != state['conversation_id']:
        raise _error('Each conversation is one task. Use New chat for separate work; cross-chat task linking is unavailable.')
    state = private_state(state)
    expected_revision = state['revision']
    state['revision'] += 1
    state['task_revision'] = state['revision']
    # Binding sends no model request. Keep the actual last completed receipt;
    # the interface separately describes the workflow for the next request.
    state['allowed_skill_ids'] = list(dict.fromkeys(step['skill'] for step in state['planner_result']['plan']['steps']))
    write_turn(root, state, expected_revision=expected_revision, expected_task_revision=expected_revision)
    return state


def write_turn(root, state, *, expected_revision, expected_task_revision, restored_view=None):
    """Save only this chat's transcript/plan; never read another chat's memory."""
    state.update(active_task_id=state['conversation_id'], linked_task_ids=[state['conversation_id']], task_revision=state['revision'])
    with transaction(root, write=True) as connection:
        latest = _get(connection, 'conversations', state['conversation_id'])
        memory = _get(connection, 'memories', state['conversation_id'])
        if (latest and latest['revision'] != expected_revision) or (memory and memory['revision'] != expected_task_revision):
            raise _error('Conversation changed; reload before sending')
        from .chat_history import archive
        archive(connection,latest)
        _put(connection, 'memories', state['conversation_id'], _memory(state))
        _put(connection, 'conversations', state['conversation_id'], state)
        archive(connection,state)
        if restored_view is not None:
            view={**restored_view,'revision':state['revision'],'conversation_id':state['conversation_id']}
            connection.records('dataset_views_v1').put(state['conversation_id']+':'+view['view'],json.dumps(view,separators=(',',':')))
            archive(connection,state,kind='view',view=view)
