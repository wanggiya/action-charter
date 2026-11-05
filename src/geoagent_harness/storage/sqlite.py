"""SQLite adapter for the existing tasks.sqlite3 schema, with no schema migration."""
from __future__ import annotations
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
import stat

from geoagent_harness.workspace import WorkspaceLayout, WorkspaceError
from .contracts import Record, RepositoryError

MAX_DATABASE_BYTES = 64_000_000

# Only these constant schemas are interpolated into SQL. Names never come from chat.
_COLLECTIONS = {
    'conversations': ('id', ()), 'tasks': ('id', ()), 'memories': ('id', ()),
    'inspection_submissions_v1': ('id', ()), 'dataset_views_v1': ('id', ()),
    'chat_history_blobs_v1': ('sha', ()),
    'chat_history_v1': ('id', ('conversation_id',)),
    'method_memory_records': ('id', ('conversation_id',)),
    'capability_attempts': ('sha', ('conversation_id',)),
    'request_diagnostics_v1': ('id', ('conversation_id', 'kind', 'parent_id')),
}
_SETTINGS = {
    'model_selection': ('model', 'TEXT', True),
    'model_reasoning_selection': ('selection', 'TEXT', True),
    'outcome_review_settings': ('seconds', 'INTEGER', True),
    'method_memory_settings': ('enabled', 'INTEGER', False),
    'method_helper_settings': ('enabled', 'INTEGER', False),
}


@contextmanager
def connection(root: Path, *, write=False):
    root = Path(root).resolve(strict=True)
    try:
        layout = WorkspaceLayout.load(root)
        directory = layout.planning_directory()
    except WorkspaceError as error:
        raise RepositoryError(f'Planning task storage is unsafe: {error}') from error
    if directory.is_symlink():
        raise RepositoryError('Planning task storage is unsafe')
    if write:
        layout.state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not directory.exists():
        yield None
        return
    if not directory.is_dir() or directory.resolve().parent != layout.state_root:
        raise RepositoryError('Planning task storage is outside the configured workspace')
    path = directory / 'tasks.sqlite3'
    for name in ('tasks.sqlite3', 'tasks.sqlite3-journal', 'tasks.sqlite3-wal', 'tasks.sqlite3-shm'):
        if (directory / name).is_symlink():
            raise RepositoryError('Planning task record is unsafe')
    if not path.exists():
        if not write:
            yield None
            return
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            pass  # A competing first writer created the same database; recheck below.
        else:
            os.close(fd)
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > MAX_DATABASE_BYTES:
        raise RepositoryError('Planning task database exceeds its storage contract')
    db = None
    try:
        db = sqlite3.connect(path.as_uri() + ('?mode=rw' if write else '?mode=ro'), uri=True, timeout=5)
        if write:
            db.execute('PRAGMA synchronous=FULL')
            db.execute(f'PRAGMA max_page_count={MAX_DATABASE_BYTES // 4096}')
            for table in ('conversations', 'tasks', 'memories'):
                db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.commit()
            db.execute('BEGIN IMMEDIATE')
        else:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'conversations', 'tasks'}.issubset(tables):
                if tables:
                    raise RepositoryError('Planning task database schema is incomplete')
                yield None
                return
            db.execute('BEGIN')  # One coherent snapshot for a repository read transaction.
        yield db
        if write:
            db.commit()
    except sqlite3.Error:
        if db is not None:
            db.rollback()
        raise RepositoryError('Planning task storage is unavailable; reload before retrying') from None
    finally:
        if db is not None:
            db.close()  # Also rolls back domain errors and cancelled transactions.


class SQLiteRecords:
    def __init__(self, db, collection, writable):
        if collection not in _COLLECTIONS:
            raise RepositoryError('Unknown record collection')
        self.db, self.collection, self.writable = db, collection, writable
        self.key, self.extra = _COLLECTIONS[collection]

    def available(self):
        return bool(self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (self.collection,)).fetchone())

    def ensure(self):
        if not self.writable:
            raise RepositoryError('Read-only storage transaction')
        columns = [f'{self.key} TEXT PRIMARY KEY'] + [f'{name} TEXT' + ('' if name == 'parent_id' else ' NOT NULL') for name in self.extra] + ['value TEXT NOT NULL']
        self.db.execute(f'CREATE TABLE IF NOT EXISTS {self.collection} ({", ".join(columns)})')
        if self.collection in {'chat_history_v1', 'request_diagnostics_v1'}:
            index = 'chat_history_owner_v1' if self.collection == 'chat_history_v1' else 'request_diagnostics_chat_v1'
            self.db.execute(f'CREATE INDEX IF NOT EXISTS {index} ON {self.collection}(conversation_id)')

    def get(self, key):
        if not self.available():
            return None
        row = self.db.execute(f'SELECT value FROM {self.collection} WHERE {self.key}=?', (key,)).fetchone()
        return row[0] if row else None

    def _where(self, owner):
        if owner is not None and 'conversation_id' not in self.extra:
            raise RepositoryError('Collection does not support owner filtering')
        return (' WHERE conversation_id=?', [owner]) if owner is not None else ('', [])

    def entries(self, *, owner=None, limit=None):
        if limit is not None and (type(limit) is not int or limit < 0):
            raise RepositoryError('Invalid record lookup limit')
        where, args = self._where(owner)
        if not self.available():
            return []
        columns = ','.join([self.key, 'value', *self.extra])
        if limit is not None:
            args.append(limit)
        rows = self.db.execute(f'SELECT {columns} FROM {self.collection}{where} ORDER BY rowid DESC' + (' LIMIT ?' if limit is not None else ''), args)
        return [Record(row[0], row[1], *row[2:]) for row in rows]

    def count(self, *, owner=None):
        where, args = self._where(owner)
        return self.db.execute(f'SELECT COUNT(*) FROM {self.collection}{where}', args).fetchone()[0] if self.available() else 0

    def put(self, key, content, *, owner=None, kind=None, parent=None, ignore_existing=False):
        self.ensure()
        if not isinstance(content, str):
            raise RepositoryError('Stored JSON must be encoded text')
        extras = {'conversation_id': owner, 'kind': kind, 'parent_id': parent}
        if any(extras[name] is None for name in self.extra if name != 'parent_id'):
            raise RepositoryError('Owned record requires provenance')
        if self.extra:
            existing = self.db.execute(f'SELECT {", ".join(self.extra)} FROM {self.collection} WHERE {self.key}=?', (key,)).fetchone()
            if existing and tuple(existing) != tuple(extras[name] for name in self.extra):
                raise RepositoryError('Stored record provenance changed')
        values = [key, *[extras[name] for name in self.extra], content]
        clause = 'INSERT OR IGNORE' if ignore_existing else 'INSERT'
        self.db.execute(f'{clause} INTO {self.collection} VALUES ({",".join("?" for _ in values)})' + ('' if ignore_existing else f' ON CONFLICT({self.key}) DO UPDATE SET value=excluded.value'), values)

    def delete(self, key, *, owner=None):
        if not self.writable:
            raise RepositoryError('Read-only storage transaction')
        where, args = self._where(owner)
        if self.available():
            self.db.execute(f'DELETE FROM {self.collection} WHERE {self.key}=?' + (' AND conversation_id=?' if owner is not None else ''), [key, *args])


class SQLiteTransaction:
    def __init__(self, db, *, write=False):
        self._db, self._write = db, write

    def records(self, collection):
        return SQLiteRecords(self._db, collection, self._write)

    def setting(self, name):
        if name not in _SETTINGS:
            raise RepositoryError('Unknown setting store')
        if not self._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone():
            return None
        field = _SETTINGS[name][0]
        row = self._db.execute(f'SELECT {field},revision FROM {name} WHERE id=1').fetchone()
        return {field: row[0], 'revision': row[1]} if row else None

    def save_setting(self, name, value, revision):
        if name not in _SETTINGS or not self._write:
            raise RepositoryError('Setting write unavailable')
        field, kind, check = _SETTINGS[name]
        constraint = ' CHECK(id=1)' if check else ''
        self._db.execute(f'CREATE TABLE IF NOT EXISTS {name} (id INTEGER PRIMARY KEY{constraint}, {field} {kind} NOT NULL, revision INTEGER NOT NULL)')
        if check:
            self._db.execute(f'INSERT OR REPLACE INTO {name} VALUES(1,?,?)', (value, revision))
        else:
            self._db.execute(f'INSERT INTO {name} VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET {field}=excluded.{field},revision=excluded.revision', (value, revision))

    def prune_diagnostics(self, *, turns, calls):
        if not self._write:
            raise RepositoryError('Read-only storage transaction')
        db = self._db
        ids = [r[0] for r in db.execute("SELECT id FROM request_diagnostics_v1 WHERE kind='turn' AND json_extract(value,'$.status')!='started' ORDER BY rowid DESC LIMIT -1 OFFSET ?", (turns,))]
        for identity in ids:
            db.execute('DELETE FROM request_diagnostics_v1 WHERE id=? OR parent_id=?', (identity, identity))
        db.execute("DELETE FROM request_diagnostics_v1 WHERE kind='call' AND json_extract(value,'$.status')!='started' AND id IN (SELECT id FROM request_diagnostics_v1 WHERE kind='call' ORDER BY rowid DESC LIMIT -1 OFFSET ?)", (calls,))

    def recent_diagnostic_chats(self):
        if not self.records('request_diagnostics_v1').available():
            return []
        return [r[0] for r in self._db.execute("SELECT conversation_id FROM request_diagnostics_v1 WHERE kind='turn' GROUP BY conversation_id ORDER BY MAX(rowid) DESC LIMIT 20")]

    def helper_note(self, owner, key):
        if not self._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='method_helper_notes'").fetchone():
            return None
        row = self._db.execute('SELECT value FROM method_helper_notes WHERE conversation_id=? AND source_key=?', (owner, key)).fetchone()
        return row[0] if row else None

    def save_helper_note(self, owner, key, content, *, per_chat, per_project):
        if not self._write:
            raise RepositoryError('Read-only storage transaction')
        db = self._db
        db.execute('CREATE TABLE IF NOT EXISTS method_helper_notes (conversation_id TEXT NOT NULL, source_key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(conversation_id,source_key))')
        # Only the existing disposable cache is pruned, never shared history.
        for query, args, limit in (
            ('SELECT rowid FROM method_helper_notes WHERE conversation_id=? ORDER BY rowid', (owner,), per_chat),
            ('SELECT rowid FROM method_helper_notes ORDER BY rowid', (), per_project),
        ):
            rows = db.execute(query, args).fetchall()
            for row in rows[:max(0, len(rows) - limit + 1)]:
                db.execute('DELETE FROM method_helper_notes WHERE rowid=?', (row[0],))
        db.execute('INSERT INTO method_helper_notes VALUES (?,?,?) ON CONFLICT(conversation_id,source_key) DO UPDATE SET value=excluded.value', (owner, key, content))


def adapt_legacy(connection):
    """Support existing private callers/tests passing a raw SQLite transaction."""
    return SQLiteTransaction(connection, write=connection.in_transaction) if isinstance(connection, sqlite3.Connection) else connection
