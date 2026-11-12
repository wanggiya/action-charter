"""Local append-only action audit and durable event claims; no operation replay."""
from contextlib import contextmanager
from collections import deque
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from threading import RLock

from geoagent_harness.contracts.task_context import ActionStorageError, DuplicateAction, ActionContextError
from geoagent_harness.platform.workspace import runtime_store_path, _no_links, WorkspaceError
from geoagent_harness.platform.project_identity import ownership_scope, resolve_identity


def _json(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def _digest(value): return hashlib.sha256(value.encode()).hexdigest()


class TransientActionLedger:
    """Bounded query telemetry only. Never a durable claim or execution permit."""
    _records=deque(maxlen=512)
    _lock=RLock()

    def __init__(self, project):self.scope=ownership_scope(project)

    def _append(self, event):
        if len(_json(event).encode())>4096:raise ActionStorageError('Query telemetry exceeds its byte bound')
        self._records.append((self.scope,{**event,'durable':False,'execution_authority_granted':False}))

    def claim(self, *, identity, run, actor, action, fingerprint, parent, key, at, decision):
        if key is not None:raise ActionContextError('An explicit event key requires a durable claim')
        with self._lock:self._append({'identity':identity,'run_id':run.run_id,'actor':asdict(actor),
            'action':action,'phase':'started','trigger':run.trigger,'parent_action_id':parent,
            'at':at,'admission':asdict(decision),'budget':asdict(run.budget)})

    def _started(self, identity):
        for scope,event in reversed(self._records):
            if scope==self.scope and event['identity']==identity and event['phase']=='started':return event
        return None

    def finish(self, identity, *, phase, at):
        with self._lock:
            event=self._started(identity)
            if event is not None:self._append({**event,'phase':phase,'at':at})

    def link(self, identity, *, kind, reference, at):
        with self._lock:
            event=self._started(identity)
            if event is not None:self._append({**event,'phase':'reference','kind':kind,'reference':reference,'at':at})

    def events(self, run_id, *, limit=1000):
        if type(limit) is not int or limit<1:raise ActionContextError('Invalid query telemetry limit')
        with self._lock:
            return [dict(event) for scope,event in self._records if scope==self.scope and event['run_id']==run_id][-limit:]


class LocalActionLedger:
    def __init__(self, project, *, namespace='local'):
        if namespace not in {'local','mcp'}:raise ActionContextError('Unknown audit namespace')
        self.project, self.namespace = Path(project), namespace

    @contextmanager
    def _db(self, *, write=True):
        db = None
        try:
            directory = (runtime_store_path(self.project, 'traces', '.action-audit') if self.namespace=='mcp'
                         else runtime_store_path(self.project, 'workflow-state'))
            _no_links(directory)
            path = directory/'action-ledger.sqlite3'
            for suffix in ('', '-journal', '-wal', '-shm'): _no_links(Path(str(path)+suffix))
            if not write and not path.exists():
                yield None
                return
            if path.exists() and (not path.is_file() or path.stat().st_nlink != 1 or path.stat().st_size > 64_000_000):
                raise ActionStorageError('Action ledger is unsafe or exceeds its byte budget')
            if write:
                directory.mkdir(parents=True, exist_ok=True, mode=0o700)
                fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
                os.close(fd)
            db = sqlite3.connect(path if write else path.as_uri()+'?mode=ro', timeout=5, uri=not write)
            if write:
                db.execute('PRAGMA synchronous=FULL')
                db.executescript('''CREATE TABLE IF NOT EXISTS action_project_scope (
                id INTEGER PRIMARY KEY CHECK(id=1), project_sha256 TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS action_claims (
                claim_key TEXT PRIMARY KEY, identity TEXT UNIQUE NOT NULL, run_id TEXT NOT NULL,
                actor TEXT NOT NULL, action TEXT NOT NULL, fingerprint TEXT NOT NULL, parent TEXT);
                CREATE TABLE IF NOT EXISTS action_events (
                run_id TEXT NOT NULL, sequence INTEGER NOT NULL, identity TEXT NOT NULL,
                phase TEXT NOT NULL, payload TEXT NOT NULL, digest TEXT NOT NULL,
                PRIMARY KEY(run_id,sequence), UNIQUE(identity,phase));''')
            db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            identity=resolve_identity(self.project)
            scope=ownership_scope(self.project)
            if write:db.execute('INSERT OR IGNORE INTO action_project_scope VALUES(1,?)',(scope,))
            stored=db.execute('SELECT project_sha256 FROM action_project_scope WHERE id=1').fetchone()
            allowed={scope,identity.legacy_scope} if identity else {scope}
            if stored is None or stored[0] not in allowed:
                raise ActionStorageError('Action ledger belongs to a different source project')
            yield db
            db.commit()
        except (sqlite3.Error, OSError, WorkspaceError) as exc:
            raise ActionStorageError('Action audit storage is unavailable or uncertain; inspect recorded runs before retrying') from exc
        finally:
            if db is not None: db.close()  # rollback any uncommitted transaction

    def _append(self, db, identity, run_id, phase, payload):
        previous = db.execute('SELECT sequence,digest FROM action_events WHERE run_id=? ORDER BY sequence DESC LIMIT 1', (run_id,)).fetchone()
        sequence = previous[0]+1 if previous else 1
        payload = {**payload, 'identity':identity, 'run_id':run_id, 'phase':phase,
                   'sequence':sequence, 'previous_sha256':previous[1] if previous else None}
        content = _json(payload)
        if sequence > 100000 or len(content.encode()) > 4096:
            raise ActionStorageError('Action audit run exceeds its event budget')
        db.execute('INSERT INTO action_events VALUES(?,?,?,?,?,?)', (run_id,sequence,identity,phase,content,_digest(content)))

    def claim(self, *, identity, run, actor, action, fingerprint, parent, key, at, decision):
        actor_json = _json(asdict(actor))
        claim = _digest(_json([actor_json, key])) if key is not None else identity
        with self._db() as db:
            previous = db.execute('SELECT identity,run_id,action,fingerprint FROM action_claims WHERE claim_key=?', (claim,)).fetchone()
            if previous:
                if (previous[2],previous[3]) != (action,fingerprint):
                    raise ActionContextError('Idempotency key conflicts with an earlier action; nothing dispatched')
                phase = db.execute('SELECT phase FROM action_events WHERE identity=? ORDER BY sequence DESC LIMIT 1', (previous[0],)).fetchone()
                status = phase[0] if phase else 'uncertain'
                raise DuplicateAction(previous[1],previous[0],status)
            db.execute('INSERT INTO action_claims VALUES(?,?,?,?,?,?,?)', (claim,identity,run.run_id,actor_json,action,fingerprint,parent))
            self._append(db,identity,run.run_id,'started',{'actor':asdict(actor),'trigger':run.trigger,
                'action':action,'parent_action_id':parent,'at':at,'admission':asdict(decision),
                'budget':asdict(run.budget),'execution_authority_granted':False})

    def finish(self, identity, *, phase, at):
        if phase not in {'completed','failed','blocked'}: raise ActionContextError('Invalid action terminal phase')
        with self._db() as db:
            row = db.execute('SELECT run_id,actor,action,parent FROM action_claims WHERE identity=?', (identity,)).fetchone()
            if row is None: raise ActionStorageError('Action claim is missing; completion is uncertain')
            if db.execute("SELECT 1 FROM action_events WHERE identity=? AND phase IN ('completed','failed','blocked')", (identity,)).fetchone():
                raise ActionStorageError('Action already has a terminal audit event')
            self._append(db,identity,row[0],phase,{'at':at,'actor':json.loads(row[1]),'action':row[2],
                'parent_action_id':row[3],'execution_authority_granted':False})

    def link(self, identity, *, kind, reference, at):
        phase='reference-'+_digest(_json([kind,reference]))
        with self._db() as db:
            row=db.execute('SELECT run_id FROM action_claims WHERE identity=?',(identity,)).fetchone()
            if row is None:raise ActionStorageError('Action claim is missing; evidence link is uncertain')
            if db.execute('SELECT 1 FROM action_events WHERE identity=? AND phase=?',(identity,phase)).fetchone():return
            self._append(db,identity,row[0],phase,{'kind':kind,'reference':reference,'at':at,'execution_authority_granted':False})

    def events(self, run_id, *, limit=1000):
        if type(limit) is not int or not 1 <= limit <= 100000: raise ActionContextError('Invalid action history limit')
        with self._db(write=False) as db:
            if db is None:return []
            rows = db.execute('SELECT payload,digest FROM action_events WHERE run_id=? ORDER BY sequence LIMIT ?', (run_id,limit+1)).fetchall()
        if len(rows)>limit: raise ActionStorageError('Action history exceeds the requested bound')
        events=[];previous=None
        for index,(content,digest) in enumerate(rows,1):
            try:event=json.loads(content)
            except (ValueError,TypeError) as exc:raise ActionStorageError('Action audit chain failed verification') from exc
            if (not isinstance(event,dict) or _digest(content)!=digest or event.get('previous_sha256')!=previous or event.get('sequence')!=index or event.get('run_id')!=run_id):
                raise ActionStorageError('Action audit chain failed verification')
            events.append(event);previous=digest
        return events
