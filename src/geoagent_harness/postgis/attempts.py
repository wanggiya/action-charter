"""Durable one-attempt receipts; diagnostic state never grants execution authority."""
import hashlib
import json
import os
import stat
from pathlib import Path
import uuid
from datetime import datetime, timezone

from geoagent_harness.workspace import runtime_store_path


class RelationAttempt:
    def __init__(self, settings, kind, plan_sha256, approval_sha256, error):
        self.error = error
        self.record = {'version': 1, 'kind': kind, 'plan_sha256': plan_sha256,
                       'approval_sha256': approval_sha256, 'status': 'claimed',
                       'automatic_retry': False}
        identity = {'kind': kind, 'plan_sha256': plan_sha256, 'approval_sha256': approval_sha256}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        self.record['created_at'] = datetime.now(timezone.utc).isoformat()
        try:
            self.directory = runtime_store_path(settings.project_root, 'workflow-state', 'postgis-attempts')
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.path = self.directory / (key + '.json')
            self.events = self.directory / (key + '.events.jsonl')
            self.sequence = 0
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w') as stream:
                json.dump(self.record, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
            self._event('claimed')
            self._sync()
        except FileExistsError:
            raise error('This exact PostGIS authority already has an attempt. Inspect its receipt and actual targets; a new exact decision is required before retry.') from None
        except (OSError, ValueError):
            raise error('PostGIS attempt could not be recorded safely; nothing was dispatched') from None

    def _sync(self):
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try: os.fsync(fd)
        finally: os.close(fd)

    def _event(self, status, step=None):
        """Append observed stages; refreshed diagnostic snapshots are not audit history."""
        flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK
        if self.sequence == 0: flags |= os.O_CREAT | os.O_EXCL
        fd = os.open(self.events, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 64000:
                raise OSError('Unsafe attempt event history')
            self.sequence += 1
            event = {'sequence': self.sequence, 'status': status,
                     'observed_at': datetime.now(timezone.utc).isoformat(), 'requested_step': step}
            data = (json.dumps(event, sort_keys=True) + '\n').encode()
            if os.write(fd, data) != len(data): raise OSError('Incomplete attempt event')
            os.fsync(fd)
        finally: os.close(fd)

    def finish(self, status, step=None):
        self._event(status, step)
        self.record['status'] = status
        self.record['updated_at'] = datetime.now(timezone.utc).isoformat()
        if step is not None: self.record['last_requested_step'] = step
        temporary = self.directory / ('.attempt-' + uuid.uuid4().hex)
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w') as stream:
                json.dump(self.record, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, self.path); self._sync()
        finally:
            temporary.unlink(missing_ok=True)
