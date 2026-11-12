"""Closed SQLite units for existing write sessions and successful-method records."""
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3

from geoagent_harness.platform.storage.ledger_contracts import LedgerStorageError
from geoagent_harness.platform.workspace import runtime_store_path


class SQLiteWritePolicy:
    def __init__(self, connection):
        self._db = connection

    def current(self):
        row = self._db.execute('SELECT * FROM policy WHERE id=1').fetchone()
        return dict(row) if row is not None else None

    def initialize(self, identity, enabled, locked):
        self._db.executescript('CREATE TABLE IF NOT EXISTS policy(\n                id INTEGER PRIMARY KEY CHECK(id=1),session_id TEXT NOT NULL,\n                revision INTEGER NOT NULL,enabled INTEGER NOT NULL,locked INTEGER NOT NULL);\n                CREATE TABLE IF NOT EXISTS authority(\n                digest TEXT PRIMARY KEY,session_id TEXT NOT NULL,revision INTEGER NOT NULL);\n                CREATE TABLE IF NOT EXISTS changes(\n                session_id TEXT,revision INTEGER,enabled INTEGER,event TEXT);')
        self._db.execute('INSERT OR REPLACE INTO policy VALUES(1,?,0,?,?)', (identity, int(enabled and not locked), int(locked)))
        self.record_change(identity, 0, enabled and not locked, 'startup')

    def begin_write(self): self._db.execute('BEGIN IMMEDIATE')
    def set_enabled(self, enabled): self._db.execute('UPDATE policy SET enabled=?,revision=revision+1 WHERE id=1', (int(enabled),))
    def record_change(self, session, revision, enabled, event): self._db.execute('INSERT INTO changes VALUES(?,?,?,?)', (session, revision, int(enabled), event))
    def bind(self, digest, session, revision): self._db.execute('INSERT INTO authority VALUES(?,?,?)', (digest, session, revision))
    def approval_scope(self, digest):
        row = self._db.execute('SELECT session_id,revision FROM authority WHERE digest=?', (digest,)).fetchone()
        return tuple(row) if row is not None else None
    def commit(self): self._db.commit()
    def rollback(self): self._db.rollback()


@contextmanager
def write_policy(database):
    db = None
    try:
        db = sqlite3.connect(database, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        yield SQLiteWritePolicy(db)
    except sqlite3.Error as exc:
        raise LedgerStorageError('Write policy storage unavailable; no write authorized') from exc
    finally:
        if db is not None: db.close()


def successful_connection(root):
    directory = runtime_store_path(root, 'workflow-state')
    path = directory / 'successful-workflows.sqlite3'
    if directory.is_symlink() or any(Path(str(path) + suffix).is_symlink() for suffix in ('', '-journal', '-wal', '-shm')):
        raise ValueError('Successful workflow storage is unsafe')
    if path.exists() and (not path.is_file() or path.stat().st_size > 16_000_000):
        raise ValueError('Successful workflow storage exceeds its budget')
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    db = sqlite3.connect(path, timeout=5)
    try:
        db.execute('CREATE TABLE IF NOT EXISTS successes (run_id TEXT PRIMARY KEY, method_id TEXT NOT NULL, conversation_id TEXT, payload TEXT NOT NULL)')
        db.execute('CREATE INDEX IF NOT EXISTS successes_scope ON successes(conversation_id, method_id)')
        db.execute('CREATE TABLE IF NOT EXISTS annotations (run_id TEXT PRIMARY KEY REFERENCES successes(run_id), payload TEXT NOT NULL)')
        db.commit()
        return db
    except Exception:
        db.close()
        raise


class SQLiteSuccessfulMethods:
    def __init__(self, root):
        try: self._db = successful_connection(root)
        except sqlite3.Error as exc: raise LedgerStorageError('Successful workflow storage is unavailable') from exc

    def _run(self, statement, arguments=()):
        try: return self._db.execute(statement, arguments)
        except sqlite3.Error as exc: raise LedgerStorageError('Successful workflow storage is unavailable') from exc

    def __enter__(self):
        self._db.__enter__()
        return self

    def __exit__(self, kind, value, traceback):
        try: return self._db.__exit__(kind, value, traceback)
        except sqlite3.Error as exc: raise LedgerStorageError('Successful workflow commit is uncertain; do not repeat execution') from exc

    def begin_write(self): self._run('BEGIN IMMEDIATE')
    def success(self, identity): return self._run('SELECT payload, conversation_id FROM successes WHERE run_id=?', (identity,)).fetchone()
    def count(self): return self._run('SELECT COUNT(*) FROM successes').fetchone()[0]
    def insert(self, identity, method, owner, content): self._run('INSERT INTO successes VALUES (?,?,?,?)', (identity, method, owner, content))
    def entries(self, owner, limit): return self._run('SELECT payload FROM successes WHERE conversation_id IS ? ORDER BY run_id LIMIT ?', (owner, limit)).fetchall()
    def annotations(self, owner): return self._run('SELECT a.run_id, a.payload FROM annotations a JOIN successes s ON s.run_id=a.run_id WHERE s.conversation_id IS ?', (owner,)).fetchall()
    def save_annotation(self, identity, content): self._run('INSERT INTO annotations VALUES (?,?) ON CONFLICT(run_id) DO UPDATE SET payload=excluded.payload', (identity, content))
    def close(self): self._db.close()
