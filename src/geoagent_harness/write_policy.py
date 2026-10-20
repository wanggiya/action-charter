"""Session-bound write availability. Model/context text never supplies a permit."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import fcntl
import hashlib
import inspect
import json
import os
from pathlib import Path
import sqlite3
import uuid

from pydantic import BaseModel, ConfigDict, Field


class WritePolicyError(ValueError):
    pass


class PolicyUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    enabled: bool
    session_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    revision: int = Field(ge=0)


_issuance: ContextVar[tuple | None] = ContextVar('write_issuance', default=None)
_authority: ContextVar[tuple | None] = ContextVar('write_authority', default=None)
_operation: ContextVar[tuple | None] = ContextVar('write_operation', default=None)


def _paths(root, create=False):
    root = Path(root).absolute()
    directory = root / 'workflow-state'
    if root.is_symlink() or directory.is_symlink():
        raise WritePolicyError('Write policy directory cannot be a symlink')
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    db, lease = directory / 'write-policy.sqlite3', directory / 'write-policy.lock'
    for path in (db, lease, Path(str(db)+'-journal'), Path(str(db)+'-wal'), Path(str(db)+'-shm')):
        if path.is_symlink():
            raise WritePolicyError('Write policy files cannot be symlinks')
    return db, lease


@contextmanager
def _connect(root):
    db, _ = _paths(root)
    try:
        connection = sqlite3.connect(db, timeout=10, isolation_level=None)
    except sqlite3.Error as error:
        raise WritePolicyError('Write policy storage unavailable; no write authorized') from error
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    except sqlite3.Error as error:
        raise WritePolicyError('Write policy storage unavailable; no write authorized') from error
    finally:
        connection.close()


def _live(root):
    db, lease = _paths(root)
    if not db.exists() or not lease.exists():
        return False
    fd = os.open(lease, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def snapshot(root):
    if not _live(root):
        return None
    with _connect(root) as db:
        row = db.execute('SELECT * FROM policy WHERE id=1').fetchone()
    _, lease = _paths(root)
    if row is None or lease.read_text() != row['session_id']:
        raise WritePolicyError('Write policy session is starting or unavailable; no write dispatched')
    return {**dict(row), 'enabled': bool(row['enabled']), 'locked': bool(row['locked']),
            'active': True, 'execution_performed': False}


@contextmanager
def session(root, *, enabled=False, locked=False):
    """One owning API per project. A new process session revokes old bindings."""
    db_path, lease = _paths(root, create=True)
    fd = os.open(lease, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise WritePolicyError('Another API owns this project write-policy session') from error
        identity = uuid.uuid4().hex
        os.ftruncate(fd, 0)
        os.write(fd, identity.encode())
        os.fsync(fd)
        with _connect(root) as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS policy(
                id INTEGER PRIMARY KEY CHECK(id=1),session_id TEXT NOT NULL,
                revision INTEGER NOT NULL,enabled INTEGER NOT NULL,locked INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS authority(
                digest TEXT PRIMARY KEY,session_id TEXT NOT NULL,revision INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS changes(
                session_id TEXT,revision INTEGER,enabled INTEGER,event TEXT);''')
            db.execute('INSERT OR REPLACE INTO policy VALUES(1,?,0,?,?)', (identity, int(enabled and not locked), int(locked)))
            db.execute('INSERT INTO changes VALUES(?,0,?,?)', (identity, int(enabled and not locked), 'startup'))
        os.chmod(db_path, 0o600)
        yield snapshot(root)
    finally:
        os.close(fd)


def update(root, request: PolicyUpdate):
    if not _live(root):
        raise WritePolicyError('No running API write-policy session')
    with _connect(root) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM policy WHERE id=1').fetchone()
        if (row['session_id'], row['revision']) != (request.session_id, request.revision):
            db.rollback()
            raise WritePolicyError('Write policy changed. Refresh its status and try again.')
        if row['locked'] and request.enabled:
            db.rollback()
            raise WritePolicyError('Writes are administratively locked read-only')
        if bool(row['enabled']) != request.enabled:
            db.execute('UPDATE policy SET enabled=?,revision=revision+1 WHERE id=1', (int(request.enabled),))
            db.execute('INSERT INTO changes VALUES(?,?,?,?)', (row['session_id'], row['revision']+1, int(request.enabled), 'operator'))
        db.commit()
    return snapshot(root)


def effective(settings, root=None):
    state = snapshot(root or settings.project_root)
    if state is None:
        return settings
    return settings.model_copy(update={'project_root': Path(root or settings.project_root), 'enable_write_tools': state['enabled']})


def ticket(root):
    state = snapshot(root)
    if state is None:
        return None
    if not state['enabled']:
        raise WritePolicyError('Write operations are OFF. Enable them in Settings, then authorize the exact workflow.')
    captured = (str(Path(root).resolve()), state['session_id'], state['revision'])
    if _issuance.get() is not None and _issuance.get() != captured:
        raise WritePolicyError('Write policy changed during review. Review and Authorize again.')
    return captured


def _digest(record):
    return hashlib.sha256(json.dumps(record.model_dump(mode='json'), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def bind(root, record, captured):
    if captured is None:
        return
    with _connect(root) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM policy WHERE id=1').fetchone()
        if not row['enabled'] or (row['session_id'], row['revision']) != captured[1:]:
            db.rollback()
            raise WritePolicyError('Write availability changed during authorization. Review and authorize again.')
        db.execute('INSERT INTO authority VALUES(?,?,?)', (_digest(record), *captured[1:]))
        db.commit()


def check(root, record):
    """Legacy decisions remain readable but cannot enter a managed write session."""
    current = ticket(root)
    db_path, _ = _paths(root)
    prior = None
    if db_path.exists():
        with _connect(root) as db:
            prior = db.execute('SELECT session_id,revision FROM authority WHERE digest=?', (_digest(record),)).fetchone()
    if current is None:
        if prior:
            raise WritePolicyError('This approval belongs to an ended API session. Record fresh authorization in a running session.')
        return None  # Standalone legacy CLI still requires its explicit startup write setting.
    if prior is None or tuple(prior) != current[1:]:
        raise WritePolicyError('Write authorization is missing or stale for this session. Review and Authorize again.')
    return current


@contextmanager
def authority(root, record):
    token = _authority.set(check(root, record))
    try:
        yield
    finally:
        _authority.reset(token)


@contextmanager
def operation(settings):
    root = settings.project_root
    active = _operation.get()
    if active and active[0] == str(Path(root).resolve()):
        yield settings.model_copy(update={'enable_write_tools': True})
        return
    current = ticket(root)
    if current is None:
        yield settings
        return
    if _authority.get() != current:
        raise WritePolicyError('This write entry point requires fresh session-bound authorization through the workflow/recipe execution service.')
    # Ticket check is the dispatch boundary. OFF does not interrupt this operation.
    token = _operation.set(current)
    try:
        yield settings.model_copy(update={'enable_write_tools': True})
    finally:
        _operation.reset(token)


def guarded(function):
    """Guard low-level mutators, including explicit/cached settings and direct calls."""
    signature = inspect.signature(function)
    @wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        settings = bound.arguments['settings']
        with operation(settings) as active:
            bound.arguments['settings'] = active
            return function(*bound.args, **bound.kwargs)
    return wrapped


@contextmanager
def issuance(root, expected):
    captured = ticket(root)
    if expected and (captured is None or captured[1:] != (expected['session_id'],expected['revision'])):
        raise WritePolicyError('Write policy changed during review. Review and Authorize again.')
    token = _issuance.set(captured)
    try:
        yield
    finally:
        _issuance.reset(token)


def root_guarded(parameter):
    def decorate(function):
        signature=inspect.signature(function)
        @wraps(function)
        def wrapped(*args,**kwargs):
            bound=signature.bind(*args,**kwargs);bound.apply_defaults()
            location=Path(bound.arguments[parameter]).absolute()
            root=location.parent
            for candidate in (location,*location.parents):
                db,_=_paths(candidate)
                if db.exists():
                    root=candidate
                    break
            from geoagent_harness.mcp_server.settings import load_settings
            with operation(load_settings().model_copy(update={'project_root':root})):
                return function(*bound.args,**bound.kwargs)
        return wrapped
    return decorate
