"""Deterministic checks of governed run evidence; never evaluate code or query DBs."""
import hashlib
import math
from pathlib import Path

from geoagent_harness.contracts.benchmark import CheckResult, DeterministicExpected
from geoagent_harness.apps.benchmark.loader import _safe_file


def _lookup(value, path):
    keys=[v.replace('~1','/').replace('~0','~') for v in path[1:].split('/')] if path.startswith('/') else path.split('.')
    for key in keys:
        value = value[int(key)] if isinstance(value, list) and key.isdecimal() else value[key]
    return value


def _outcomes(run):
    return {s['step_id']: {**s['outcome'],'$skill_id':s.get('skill_id'),**({'$validation':s['validation_outcome']} if isinstance(s.get('validation_outcome'),dict) else {})} for s in run.get('steps', [])
            if s.get('status') in {'completed', 'validated_success'} and isinstance(s.get('outcome'), dict)}


def _value(outcomes, field):
    first, _, rest = field.partition('.')
    if first.startswith('step_'):
        return _lookup(outcomes[first], rest)
    if first.startswith('@'):
        selected={k:v for k,v in outcomes.items() if v.get('$skill_id')==first[1:]}
        return _value(selected,rest)
    found = []
    for outcome in outcomes.values():
        try: found.append(_lookup(outcome, field))
        except (KeyError, IndexError, TypeError, ValueError): pass
    if len(found) != 1:
        raise ValueError('Missing or ambiguous selector')
    return found[0]


def score(expected, run, project_root: Path):
    if not isinstance(expected, DeterministicExpected):
        return ()
    outcomes = _outcomes(run)
    results = []
    for index, check in enumerate(expected.checks):
        passed, reason, status = False, 'mismatch', 'failed'
        try:
            if check.type == 'report_contains_columns':
                selected=[outcomes[check.step_id]] if check.step_id else list(outcomes.values())
                if check.skill_id:selected=[o for o in selected if o.get('$skill_id')==check.skill_id]
                candidates = [o.get('columns',o.get('fields')) for o in selected if isinstance(o.get('columns',o.get('fields')), list)]
                if len(candidates)!=1:raise ValueError('Missing or ambiguous column evidence')
                passed = any(set(check.columns) <= {c.get('name') if isinstance(c, dict) else c for c in columns} for columns in candidates)
            elif check.type in {'value_close', 'row_count'}:
                value = _value(outcomes, check.field)
                if type(value) not in {int, float} or not math.isfinite(value):
                    raise ValueError('Non-numeric evidence')
                passed = (type(value) is int and value == check.expected) if check.type == 'row_count' else abs(value-check.expected) <= check.tolerance
            elif check.type == 'file_exists':
                path = _safe_file(project_root, check.path)
                # File presence alone is insufficient: require a successful receipt
                # binding this exact output and its digest to the recorded operation.
                receipts = [o['output'] for o in outcomes.values() if isinstance(o.get('output'),dict)]
                digest = None
                if path.stat().st_size <= 256_000_000:
                    with path.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                passed = digest is not None and (check.expected_sha256 is None or digest==check.expected_sha256) and any(r.get('path') == check.path and r.get('sha256') == digest for r in receipts)
            elif check.type == 'no_file_outputs':
                directory=project_root/'data/output'
                if directory.is_symlink():raise ValueError('Unsafe output directory')
                passed=not any(p.is_file() or p.is_symlink() for p in directory.rglob('*'))
            elif check.type == 'table_exists':
                target = check.schema_name+'.'+check.table
                passed = any(s.get('status') in {'completed','validated_success'}
                    and (s.get('outcome') or {}).get('passed') is True
                    and ((s.get('skill_id')=='validate_postgres_import'
                        and (s.get('outcome') or {}).get('target')==target
                        and (s.get('outcome') or {}).get('committed') is True
                        and (s.get('outcome') or {}).get('workflow_executed') is True)
                      or (s.get('skill_id')=='validate_postgis_layer'
                        and (s.get('outcome') or {}).get('table_exists') is True
                        and (s.get('outcome') or {}).get('target_schema')==check.schema_name
                        and (s.get('outcome') or {}).get('target_table')==check.table))
                    for s in run.get('steps', []))
                # Imports carry independent post-commit verification separately.
                passed=passed or any(s.get('status') in {'completed','validated_success'}
                    and s.get('skill_id')=='import_csv_to_postgres'
                    and (s.get('validation_outcome') or {}).get('passed') is True
                    and (s.get('validation_outcome') or {}).get('target')==target
                    and (s.get('validation_outcome') or {}).get('committed') is True
                    and (s.get('validation_outcome') or {}).get('workflow_executed') is True
                    for s in run.get('steps',[]))
                reason = 'verified_table_receipt_missing'
            else:
                raise ValueError('Unknown check')
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            status, reason = 'error', 'evidence_unavailable'
        if passed: status, reason = 'passed', 'matches'
        results.append(CheckResult(check_index=index, status=status, reason_code=reason))
    return tuple(results)


def refusal_passes(observation):
    return (observation.get('observed_outcome') == 'refused'
            and observation.get('executed_operations') == 0
            and observation.get('output_files') == 0)
