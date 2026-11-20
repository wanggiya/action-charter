"""Explicit offline recovery of legacy bindings after mount device renumbering.

Only the identity marker is replaced. UUIDs, payloads, ledger claims, configuration
and external ownership remain untouched. This protocol cannot prove that a legacy
volume was not cloned; its first stable filesystem enrollment requires owner review.
"""
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

from geoagent_harness.platform import project_identity as identity
from geoagent_harness.platform.workspace import (
    CONFIG_NAME, OWNER_NAME, RUNTIME_STORES, _configured_state, _no_links,
)
from geoagent_harness.platform.workspace_migration import (
    MANIFEST, MAX_BYTES, _hash, _json_write, _sql_copy, _sql_read, inventory,
)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _metadata(path, *, optional=False, limit=4096):
    _no_links(path)
    if optional and not path.exists():
        return None
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit
            or info.st_uid != os.getuid() or info.st_mode & 0o022):
        raise identity.ProjectIdentityError('Unsafe recovery configuration or ownership metadata')
    return path.read_bytes().decode('utf-8')


def _snapshot(project, backup, *, backup_created=False):
    project, backup = Path(project).absolute(), Path(backup).absolute()
    identity._object(project)  # Reject aliases before resolving paths.
    record = identity.read_record(project)
    if record is None or record['version'] != 1:
        raise identity.ProjectIdentityError('Recovery requires an existing legacy version-1 identity')
    state = _configured_state(project)
    if str(project) != record['source_root'] or str(state) != record['state_root']:
        raise identity.ProjectIdentityError('Recovery requires the exact recorded source and state paths')
    source_object, state_object = identity._object(project), identity._object(state)
    if source_object[1] != record['source_object'][1] or state_object[1] != record['state_object'][1]:
        raise identity.ProjectIdentityError('Filesystem object differs; copied source/state cannot recover')
    if source_object == record['source_object'] and state_object == record['state_object']:
        raise identity.ProjectIdentityError('No device-number change to recover')
    updated = {**record, 'version': 2, 'source_object': source_object, 'state_object': state_object,
               'source_filesystem': identity._filesystem(project),
               'state_filesystem': identity._filesystem(state)}
    metadata = {IDENTITY: _metadata(project / IDENTITY),
                CONFIG_NAME: _metadata(project / CONFIG_NAME, optional=True),
                MANIFEST: _metadata(state / MANIFEST, optional=True, limit=64 * 1024**2)}
    if state != project:
        metadata[OWNER_NAME] = _metadata(state / OWNER_NAME)
        if json.loads(metadata[OWNER_NAME]) != {'version': 2, 'project_id': record['project_id']}:
            raise identity.ProjectIdentityError('State ownership differs; recovery refused')
    _no_links(backup)
    if any(backup == root or backup in root.parents or backup.is_relative_to(root)
           for root in (project, state)):
        raise identity.ProjectIdentityError('Backup must be outside the source project and state trees')
    if backup.exists() and not backup_created:
        raise identity.ProjectIdentityError('Backup destination must be new; existing backups are never replaced')
    if not backup.parent.is_dir():
        raise identity.ProjectIdentityError('Backup parent must already exist')
    parent = backup.parent.stat()
    if parent.st_uid != os.getuid() or parent.st_mode & 0o022:
        raise identity.ProjectIdentityError('Backup parent must be owner-controlled and not group/world writable')
    contents = inventory(state)
    # SQLite payloads can change solely in WAL. Bind the preview to those bytes
    # too; SHM is coordination, never a portable database backup.
    sidecars, sidecar_bytes = {}, 0
    for name in contents['files']:
        if not name.endswith('.sqlite3'):
            continue
        for suffix in ('-wal', '-journal'):
            path = state / (name + suffix)
            _no_links(path)
            if path.exists():
                if path.stat().st_size + contents['bytes'] + sidecar_bytes > MAX_BYTES:
                    raise identity.ProjectIdentityError('Recovery backup exceeds byte limit')
                digest, size = _hash(path)
                sidecars[name + suffix] = {'sha256': digest, 'bytes': size}
                sidecar_bytes += size
    return {'previous_identity': record, 'updated_identity': updated, 'metadata': metadata,
            'inventory': contents, 'sqlite_sidecars': sidecars, 'backup_root': str(backup)}


IDENTITY = identity.IDENTITY_NAME


def preview(project, backup):
    """Read and hash existing state; no marker, backup, lease or authority created."""
    snapshot = _snapshot(project, backup)
    record, updated = snapshot['previous_identity'], snapshot['updated_identity']
    return {'status': 'review_required', 'project_id': record['project_id'],
            'project_root': record['source_root'], 'state_root': record['state_root'],
            'recorded_devices': [record[key][0] for key in ('source_object', 'state_object')],
            'observed_devices': [updated[key][0] for key in ('source_object', 'state_object')],
            'matching_paths_and_inodes': True, 'backup_root': snapshot['backup_root'],
            'file_count': snapshot['inventory']['file_count'], 'bytes': snapshot['inventory']['bytes'],
            'preview_sha256': _digest(snapshot), 'execution_authority': False, 'execution_performed': False,
            'limitation': 'Legacy records have no prior filesystem ID. Owner must confirm the original '
                          'workspace, not a restored/cloned volume. No automatic recovery is permitted.'}


@contextmanager
def _offline(project, state, record):
    from geoagent_harness.core.policy.write_policy import _owner_fd
    stable = identity.ProjectIdentity(record['project_id'], record['legacy_scope'])
    with ExitStack() as leases:
        # Explicit scopes avoid invoking the normal resolver while it is blocked.
        for scope in sorted({stable.scope, record['legacy_scope'], identity.path_scope(project)}):
            fd = _owner_fd(project, create=True, scope=scope)
            leases.callback(os.close, fd)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise identity.ProjectIdentityError('Project is in use; stop all processes before recovery') from error
        for store in sorted(RUNTIME_STORES):
            directory = state / store
            _no_links(directory)
            if not directory.exists():
                continue
            for path in directory.rglob('*.lock'):
                _no_links(path)
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                leases.callback(os.close, fd)
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise identity.ProjectIdentityError('Unsafe state lease; recovery refused')
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise identity.ProjectIdentityError('State is in use; stop all writers before recovery') from error
        identity._check_audits(state, {stable.scope, stable.legacy_scope})
        yield


def _copy_state(state, backup, contents):
    payload = backup / 'state'
    payload.mkdir(mode=0o700)
    for name in contents['directories']:
        (payload / name).mkdir(mode=0o700, parents=True, exist_ok=True)
    sql = {}
    for name in contents['files']:
        origin, target = state / name, payload / name
        if origin.suffix == '.sqlite3':
            sql[name] = _sql_copy(origin, target)
        else:
            fd = os.open(origin, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as source, target.open('xb') as destination:
                target.chmod(0o600)
                copied_bytes = 0
                while chunk := source.read(1024**2):
                    copied_bytes += len(chunk)
                    if copied_bytes > contents['files'][name]['bytes']:
                        raise identity.ProjectIdentityError('Source grew during backup; identity unchanged')
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
    copied = inventory(payload)
    if copied['directories'] != contents['directories'] or copied['files'].keys() != contents['files'].keys():
        raise identity.ProjectIdentityError('Backup inventory differs; identity unchanged')
    for name, expected in contents['files'].items():
        if name in sql:
            if _sql_read(state / name) != sql[name] or _sql_read(payload / name) != sql[name]:
                raise identity.ProjectIdentityError('SQLite backup differs; identity unchanged')
        elif copied['files'][name] != expected:
            raise identity.ProjectIdentityError('Backup bytes differ; identity unchanged')
    # Sync SQLite backups and directory entries before publishing the marker.
    for path in (payload / name for name in copied['files']):
        with path.open('rb') as stream:
            os.fsync(stream.fileno())
    for directory in [payload / name for name in reversed(copied['directories'])] + [payload]:
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return {'copied_inventory': copied, 'sqlite_logical_sha256': sql}


def recover(project, backup, *, expected_digest, offline=False):
    if not offline:
        raise identity.ProjectIdentityError('Stop all processes and supply explicit offline confirmation')
    project, backup = Path(project).absolute(), Path(backup).absolute()
    snapshot = _snapshot(project, backup)
    if not isinstance(expected_digest, str) or _digest(snapshot) != expected_digest:
        raise identity.ProjectIdentityError('Recovery preview changed; inspect a new preview before retrying')
    state = Path(snapshot['previous_identity']['state_root'])
    with _offline(project, state, snapshot['previous_identity']):
        if _snapshot(project, backup) != snapshot:
            raise identity.ProjectIdentityError('State changed after review; identity unchanged')
        backup.mkdir(mode=0o700)
        receipt = {'version': 1, 'status': 'copying', 'preview_sha256': expected_digest,
                   **snapshot, 'execution_authority': False, 'execution_performed': False}
        _json_write(backup / 'recovery.json', receipt)
        for name, value in snapshot['metadata'].items():
            if value is not None:
                # Preserve exact original metadata bytes, not reserialized JSON.
                fd = os.open(backup / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, 'w', encoding='utf-8', newline='') as stream:
                    stream.write(value)
                    stream.flush()
                    os.fsync(stream.fileno())
        verified = _copy_state(state, backup, snapshot['inventory'])
        for name, value in snapshot['metadata'].items():
            if value is not None and _metadata(backup / name, limit=64 * 1024**2) != value:
                raise identity.ProjectIdentityError('Backup metadata differs; identity unchanged')
        check = _snapshot(project, backup, backup_created=True)
        if check != snapshot:
            raise identity.ProjectIdentityError('State changed during backup; identity unchanged')
        receipt.update(status='verified_before_publication', **verified)
        _json_write(backup / 'recovery.json', receipt)
        # Persist the newly created backup directory's name as well as its
        # contents before publishing the only changed ownership record.
        parent_fd = os.open(backup.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        # Sole cutover: a crash before this keeps v1; after this v2 is coherent.
        # No owner/config/database records need a second publication.
        _json_write(project / IDENTITY, snapshot['updated_identity'])
        receipt['status'] = 'complete'
        _json_write(backup / 'recovery.json', receipt)
    return {**identity.status(project), 'recovery_status': 'complete', 'backup_root': str(backup),
            'preview_sha256': expected_digest}
