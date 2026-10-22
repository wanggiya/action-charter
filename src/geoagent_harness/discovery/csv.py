"""Streaming CSV characteristics and complete identity, without a dataframe."""
from __future__ import annotations
from contextlib import contextmanager, ExitStack
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import time

MAX_BYTES = 1024**3
SAMPLE_BYTES = 256 * 1024
MAX_SECONDS = 120


class SampleLimit(ValueError):
    pass


def identity(info):
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]


@contextmanager
def source(root, path):
    from .source import _parent, relative_path, TabularError
    path = relative_path(path, 'input')
    if Path(path).suffix.lower() not in {'.csv', '.tsv'}:
        raise TabularError('CSV discovery requires .csv or .tsv')
    try:
        with ExitStack() as stack:
            parent, name = _parent(stack, root, path)
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            stack.callback(os.close, fd)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise TabularError('CSV discovery requires a regular file of at most 1 GiB')
            yield fd, path, identity(info)
    except OSError as error:
        raise TabularError('CSV source is unavailable or unsafe') from error


class Reader(io.RawIOBase):
    def __init__(self, fd, *, limit, sample=False, checkpoint=None):
        super().__init__()
        self.fd, self.limit, self.sample, self.checkpoint = fd, limit, sample, checkpoint
        self.bytes = 0
        self.sha = hashlib.sha256()
        self.deadline = time.monotonic() + MAX_SECONDS

    def readable(self):
        return True

    def readinto(self, buffer):
        if time.monotonic() > self.deadline:
            raise ValueError('CSV discovery exceeded its 120-second budget')
        if self.checkpoint:
            self.checkpoint()
        if self.bytes >= self.limit:
            if self.sample:
                raise SampleLimit()
            if os.read(self.fd, 1):
                raise ValueError('CSV discovery exceeds its byte budget')
            return 0
        chunk = os.read(self.fd, min(len(buffer), 65536, self.limit - self.bytes))
        buffer[:len(chunk)] = chunk
        self.bytes += len(chunk)
        self.sha.update(chunk)
        return len(chunk)


def text_reader(reader):
    return io.TextIOWrapper(io.BufferedReader(reader, buffer_size=65536), encoding='utf-8-sig', newline='')


class RecordLines:
    """Bound a logical CSV record, including quoted multiline records."""
    def __init__(self,text):
        self.text=text
        self.remaining=1024*1024
    def __iter__(self):return self
    def __next__(self):
        line=self.text.readline(self.remaining+1)
        if not line:raise StopIteration
        if len(line)>self.remaining:
            raise ValueError('CSV record exceeds the 1 Mi-character budget')
        self.remaining-=len(line)
        return line


def records(text,delimiter):
    lines=RecordLines(text)
    parsed=csv.reader(lines,delimiter=delimiter,strict=True)
    while True:
        lines.remaining=1024*1024
        try:row=next(parsed)
        except StopIteration:return
        yield row


def header(parsed):
    names = next(parsed)
    if (not names or len(names)>100 or len(set(names))!=len(names)
            or any(not name or len(name)>200 for name in names)
            or sum(len(name.encode()) for name in names)>1024):
        raise ValueError('CSV header requires 1–100 unique bounded column names')
    return names


def row_values(row, names):
    if len(row)!=len(names) or any(len(value)>4096 for value in row):
        raise ValueError('CSV has inconsistent rows or a field exceeds 4096 characters')


def append_preview(preview, names, row, count):
    if len(preview)>=count:
        return False
    item={name: value[:160] if value else None for name,value in zip(names[:20], row[:20])}
    if len(json.dumps(preview+[item], ensure_ascii=False).encode())<=4096:
        preview.append(item)
        return len(preview)<count
    return False


def metadata(path, file_bytes, names, preview, sampled_rows):
    return {'operation':'inspect_csv','data_contract':'table/csv-v1','source':path,
            'columns':names,'column_count':len(names),'row_count':None,
            'preview':preview,'preview_truncated':True,
            'column_types':{name:'string' for name in names},
            'effects':'read_only','execution_performed':True,'validation_performed':False,
            'discovery':{'schema_version':'csv-discovery-v1','phase':'verifying',
                         'verification':'pending','statistics_scope':'sample',
                         'sampled_rows':sampled_rows,'file_bytes':file_bytes,
                         'encoding':'UTF-8 (validated for sampled content only)'},
            'warnings':['Preliminary sample; full row count and source SHA-256 are not yet established.']}


def probe(root, path, *, delimiter=',', preview_rows=5):
    with source(root, path) as (fd, path, before):
        reader=Reader(fd, limit=SAMPLE_BYTES, sample=True)
        names, preview, count=None, [], 0
        try:
            with text_reader(reader) as text:
                parsed=records(text,delimiter)
                names=header(parsed)
                for row in parsed:
                    if not row:
                        continue
                    row_values(row, names)
                    count+=1
                    append_preview(preview,names,row,preview_rows)
                    if count>=20:
                        break
        except SampleLimit:
            if names is None:
                raise ValueError('CSV header exceeds the sampling budget')
        if identity(os.fstat(fd))!=before:
            raise ValueError('CSV source changed during discovery')
        return {'path':path,'bytes':before[2], 'source_identity':before,
                'discovery_kind':'streaming_csv_v1',
                'metadata':metadata(path,before[2],names,preview,count)}


def inspect(root, path, *, delimiter=',', preview_rows=5, expected_identity=None,
            on_metadata=None, checkpoint=None):
    if delimiter not in {',','\t'} or not 0<=preview_rows<=20:
        raise ValueError('Invalid CSV inspection parameters')
    preliminary=probe(root,path,delimiter=delimiter,preview_rows=preview_rows)
    if expected_identity is not None and preliminary['source_identity']!=expected_identity:
        raise ValueError('CSV source changed since submission')
    if on_metadata:
        on_metadata(preliminary['metadata'])
    with source(root,path) as (fd,path,before):
        if before!=preliminary['source_identity']:
            raise ValueError('CSV source changed before verification')
        reader=Reader(fd,limit=MAX_BYTES,checkpoint=checkpoint)
        count, preview=0, []
        collect_preview=True
        with text_reader(reader) as text:
            parsed=records(text,delimiter)
            names=header(parsed)
            missing={name:0 for name in names}
            for row in parsed:
                if not row:
                    continue
                row_values(row,names)
                count+=1
                for name,value in zip(names,row):
                    if value=='':missing[name]+=1
                if collect_preview:
                    collect_preview=append_preview(preview,names,row,preview_rows)
        if identity(os.fstat(fd))!=before or reader.bytes!=before[2]:
            raise ValueError('CSV source changed during verification')
        # Detect pathname replacement as well as mutation of the open file.
        with source(root,path) as (_,_,after):
            if after!=before:
                raise ValueError('CSV source was replaced during verification')
    result=metadata(path,before[2],names,preview,min(count,20))
    result.update(row_count=count,missing_counts=missing,preview_truncated=len(preview)<count,
                  source_sha256=reader.sha.hexdigest())
    result['discovery'].update(phase='completed',verification='sha256_complete',
        statistics_scope='complete_parsed_file',bytes_hashed=reader.bytes,
        consistency='opened-file and pathname stat checks; not an immutable snapshot',
        encoding='UTF-8 (validated for complete content)')
    result['warnings']=['Values remain strings; empty fields are missing; literal NA/NULL are preserved.',
                        'Preview is bounded to 20 columns, requested rows and 4 KiB.',
                        'Complete CSV exploration and transformations retain their separate limits.']
    return result
