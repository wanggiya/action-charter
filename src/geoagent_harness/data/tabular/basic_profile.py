"""Bounded basic inspection aggregates and pure recorded-evidence reporting.

No new scan, model call, arbitrary expression or authority. Cardinality counters
have a shared memory budget; exhausted counters become unavailable, never samples.
Compact positional records keep ordinary worker outcomes within their 16 KB limit.
"""
import hashlib
import json
import math
import sys
from collections import Counter

from geoagent_harness.data.tabular.field_guidance import classify_role


FIELD_COLUMNS = ['name', 'role', 'distinct', 'once_only', 'repeated_values', 'excess_occurrences']
NUMERIC_COLUMNS = ['count', 'mean', 'minimum', 'maximum', 'sample_standard_deviation', 'non_numeric']


class BasicProfile:
    """Exact nonmissing value counts plus SHA-256 whole-row duplicate counts.

    Memory estimates deliberately include dictionary overhead. Once a counter
    exceeds a budget it is cleared; other counts and the complete scan continue.
    """
    def __init__(self, names, missing_values=None, *, max_entries=500000, max_bytes=64 * 1024**2):
        self.counts = [Counter() for _ in names] + [Counter()]
        self.costs = [0] * len(self.counts)
        self.entries = self.bytes = 0
        self.max_entries, self.max_bytes = max_entries, max_bytes
        self.missing = missing_values or {}
        self.names = list(names)

    def _add(self, index, value):
        counter = self.counts[index]
        if counter is None:
            return
        if value in counter:
            counter[value] += 1
            return
        cost = sys.getsizeof(value) + 160
        if self.entries + 1 > self.max_entries or self.bytes + cost > self.max_bytes:
            self.entries -= len(counter)
            self.bytes -= self.costs[index]
            self.counts[index] = None
            return
        self.entries += 1
        self.bytes += cost
        self.costs[index] += cost
        counter[value] = 1

    def add(self, row):
        for i, (name, value) in enumerate(zip(self.names, row.analytical)):
            if value != '' and value not in self.missing.get(name, ()):
                self._add(i, value)
        if self.counts[-1] is not None:
            # Include native storage types: JSON null, empty text and date text
            # must not collapse to the same record through the analytical view.
            encoded = json.dumps([row.storage_types, row.native], default=str,
                                 separators=(',', ':'), ensure_ascii=True).encode()
            self._add(len(self.names), hashlib.sha256(encoded).digest())

    @staticmethod
    def _summary(counter):
        if counter is None:
            return [None] * 4
        return [len(counter), sum(n == 1 for n in counter.values()),
                sum(n > 1 for n in counter.values()), sum(n - 1 for n in counter.values())]

    def result(self, guidance, source, sha256):
        fields, numeric = [], {}
        for i, (name, p) in enumerate(guidance.fields.items()):
            role, _, _ = classify_role(name, coded=name in guidance.coded,
                **{k: p[k] for k in ('nonmarker', 'numeric', 'integer', 'minimum', 'bands', 'overflow')})
            fields.append([name, role, *self._summary(self.counts[i])])
            if role in {'numerical', 'count'} and p['numeric']:
                n = p['numeric']
                numeric[name] = [n, p['mean'], p['minimum'], p['maximum'],
                    math.sqrt(max(0., p['m2']) / (n - 1)) if n > 1 else None,
                    guidance.rows - p['missing'] - n]
        return {'schema_version': 'basic-table-profile-v1', 'source': source,
            'source_sha256': sha256, 'rows': guidance.rows,
            'field_columns': FIELD_COLUMNS, 'fields': fields,
            'numeric_columns': NUMERIC_COLUMNS, 'numeric': numeric,
            'duplicate_rows': self._summary(self.counts[-1]),
            'duplicate_method': 'SHA-256 of complete typed native records; theoretical hash collisions remain possible',
            'missing_values': self.missing, 'omitted_fields': 0,
            'candidate_missing_markers': {name: dict(p['markers']) for name, p in guidance.fields.items() if p['markers']},
            'limits': {'entries': self.max_entries, 'estimated_bytes': self.max_bytes},
            'scope': 'complete_selected_table', 'roles': 'candidates, not domain definitions'}


def bound_profile(profile, max_bytes):
    """Only presentation may be shortened; omissions never become zero counts."""
    while len(json.dumps(profile, separators=(',', ':'), allow_nan=False).encode()) > max_bytes:
        if not profile['fields']:
            return None
        field = profile['fields'].pop()
        profile['numeric'].pop(field[0], None)
        profile['omitted_fields'] += 1
    return profile


def recorded_report(outcome):
    """Render saved table facts, including legacy metadata-only inspections.

    No filesystem access. Absence of evidence is never a zero or a passing check.
    A profile from another source/hash/row scope is not used.
    """
    from geoagent_harness.data.tabular.readiness import _cell, _table
    source, sha, rows = (outcome.get(k) for k in ('source', 'source_sha256', 'row_count'))
    columns = outcome.get('columns')
    if not (source and sha and isinstance(rows, int) and isinstance(columns, list)
            and isinstance(outcome.get('missing_counts'), dict)):
        return None
    scope = (outcome.get('table_source') or {}).get('scope',
                (outcome.get('discovery') or {}).get('statistics_scope', 'not recorded'))
    profile = outcome.get('basic_profile') or {}
    valid = (profile.get('schema_version') == 'basic-table-profile-v1'
        and profile.get('source') == source and profile.get('source_sha256') == sha
        and profile.get('rows') == rows and profile.get('field_columns') == FIELD_COLUMNS
        and profile.get('numeric_columns') == NUMERIC_COLUMNS)
    profile = profile if valid else {}
    fields = {f[0]: f for f in profile.get('fields', [])}
    advice = outcome.get('field_guidance') or {}
    if advice.get('source') != source or advice.get('source_sha256') != sha or advice.get('matching_rows') != rows:
        advice = {}
    hints = {f['name']: f for f in advice.get('fields', [])}
    missing = outcome['missing_counts']
    native = outcome.get('data_contract') == 'table/records-v1'
    schema = (outcome.get('table_source') or {}).get('schema', {})
    nulls, empty = schema.get('null_counts', {}), schema.get('empty_string_counts', {})
    parts = ['# Recorded inspection quality', '## Source and scope',
        _table(['Source', 'SHA-256', 'Rows', 'Columns', 'Scope'], [[source, sha, rows, len(columns), scope]]),
        'Counts cover the recorded complete table, not the preview rows. Row counts are not distinct-person counts. '
        'No source was reread and no model or workflow was run to produce this report. '
        'A saved hash identifies the inspected version, not current file freshness.',
        '## Missingness and field coverage',
        'Metadata missingness: ' + ('native nulls; empty text is reported separately.' if native else
            'empty CSV cells only; literal markers such as ? and NA remain values.'),
        'Profile distinct/repeat counts exclude empty analytical cells and explicitly declared missing tokens. '
        'Once-only means values occurring exactly once; excess occurrences means occurrences after the first. '
        'Unavailable cardinality is not a sampled estimate. Roles are candidates; identifiers and codes are not automatically measurements.']
    table, cardinality = [], []
    for name in columns:
        field, hint = fields.get(name), hints.get(name, {})
        count = missing.get(name)
        distinct = field[2] if field else hint.get('distinct_count')
        role = field[1] if field else hint.get('role', 'Not recorded')
        table.append([name, (outcome.get('column_types') or {}).get(name, 'Not recorded'), role,
            count, round(100 * count / rows, 3) if rows and isinstance(count, (int, float)) else None,
            empty.get(name, 0) if native and schema else '—'])
        cardinality.append([name,
            distinct if distinct is not None else 'Not calculated / budget limited',
            field[3] if field and field[3] is not None else 'Not calculated',
            field[4] if field and field[4] is not None else 'Not calculated',
            field[5] if field and field[5] is not None else 'Not calculated'])
    parts.append(_table(['Field', 'Storage type', 'Candidate role', 'Missing', 'Missing %', 'Empty text'], table))
    parts += ['## Distinct and repeated values',
        _table(['Field', 'Distinct nonmissing', 'Once-only values', 'Repeated values', 'Excess occurrences'], cardinality)]
    if profile.get('omitted_fields'):
        parts.append(f"Response budget omitted basic profiles for {profile['omitted_fields']} fields; missingness remains recorded above.")
    if native and nulls:
        parts.append('Native null counts: ' + _cell(json.dumps(nulls, sort_keys=True)))
    policy = profile.get('missing_values')
    parts.append('Declared profile missing tokens: ' + _cell(json.dumps(policy, sort_keys=True))
                 if policy is not None else 'Declared profile missing-token policy: not recorded.')
    markers = profile.get('candidate_missing_markers', {})
    if markers:
        parts += ['## Candidate missing markers',
            'Observed marker strings require domain definitions; they are values unless explicitly declared missing.',
            _table(['Field', 'Marker', 'Occurrences'], [[name, token, count]
                for name, counts in markers.items() if isinstance(counts, dict) for token, count in counts.items()])]
    parts += ['## Whole-row duplicates']
    duplicates = profile.get('duplicate_rows')
    if duplicates and duplicates[0] is not None:
        parts += [_table(['Distinct rows', 'Once-only rows', 'Repeated row patterns', 'Excess duplicate rows'], [duplicates]),
            _cell(profile['duplicate_method']),
            'Whole-row duplicates do not establish a patient/entity key. Repeated observations can be legitimate.']
    else:
        parts.append('Not calculated / counter budget exceeded. This is not a zero-duplicate result.')
    parts += ['## Numerical summaries']
    numeric = {name: values for name, values in profile.get('numeric', {}).items()
               if isinstance(values, list) and len(values) == len(NUMERIC_COLUMNS)}
    if numeric:
        parts += [_table(['Field', 'Numeric count', 'Mean', 'Minimum', 'Maximum', 'Sample standard deviation',
            'Non-numeric nonmissing'], [[name, *values] for name, values in numeric.items()]),
            'Finite numeric values within ±10^15 only; incompatible values and undeclared marker strings are excluded '
            'and counted as non-numeric, never silently imputed. Sample standard deviation uses n−1 and is unavailable for n<2. '
            'These are descriptive candidate measurements; units and domain meaning require review.']
    else:
        parts.append('No basic numerical summaries recorded. No means or ranges were invented.')
    parts += ['## Analysis coverage and limits',
        'The basic-quality section does not calculate correlation, regression coefficients, P-values, confidence intervals, '
        'prediction error, precision or causality. Those require a specified analysis, valid input roles and an actual recorded calculation. '
        'Use the recorded statistical/readiness sections when present; absence is not a negative finding.',
        'Distinct/repeat counters are memory bounded. A missing count is not zero; no partial counter is presented as a full-table result. '
        'Downloads preserve recorded scope and do not create new analysis.']
    return '\n\n'.join(parts) + '\n'
