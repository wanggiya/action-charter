"""Bounded metadata snapshots below a fixed project-local directory."""
import hashlib
import json
import os
import re
import stat
import uuid
from contextlib import ExitStack
from pathlib import Path

DIRECTORY='library-discovery'
MAX_BYTES=12000000

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def _parent(stack,root,create=False):
    fd=os.open(Path(root).resolve(strict=True),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    stack.callback(os.close,fd)
    if create:
        try:os.mkdir(DIRECTORY,0o700,dir_fd=fd)
        except FileExistsError:pass
    child=os.open(DIRECTORY,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
    stack.callback(os.close,child)
    return child

def save_scan(root,report):
    digest=report['scan_sha256'];data=canonical(report)
    if len(data)>MAX_BYTES:raise ValueError('Discovery snapshot exceeds its byte bound')
    if not re.fullmatch(r'[a-f0-9]{64}',digest):raise ValueError('Invalid scan digest')
    with ExitStack() as stack:
        parent=_parent(stack,root,True)
        if len(os.listdir(parent))>=20:raise ValueError('Discovery snapshot limit reached; explicitly remove old project-local snapshots before a new scan')
        temporary=f'.{uuid.uuid4().hex}.tmp'
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
        try:
            with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
            try:os.link(temporary,digest+'.json',src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False)
            except FileExistsError:
                if read_scan(root,digest)!=report:raise ValueError('Existing snapshot conflicts with this scan')
            os.fsync(parent)
        finally:os.unlink(temporary,dir_fd=parent)
    return digest

def read_scan(root,digest):
    if not re.fullmatch(r'[a-f0-9]{64}',digest):raise ValueError('Invalid scan digest')
    with ExitStack() as stack:
        parent=_parent(stack,root)
        fd=os.open(digest+'.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        with os.fdopen(fd,'rb') as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):raise ValueError('Scan is not a regular file')
            data=handle.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:raise ValueError('Scan exceeds its byte bound')
    report=json.loads(data)
    core={key:value for key,value in report.items() if key!='scan_sha256'}
    if report.get('scan_sha256')!=digest or hashlib.sha256(canonical(core)).hexdigest()!=digest:raise ValueError('Discovery snapshot identity changed')
    return report

def candidate_page(report,query='',distribution='',kind='',offset=0,limit=50):
    if offset<0 or not 1<=limit<=100 or len(query)>200:raise ValueError('Invalid discovery search bounds')
    query=query.strip().lower()
    rows=[row for row in report['candidates'] if query in (row['qualified_name']+' '+row['documentation']).lower() and (not distribution or row['distribution']==distribution) and (not kind or row['kind']==kind)]
    return {'scan_sha256':report['scan_sha256'],'candidates':rows[offset:offset+limit],'match_count':len(rows),'offset':offset,'limit':limit,'next_offset':offset+limit if offset+limit<len(rows) else None,'truncated':report['truncated'],'execution_performed':False,'approval_performed':False}


def saved_scans(root):
    """List verified persisted snapshots, without importing library candidates."""
    try:
        with ExitStack() as stack:
            parent = _parent(stack, root)
            names = sorted(name for name in os.listdir(parent) if re.fullmatch(r'[a-f0-9]{64}\.json', name))
    except FileNotFoundError:
        names = []
    if len(names) > 20:
        raise ValueError('Discovery snapshot limit exceeded')
    scans = []
    for name in names:
        report = read_scan(root, name[:-5])
        scans.append({key: value for key, value in report.items() if key != 'candidates'})
    return {'scans': scans, 'execution_performed': False, 'approval_performed': False}
