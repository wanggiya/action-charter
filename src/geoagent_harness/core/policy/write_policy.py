"""Session-bound write availability. Model/context text never supplies a permit."""
from __future__ import annotations
from geoagent_harness.platform.storage.ledger_provider import ledger_repositories

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
import stat
import tempfile
import uuid

from geoagent_harness.platform.storage.ledger_contracts import LedgerStorageError
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


def _owner_directory():
    # Coordination only, not authority/history. Never unlink a lock inode while
    # processes may hold it. Its key stays stable across state-root changes.
    return Path(tempfile.gettempdir()) / f'actioncharter-write-owners-{os.getuid()}'


def _owner_fd(root, *, create=False, scope=None):
    directory = _owner_directory()
    if create:
        try: directory.mkdir(mode=0o700)
        except FileExistsError: pass
    try:
        metadata = directory.lstat()
    except FileNotFoundError:
        return None
    if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid!=os.getuid()
            or metadata.st_mode & 0o077):
        raise WritePolicyError('Project ownership directory is unsafe')
    descriptor=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        from geoagent_harness.platform.project_identity import ownership_scope
        identity=scope if scope is not None else ownership_scope(root)
        try:
            fd=os.open(identity+'.lock',os.O_NOFOLLOW|os.O_NONBLOCK|
                (os.O_CREAT|os.O_RDWR if create else os.O_RDONLY),0o600,dir_fd=descriptor)
        except FileNotFoundError:
            return None
    finally:
        os.close(descriptor)
    metadata=os.fstat(fd)
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid!=os.getuid()
            or metadata.st_nlink!=1 or metadata.st_mode & 0o077 or metadata.st_size>4096):
        os.close(fd)
        raise WritePolicyError('Project ownership lease is unsafe')
    return fd


def _state_identity(directory, root=None):
    if root is not None:
        from geoagent_harness.platform.project_identity import resolve_identity
        identity=resolve_identity(root)
        if identity:
            state=Path(directory).parent.stat()
            return hashlib.sha256(f'{identity.project_id}:{state.st_dev}:{state.st_ino}'.encode()).hexdigest()
    return hashlib.sha256(str(directory.resolve()).encode()).hexdigest()


def _owner_active(root, directory):
    fd=_owner_fd(root)
    if fd is None:return False
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            if os.pread(fd,4096,0) != _state_identity(directory,root).encode():
                raise WritePolicyError('Workspace storage changed during an active write session; restore its configuration and stop the launcher before migration')
            return True
        fcntl.flock(fd,fcntl.LOCK_UN)
        return False
    finally:os.close(fd)


@contextmanager
def _project_owner(root):
    from geoagent_harness.platform.workspace import WorkspaceLayout, WorkspaceError
    from geoagent_harness.platform.project_identity import ownership_scope
    try:layout=WorkspaceLayout.load(root)
    except WorkspaceError as error:raise WritePolicyError(str(error)) from error
    scope=ownership_scope(layout.project_root)
    fd=_owner_fd(layout.project_root,create=True,scope=scope)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise WritePolicyError('Another API owns this project write-policy session') from error
        if ownership_scope(layout.project_root)!=scope or WorkspaceLayout.load(root)!=layout:
            raise WritePolicyError('Project ownership changed during startup; stop and inspect its configuration')
        os.ftruncate(fd,0);os.write(fd,_state_identity(layout.state_root/'workflow-state',layout.project_root).encode());os.fsync(fd)
        yield
    finally:os.close(fd)


def _paths(root, create=False):
    root = Path(root).absolute()
    from geoagent_harness.platform.workspace import WorkspaceLayout, WorkspaceError
    try:
        if not root.exists() and not create:
            return root/'workflow-state/write-policy.sqlite3',root/'workflow-state/write-policy.lock'
        if root.is_symlink():raise WorkspaceError('Write policy directory cannot be a symlink')
        layout=WorkspaceLayout.load(root)
        root=layout.project_root
        directory=layout.runtime_path('workflow-state')
        _owner_active(root,directory)
        legacy=root/'workflow-state'
        if directory!=legacy:
            if legacy.is_symlink():raise WorkspaceError('Write policy directory cannot be a symlink')
            legacy_lease=legacy/'write-policy.lock'
            if legacy_lease.is_symlink():raise WorkspaceError('Write policy files cannot be symlinks')
            if legacy_lease.exists():
                fd=os.open(legacy_lease,os.O_RDONLY|os.O_NOFOLLOW)
                try:
                    try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    except BlockingIOError as error:
                        raise WritePolicyError('Another API owns the legacy project write-policy session; stop it before migration') from error
                    fcntl.flock(fd,fcntl.LOCK_UN)
                finally:os.close(fd)
            if (legacy/'write-policy.sqlite3').exists() and not (directory/'write-policy.sqlite3').exists():
                raise WorkspaceError('Write policy migration required; complete an offline SQLite backup before switching workspace storage')
    except WorkspaceError as error:
        raise WritePolicyError(str(error)) from error
    if create:
        directory.mkdir(mode=0o700,parents=True, exist_ok=True)
    db, lease = directory / 'write-policy.sqlite3', directory / 'write-policy.lock'
    for path in (db, lease, Path(str(db)+'-journal'), Path(str(db)+'-wal'), Path(str(db)+'-shm')):
        if path.is_symlink():
            raise WritePolicyError('Write policy files cannot be symlinks')
    return db, lease


@contextmanager
def _connect(root):
    db, _ = _paths(root)
    try:
        with ledger_repositories().write_policy(db) as unit:
            yield unit
    except (sqlite3.Error, LedgerStorageError) as error:
        raise WritePolicyError('Write policy storage unavailable; no write authorized') from error



def _live(root):
    db, lease = _paths(root)
    if not db.exists() or not lease.exists():
        if _owner_active(root,db.parent):
            raise WritePolicyError('Write policy session is starting or unavailable; no write dispatched')
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
        row = db.current()
    _, lease = _paths(root)
    if row is None or lease.read_text() != row['session_id']:
        raise WritePolicyError('Write policy session is starting or unavailable; no write dispatched')
    return {**dict(row), 'enabled': bool(row['enabled']), 'locked': bool(row['locked']),
            'active': True, 'execution_performed': False}


@contextmanager
def _session(root, *, enabled=False, locked=False):
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
            db.initialize(identity, enabled, locked)
        os.chmod(db_path, 0o600)
        yield snapshot(root)
    finally:
        os.close(fd)


@contextmanager
def session(root, *, enabled=False, locked=False):
    """Own the project independently of state location; restart revokes authority."""
    with _project_owner(root):
        with _session(root,enabled=enabled,locked=locked) as state:
            yield state


def update(root, request: PolicyUpdate):
    if not _live(root):
        raise WritePolicyError('No running API write-policy session')
    with _connect(root) as db:
        db.begin_write()
        row = db.current()
        if (row['session_id'], row['revision']) != (request.session_id, request.revision):
            db.rollback()
            raise WritePolicyError('Write policy changed. Refresh its status and try again.')
        if row['locked'] and request.enabled:
            db.rollback()
            raise WritePolicyError('Writes are administratively locked read-only')
        if bool(row['enabled']) != request.enabled:
            db.set_enabled(request.enabled)
            db.record_change(row['session_id'], row['revision']+1, request.enabled, 'operator')
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


def approval_policy_root(approval_root, project_root=None):
    """Use source identity only for its configured approval store.

    An unrelated explicit approval directory must not acquire authority in a
    project's live write session merely by supplying its registry/project root.
    """
    legacy = Path(approval_root).absolute().parent
    if project_root is None:
        return legacy
    from geoagent_harness.platform.workspace import runtime_store_path
    if Path(approval_root).absolute() == runtime_store_path(project_root,'approvals').absolute():
        return Path(project_root).resolve()
    return legacy


def bind(root, record, captured):
    if captured is None:
        return
    with _connect(root) as db:
        db.begin_write()
        row = db.current()
        if not row['enabled'] or (row['session_id'], row['revision']) != captured[1:]:
            db.rollback()
            raise WritePolicyError('Write availability changed during authorization. Review and authorize again.')
        db.bind(_digest(record), *captured[1:])
        db.commit()


def check(root, record):
    """Legacy decisions remain readable but cannot enter a managed write session."""
    current = ticket(root)
    db_path, _ = _paths(root)
    prior = None
    if db_path.exists():
        with _connect(root) as db:
            prior = db.approval_scope(_digest(record))
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
        if settings.enable_write_tools:
            from geoagent_harness.core.execution.actions import credential_request
            credential_request('approved_write_operation')
        yield settings
        return
    if _authority.get() != current:
        raise WritePolicyError('This write entry point requires fresh session-bound authorization through the workflow/recipe execution service.')
    # Ticket check is the dispatch boundary. OFF does not interrupt this operation.
    token = _operation.set(current)
    try:
        from geoagent_harness.core.execution.actions import credential_request
        credential_request('approved_write_operation')
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
            root=bound.arguments.get('project_root')
            if root is None:
                root=location.parent
                for candidate in (location,*location.parents):
                    if not candidate.is_dir():continue
                    db,_=_paths(candidate)
                    if db.exists():
                        root=candidate
                        break
            from geoagent_harness.platform.settings import load_settings
            with operation(load_settings().model_copy(update={'project_root':root})):
                return function(*bound.args,**bound.kwargs)
        return wrapped
    return decorate
