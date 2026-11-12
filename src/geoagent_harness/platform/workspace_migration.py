"""Explicit offline storage copy/cutover. Never dispatches operations or rewrites evidence."""
from contextlib import ExitStack, contextmanager, closing
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import time
import uuid

from geoagent_harness.platform.workspace import CONFIG_NAME, OWNER_NAME, RUNTIME_FILES, RUNTIME_STORES, WorkspaceLayout, WorkspaceError, _no_links
from geoagent_harness.platform.project_identity import IDENTITY_NAME, read_record, resolve_identity, owner_record, path_scope, _object

MANIFEST = '.actioncharter-migration.json'
MAX_FILES = 200_000
MAX_BYTES = 64 * 1024**3


def _hash(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise WorkspaceError('Migration accepts regular private files only')
        result = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = os.fstat(stream.fileno())
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise WorkspaceError('State changed during migration; stop all writers and retry')
    return result, before.st_size


def inventory(root):
    """Bounded physical inventory, excluding SQLite coordination sidecars only."""
    files, directories = {}, []
    total = 0
    def walk(path):
        nonlocal total
        _no_links(path)
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            directories.append(path.relative_to(root).as_posix())
            if len(directories) + len(files) > MAX_FILES:
                raise WorkspaceError('Workspace exceeds migration entry limit')
            for child in sorted(path.iterdir()): walk(child)
        elif stat.S_ISREG(info.st_mode):
            if any(str(path).endswith('.sqlite3' + suffix) for suffix in ('-wal', '-shm', '-journal')):
                return
            if total + info.st_size > MAX_BYTES:
                raise WorkspaceError('Workspace exceeds migration byte limit')
            digest, size = _hash(path)
            total += size
            if len(directories) + len(files) >= MAX_FILES or total > MAX_BYTES:
                raise WorkspaceError('Workspace exceeds migration file/byte limits')
            files[path.relative_to(root).as_posix()] = {'sha256': digest, 'bytes': size}
        else:
            raise WorkspaceError('Workspace contains a link, socket or non-regular artifact')
    for name in sorted(RUNTIME_STORES | RUNTIME_FILES):
        path = root / name
        if path.exists() or path.is_symlink(): walk(path)
    return {'files': files, 'directories': directories, 'file_count': len(files), 'bytes': total}


def _json_write(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


def _sql_digest(connection):
    digest = hashlib.sha256()
    for line in connection.iterdump():
        digest.update(line.encode()); digest.update(b'\n')
    return digest.hexdigest()


def _sql_read(path):
    _no_links(path)
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)) as db:
            return _sql_digest(db)
    except sqlite3.Error as error:
        raise WorkspaceError('SQLite state is unavailable or invalid; stop writers and inspect the database') from error


def _sql_copy(origin, target):
    try:
        with closing(sqlite3.connect(origin.as_uri() + '?mode=ro', uri=True, timeout=5)) as src:
            src.execute('BEGIN')
            if src.execute('PRAGMA quick_check').fetchone() != ('ok',):
                raise WorkspaceError('Source SQLite integrity check failed')
            digest = _sql_digest(src)
            deadline = time.monotonic() + 30
            def progress(*_):
                if time.monotonic() > deadline:
                    raise WorkspaceError('SQLite backup exceeded its time budget; stop all database writers')
            with closing(sqlite3.connect(target)) as dst:
                src.backup(dst, pages=256, progress=progress, sleep=0.05)
                dst.execute('PRAGMA journal_mode=DELETE')
                if dst.execute('PRAGMA quick_check').fetchone() != ('ok',) or _sql_digest(dst) != digest:
                    raise WorkspaceError('SQLite backup verification failed')
        target.chmod(0o600)
        return digest
    except sqlite3.Error as error:
        raise WorkspaceError('SQLite backup failed; configuration is unchanged, inspect the source database') from error


@contextmanager
def _offline(project, source):
    # Same independent host-local project ownership as the launcher. No session
    # is started and no authority is issued. Legacy artifact locks also stay held.
    from geoagent_harness.core.policy.write_policy import _project_owner, WritePolicyError
    try:
        with _project_owner(project), ExitStack() as locks:
            for path in source.rglob('*.lock') if source != project else (
                    p for store in RUNTIME_STORES if (source / store).is_dir()
                    for p in (source / store).rglob('*.lock')):
                _no_links(path)
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                locks.callback(os.close, fd)
                try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as error:
                    raise WorkspaceError('State is in use; stop all launcher/CLI/worker processes') from error
            yield
    except WritePolicyError as error:
        raise WorkspaceError('State is in use; stop the launcher before offline migration') from error


def plan(project_root, destination):
    layout = WorkspaceLayout.load(project_root)
    destination = Path(destination).absolute()
    _no_links(destination)
    # Reuse the exact config validation without changing the project's config.
    if (destination == layout.project_root or destination in layout.project_root.parents
            or destination.is_relative_to(layout.project_root)
            or destination == layout.state_root or destination.is_relative_to(layout.state_root)
            or layout.state_root.is_relative_to(destination)):
        raise WorkspaceError('Choose a new dedicated destination outside the source project and current state')
    if destination.exists():
        raise WorkspaceError('Migration destination must not exist; no merge or replacement is supported')
    current = inventory(layout.state_root)
    legacy = [name for name in sorted(RUNTIME_STORES | RUNTIME_FILES)
              if (layout.project_root / name).exists()]
    return {'version': 1, 'project_root': str(layout.project_root), 'source_root': str(layout.state_root),
            'destination_root': str(destination), 'inventory': current,
            'legacy_entries': legacy, 'legacy_inventory': inventory(layout.project_root),
            'execution_performed': False}


def _references(root, contents):
    # Preserve existing broken links too; migration must neither invent nor erase
    # history. Only logical internal file references are compared, never data reads.
    references = {}
    for name in contents['files']:
        path = root / name
        if path.suffix != '.json' or path.stat().st_size > 4 * 1024**2: continue
        try: value = json.loads(path.read_bytes())
        except (ValueError, UnicodeError): continue
        def visit(item):
            if isinstance(item, dict):
                for child in item.values(): visit(child)
            elif isinstance(item, list):
                for child in item: visit(child)
            elif isinstance(item, str):
                reference = Path(item)
                if (len(reference.parts) >= 2 and reference.parts[0] in RUNTIME_STORES
                        and not reference.is_absolute() and '..' not in reference.parts
                        and reference.as_posix() == item and '\\' not in item):
                    target = root / reference
                    _no_links(target)
                    references[item] = _hash(target)[0] if target.is_file() else None
        visit(value)
        if len(references) > MAX_FILES: raise WorkspaceError('Too many artifact references')
    return references


def migrate(project_root, destination, *, offline=False, apply=False, archive_legacy=False):
    if not apply:
        return plan(project_root, destination)
    if not offline:
        raise WorkspaceError('Explicit offline confirmation is required; stop all application processes first')
    project = WorkspaceLayout.load(project_root).project_root
    source = WorkspaceLayout.load(project).state_root
    with _offline(project, source):
        proposal = plan(project, destination)
        destination = Path(proposal['destination_root'])
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if archive_legacy and any((project / name).stat().st_dev != destination.parent.stat().st_dev
                                  for name in proposal['legacy_entries']):
            raise WorkspaceError('Legacy archive requires the same filesystem; use copy-only migration')
        stage = destination.with_name(destination.name + '.migrating-' + uuid.uuid4().hex)
        stage.mkdir(mode=0o700)
        source_inventory = proposal['inventory']
        config = project / CONFIG_NAME
        record = {**proposal, 'status': 'copying', 'archived_entries': [],
                  'previous_config': config.read_text() if config.exists() else None}
        identity_record = read_record(project)
        if identity_record:
            record.update(project_id=identity_record['project_id'], previous_identity=identity_record)
        _json_write(stage / MANIFEST, record)
        for name in source_inventory['directories']:
            (stage / name).mkdir(mode=0o700, parents=True, exist_ok=True)
        sql = {}
        for name in source_inventory['files']:
            origin, target = source / name, stage / name
            if origin.suffix == '.sqlite3':
                sql[name] = _sql_copy(origin, target)
            else:
                fd = os.open(origin, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as src, target.open('xb') as dst:
                    target.chmod(0o600)
                    while chunk := src.read(1024**2): dst.write(chunk)
                    dst.flush(); os.fsync(dst.fileno())
            metadata = origin.stat()
            os.utime(target, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
        if inventory(source) != source_inventory:
            raise WorkspaceError(f'Source changed during copy; configuration unchanged, inspect {stage}')
        copied = inventory(stage)
        if set(copied['files']) != set(source_inventory['files']) or copied['directories'] != source_inventory['directories']:
            raise WorkspaceError('Copied workspace inventory differs')
        for name, expected in source_inventory['files'].items():
            if name not in sql and copied['files'][name] != expected:
                raise WorkspaceError('Copied artifact bytes differ')
        source_refs, copied_refs = _references(source, source_inventory), _references(stage, copied)
        if source_refs != copied_refs:
            raise WorkspaceError('Copied artifact references differ')
        if inventory(source) != source_inventory or inventory(project) != proposal['legacy_inventory']:
            raise WorkspaceError('Source changed before cutover; configuration unchanged')
        if any(_sql_read(source / name) != digest for name, digest in sql.items()):
            raise WorkspaceError('SQLite source changed before cutover; configuration unchanged')
        if (config.read_text() if config.exists() else None) != record['previous_config']:
            raise WorkspaceError('Project configuration changed before cutover')
        owner = owner_record(project, destination)
        _json_write(stage / OWNER_NAME, owner)
        record.update(status='verified_copy', copied_inventory=copied, sqlite_logical_sha256=sql,
                      references=source_refs)
        _json_write(stage / MANIFEST, record)
        if destination.exists(): raise WorkspaceError('Destination appeared during copy; configuration unchanged')
        os.rename(stage, destination)
        if identity_record:
            # The verified destination is the only permissible new state binding.
            # A crash between metadata/config writes fails closed; the manifest
            # retains previous_identity for explicit offline recovery.
            _json_write(project / IDENTITY_NAME, {**identity_record,
                        'state_root': str(destination), 'state_object': _object(destination)})
        # Atomic config is the sole cutover. Old records stay in place by default.
        _json_write(config, {'version': 1, 'state_root': str(destination)})
        record['status'] = 'configured'
        _json_write(destination / MANIFEST, record)
        if archive_legacy:
            # Old roots move only after complete verified copy/cutover. No deletion.
            backup = destination / '.legacy-source'
            backup.mkdir(mode=0o700)
            for name in proposal['legacy_entries']:
                # Recheck before moving, including legacy copies from prior relocations.
                original = project / name
                _no_links(original)
                if original.stat().st_dev != backup.stat().st_dev:
                    raise WorkspaceError('Legacy archive requires the same filesystem; verified copy is active, originals retained')
                record['archived_entries'].append(name)
                _json_write(destination / MANIFEST, record)
                os.rename(original, backup / name)
        record['status'] = 'complete'
        _json_write(destination / MANIFEST, record)
        return verify(project)


def _record(layout):
    path = layout.state_root / MANIFEST
    _no_links(path)
    if not path.is_file() or path.stat().st_size > 64 * 1024**2:
        raise WorkspaceError('Workspace migration manifest is missing or oversized')
    record = json.loads(path.read_text())
    required = {'project_root', 'source_root', 'destination_root', 'archived_entries',
                'legacy_inventory', 'inventory', 'copied_inventory', 'previous_config', 'status'}
    if not isinstance(record, dict) or not required <= record.keys():
        raise WorkspaceError('Invalid migration manifest')
    identity = resolve_identity(layout.project_root, layout.state_root)
    same_project = (record.get('project_id') == identity.project_id if identity and 'project_id' in record
                    else path_scope(record['project_root']) == identity.legacy_scope if identity
                    else record['project_root'] == str(layout.project_root))
    if not same_project or record['destination_root'] != str(layout.state_root):
        raise WorkspaceError('Migration manifest does not match project/storage identity')
    if (not isinstance(record.get('archived_entries'), list)
            or any(not isinstance(name, str) for name in record['archived_entries'])
            or len(record['archived_entries']) != len(set(record['archived_entries']))
            or not set(record['archived_entries']) <= RUNTIME_STORES | RUNTIME_FILES):
        raise WorkspaceError('Invalid migration archive entries')
    for key in ('inventory', 'legacy_inventory', 'copied_inventory'):
        snapshot = record[key]
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get('files'), dict) or not isinstance(snapshot.get('directories'), list):
            raise WorkspaceError('Invalid migration inventory')
        for name in list(snapshot['files']) + snapshot['directories']:
            relative = Path(name)
            if (not isinstance(name, str) or relative.is_absolute() or not relative.parts
                    or relative.parts[0] not in RUNTIME_STORES | RUNTIME_FILES
                    or '..' in relative.parts or relative.as_posix() != name or '\\' in name):
                raise WorkspaceError('Unsafe migration inventory entry')
    return record


def verify(project_root):
    layout = WorkspaceLayout.load(project_root)
    record = _record(layout)
    current = inventory(layout.state_root)
    exact = (current == record['copied_inventory'] and
             all(_sql_read(layout.state_root / name) == digest
                 for name, digest in record['sqlite_logical_sha256'].items()))
    # Exact verification is a cutover certificate, not a promise that no future
    # workflow changes state. Later writes remain valid but require a new backup.
    legacy = [name for name in sorted(RUNTIME_STORES | RUNTIME_FILES) if (layout.project_root / name).exists()]
    return {'status': 'verified' if exact else 'changed_since_migration', 'project_root': str(layout.project_root),
            'state_root': str(layout.state_root), 'migration_status': record['status'],
            'file_count': current['file_count'], 'bytes': current['bytes'],
            'exact_copy': exact, 'source_only': not legacy, 'legacy_entries': legacy,
            'execution_performed': False}


def rollback(project_root, *, offline=False):
    if not offline: raise WorkspaceError('Explicit offline confirmation is required')
    layout = WorkspaceLayout.load(project_root)
    with _offline(layout.project_root, layout.state_root):
        check = verify(project_root)
        if not check['exact_copy']:
            raise WorkspaceError('Workspace changed since migration; automatic rollback would lose newer state')
        record = _record(layout)
        if record['project_root'] != str(layout.project_root):
            raise WorkspaceError('Project moved since migration; automatic rollback will not access historical source paths')
        if read_record(layout.project_root) and 'previous_identity' not in record:
            raise WorkspaceError('Identity was adopted after migration; automatic rollback requires a new verified backup')
        # The old side must still match its original inventory too. A writer
        # using an old explicit root must never have its new records overwritten.
        source = Path(record['source_root'])
        _no_links(source)
        original = inventory(source)
        archived = inventory(layout.state_root / '.legacy-source')
        legacy = inventory(layout.project_root)
        def merged(left, right):
            files = {**left['files'], **right['files']}
            return {'files': files, 'directories': sorted(set(left['directories'] + right['directories'])),
                    'file_count': len(files), 'bytes': sum(f['bytes'] for f in files.values())}
        combined = merged(legacy, archived)
        expected_legacy = record['legacy_inventory']
        # Directory order is traversal order in inventory; compare sets here.
        def equivalent(a, b):
            return a['files'] == b['files'] and set(a['directories']) == set(b['directories'])
        if not equivalent(combined, expected_legacy):
            raise WorkspaceError('Legacy state changed; automatic rollback will not discard it')
        if source != layout.project_root and not equivalent(original, record['inventory']):
            raise WorkspaceError('Previous state changed; automatic rollback is unavailable')
        for name, digest in record['sqlite_logical_sha256'].items():
            base = (layout.state_root / '.legacy-source' if source == layout.project_root
                    and Path(name).parts[0] in record['archived_entries'] else source)
            if _sql_read(base / name) != digest:
                raise WorkspaceError('Previous SQLite state changed; automatic rollback is unavailable')
        for name in record['archived_entries']:
            archive = layout.state_root / '.legacy-source' / name
            _no_links(archive)
            if archive.exists() and (layout.project_root / name).exists():
                raise WorkspaceError('Legacy destination exists; rollback will not overwrite it')
        for name in record['archived_entries']:
            archive = layout.state_root / '.legacy-source' / name
            if archive.exists(): os.rename(archive, layout.project_root / name)
        config = layout.project_root / CONFIG_NAME
        if 'previous_identity' in record:
            _json_write(layout.project_root / IDENTITY_NAME, record['previous_identity'])
        if record['previous_config'] is None:
            config.unlink()
        else:
            _json_write(config, json.loads(record['previous_config']))
        record['status'] = 'rolled_back'
        _json_write(layout.state_root / MANIFEST, record)
        return {'status': 'rolled_back', 'destination_preserved': True, 'execution_performed': False}
