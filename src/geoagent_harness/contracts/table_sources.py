"""Closed table-reader contracts and bounded batches; standard library only.

This catalog describes trusted readers. It never imports discovered packages,
installs dependencies, approves an operation or dispatches user-supplied code.
"""
from dataclasses import dataclass, field
from datetime import date, time
from pathlib import PurePosixPath
from typing import Iterable, Iterator

CSV_MAX_BYTES = 1024**3
RECORD_MAX_BYTES = 16 * 1024**2
RECORD_MAX_ROWS = 200000
BATCH_ROWS = 256
BATCH_BYTES = 256 * 1024


@dataclass(frozen=True)
class TableFormat:
    id: str
    suffixes: tuple[str, ...]
    native_values: bool
    max_bytes: int
    max_rows: int | None
    selectors: tuple[str, ...] = ()
    requirements: tuple[tuple[str, str], ...] = ()
    inspect_on_send: bool = False
    reader_id: str = 'delimited'
    encoding: str = 'UTF-8'
    limitations: tuple[str, ...] = ()

    def describe(self):
        return {'id': self.id, 'suffixes': list(self.suffixes), 'reader_id': self.reader_id, 'encoding': self.encoding,
                'value_contract': 'native_scalars' if self.native_values else 'csv_text',
                'selection_parameters': list(self.selectors),
                'limits': {'file_bytes': self.max_bytes, 'rows': self.max_rows,
                           'columns': 100, 'cell_characters': 4096},
                'runtime_requirements': [{'distribution': name, 'requirement': version}
                                         for name, version in self.requirements],
                'inspect_on_send': self.inspect_on_send,
                'limitations': list(self.limitations),
                'effects': 'read_only', 'execution_authority': False}


FORMATS = (
    TableFormat('csv', ('.csv',), False, CSV_MAX_BYTES, None, ('delimiter',), inspect_on_send=True),
    TableFormat('tsv', ('.tsv',), False, CSV_MAX_BYTES, None, ('delimiter',), inspect_on_send=True),
    TableFormat('xlsx', ('.xlsx',), True, RECORD_MAX_BYTES, RECORD_MAX_ROWS,
                ('sheet', 'header_row', 'cell_range'),
                (('openpyxl', '>=3.1.5,<4'), ('defusedxml', '>=0.7.1,<1')),reader_id='records',encoding='XLSX XML',
                limitations=('Select a sheet when ambiguous; range first row is its header.', 'Literal values only: formulas/errors, macros and external links reject.')),
    TableFormat('json', ('.json',), True, RECORD_MAX_BYTES, RECORD_MAX_ROWS, ('records_key',),reader_id='records',
                limitations=('Flat record array, or explicit top-level records_key.', 'Nested cells, duplicate keys and new later columns reject; absent keys become null.')),
    TableFormat('jsonl', ('.jsonl', '.ndjson'), True, RECORD_MAX_BYTES, RECORD_MAX_ROWS,reader_id='records',
                limitations=('One flat object per nonempty line; no worksheet or records_key selectors.', 'Nested cells, duplicate keys and new later columns reject; absent keys become null.')),
)
TABLE_SUFFIXES = tuple(suffix for item in FORMATS for suffix in item.suffixes)
RECORD_SUFFIXES = tuple(suffix for item in FORMATS if item.reader_id=='records' for suffix in item.suffixes)


def table_format(path: str) -> TableFormat:
    suffix = PurePosixPath(path).suffix.lower()
    for item in FORMATS:
        if suffix in item.suffixes:
            return item
    raise ValueError('Unsupported table source format: ' + suffix)


def table_format_catalog():
    return {'schema_version': 'table-formats-v1', 'formats': [f.describe() for f in FORMATS],
            'analytical_value_contract': 'table-string-view-v1',
            'execution_authority': False}


@dataclass(frozen=True)
class TableRow:
    """A source record and its explicit legacy analytical representation."""
    native: tuple[str | int | float | bool | None | date | time, ...]
    analytical: tuple[str, ...]
    storage_types: tuple[str, ...]


@dataclass(frozen=True)
class TableBatch:
    rows: tuple[TableRow, ...]
    analytical_bytes: int = field(init=False)

    def __post_init__(self):
        if len(self.rows)>BATCH_ROWS or any(not isinstance(row,TableRow) for row in self.rows):
            raise ValueError('Table batch exceeds its row contract')
        if any(not isinstance(value,str) for row in self.rows for value in row.analytical):
            raise ValueError('The analytical compatibility view requires text values')
        size=sum(len(value.encode('utf-8')) for row in self.rows for value in row.analytical)
        if len(self.rows)>1 and size>BATCH_BYTES:
            raise ValueError('Table batch exceeds its payload contract')
        object.__setattr__(self,'analytical_bytes',size)


def row_batches(rows: Iterable[TableRow], *, checkpoint=None) -> Iterator[TableBatch]:
    """Bound retained rows/UTF-8 payload; one already-bounded large row can exceed 256 KB."""
    pending = []
    size = 0
    for row in rows:
        if not isinstance(row, TableRow):
            raise ValueError('A table reader must yield TableRow records')
        amount = sum(len(value.encode('utf-8')) for value in row.analytical)
        if pending and (len(pending) >= BATCH_ROWS or size + amount > BATCH_BYTES):
            if checkpoint:
                checkpoint()
            yield TableBatch(tuple(pending))
            pending, size = [], 0
        pending.append(row)
        size += amount
    if pending:
        if checkpoint:
            checkpoint()
        yield TableBatch(tuple(pending))
