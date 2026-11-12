"""Opt-in local project identity. This trusted configuration never grants authority.

Filesystem object bindings deliberately reject copied markers. Cross-filesystem
copies and container path aliases need a separate verified provisioning protocol;
they are not inferred from matching UUIDs or user/model text.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from uuid import UUID, uuid4

IDENTITY_NAME = '.actioncharter-project.json'


class ProjectIdentityError(ValueError):
    pass


def path_scope(root):
    return hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()


def _object(path):
    path = Path(path)
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ProjectIdentityError('Project identity paths cannot contain symbolic links')
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode):
        raise ProjectIdentityError('Project identity requires existing directories')
    return [info.st_dev, info.st_ino]


def read_record(project):
    path = Path(project) / IDENTITY_NAME
    if not path.exists() and not path.is_symlink():
        return None
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_size > 4096 or info.st_mode & 0o022 or info.st_uid != os.getuid()):
        raise ProjectIdentityError('Project identity file is unsafe')
    try:
        value = json.loads(path.read_text())
        fields = {'version', 'project_id', 'source_root', 'state_root',
                  'source_object', 'state_object', 'legacy_scope'}
        if not isinstance(value, dict) or set(value) != fields or type(value['version']) is not int or value['version'] != 1:
            raise ValueError()
        if str(UUID(value['project_id'])) != value['project_id']:
            raise ValueError()
        for key in ('source_root', 'state_root'):
            p = Path(value[key])
            if not p.is_absolute() or p.as_posix() != value[key] or '..' in p.parts or '\x00' in value[key]:
                raise ValueError()
        for key in ('source_object', 'state_object'):
            if (not isinstance(value[key], list) or len(value[key]) != 2
                    or any(type(n) is not int or n < 0 for n in value[key])):
                raise ValueError()
        if (not isinstance(value['legacy_scope'], str) or len(value['legacy_scope']) != 64
                or any(c not in '0123456789abcdef' for c in value['legacy_scope'])):
            raise ValueError()
        return value
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError) as error:
        raise ProjectIdentityError('Invalid project identity record') from error


@dataclass(frozen=True)
class ProjectIdentity:
    project_id: str
    legacy_scope: str

    @property
    def scope(self):
        return hashlib.sha256(('project:' + self.project_id).encode()).hexdigest()


def resolve_identity(project, state_root=None):
    """Pure read; absent marker retains legacy behavior, invalid markers fail closed."""
    project = Path(project).absolute()
    record = read_record(project)
    if record is None:
        return None
    if _object(project) != record['source_object']:
        raise ProjectIdentityError('Copied project identity: initialize an independent project with fresh state')
    if str(project) != record['source_root']:
        raise ProjectIdentityError('Project moved; stop all processes and explicitly rebind its identity offline')
    state = Path(record['state_root']) if state_root is None else Path(state_root)
    if str(state) != record['state_root'] or _object(state) != record['state_object']:
        raise ProjectIdentityError('Project state binding changed; verified offline transition required')
    return ProjectIdentity(record['project_id'], record['legacy_scope'])


def ownership_scope(project):
    identity = resolve_identity(project)
    return identity.scope if identity else path_scope(project)


def owner_record(project, state):
    identity = resolve_identity(project)
    return ({'version': 2, 'project_id': identity.project_id}
            if identity else {'version': 1, 'project_sha256': path_scope(project)})


def status(project):
    from geoagent_harness.platform.workspace import WorkspaceLayout
    layout = WorkspaceLayout.load(project)
    identity = resolve_identity(layout.project_root, layout.state_root)
    return {'mode': 'stable' if identity else 'legacy_path',
            'project_id': identity.project_id if identity else None,
            'project_root': str(layout.project_root), 'state_root': str(layout.state_root),
            'execution_authority': False, 'execution_performed': False}


def initialize(project, *, offline=False):
    """Adopt existing state without modifying any historical artifact or SQLite row."""
    from geoagent_harness.platform.workspace import WorkspaceLayout, OWNER_NAME
    from geoagent_harness.platform.workspace_migration import _offline, _json_write
    layout = WorkspaceLayout.load(project)
    if not offline:
        raise ProjectIdentityError('Stop all processes and supply explicit offline confirmation')
    if read_record(layout.project_root) is not None:
        raise ProjectIdentityError('Project already has an identity; it will not be replaced')
    if not layout.state_root.exists():
        raise ProjectIdentityError('State directory must exist before identity adoption')
    record = {'version': 1, 'project_id': str(uuid4()), 'source_root': str(layout.project_root),
              'state_root': str(layout.state_root), 'source_object': _object(layout.project_root),
              'state_object': _object(layout.state_root), 'legacy_scope': path_scope(layout.project_root)}
    # Hold both the old path key and new ID key until publication finishes. Any
    # error leaves existing payloads intact; partial owner publication fails closed.
    from geoagent_harness.core.policy.write_policy import _owner_fd
    import fcntl
    identity = ProjectIdentity(record['project_id'], record['legacy_scope'])
    with _offline(layout.project_root, layout.state_root):
        _check_audits(layout.state_root, {record['legacy_scope']})
        fd = _owner_fd(layout.project_root, create=True, scope=identity.scope)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if read_record(layout.project_root) is not None:
                raise ProjectIdentityError('Identity appeared during adoption; inspect before retrying')
            _json_write(layout.project_root / IDENTITY_NAME, record)
            if layout.state_root != layout.project_root:
                _json_write(layout.state_root / OWNER_NAME, {'version': 2, 'project_id': identity.project_id})
        finally:
            os.close(fd)
    return status(project)


def _check_audits(state, scopes):
    """Read-only scope preflight, including the existing MCP audit namespace."""
    import sqlite3
    from contextlib import closing
    for relative in ('workflow-state/action-ledger.sqlite3', 'traces/.action-audit/action-ledger.sqlite3'):
        path = state / relative
        if not path.exists() and not path.is_symlink():
            continue
        for item in (path, *path.parents):
            if item.is_symlink():
                raise ProjectIdentityError('Unsafe action ledger during identity adoption')
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 64_000_000:
            raise ProjectIdentityError('Unsafe action ledger during identity adoption')
        try:
            with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
                if db.execute('PRAGMA quick_check').fetchone() != ('ok',):
                    raise ProjectIdentityError('Invalid action ledger during identity adoption')
                row = db.execute('SELECT project_sha256 FROM action_project_scope WHERE id=1').fetchone()
                if row is None or row[0] not in scopes:
                    raise ProjectIdentityError('Action ledger belongs to another project; adoption refused')
        except sqlite3.Error as error:
            raise ProjectIdentityError('Unreadable action ledger; adoption refused') from error


def rebind(project, *, offline=False):
    """Accept a same-filesystem rename only; never claim a copied source/state."""
    from geoagent_harness.platform.workspace import CONFIG_NAME, OWNER_NAME, RUNTIME_STORES, _no_links
    from geoagent_harness.platform.workspace_migration import _json_write
    from geoagent_harness.core.policy.write_policy import _owner_fd
    import fcntl
    if not offline:
        raise ProjectIdentityError('Stop all processes and supply explicit offline confirmation')
    project = Path(project).absolute()
    record = read_record(project)
    if record is None:
        raise ProjectIdentityError('No stable identity to rebind')
    old = Path(record['source_root'])
    if old == project or old.exists() or old.is_symlink():
        raise ProjectIdentityError('Old source location must be absent; copies cannot rebind ownership')
    if _object(project) != record['source_object']:
        raise ProjectIdentityError('Source filesystem object differs; copied identities cannot be rebound')
    old_state = Path(record['state_root'])
    state = project / old_state.relative_to(old) if old_state.is_relative_to(old) else old_state
    if _object(state) != record['state_object']:
        raise ProjectIdentityError('State filesystem object differs; cross-filesystem copies require separate provisioning')
    # Check the config at the new location without invoking the deliberately
    # failing normal resolver. Absolute old paths are never silently rewritten.
    config = project / CONFIG_NAME
    if config.exists() or config.is_symlink():
        if config.is_symlink() or config.stat().st_nlink != 1 or config.stat().st_size > 4096:
            raise ProjectIdentityError('Unsafe workspace configuration')
        try:
            value = json.loads(config.read_text())
            if (not isinstance(value, dict) or set(value) != {'version', 'state_root'}
                    or type(value['version']) is not int or value['version'] != 1
                    or not isinstance(value['state_root'], str) or not value['state_root'].strip()
                    or '\x00' in value['state_root'] or '..' in Path(value['state_root']).parts):
                raise ValueError()
            expected = Path(value['state_root'])
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            raise ProjectIdentityError('Invalid workspace configuration; rebind refused') from error
        expected = expected if expected.is_absolute() else project / expected
        if expected != state:
            raise ProjectIdentityError('Update the offline workspace location to its verified state directory first')
    elif state != project:
        raise ProjectIdentityError('Workspace configuration is missing')
    identity = ProjectIdentity(record['project_id'], record['legacy_scope'])
    if state != project:
        owner = state / OWNER_NAME
        _no_links(owner)
        if (not owner.is_file() or owner.stat().st_size > 4096 or owner.stat().st_nlink != 1
                or json.loads(owner.read_text()) != {'version': 2, 'project_id': identity.project_id}):
            raise ProjectIdentityError('State ownership differs; rebind refused')
    fd = _owner_fd(project, create=True, scope=identity.scope)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ProjectIdentityError('Project is in use; stop the launcher before rebinding') from error
        # Source inode + absent old location prove a rename; stable-ID lease
        # proves no managed owner is active. Existing authority is never renewed.
        from contextlib import ExitStack
        with ExitStack() as leases:
            for store in RUNTIME_STORES:
                directory = state / store
                if not directory.exists():
                    continue
                _no_links(directory)
                for lock in directory.rglob('*.lock'):
                    _no_links(lock)
                    handle = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    leases.callback(os.close, handle)
                    if not stat.S_ISREG(os.fstat(handle).st_mode):
                        raise ProjectIdentityError('Unsafe state lease; rebind refused')
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError as error:
                        raise ProjectIdentityError('State is in use; stop all writers before rebinding') from error
            _check_audits(state, {identity.scope, identity.legacy_scope})
            _json_write(project / IDENTITY_NAME, {**record, 'source_root': str(project), 'state_root': str(state)})
    finally:
        os.close(fd)
    return status(project)
