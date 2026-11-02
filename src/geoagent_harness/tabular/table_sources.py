"""Bounded read-only record adapters feeding the existing analytical accumulator.

No source conversion files, arbitrary reader kwargs, macros, formulas or nested-cell
flattening. Native source types are recorded; analytical values use the CSV string view.
"""
from contextlib import ExitStack
import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import stat
import zipfile

from geoagent_harness.discovery.source import relative_path,_parent
from geoagent_harness.discovery.csv import identity,header
from .source_contracts import RECORD_SUFFIXES, RECORD_MAX_BYTES, RECORD_MAX_ROWS, TableRow
from .analysis_contracts import TableSourceOptions

SUFFIXES=set(RECORD_SUFFIXES)
MAX_BYTES=RECORD_MAX_BYTES
MAX_ROWS=RECORD_MAX_ROWS


def _object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON keys are ambiguous')
        result[key]=value
    return result


def _scalar(value):
    if value is None:return '', 'null'
    if isinstance(value,bool):return str(value).lower(),'boolean'
    if isinstance(value,(datetime.datetime,datetime.date,datetime.time)):return value.isoformat(),'datetime'
    if isinstance(value,str):return value,'string'
    if isinstance(value,(int,float)):
        if not math.isfinite(value):raise ValueError('Non-finite numeric source value')
        return str(value),'integer' if isinstance(value,int) else 'number'
    raise ValueError('Nested arrays/objects are not table cells; select or flatten records explicitly outside this reader')


def _json_records(stream,options,lines):
    if options.cell_range:raise ValueError('JSON does not accept spreadsheet ranges')
    decoder=json.JSONDecoder(object_pairs_hook=_object,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Non-finite JSON value')))
    if lines:
        if options.records_key or options.sheet or options.header_row!=1:raise ValueError('JSON Lines does not accept sheet/header/records_key options')
        for line in stream:
            if len(line)>1024**2:raise ValueError('JSON Lines record exceeds 1 MiB')
            if not line.strip():continue
            yield decoder.decode(line)
        return
    if options.sheet or options.header_row!=1:raise ValueError('JSON does not accept spreadsheet selection options')
    # A bounded object wrapper is explicit; a plain record array streams incrementally.
    if options.records_key:
        text=stream.read(MAX_BYTES+1)
        if len(text)>MAX_BYTES:raise ValueError('JSON wrapper exceeds 16 MiB')
        value=decoder.decode(text)
        if not isinstance(value,dict) or options.records_key not in value or not isinstance(value[options.records_key],list):raise ValueError('records_key must select a top-level array of records')
        yield from value[options.records_key];return
    buffer='';ended=False
    def fill():
        nonlocal buffer,ended
        chunk=stream.read(65536);buffer+=chunk
        if not chunk:ended=True
    def space():
        nonlocal buffer
        while True:
            buffer=buffer.lstrip()
            if buffer or ended:return
            fill()
    fill();space()
    if not buffer.startswith('['):raise ValueError('JSON table requires a record array, or explicit source_options.records_key; GeoJSON is not a JSON table')
    buffer=buffer[1:];first=True
    while True:
        space()
        if buffer.startswith(']'):
            buffer=buffer[1:];break
        if not first:
            if not buffer.startswith(','):raise ValueError('Invalid JSON record-array separator')
            buffer=buffer[1:];space()
            if buffer.startswith(']'):raise ValueError('Trailing JSON comma is invalid')
        while True:
            try:value,end=decoder.raw_decode(buffer);break
            except json.JSONDecodeError:
                if ended or len(buffer)>1024**2:raise ValueError('Malformed JSON or record exceeds 1 MiB') from None
                fill()
        if end>1024**2:raise ValueError('JSON record exceeds 1 MiB')
        yield value;buffer=buffer[end:];first=False
    space()
    if not ended:buffer+=stream.read(MAX_BYTES+1)
    if buffer.strip():raise ValueError('Unexpected content after JSON record array')


def _rows(stream,suffix,options,stack,selection):
    if suffix=='.xlsx':
        if options.records_key:raise ValueError('XLSX does not accept records_key')
        try:
            import defusedxml.ElementTree
            import openpyxl
        except ImportError:raise ValueError('XLSX runtime unavailable; install the project table-formats dependency profile in the launcher environment') from None
        with zipfile.ZipFile(stream) as archive:
            infos=archive.infolist()
            if len(infos)>2000 or sum(i.file_size for i in infos)>64*1024**2 or any(i.file_size>32*1024**2 for i in infos):raise ValueError('Workbook expanded ZIP budget exceeded')
            if any('vbaproject' in i.filename.lower() or i.filename.startswith('xl/externalLinks/') for i in infos):raise ValueError('Macros and external workbook links are unsupported')
        stream.seek(0)
        book=openpyxl.load_workbook(stream,read_only=True,data_only=False,keep_links=False)
        stack.callback(book.close)
        selection['available_sheets']=book.sheetnames[:32]
        if options.sheet is None and len(book.sheetnames)!=1:raise ValueError('Choose source_options.sheet explicitly from: '+', '.join(book.sheetnames[:16]))
        name=options.sheet or book.sheetnames[0]
        if name not in book.sheetnames:raise ValueError('Selected worksheet is absent')
        selection.update(sheet=name,header_row=options.header_row)
        sheet=book[name]
        bounds={}
        if options.cell_range:
            from openpyxl.utils.cell import range_boundaries
            left,top,right,bottom=range_boundaries(options.cell_range)
            if options.header_row!=1:raise ValueError('Use cell_range or header_row, not both')
            if right<left or bottom<=top or right>16384 or bottom>1048576 or right-left>=100 or bottom-top>MAX_ROWS:raise ValueError('Selected worksheet range exceeds table bounds')
            bounds={'min_col':left,'max_col':right,'max_row':bottom};selection.update(cell_range=options.cell_range,header_row=top)
        elif sheet.max_column and sheet.max_column>100 or sheet.max_row and sheet.max_row-options.header_row>MAX_ROWS:raise ValueError('Worksheet dimensions exceed row/column budgets')
        sheet.reset_dimensions()
        rows=sheet.iter_rows(min_row=selection['header_row'],**bounds)
        first=next(rows,None)
        if first is None:raise ValueError('Worksheet has no header')
        names=[c.value for c in first]
        if any(c.data_type in {'f','e'} for c in first) or any(not isinstance(n,str) for n in names):raise ValueError('Worksheet header must contain literal text names')
        header(iter([names]))
        yield names
        for cells in rows:
            if len(cells)>100:raise ValueError('Worksheet exceeds 100 columns')
            if any(c.data_type in {'f','e'} for c in cells):raise ValueError('Formula/error cells are unsupported; provide literal values, not cached formula results')
            values=[c.value for c in cells]
            if len(values)>len(names):raise ValueError('Worksheet row has cells outside the header schema')
            yield values+[None]*(len(names)-len(values))
    else:
        text=io.TextIOWrapper(stream,encoding='utf-8-sig',newline='');stack.callback(text.detach)
        records=_json_records(text,options,suffix in {'.jsonl','.ndjson'})
        first=next(records,None)
        if not isinstance(first,dict) or not first:raise ValueError('Records need a nonempty first object defining the table columns')
        names=list(first);header(iter([names]));yield names
        for record in _chain(first,records):
            if not isinstance(record,dict) or set(record)-set(names):raise ValueError('All records must be flat objects with no new columns after the first record')
            yield [record.get(name) for name in names]


def _chain(first,records):
    yield first
    yield from records


def inspect(root,path,*,delimiter=',',preview_rows=5,analysis=None,expected_identity=None,on_metadata=None,checkpoint=None):
    path=relative_path(path,'input');suffix=Path(path).suffix.lower()
    if suffix not in SUFFIXES:raise ValueError('Unsupported table source format')
    if delimiter!=',':raise ValueError('Delimiter applies only to CSV/TSV')
    if not 0<=preview_rows<=20:raise ValueError('Invalid preview size')
    options=TableSourceOptions.model_validate((analysis or {}).get('source_options') or {})
    with ExitStack() as stack:
        parent,name=_parent(stack,root,path);fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent);stack.callback(os.close,fd)
        before=identity(os.fstat(fd))
        if not stat.S_ISREG(os.fstat(fd).st_mode) or before[2]>MAX_BYTES:raise ValueError('Record sources require a regular file of at most 16 MiB')
        if expected_identity is not None and before!=expected_identity:raise ValueError('Table source changed since selection')
        stream=stack.enter_context(os.fdopen(os.dup(fd),'rb'));sha=hashlib.sha256()
        for chunk in iter(lambda:stream.read(65536),b''):
            if checkpoint:checkpoint()
            sha.update(chunk)
        stream.seek(0);selection={};rows=_rows(stream,suffix,options,stack,selection);names=next(rows)
        from .inspection import TableInspection
        session=TableInspection(root,path,names,analysis=analysis,preview_rows=preview_rows,row_limit=MAX_ROWS)
        def typed_rows():
            for row in rows:
                cells=[_scalar(value) for value in row]
                yield TableRow(tuple(row),tuple(value for value,_ in cells),tuple(kind for _,kind in cells))
        session.consume(typed_rows(),checkpoint=checkpoint)
        after=identity(os.fstat(fd))
        current_parent,current_name=_parent(stack,root,path)
        check=os.open(current_name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=current_parent);stack.callback(os.close,check)
        if before!=after or before!=identity(os.fstat(check)):raise ValueError('Table source changed during reading')
    return session.finish(sha256=sha.hexdigest(),file_bytes=before[2],delimiter=',',
                          selection=selection,source_options=options.model_dump(mode='json'))
