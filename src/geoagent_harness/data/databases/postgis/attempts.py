"""Durable one-attempt receipts; diagnostic state never grants execution authority."""
from geoagent_harness.platform.storage.ledger_provider import ledger_repositories
import hashlib
import json
import os
import stat
from pathlib import Path
import uuid
from datetime import datetime, timezone

from geoagent_harness.platform.workspace import runtime_store_path


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
            ledger_repositories().attempts(self.directory).claim(self.path.name, json.dumps(self.record, sort_keys=True).encode())
            self._event('claimed')
            self._sync()
        except FileExistsError:
            raise error('This exact PostGIS authority already has an attempt. Inspect its receipt and actual targets; a new exact decision is required before retry.') from None
        except (OSError, ValueError):
            raise error('PostGIS attempt could not be recorded safely; nothing was dispatched') from None

    def _sync(self):
        ledger_repositories().attempts(self.directory).sync()

    def _event(self, status, step=None):
        """Construct the same event only after the journal's storage checks."""
        def content():
            self.sequence += 1
            event = {'sequence': self.sequence, 'status': status,
                     'observed_at': datetime.now(timezone.utc).isoformat(), 'requested_step': step}
            return (json.dumps(event, sort_keys=True) + '\n').encode()
        ledger_repositories().attempts(self.directory).append(self.events.name, content,
            create=self.sequence == 0, max_existing_bytes=64000)

    def finish(self, status, step=None):
        self._event(status, step)
        self.record['status'] = status
        self.record['updated_at'] = datetime.now(timezone.utc).isoformat()
        if step is not None: self.record['last_requested_step'] = step
        ledger_repositories().attempts(self.directory).replace_snapshot(self.path.name, json.dumps(self.record, sort_keys=True).encode())
