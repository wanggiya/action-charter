"""One analytical consumer/result builder for trusted table-source adapters.

Readers own parsing, selection, file/hash verification and native conversion. This
pipeline owns full-table counters, bounded preview, analysis, guidance and projection.
Legacy fields/reference identities remain compatible; table_source is additive.
"""
import datetime
from collections import Counter
import json
import re

from .source_contracts import TableRow, TableBatch, table_format, row_batches
from .field_guidance import GuidanceAccumulator, bound_guidance


def inspect_table(root, path, **options):
    """Closed trusted-reader selection, independent of frontend/CLI/MCP callers."""
    kind = table_format(path)
    if kind.reader_id == 'records':
        from .table_sources import inspect
    elif kind.reader_id == 'delimited':
        from geoagent_harness.discovery.csv import inspect
    else:
        raise ValueError('No qualified table reader is registered for ' + kind.id)
    return inspect(root, path, **options)


class TableInspection:
    def __init__(self, root, path, columns, *, analysis=None, preview_rows=5, row_limit=None):
        self.root, self.path, self.columns = root, path, list(columns)
        self.format = table_format(path)
        self.analysis, self.preview_rows = analysis, preview_rows
        self.row_limit = self.format.max_rows if row_limit is None else row_limit
        self.analytical = None
        if analysis is not None:
            from .analysis import Accumulator
            self.analytical = Accumulator(root, self.columns, analysis)
        mappings = self.analytical.mappings if self.analytical else None
        self.guidance = GuidanceAccumulator(self.columns, (analysis or {}).get('missing_values'),
                                           (mappings or {}).get('sections', {}))
        self.count = 0
        self.preview = []
        self.collect_preview = True
        self.missing = dict.fromkeys(self.columns, 0)
        self.nulls = dict.fromkeys(self.columns, 0)
        self.empty = dict.fromkeys(self.columns, 0)
        self.types = {name: set() for name in self.columns}

    def consume(self, rows, *, checkpoint=None):
        for batch in row_batches(rows, checkpoint=checkpoint):
            self.add_batch(batch)

    def add_batch(self, batch: TableBatch):
        from geoagent_harness.discovery.csv import row_values, append_preview
        if not isinstance(batch, TableBatch):
            raise ValueError('TableInspection requires typed TableBatch input')
        for row in batch.rows:
            if not (len(row.native) == len(row.analytical) == len(row.storage_types) == len(self.columns)):
                raise ValueError('Reader row does not match the declared table schema')
            row_values(row.analytical, self.columns)
            self.count += 1
            if self.row_limit is not None and self.count > self.row_limit:
                raise ValueError('Record source exceeds 200,000 rows; no implicit sample')
            self.guidance.add(row.analytical)
            if self.analytical is not None:
                self.analytical.add(row.analytical)
            for name, value, kind in zip(self.columns, row.native, row.storage_types):
                self.types[name].add(kind)
                self.nulls[name] += value is None
                self.empty[name] += isinstance(value, str) and value == ''
                self.missing[name] += (value is None) if self.format.native_values else (value == '')
            if not self.format.native_values:
                if self.collect_preview:
                    self.collect_preview = append_preview(self.preview, self.columns, row.analytical, self.preview_rows)
            elif len(self.preview) < self.preview_rows:
                item = {name: value[:160] if isinstance(value, str) else
                        value.isoformat() if isinstance(value, (datetime.date, datetime.time)) else value
                        for name, value in zip(self.columns[:20], row.native[:20])}
                if len(json.dumps(self.preview + [item]).encode()) <= 4096:
                    self.preview.append(item)

    def finish(self, *, sha256, file_bytes, delimiter=',', selection=None, source_options=None):
        """Called only after the reader's complete hash/stat/path checks succeed."""
        from geoagent_harness.discovery.csv import metadata
        if not re.fullmatch(r'[a-f0-9]{64}', sha256):
            raise ValueError('A completed table inspection requires a full SHA-256')
        result = metadata(self.path, file_bytes, self.columns, self.preview, min(self.count, 20))
        result.update(row_count=self.count, missing_counts=self.missing,
                      preview_truncated=len(self.preview) < self.count, source_sha256=sha256)
        native = self.format.native_values
        if native:
            result.update(data_contract='table/records-v1',
                          column_types={n: ' | '.join(sorted(t)) for n, t in self.types.items()},
                          source_format=self.path.rsplit('.', 1)[-1].lower(),
                          source_selection=selection or {}, empty_string_counts=self.empty)
        result['discovery'].update(phase='completed', verification='sha256_complete',
            statistics_scope='complete_parsed_file', bytes_hashed=file_bytes,
            encoding=self.format.encoding if native else 'UTF-8 (validated for complete content)')
        if native:
            result['discovery']['schema_version'] = 'record-discovery-v1'
            result['warnings'] = [
                'Original file identity retained; no conversion artifact was written.',
                'Analytical view uses strings; null and empty string both count as missing in analysis. Native type, null and empty-string counts remain separate in metadata.',
                'Numeric cell formatting is not a text identifier; store leading-zero identifiers as text. Dates use ISO text.',
                'Flat records only; absent keys become null. New keys after the first record reject.']
        else:
            result['discovery']['consistency'] = 'opened-file and pathname stat checks; not an immutable snapshot'
            result['warnings'] = ['Values remain strings; empty fields are missing; literal NA/NULL are preserved.',
                'Preview is bounded to 20 columns, requested rows and 4 KiB.',
                'Complete CSV exploration and transformations retain their separate limits.']
        kinds = {n: tuple(sorted(self.types[n])) for n in self.columns}
        default_types = Counter(kinds.values()).most_common(1)[0][0]
        result['table_source'] = {
            'schema_version': 'table-source-v1', 'path': self.path, 'sha256': sha256,
            'format': self.format.id, 'selection': selection or {},
            'source_options': source_options, 'delimiter': delimiter if not native else None,
            'rows': self.count, 'scope': 'complete_selected_table' if native else 'complete_parsed_file',
            'record_grain': 'parsed_table_record',
            'schema': {'columns': self.columns, 'storage_types_default': list(default_types),
                'storage_types_overrides': {n: list(t) for n, t in kinds.items() if t != default_types},
                'null_counts': {n: v for n, v in self.nulls.items() if v},
                'empty_string_counts': {n: v for n, v in self.empty.items() if v},
                'absent_count_means': 0},
            'analytical_view': {'schema_version': 'table-string-view-v1',
                'conversion': 'native scalars to text; null to empty; dates to ISO' if native else 'source CSV text',
                'missingness': 'empty analytical cells and explicitly declared tokens; no imputation',
                'numeric_selection': 'explicit parameters, never identifier/type inference'},
            'verified': 'full_sha256_and_reader_identity_checks', 'effects': 'read_only',
            'execution_authority': False}
        from .analysis_contracts import TableSourceDescriptor
        TableSourceDescriptor.model_validate(result['table_source'])
        if self.analytical is not None:
            result['table_analysis'] = self.analytical.result(self.count)
            statistics = result['table_analysis'].get('statistics')
            if statistics:
                from .statistics import render_report
                statistics.update(source={'path': self.path, 'sha256': sha256}, source_rows=self.count)
                if native:
                    statistics['source_selection'] = {**(source_options or {}),
                        **{k: v for k, v in (selection or {}).items() if k != 'available_sheets'},
                        'scope': 'complete selected table; hash identifies original file'}
                statistics['report_markdown'] = render_report(statistics)
            result['delimiter'] = delimiter
            from .analytical_service import source_reference
            result['table_reference'] = source_reference(result)
        available = (128000 if self.analysis is not None else 16000) - len(json.dumps(result, separators=(',', ':'), allow_nan=False).encode()) - 512
        advice = self.guidance.result(self.path, sha256)
        if native:
            advice['source_options'] = source_options or {}
            for starter in advice['analysis_starters']:
                starter['analysis']['source_options'] = source_options or {}
        advice = bound_guidance(advice, min(12000, available))
        if advice is not None:
            result['field_guidance'] = advice
        elif not native:
            result['warnings'].append('Field guidance unavailable within this response budget; use comprehensive profiling.')
        if self.analytical is not None:
            from .readiness import attach_assessment
            attach_assessment(result)
        return result
