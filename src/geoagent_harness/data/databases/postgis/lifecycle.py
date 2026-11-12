"""Shared mechanics for the two fixed, separately authorized relation lifecycles."""
from contextlib import contextmanager
from datetime import timezone
import hashlib
import json
import uuid
from typing import Protocol

import psycopg
from psycopg import IsolationLevel, sql

from geoagent_harness.platform.settings import validate_identifier
from geoagent_harness.data.databases.postgis.inspection import PostGISInspectionRequest
from geoagent_harness.data.databases.postgis.inspection import inspect_postgis_table
from geoagent_harness.data.databases.postgis.inspection.service import PsycopgPostGISInspectionReader, PostGISInspectionError
from geoagent_harness.core.verification.postgis import _read_password
from geoagent_harness.contracts.redaction import redact_text


def snapshot_sha256(value):
    payload = value.model_dump(mode='json') if hasattr(value, 'model_dump') else value
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def relation_profile(value):
    """Existing identity-independent contract; this is not a row-content checksum."""
    return {'columns': [x.model_dump(mode='json') for x in value.columns],
            'primary_key': value.primary_key.columns if value.primary_key else None,
            'unique_keys': sorted(x.columns for x in value.unique_keys),
            'row_count': value.row_count,
            'geometry_columns': [x.model_dump(mode='json') for x in value.geometry_columns]}


def check_authority(*, kind, approval, plan_digest, approval_digest, confirmed_plan,
                    confirmed_approval, step_ids, bindings, now, error):
    if (confirmed_plan, confirmed_approval) != (plan_digest, approval_digest):
        raise error('explicit digest confirmation does not match')
    if approval.decision != 'approved' or approval.approved_step_ids != step_ids:
        raise error(f'{kind} is not approved for the exact scope')
    for actual, expected, message in bindings:
        if actual != expected: raise error(message)
    if now.tzinfo is None or now.utcoffset() is None:
        raise error('execution time must be timezone-aware')
    if approval.created_at.tzinfo is None or approval.created_at.utcoffset() is None:
        raise error('approval time must be timezone-aware')
    if now < approval.created_at: raise error(f'{kind} approval is not yet valid')
    if approval.expires_at is not None:
        if approval.expires_at.tzinfo is None or approval.expires_at.utcoffset() is None:
            raise error('approval expiry must be timezone-aware')
        if now >= approval.expires_at: raise error(f'{kind} approval has expired')


def approval_fields(*, kind, decision, approver, reason, corrections, expires_at,
                    now, approval_id, step_ids, error):
    if decision not in {'approved', 'denied'}:
        raise error('decision must be approved or denied')
    if now.tzinfo is None or now.utcoffset() is None:
        raise error('approval time must be timezone-aware')
    if expires_at is not None and (expires_at.tzinfo is None or expires_at.utcoffset() is None):
        raise error('approval expiry must be timezone-aware')
    stamp = now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ').lower()
    return {'approval_id': approval_id or f'postgis-{kind}-approval-{stamp}-{uuid.uuid4().hex[:8]}',
            'decision': decision, 'approved_step_ids': list(step_ids) if decision == 'approved' else [],
            'approver': redact_text(approver), 'reason': redact_text(reason),
            'human_corrections': [redact_text(value) for value in (corrections or [])],
            'created_at': now, 'expires_at': expires_at}


def relation_requests(relations, settings, *, label, error):
    requests = [PostGISInspectionRequest(target_schema=x.target_schema, target_table=x.target_table) for x in relations]
    for request in requests:
        validate_identifier(request.target_schema, label='target_schema')
        validate_identifier(request.target_table, label='target_table')
        if request.target_schema not in settings.allowed_schemas:
            raise error(f'{label} schema is not allowlisted')
    return requests


class RelationTransaction(Protocol):
    def lock(self, relations): ...
    def inspect(self, request): ...
    def rename(self, source, target): ...
    def commit(self): ...
    def rollback(self): ...
    def close(self): ...


class PsycopgRelationTransaction:
    """Fixed identifier-safe SQL; no arbitrary SQL or model-selected entrypoint."""
    def __init__(self, settings):
        self.settings = settings
        self.connection = None
        try:
            self.connection = psycopg.connect(host=settings.postgres_host, port=settings.postgres_port,
                dbname=settings.postgres_database, user=settings.postgres_user,
                password=_read_password(settings.postgres_password_file), connect_timeout=5)
            self.connection.isolation_level = IsolationLevel.SERIALIZABLE
            self.reader = PsycopgPostGISInspectionReader(settings, connection=self.connection)
        except Exception:
            if self.connection is not None:
                try: self.connection.close()
                except Exception: pass
            raise RuntimeError('PostGIS relation connection failed; details were redacted') from None

    def lock(self, relations):
        self.connection.execute("SELECT set_config('statement_timeout', %s, true), set_config('lock_timeout', %s, true)", ('30000', '10000'))
        self.connection.execute(sql.SQL('LOCK TABLE {} IN ACCESS EXCLUSIVE MODE').format(
            sql.SQL(', ').join(sql.Identifier(s, t) for s, t in relations)))

    def inspect(self, request):
        return inspect_postgis_table(request=request, settings=self.settings, reader=self.reader)

    def rename(self, source, target):
        source_schema, source_table = source
        target_schema, target_table = target
        if source_schema != target_schema:
            self.connection.execute(sql.SQL('ALTER TABLE {} SET SCHEMA {}').format(
                sql.Identifier(source_schema, source_table), sql.Identifier(target_schema)))
        if source_table != target_table:
            self.connection.execute(sql.SQL('ALTER TABLE {} RENAME TO {}').format(
                sql.Identifier(target_schema, source_table), sql.Identifier(target_table)))

    def commit(self): self.connection.commit()
    def rollback(self): self.connection.rollback()
    def close(self): self.connection.close()


def execute_change(*, kind, reference, candidate, archive, settings, transaction,
                   factory, error, attempt):
    """Lock/reinspect, run two fixed renames, validate and commit exactly once."""
    if kind not in {'promotion', 'rollback'}: raise error('unknown relation lifecycle')
    requests = relation_requests((reference, candidate, archive), settings, label=kind, error=error)
    try: active = transaction if transaction is not None else factory(settings)
    except Exception:
        attempt.finish('connection_failed')
        raise error(f'PostGIS {kind} connection failed; details were redacted. Inspect the attempt before a new authorization.') from None
    committed = False
    commit_requested = False
    try:
        identity = lambda x: (x.target_schema, x.target_table)
        active.lock([identity(reference), identity(candidate if kind == 'promotion' else archive)])
        observed = [active.inspect(request) for request in requests]
        if kind == 'promotion':
            if snapshot_sha256(observed[0]) != snapshot_sha256(reference): raise error('reference snapshot changed')
            if snapshot_sha256(observed[1]) != snapshot_sha256(candidate): raise error('candidate snapshot changed')
            if observed[2].table_exists: raise error('archive relation now exists')
            moves = [(reference, archive), (candidate, reference)]
        else:
            if not observed[0].table_exists or relation_profile(observed[0]) != relation_profile(candidate): raise error('promoted reference changed')
            if observed[1].table_exists: raise error('original candidate identity now exists')
            if not observed[2].table_exists or relation_profile(observed[2]) != relation_profile(reference): raise error('archived reference changed')
            moves = [(reference, candidate), (archive, reference)]
        labels = ('archive_reference', 'promote_candidate') if kind == 'promotion' else ('restore_candidate', 'restore_reference')
        for label, (source, target) in zip(labels, moves):
            attempt.finish('mutating', label)
            active.rename(identity(source), identity(target))
        attempt.finish('validating', 'validate_relations')
        promoted = active.inspect(requests[0])
        restored_candidate = None
        if kind == 'promotion':
            if not promoted.table_exists or relation_profile(promoted) != relation_profile(candidate): raise error('promoted relation failed validation')
        else:
            restored_candidate = active.inspect(requests[1])
            if (not promoted.table_exists or not restored_candidate.table_exists
                    or relation_profile(promoted) != relation_profile(reference)
                    or relation_profile(restored_candidate) != relation_profile(candidate)):
                raise error('restored relations failed validation')
        attempt.finish('commit_requested')
        commit_requested = True
        active.commit()
        committed = True
        attempt.finish('committed')
        return promoted, restored_candidate
    except Exception as exc:
        rolled_back = False
        if not committed:
            try: active.rollback(); rolled_back = True
            except Exception: pass
        status = ('committed_receipt_failed' if committed else 'commit_unknown' if commit_requested
                  else 'rolled_back' if rolled_back else 'rollback_unconfirmed')
        try: attempt.finish(status)
        except Exception: pass  # Initial claim remains consumed even if status I/O fails.
        if committed or commit_requested or not rolled_back:
            raise error(f'PostGIS {kind} outcome requires inspection ({status}). Do not repeat this authority; inspect actual targets and obtain a new exact decision.') from None
        if isinstance(exc, error): raise
        raise error(f'PostGIS {kind} failed and was rolled back; details were redacted') from None
    finally:
        try: active.close()
        except Exception:
            if not committed:
                raise error(f'PostGIS {kind} connection could not be closed safely; inspect the recorded attempt') from None
            try: attempt.finish('committed_close_unconfirmed')
            except Exception: pass


@contextmanager
def inspection_reader(settings, reader=None):
    """Independent verifier/planner reader; never reuse a mutation transaction."""
    active = reader if reader is not None else PsycopgPostGISInspectionReader(settings)
    try: yield active
    finally:
        if reader is None: active.close()


def read_relations(requests, settings, reader):
    relation_requests(requests, settings, label='inspection', error=PostGISInspectionError)
    if hasattr(reader, 'inspect') and not hasattr(reader, 'table_exists'):
        results = [reader.inspect(request) for request in requests]
    else:
        results = [inspect_postgis_table(request=request, settings=settings, reader=reader) for request in requests]
    if any((value.target_schema, value.target_table) != (request.target_schema, request.target_table)
           for request, value in zip(requests, results)):
        raise PostGISInspectionError('Independent inspection returned a different relation identity')
    return results
