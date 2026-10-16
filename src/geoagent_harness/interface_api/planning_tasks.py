"""Project-local task state. No models, tools, credentials or authority records.

Each conversation owns one private task/memory snapshot. SQLite commits both
records together; legacy JSON and former shared-task records remain preserved.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sqlite3
import stat

MAX_RECORD_BYTES = 2_000_000
MAX_RECORDS = 128
MAX_DATABASE_BYTES = 64_000_000
IDENTITY = re.compile(r'^[a-f0-9]{32}$')


def _error(message):
    from .server import InterfaceApiError
    return InterfaceApiError(message)


def _identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise _error('Invalid planning task identity')
    return value


@contextmanager
def database(root: Path, *, write=False):
    root = Path(root).resolve(strict=True)
    directory = root / 'planner-workspace'
    if directory.is_symlink():
        raise _error('Planning task storage is unsafe')
    if write:
        directory.mkdir(mode=0o700, exist_ok=True)
    if not directory.exists():
        yield None
        return
    if not directory.is_dir() or directory.resolve().parent != root.resolve():
        raise _error('Planning task storage is outside the project')
    path = directory / 'tasks.sqlite3'
    for name in ('tasks.sqlite3', 'tasks.sqlite3-journal', 'tasks.sqlite3-wal', 'tasks.sqlite3-shm'):
        candidate = directory / name
        if candidate.is_symlink():
            raise _error('Planning task record is unsafe')
    if not path.exists():
        if not write:
            yield None
            return
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.close(fd)
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > MAX_DATABASE_BYTES:
        raise _error('Planning task database exceeds its storage contract')
    connection = None
    try:
        connection = sqlite3.connect(path.as_uri() + ('?mode=rw' if write else '?mode=ro'), uri=True, timeout=5)
        if write:
            connection.execute('PRAGMA synchronous=FULL')
            connection.execute(f'PRAGMA max_page_count={MAX_DATABASE_BYTES // 4096}')
            connection.execute('CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, value TEXT NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, value TEXT NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, value TEXT NOT NULL)')
            connection.commit()
            connection.execute('BEGIN IMMEDIATE')
        else:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'conversations', 'tasks'}.issubset(tables):
                if tables:
                    raise _error('Planning task database schema is incomplete')
                yield None
                return
        yield connection
        if write:
            connection.commit()
    except sqlite3.Error:
        if connection is not None:
            connection.rollback()
        raise _error('Planning task storage is unavailable; reload before retrying') from None
    finally:
        if connection is not None:
            connection.close()


def _get(connection, table, identity):
    _identity(identity)
    if connection is None:
        return None
    if table == 'memories' and not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memories'").fetchone():
        return None
    row = connection.execute(f'SELECT value FROM {table} WHERE id=?', (identity,)).fetchone()
    if not row:
        return None
    if len(row[0].encode()) > MAX_RECORD_BYTES:
        raise _error('Planning task record exceeds its byte bound')
    value = json.loads(row[0])
    if not isinstance(value, dict) or value.get('task_id' if table in {'tasks','memories'} else 'conversation_id') != identity:
        raise _error('Planning task record identity changed')
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
    if _get(connection, table, identity) is None and connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] >= MAX_RECORDS:
        raise _error('Planning task storage limit reached')
    connection.execute(f'INSERT INTO {table} VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET value=excluded.value', (identity, content))


def conversation_record(root, identity):
    with database(root) as connection:
        return _get(connection, 'conversations', identity)


def task_record(root, identity):
    with database(root) as connection:
        task = _get(connection, 'memories', identity)
    if task is None:
        raise _error('Planning task is not available in this project')
    return task


def stored_conversations(root):
    with database(root) as connection:
        return [] if connection is None else [row[0] for row in connection.execute('SELECT id FROM conversations ORDER BY rowid DESC')]


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
    with database(root) as connection:
        exists = connection is not None and connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memories'").fetchone()
        rows = list(connection.execute('SELECT id FROM memories ORDER BY rowid DESC')) if exists else []
        tasks = [_get(connection, 'memories', row[0]) for row in rows]
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


def write_turn(root, state, *, expected_revision, expected_task_revision):
    """Save only this chat's transcript/plan; never read another chat's memory."""
    state.update(active_task_id=state['conversation_id'], linked_task_ids=[state['conversation_id']], task_revision=state['revision'])
    with database(root, write=True) as connection:
        latest = _get(connection, 'conversations', state['conversation_id'])
        memory = _get(connection, 'memories', state['conversation_id'])
        if (latest and latest['revision'] != expected_revision) or (memory and memory['revision'] != expected_task_revision):
            raise _error('Conversation changed; reload before sending')
        _put(connection, 'memories', state['conversation_id'], _memory(state))
        _put(connection, 'conversations', state['conversation_id'], state)
