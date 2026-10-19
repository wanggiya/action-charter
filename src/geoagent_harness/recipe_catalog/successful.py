"""Deterministic successful-method index; private bindings stay in durable runs.

This is historical execution evidence, not a generalized template or authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

MAX_RECORDS = 200  # Same bounded inventory as durable runs; never silently evict.


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def contracts(root):
    from geoagent_harness.operations.registry import operation_catalog
    result = {}
    for operation in operation_catalog(root)['operations']:
        stable = {key: operation[key] for key in ('id', 'version', 'parameters_schema', 'output_schema', 'outputs', 'effects', 'approval_required', 'validation_required', 'package_sha256')}
        result[operation['id']] = {**operation, 'contract_sha256': digest(stable)}
    return result


def capture_basis(root, steps):
    """Capture trusted contracts at dispatch preparation, not after execution."""
    from geoagent_harness.operations.registry import argument_models
    declared, models = contracts(root), argument_models(root)
    operations, normalized, tags, bindings = [], [], set(), {}
    for step in steps:
        skill = step.get('skill', step.get('skill_id'))
        contract = declared[skill]
        arguments = models[skill].model_validate(step['arguments']).model_dump(mode='json', exclude_none=True)
        # Filename choices do not define a method, but suffix/roles/aliasing do.
        for key in ('path', 'right_path', 'target_path'):
            value = arguments.get(key)
            if isinstance(value, str):
                identity = ('output' if key == 'target_path' else 'input', value)
                bindings.setdefault(identity, len(bindings) + 1)
                arguments[key] = {'binding': bindings[identity], 'role': identity[0], 'suffix': Path(value).suffix.lower()}
        # Never retain a secret or an offline password hash in this index.
        def without_secrets(value):
            if isinstance(value, dict):
                return {k: '[excluded]' if re.search(r'password|secret|token|credential|approval|api_key', k, re.I) else without_secrets(v) for k, v in value.items()}
            if isinstance(value, list):
                return [without_secrets(v) for v in value]
            return value
        dependencies = step.get('depends_on') or []
        requires_validation = bool(step.get('validation_required')) or contract['validation_required'] or contract['effects']['access'] != 'read_only'
        operations.append({'step_id': step['step_id'], 'skill_id': skill, 'name': contract['name'][:100],
                           'version': contract['version'], 'contract_sha256': contract['contract_sha256'],
                           'outputs': [o['contract'] for o in contract['outputs']], 'validation_required': requires_validation})
        normalized.append({'skill': skill, 'arguments': without_secrets(arguments), 'depends_on': dependencies,
                           'contract': contract['contract_sha256'], 'validation_required': requires_validation})
        tags.update({'workflow'})
        if 'csv' in skill or skill.startswith('ext_'): tags.add('csv')
        if 'vector' in skill: tags.update({'geospatial', 'vector'})
        if 'raster' in skill: tags.update({'geospatial', 'raster'})
        if 'postgis' in skill: tags.update({'geospatial', 'postgis'})
        if skill.startswith('inspect_'): tags.add('inspection')
        if skill in {'select_csv_columns', 'filter_csv_rows', 'handle_csv_missing'}: tags.add('cleaning')
        if skill == 'join_csv': tags.add('join')
        if skill == 'aggregate_csv': tags.add('aggregation')
        if skill == 'calculate_csv_columns': tags.add('calculation')
        if skill.startswith(('export_', 'convert_')): tags.add('export')
    return {'method_id': digest(normalized), 'operations': operations, 'tags': sorted(tags),
            'name': ' → '.join(o['name'] for o in operations)[:180]}


def _connection(root):
    directory = Path(root) / 'workflow-state'
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
        db.commit()
        return db
    except Exception:
        db.close()
        raise


def retain(root, record):
    """Idempotent metadata-only indexing. No operation, approval or model calls."""
    if record.get('status') != 'completed' or not record.get('execution_performed') or not record.get('finished_at'):
        return {'status': 'not_eligible', 'finding': 'Only completed executions can become successful records.'}
    basis = record.get('retention_basis')
    if not basis or not basis.get('operations'):
        return {'status': 'unavailable', 'finding': 'No dispatch-time contract snapshot. This run was not retroactively labelled as reusable.'}
    steps = record['steps']
    if len(steps) != len(basis['operations']):
        return {'status': 'not_eligible', 'finding': 'Recorded step evidence is incomplete.'}
    for step, operation in zip(steps, basis['operations']):
        validation = step.get('validation_outcome') or {}
        if (step['step_id'], step['skill_id']) != (operation['step_id'], operation['skill_id']) or step['status'] not in {'completed', 'validated_success'} or not isinstance(step.get('outcome'), dict):
            return {'status': 'not_eligible', 'finding': 'Every operation must have successful recorded evidence.'}
        if operation['validation_required'] and validation.get('passed') is not True:
            return {'status': 'not_eligible', 'finding': 'Required deterministic validation did not pass.'}
    evidence = {'plan_sha256': record['plan_sha256'], 'steps': [{k: s.get(k) for k in ('step_id', 'skill_id', 'status', 'outcome', 'validation_outcome')} for s in steps]}
    payload = {'schema_version': '1.0', 'run_id': record['run_id'], 'plan_sha256': record['plan_sha256'],
               'method_id': basis['method_id'], 'name': basis['name'], 'tags': basis['tags'], 'operations': basis['operations'],
               'evidence_sha256': digest(evidence), 'finished_at': record['finished_at'],
               'evidence_kind': 'recorded_success_not_general_validation', 'execution_authority_granted': False}
    content = json.dumps(payload, sort_keys=True)
    if len(content.encode()) > 24_000:
        raise ValueError('Successful workflow metadata exceeds its budget')
    db = _connection(root)
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT payload, conversation_id FROM successes WHERE run_id=?', (record['run_id'],)).fetchone()
            if previous and (previous[0] != content or previous[1] != record.get('conversation_id')):
                raise ValueError('Successful evidence changed; existing record was not overwritten')
            if not previous:
                if db.execute('SELECT COUNT(*) FROM successes').fetchone()[0] >= MAX_RECORDS:
                    raise ValueError('Successful workflow inventory is full; no record was silently evicted')
                db.execute('INSERT INTO successes VALUES (?,?,?,?)', (record['run_id'], basis['method_id'], record.get('conversation_id'), content))
    finally:
        db.close()
    return {'status': 'saved', 'method_id': basis['method_id'], 'run_id': record['run_id'], 'evidence_sha256': payload['evidence_sha256']}


def inventory(root, *, conversation_id=None, query=''):
    """Only own-chat records (or unlinked CLI records); no private chat pooling."""
    path = Path(root) / 'workflow-state' / 'successful-workflows.sqlite3'
    if not path.exists() and not path.is_symlink():
        return []
    db = _connection(root)
    try:
        rows = db.execute('SELECT payload FROM successes WHERE conversation_id IS ? ORDER BY run_id LIMIT ?', (conversation_id, MAX_RECORDS + 1)).fetchall()
    finally:
        db.close()
    if len(rows) > MAX_RECORDS:
        raise ValueError('Successful workflow inventory exceeds its budget')
    if not rows:
        return []
    current = contracts(root)
    groups = {}
    for (content,) in rows:
        if len(content.encode()) > 24_000: raise ValueError('Successful metadata exceeds its budget')
        entry = json.loads(content)
        if query.casefold() not in (' '.join([entry['name'], *entry['tags'], *(o['skill_id'] for o in entry['operations'])])).casefold():
            continue
        group = groups.setdefault(entry['method_id'], {k: entry[k] for k in ('method_id', 'name', 'tags', 'operations', 'evidence_kind', 'execution_authority_granted')})
        group.setdefault('sources', []).append({k: entry[k] for k in ('run_id', 'plan_sha256', 'evidence_sha256', 'finished_at')})
        group['contract_status'] = 'current' if all(current.get(o['skill_id'], {}).get('contract_sha256') == o['contract_sha256'] for o in entry['operations']) else 'changed_or_unavailable'
    return sorted(groups.values(), key=lambda g: max(s['finished_at'] for s in g['sources']), reverse=True)
