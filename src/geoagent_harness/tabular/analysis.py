"""Incremental full-file profiles, codebook labels and bounded table pages."""
from collections import Counter
import math
import os
import json
import sys

from .analysis_contracts import AnalysisOptions
from geoagent_harness.discovery.csv import source, Reader, text_reader, records, identity


def codebook(root, path):
    """Read explicitly delimited two-column mapping sections, never a row join."""
    sections = {}
    current = None
    with source(root, path) as (fd, path, before):
        if before[2] > 256 * 1024:
            raise AnalysisError('Codebook exceeds 256 KiB')
        reader = Reader(fd, limit=256 * 1024)
        with text_reader(reader) as text:
            for row in records(text, ','):
                if not row or all(not value.strip() for value in row):
                    current = None
                    continue
                if len(row) != 2 or any(len(v) > 1000 for v in row):
                    raise AnalysisError('Codebook requires bounded two-column sections')
                key, description = (v.strip() for v in row)
                if current is None:
                    if not key or description.casefold() != 'description' or key in sections or len(sections) >= 16:
                        raise AnalysisError('Codebook section requires a unique field,description header')
                    current = key
                    sections[current] = {}
                else:
                    if not key or not description or key in sections[current] or len(sections[current]) >= 256:
                        raise AnalysisError('Codebook has empty/duplicate/over-budget codes')
                    sections[current][key] = description
        if identity(os.fstat(fd)) != before:
            raise AnalysisError('Codebook changed during read')
        with source(root, path) as (_, _, after):
            if after != before:
                raise AnalysisError('Codebook path changed during read')
    return {'path': path, 'sha256': reader.sha.hexdigest(), 'identity': before, 'sections': sections}


class AnalysisError(ValueError):
    """Safe, fixed analytical finding suitable for the interface."""


class Accumulator:
    """Bound state explicitly; never approximate exact requested counts silently."""
    def __init__(self, root, names, options):
        self.options = AnalysisOptions.model_validate(options or {})
        o = self.options
        requested = set(o.profile_columns + o.numeric_columns + o.count_columns + o.distinct_columns + o.quality_columns + o.duplicate_key + o.group_by + list(o.missing_values) + [f.column for f in o.filters])
        if requested - set(names):
            raise AnalysisError('Analytical column is not present in the source')
        if any(len(v) > 20 or any(len(token) > 200 for token in v) for v in o.missing_values.values()):
            raise AnalysisError('Missing-code declarations exceed their budget')
        self.columns = o.profile_columns or names
        self.page_columns = o.profile_columns or names[:16]
        reserved = {'row_count', 'proportion'} | {f'{n}_{s}' for n in o.numeric_columns for s in ('count','mean','sum','min','max')} | {f'{n}_count' for n in o.count_columns} | {f'{n}_distinct' for n in o.distinct_columns}
        if reserved.intersection(o.group_by):
            raise AnalysisError('Group keys conflict with summary output names')
        self.names = names
        self.mappings = codebook(root, o.codebook_path) if o.codebook_path else None
        self.root = root
        self.profiles = {name: {'missing': 0, 'empty': 0, 'values': Counter(), 'overflow': False} for name in self.columns}
        self.quality = {name: Counter() for name in o.quality_columns}
        self.row_keys, self.key_values = Counter(), Counter()
        self.key_missing = 0
        self.exact_bytes = self.exact_entries = self.group_distinct_entries = 0
        self.distinct = {name: set() for name in o.distinct_columns}
        self.numeric = {name: [0, 0.0, None, None, 0, 0.0] for name in o.numeric_columns}
        self.groups = {}
        self.page = []
        self.matched = 0
        self.coverage = {name: {'matched_rows': 0, 'unmatched_rows': 0, 'unknown_codes': Counter()} for name in (self.mappings['sections'] if self.mappings else {}) if name in names}

    def missing(self, name, value):
        return value == '' or value in self.options.missing_values.get(name, [])

    def reserve_exact(self, value):
        self.exact_entries += 1
        # Includes conservative per-entry mapping/count overhead; hard worker RSS
        # and CPU limits remain the outer boundary. No temporary dataset writes.
        self.exact_bytes += sys.getsizeof(value) + 128
        if self.exact_entries > 500000 or self.exact_bytes > 128 * 1024**2:
            raise AnalysisError('Exact quality budget exceeded (500,000 entries / 128 MiB state); narrow the request. No partial checks returned')

    def count_exact(self, counter, value):
        if value not in counter:
            self.reserve_exact(value)
        counter[value] += 1

    @staticmethod
    def frequency_summary(counter):
        repeated = [count for count in counter.values() if count > 1]
        return {'status': 'exact', 'distinct_count': len(counter),
                'once_only_values': sum(count == 1 for count in counter.values()),
                'repeated_values': len(repeated), 'rows_in_repeated_groups': sum(repeated),
                'excess_occurrences': sum(count - 1 for count in repeated)}

    def add(self, row):
        values = dict(zip(self.names, row))
        if any(values[f.column] != f.value for f in self.options.filters):
            return
        self.matched += 1
        o = self.options
        if o.offset < self.matched <= o.offset + o.limit:
            self.page.append({name: values[name][:160] or None for name in self.page_columns})
        for name, p in self.profiles.items():
            value = values[name]
            p['empty'] += value == ''
            if self.missing(name, value):
                p['missing'] += 1
            elif not p['overflow']:
                p['values'][value] += 1
                if len(p['values']) > 128:
                    p['values'].clear()
                    p['overflow'] = True
        for name, counter in self.quality.items():
            if not self.missing(name, values[name]):
                self.count_exact(counter, values[name])
        if o.duplicate_rows:
            self.count_exact(self.row_keys, json.dumps(row, ensure_ascii=False, separators=(',', ':')))
        if o.duplicate_key:
            if any(self.missing(name, values[name]) for name in o.duplicate_key):
                self.key_missing += 1
            else:
                self.count_exact(self.key_values, json.dumps([values[name] for name in o.duplicate_key], ensure_ascii=False, separators=(',', ':')))
        for name, seen in self.distinct.items():
            if not self.missing(name, values[name]):
                if values[name] not in seen:
                    self.reserve_exact(values[name])
                seen.add(values[name])
                if len(seen) > 250000:
                    raise AnalysisError('Exact distinct-count budget exceeded; no approximation returned')
        parsed = {}
        for name, stats in self.numeric.items():
            if self.missing(name, values[name]):
                continue
            try:
                number = float(values[name])
            except ValueError:
                stats[4] += 1
                continue
            if not math.isfinite(number) or abs(number) > 1e15:
                raise AnalysisError('Numeric profile requires finite values within 1e15')
            parsed[name] = number
            stats[0] += 1
            stats[1] += (number - stats[1]) / stats[0]
            stats[2] = number if stats[2] is None else min(number, stats[2])
            stats[3] = number if stats[3] is None else max(number, stats[3])
            stats[5] += number
            if not math.isfinite(stats[5]):
                raise AnalysisError('Numeric sum overflow')
        if o.group_by:
            key = tuple(values[name] for name in o.group_by)
            group = self.groups.setdefault(key, {'row_count': 0, 'counts': {n: 0 for n in o.count_columns},
                                                 'distinct': {n: set() for n in o.distinct_columns},
                                                 'numeric': {n: [0, 0.0, 0.0, None, None] for n in o.numeric_columns}})
            if len(self.groups) > 2000:
                raise AnalysisError('Group budget exceeds 2,000; no partial aggregate returned')
            group['row_count'] += 1
            for name, seen in group['distinct'].items():
                value = values[name]
                if not self.missing(name, value) and value not in seen:
                    self.reserve_exact(value)
                    seen.add(value)
                    self.group_distinct_entries += 1
                    if self.group_distinct_entries > 250000:
                        raise AnalysisError('Grouped exact distinct budget exceeds 250,000 entries; no partial aggregate returned')
            for name in o.count_columns:
                if not self.missing(name, values[name]):
                    group['counts'][name] += 1
            for name, number in parsed.items():
                n = group['numeric'][name]
                n[0] += 1
                n[1] += (number - n[1]) / n[0]
                n[2] += number
                n[3] = number if n[3] is None else min(n[3], number)
                n[4] = number if n[4] is None else max(n[4], number)
        for name, coverage in self.coverage.items():
            value = values[name]
            if value in self.mappings['sections'][name]:
                coverage['matched_rows'] += 1
            else:
                coverage['unmatched_rows'] += 1
                if value in coverage['unknown_codes'] or len(coverage['unknown_codes']) < 20:
                    coverage['unknown_codes'][value] += 1

    def result(self, total):
        if self.mappings:
            with source(self.root, self.mappings['path']) as (_, _, after):
                if after != self.mappings['identity']:
                    raise AnalysisError('Codebook changed while profiling the main table')
        profiles = []
        for name, p in self.profiles.items():
            category_values = self.quality.get(name, p['values'])
            category_available = name in self.quality or not p['overflow']
            categories = [] if not category_available else [
                {'value': value[:160], 'count': count, 'proportion': count / self.matched if self.matched else None,
                 'description': (self.mappings['sections'].get(name, {}).get(value) if self.mappings else None)}
                for value, count in category_values.most_common(12)]
            numeric = dict(zip(('count','mean','minimum','maximum','invalid_count','sum'), self.numeric[name])) if name in self.numeric else None
            if numeric is not None and numeric['count'] == 0:
                numeric['mean'] = None
            frequency = self.frequency_summary(self.quality[name]) if name in self.quality else None if p['overflow'] else self.frequency_summary(p['values'])
            profiles.append({'name': name, 'missing_count': p['missing'], 'empty_count': p['empty'],
                'declared_missing_count': p['missing'] - p['empty'],
                'frequency': frequency, 'missing_tokens': self.options.missing_values.get(name, []),
                'distinct_count': frequency['distinct_count'] if frequency is not None else len(self.distinct[name]) if name in self.distinct else None,
                'categories': categories, 'categories_status': 'exact_counts_top_12' if category_available else 'unavailable_above_128_distinct',
                'numeric': numeric})
        groups = [{**dict(zip(self.options.group_by, key)), 'row_count': v['row_count'],
                   'proportion': v['row_count'] / self.matched,
                   **{f'{n}_count': stats[0] for n, stats in v['numeric'].items()},
                   **{f'{n}_count': count for n, count in v['counts'].items()},
                   **{f'{n}_distinct': len(seen) for n, seen in v['distinct'].items()},
                   **{f'{n}_{metric}': stats[index] if stats[0] else None for n, stats in v['numeric'].items()
                      for metric, index in [('mean',1),('sum',2),('min',3),('max',4)]}}
                  for key, v in sorted(self.groups.items())]
        return {'schema_version': 'table-analysis-v1', 'scope': 'complete_parsed_file', 'source_row_count': total,
            'matched_row_count': self.matched, 'available_columns': self.names, 'columns': self.columns, 'columns_omitted': [n for n in self.names if n not in self.columns],
            'quality': {'scope': 'matching_rows',
                'columns': {n: self.frequency_summary(c) for n, c in self.quality.items()},
                'duplicate_rows': self.frequency_summary(self.row_keys) if self.options.duplicate_rows else None,
                'duplicate_key': {**self.frequency_summary(self.key_values), 'columns': self.options.duplicate_key,
                    'missing_key_rows': self.key_missing, 'missing_policy': 'exclude rows with any missing key field',
                    'candidate_key': self.key_missing == 0 and self.matched > 0 and len(self.key_values) == self.matched} if self.options.duplicate_key else None,
                'limits': {'exact_entries': 500000, 'estimated_state_bytes': 128 * 1024**2, 'group_distinct_entries': 250000}},
            'profiles': profiles, 'distinct_counts': {n: len(v) for n, v in self.distinct.items()},
            'groups': groups, 'group_by': self.options.group_by, 'denominator': self.matched,
            'table': {'columns': self.page_columns, 'preview': self.page, 'row_count': self.matched,
                      'columns_omitted': [n for n in self.names if n not in self.page_columns], 'cell_characters': 160,
                      'offset': self.options.offset, 'limit': self.options.limit, 'preview_truncated': len(self.page) < self.matched},
            'codebook': {**self.mappings, 'coverage': self.coverage,
                         'unbound_sections': [n for n in self.mappings['sections'] if n not in self.names]} if self.mappings else None,
            'request': self.options.model_dump(mode='json'),
            'checks': {'group_count_reconciles': not self.options.group_by or sum(v['row_count'] for v in groups) == self.matched,
                       'page_within_matches': len(self.page) <= self.matched},
            'limitations': ['Definitions are supplied codebook claims, not independent clinical verification.',
                'Numeric columns are explicitly requested; values are not inferred to be measurements.',
                'Category counts cover matching full-file rows; display shows at most 12 categories per column.',
                'Unknown-code examples are capped at 20; unmatched_rows counts all unmatched values.']}
