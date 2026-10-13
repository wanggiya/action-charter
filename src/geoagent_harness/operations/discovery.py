"""Bounded static discovery. Scanned packages are never imported or executed."""
from __future__ import annotations
import ast
import hashlib
import json
import os
import re
import stat
import time
from contextlib import ExitStack
from importlib import metadata
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.context_pack.redaction import redact_text

MAX_SOURCE_BYTES=256000
MAX_SCAN_BYTES=16000000
MAX_CANDIDATES=10000
MAX_FILES=2000
MAX_SECONDS=10

class ScanRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    action:Literal['scan_installed_libraries']='scan_installed_libraries'
    distributions:list[str]=Field(default_factory=list,max_length=20)
    include_private:bool=False


def library_inventory(distributions=None):
    rows=[]
    for distribution in (metadata.distributions() if distributions is None else distributions):
        name=str(distribution.metadata.get('Name') or '').strip()
        if not name:continue
        rows.append({'name':name[:200],'version':str(distribution.version)[:100],'discovery':'static Python declarations/stubs; imports and native execution disabled'})
    rows.sort(key=lambda row:row['name'].lower())
    return {'libraries':rows[:1000],'total_libraries':len(rows),'inventory_truncated':len(rows)>1000,'execution_performed':False,'approval_performed':False}

def _normalize(name):return name.lower().replace('_','-').replace('.','-')

def _text(node):
    if node is None:return None
    try:return redact_text(ast.unparse(node))[:160]
    except (RecursionError,ValueError):return '[static expression too complex]'

def _signature(node):
    args=node.args;parameters=[]
    positional=[*args.posonlyargs,*args.args]
    defaults=[None]*(len(positional)-len(args.defaults))+list(args.defaults)
    for index,(argument,default) in enumerate(zip(positional,defaults)):
        parameters.append({'name':argument.arg[:80],'kind':'positional_only' if index<len(args.posonlyargs) else 'positional_or_keyword','annotation':_text(argument.annotation),'default':('[redacted]' if default is not None and re.search(r'password|secret|credential|token|api_?key',argument.arg,re.I) else _text(default)),'required':default is None and argument.arg not in {'self','cls'}})
    if args.vararg:parameters.append({'name':args.vararg.arg[:80],'kind':'varargs','annotation':_text(args.vararg.annotation),'default':None,'required':False})
    for argument,default in zip(args.kwonlyargs,args.kw_defaults):
        parameters.append({'name':argument.arg[:80],'kind':'keyword_only','annotation':_text(argument.annotation),'default':('[redacted]' if default is not None and re.search(r'password|secret|credential|token|api_?key',argument.arg,re.I) else _text(default)),'required':default is None})
    if args.kwarg:parameters.append({'name':args.kwarg.arg[:80],'kind':'kwargs','annotation':_text(args.kwarg.annotation),'default':None,'required':False})
    return parameters[:32],len(parameters)>32

def _declarations(nodes,module,prefix='',include_private=False):
    for node in nodes:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            if not include_private and node.name.startswith('_'):continue
            qualified=prefix+node.name
            if isinstance(node,ast.ClassDef):
                constructor=next((n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='__init__'),None)
                parameters,truncated=_signature(constructor) if constructor else ([],False)
                yield {'qualified_name':(module+'.'+qualified)[:500],'kind':'class','parameters':parameters,'parameters_truncated':truncated,'return_annotation':None,'documentation':redact_text(ast.get_docstring(node) or '')[:240],'signature_source':'static_declaration'}
                yield from _declarations(node.body,module,qualified+'.',include_private)
            else:
                parameters,truncated=_signature(node)
                kind='method' if prefix else 'function'
                if any(isinstance(d,ast.Name) and d.id=='property' for d in node.decorator_list):kind='property'
                yield {'qualified_name':(module+'.'+qualified)[:500],'kind':kind,'parameters':parameters,'parameters_truncated':truncated,'return_annotation':_text(node.returns),'documentation':redact_text(ast.get_docstring(node) or '')[:240],'signature_source':'static_declaration'}
        elif isinstance(node,(ast.If,ast.Try)):
            # Declarations are potential candidates; branches/decorators are not run.
            yield from _declarations(node.body,module,prefix,include_private)
            yield from _declarations(node.orelse,module,prefix,include_private)
            if isinstance(node,ast.Try):
                for handler in node.handlers:yield from _declarations(handler.body,module,prefix,include_private)
                yield from _declarations(node.finalbody,module,prefix,include_private)


def _read_source(root,parts,limit):
    with ExitStack() as stack:
        parent=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        stack.callback(os.close,parent)
        for part in parts[:-1]:
            parent=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
            stack.callback(os.close,parent)
        fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        with os.fdopen(fd,'rb') as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):raise OSError('not regular')
            return handle.read(limit+1)


def scan_libraries(request:ScanRequest, distributions=None):
    started=time.monotonic();all_distributions=list(metadata.distributions() if distributions is None else distributions)
    inventory=library_inventory(all_distributions);selected={_normalize(n) for n in request.distributions}
    available={_normalize(row['name']) for row in inventory['libraries']}
    if selected-available:raise ValueError('Choose distributions present in the installed library inventory')
    candidates=[];coverage=[];total_bytes=0;total_files=0;result_bytes=0;global_truncated=False
    for distribution in sorted(all_distributions,key=lambda item:str(item.metadata.get('Name','')).lower())[:1000]:
        name=str(distribution.metadata.get('Name') or '')
        if not name or (selected and _normalize(name) not in selected):continue
        root=Path(distribution.locate_file('')).resolve()
        files=list(distribution.files or [])
        counts={'distribution':name[:200],'version':str(distribution.version)[:100],'files_scanned':0,'candidates':0,'native_files':0,'skipped_files':0,'complete':True,'reasons':[]}
        if not files:counts['complete']=False;counts['reasons'].append('No source file manifest; editable/dynamic modules may be absent')
        for file in sorted(files,key=str):
            if len(candidates)>=MAX_CANDIDATES or total_files>=MAX_FILES or total_bytes>=MAX_SCAN_BYTES or time.monotonic()-started>MAX_SECONDS:
                counts['complete']=False;counts['reasons'].append('Global scan budget reached; narrow the selected distributions');global_truncated=True;break
            suffix=Path(str(file)).suffix.lower()
            if suffix in {'.so','.pyd','.dll'}:counts['native_files']+=1;counts['complete']=False;continue
            if suffix not in {'.py','.pyi'}:continue
            parts=Path(str(file)).parts
            if '..' in parts or Path(str(file)).is_absolute() or any(part.endswith(('.dist-info','.egg-info')) for part in parts):
                counts['skipped_files']+=1;counts['complete']=False;continue
            path=Path(distribution.locate_file(file))
            try:
                resolved=path.resolve(strict=True)
                if not resolved.is_relative_to(root) or any((root.joinpath(*parts[:i])).is_symlink() for i in range(1,len(parts)+1)):raise OSError('unsafe file')
                source=_read_source(root,parts,min(MAX_SOURCE_BYTES,MAX_SCAN_BYTES-total_bytes))
                if len(source)>MAX_SOURCE_BYTES or total_bytes+len(source)>MAX_SCAN_BYTES:raise ValueError('source budget')
                total_bytes+=len(source);total_files+=1
                tree=ast.parse(source)
            except (OSError,ValueError,SyntaxError,UnicodeError,RecursionError):
                counts['skipped_files']+=1;counts['complete']=False;continue
            counts['files_scanned']+=1
            module='.'.join(parts)[:-len(suffix)]
            if module.endswith('.__init__'):module=module[:-9]
            for declaration in _declarations(tree.body,module,include_private=request.include_private):
                if len(candidates)>=MAX_CANDIDATES:counts['complete']=False;global_truncated=True;break
                identity=f'{name}:{distribution.version}:{str(file)}:{declaration["qualified_name"]}:{declaration["kind"]}'
                candidate={'candidate_id':hashlib.sha256(identity.encode()).hexdigest(), 'distribution':name[:200],'version':str(distribution.version)[:100],**declaration,'executable':False,'promotion':'requires a tested typed adapter; discovery is not installation or approval'}
                size=len(json.dumps(candidate,ensure_ascii=False).encode())
                if result_bytes+size>8000000:
                    counts['complete']=False;global_truncated=True;counts['reasons'].append('Candidate result byte budget reached');break
                result_bytes+=size
                candidates.append(candidate)
                counts['candidates']+=1
        if counts['native_files']:counts['reasons'].append('Native symbols are not introspected; available Python stubs may describe some')
        if counts['skipped_files']:counts['reasons'].append('Oversized, unavailable, unsafe or unsupported source files skipped')
        counts['reasons'].append('Runtime-generated exports, inherited methods, reexports and decorator effects are not verified')
        coverage.append(counts)
        if global_truncated:break
    report={'schema_version':'1.0','candidates':candidates,'candidate_count':len(candidates),'coverage':coverage,'truncated':global_truncated or inventory['inventory_truncated'],'inventory_libraries':inventory['total_libraries'],'include_private':request.include_private,'selected_distributions':request.distributions,'scan_bytes':total_bytes,'scan_files':total_files,'candidate_bytes':result_bytes,'unscanned_libraries':max(0,len(selected) if selected else inventory['total_libraries'])-len(coverage),'limits':{'result_bytes':8000000,'bytes':MAX_SCAN_BYTES,'files':MAX_FILES,'candidates':MAX_CANDIDATES,'seconds':MAX_SECONDS},'execution_performed':False,'approval_performed':False,'imports_performed':False}
    report['scan_sha256']=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    return report
