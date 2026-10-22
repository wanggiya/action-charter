"""Pandas table operations with bounded reads, bounded typed calculations and create-only outputs."""
from __future__ import annotations
from contextlib import ExitStack
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat
import uuid

import pandas as pd

from .schemas import ARGUMENTS, WRITE_IDS

MAX_BYTES = 8 * 1024 * 1024
MAX_ROWS = 10000
MAX_COLUMNS = 100
MAX_CELL = 4096
MAX_MEMORY = 64 * 1024 * 1024

class TabularError(ValueError):
    pass

def relative_path(value, area):
    if not isinstance(value,str): raise TabularError('File reference must be a string')
    if area == 'input' and '/' not in value and '\\' not in value and value not in {'.','..'}:
        value = 'data/input/' + value
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or str(parsed) != value or '\\' in value or any(ord(c)<32 for c in value) or '..' in parsed.parts or len(parsed.parts)<3 or parsed.parts[:2] != ('data',area):
        raise TabularError('Use a normalized relative path under data/' + area)
    return value

def _parent(stack, root, value, create=False):
    fd=os.open(root.resolve(strict=True),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    stack.callback(os.close,fd)
    parts=PurePosixPath(value).parts
    for part in parts[:-1]:
        if create:
            try: os.mkdir(part,mode=0o700,dir_fd=fd)
            except FileExistsError: pass
        fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
        stack.callback(os.close,fd)
    return fd,parts[-1]

def read_bytes(root, value, area='input'):
    value=relative_path(value,area)
    try:
        with ExitStack() as stack:
            parent,name=_parent(stack,root,value)
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
            stack.callback(os.close,fd)
            if not stat.S_ISREG(os.fstat(fd).st_mode): raise TabularError('Input must be a regular file')
            if os.fstat(fd).st_size>MAX_BYTES: raise TabularError('Input exceeds 8 MiB')
            chunks=[]; remaining=MAX_BYTES+1
            while remaining:
                chunk=os.read(fd,min(65536,remaining))
                if not chunk: break
                chunks.append(chunk);remaining-=len(chunk)
            data=b''.join(chunks)
            if len(data)>MAX_BYTES: raise TabularError('Input exceeds 8 MiB')
        return data
    except OSError as error:
        raise TabularError('Input is unavailable or contains an unsafe file/directory link') from error

def _guard(frame):
    if len(frame)>MAX_ROWS or len(frame.columns)>MAX_COLUMNS: raise TabularError('Table exceeds 10,000 rows or 100 columns')
    if any(not isinstance(c,str) or not c or len(c)>200 for c in frame.columns) or sum(len(str(c).encode()) for c in frame.columns)>1024: raise TabularError('Column metadata exceeds its bounded preview contract')
    if not len(frame.columns) or not frame.columns.is_unique: raise TabularError('Table needs unique non-empty column names')
    if int(frame.memory_usage(index=True,deep=True).sum())>MAX_MEMORY: raise TabularError('Table exceeds 64 MiB memory budget')
    return frame

def read_frame(data, delimiter=','):
    try:
        text=data.decode('utf-8-sig')
        parsed=csv.reader(io.StringIO(text),delimiter=delimiter,strict=True)
        header=next(parsed)
        if not header or len(header)>MAX_COLUMNS or len(set(header))!=len(header) or any(not c or len(c)>200 for c in header): raise TabularError('CSV header must have 1–100 unique non-empty names')
        count=0
        for row in parsed:
            if not row: continue
            count+=1
            if count>MAX_ROWS or len(row)!=len(header) or any(len(c)>MAX_CELL for c in row): raise TabularError('CSV has ragged rows or exceeds row/cell bounds')
        frame=pd.read_csv(io.BytesIO(data),sep=delimiter,dtype='string',keep_default_na=False,na_values=[''],nrows=MAX_ROWS+1,encoding='utf-8-sig',on_bad_lines='error')
        return _guard(frame)
    except (UnicodeError,csv.Error,StopIteration,pd.errors.ParserError,pd.errors.EmptyDataError) as error:
        raise TabularError('CSV must be valid bounded UTF-8 with a header and consistent rows') from error

def _preview(frame, count=5):
    # Bound both rows and characters. Nulls are JSON null; IDs remain strings.
    rows=[]
    for row in frame.head(count).to_dict(orient='records'):
        item={str(k):None if pd.isna(v) else str(v)[:160] for k,v in row.items()}
        if len(json.dumps(rows+[item],ensure_ascii=False).encode())>4096: break
        rows.append(item)
    return {'columns':list(frame.columns),'row_count':len(frame),'column_count':len(frame.columns),'missing_counts':{c:int(frame[c].isna().sum()) for c in frame.columns},'preview':rows,'preview_truncated':len(rows)<len(frame),'column_types':{c:'string' for c in frame.columns}}

def _columns(frame, names):
    if len(names)!=len(set(names)) or any(c not in frame.columns for c in names): raise TabularError('Columns must be unique known table columns')

def _numeric(series):
    try: numeric=pd.to_numeric(series,errors='raise')
    except (ValueError,TypeError) as error: raise TabularError('Numeric operation has non-numeric values') from error
    if any(not math.isfinite(float(x)) for x in numeric.dropna()): raise TabularError('Numeric values must be finite')
    return numeric

def _source(root, args, completed, right=False):
    path=getattr(args,'right_path' if right else 'path',None)
    source_step=getattr(args,'right_step' if right else 'source_step',None)
    area='input';expected=None
    if source_step:
        prior=completed.get(source_step)
        if not prior or not prior.validation_performed or not prior.validation_result or prior.validation_result.get('passed') is not True:
            raise TabularError('Intermediate input requires a completed, validated ancestor output')
        output=prior.execution.result.get('output')
        if prior.execution.result.get('data_contract')!='table/csv-v1' or not output:
            raise TabularError('Intermediate operation does not produce a compatible CSV table')
        path=output['path'];expected=output['sha256'];area='output'
    path=relative_path(path,area)
    if Path(path).suffix.lower() not in {'.csv','.tsv'}: raise TabularError('Tabular input must be CSV or TSV')
    data=read_bytes(root,path,area)
    digest=hashlib.sha256(data).hexdigest()
    if expected and digest!=expected: raise TabularError('Intermediate output digest changed after validation')
    # Produced artifacts are always comma-delimited CSV; source files use explicit delimiter.
    frame=read_frame(data,',' if source_step else (getattr(args,'right_delimiter',args.delimiter) if right else args.delimiter))
    return frame,{'path':path,'sha256':digest,'area':area,'source_step':source_step}

def _transform(skill,args,left,right=None):
    if skill=='select_csv_columns':
        _columns(left,args.columns);return left.loc[:,args.columns].copy()
    if skill=='filter_csv_rows':
        masks=[]
        for predicate in args.predicates:
            _columns(left,[predicate.column]);series=left[predicate.column]
            if predicate.operator in {'is_missing','not_missing'}:
                mask=series.isna() if predicate.operator=='is_missing' else series.notna()
            else:
                values=_numeric(series) if predicate.value_type=='number' else series
                try: value=float(predicate.value) if predicate.value_type=='number' else str(predicate.value)
                except (TypeError,ValueError) as error: raise TabularError('Numeric predicate requires a numeric scalar') from error
                if predicate.value_type=='number' and not math.isfinite(value): raise TabularError('Numeric predicate must be finite')
                mask={'eq':values.eq,'ne':values.ne,'gt':values.gt,'ge':values.ge,'lt':values.lt,'le':values.le}[predicate.operator](value).fillna(False)
            masks.append(mask)
        mask=masks[0]
        for other in masks[1:]:mask=(mask & other) if args.match=='all' else (mask | other)
        return left.loc[mask].copy()
    if skill=='handle_csv_missing':
        columns=list(args.fill_values) if args.method=='fill' else (args.columns or list(left.columns));_columns(left,columns)
        return left.fillna({k:str(v) for k,v in args.fill_values.items()}) if args.method=='fill' else left.dropna(subset=columns)
    if skill=='join_csv':
        _columns(left,args.keys);_columns(right,args.keys)
        if left[args.keys].isna().any().any() or right[args.keys].isna().any().any(): raise TabularError('Join keys must not be missing')
        if args.cardinality in {'one_to_one','one_to_many'} and left.duplicated(args.keys).any(): raise TabularError('Join violates declared left-key cardinality')
        if args.cardinality in {'one_to_one','many_to_one'} and right.duplicated(args.keys).any(): raise TabularError('Join violates declared right-key cardinality')
        if len(left.columns)+len(right.columns)-len(args.keys)>MAX_COLUMNS: raise TabularError('Join would exceed the column bound')
        overlapping=(set(left.columns)&set(right.columns))-set(args.keys)
        if overlapping: raise TabularError('Join non-key columns overlap; select distinct columns first')
        counts=left.groupby(args.keys,dropna=False).size().rename('left').to_frame().join(right.groupby(args.keys,dropna=False).size().rename('right'),how='left').fillna(0)
        projected=int((counts['left'] * (counts['right'].clip(lower=1) if args.how=='left' else counts['right'])).sum())
        if projected>MAX_ROWS: raise TabularError('Join would exceed the row bound')
        return _guard(left.merge(right,on=args.keys,how=args.how,validate=args.cardinality,sort=False))
    if skill=='aggregate_csv':
        _columns(left,args.by);outputs=[a.output_column for a in args.aggregations]
        if len(set(outputs))!=len(outputs) or set(outputs)&set(args.by): raise TabularError('Aggregation output columns must be unique and distinct from group keys')
        work=left.copy();named={}
        for aggregate in args.aggregations:
            _columns(left,[aggregate.column])
            if aggregate.function!='count':work[aggregate.column]=_numeric(work[aggregate.column])
            named[aggregate.output_column]=pd.NamedAgg(column=aggregate.column,aggfunc=aggregate.function)
        grouped=work.groupby(args.by,dropna=False,sort=True).agg(**named).reset_index()
        for column in outputs:
            _numeric(grouped[column])
        return _guard(grouped)
    if skill=='calculate_csv_columns':
        from .calculations import calculate
        return calculate(left, args)
    if skill=='export_csv':return left.copy()
    raise TabularError('Operation is outside the tabular allowlist')

def _csv_bytes(frame):
    data=frame.to_csv(index=False,lineterminator='\n',na_rep='').encode('utf-8')
    if len(data)>MAX_BYTES:raise TabularError('Result exceeds the 8 MiB output bound')
    return data

def _publish(root,value,data):
    value=relative_path(value,'output')
    if Path(value).suffix.lower()!='.csv':raise TabularError('Table outputs must use .csv')
    with ExitStack() as stack:
        try:
            parent,name=_parent(stack,root,value,create=True)
            temporary='.'+uuid.uuid4().hex+'.csv.tmp'
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            try:
                with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
                # Atomic create-only publication: never replace any existing file/link.
                os.link(temporary,name,src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False)
                os.fsync(parent)
            finally:os.unlink(temporary,dir_fd=parent)
        except FileExistsError as error:raise TabularError('Output exists; choose a fresh path. Overwrite is prohibited') from error
        except OSError as error:raise TabularError('Output directory is unavailable or unsafe') from error
    return value

def inspect_csv(path,settings,delimiter=',',preview_rows=5):
    args=ARGUMENTS['inspect_csv'](path=path,delimiter=delimiter,preview_rows=preview_rows)
    root=Path(settings.project_root).resolve();path=relative_path(args.path,'input')
    data=read_bytes(root,path);frame=read_frame(data,args.delimiter)
    return {'operation':'inspect_csv','data_contract':'table/csv-v1','source':path,'source_sha256':hashlib.sha256(data).hexdigest(),**_preview(frame,args.preview_rows),'effects':'read_only','execution_performed':True,'validation_performed':False,'warnings':['Values are read as strings; empty fields are missing, literal NA/NULL strings are preserved.']}

from geoagent_harness.write_policy import guarded

@guarded
def run_operation(skill,arguments,settings,completed_results=None):
    if skill not in WRITE_IDS:raise TabularError('Unsupported tabular write operation')
    if not settings.enable_write_tools:raise TabularError('Write tools are disabled')
    args=ARGUMENTS[skill].model_validate(arguments);root=Path(settings.project_root).resolve();sources=[]
    if skill=='vector_attributes_to_csv':
        path=relative_path(args.path,'input')
        if Path(path).suffix.lower() not in {'.geojson','.json'}:raise TabularError('Vector table bridge supports bounded GeoJSON only')
        data=read_bytes(root,path)
        try:
            document=json.loads(data,parse_constant=lambda _: (_ for _ in ()).throw(TabularError('Non-finite GeoJSON value')))
            if document.get('type')!='FeatureCollection' or not isinstance(document.get('features'),list) or len(document['features'])>MAX_ROWS:raise TabularError('GeoJSON must be a bounded FeatureCollection')
            records=[]
            for feature in document['features']:
                properties=feature.get('properties') or {}
                if feature.get('type')!='Feature' or not isinstance(properties,dict) or any(isinstance(v,(dict,list)) or (isinstance(v,float) and not math.isfinite(v)) for v in properties.values()):raise TabularError('GeoJSON attributes must be flat finite scalar properties')
                records.append(properties)
            frame=pd.DataFrame(records).reindex(sorted({k for record in records for k in record}),axis=1).astype('string')
            _guard(frame)
        except (ValueError,TypeError,AttributeError) as error:raise TabularError('GeoJSON attribute contract is invalid') from error
        sources=[{'path':path,'sha256':hashlib.sha256(data).hexdigest(),'area':'input','source_step':None}]
    else:
        frame,source=_source(root,args,completed_results or {});sources.append(source)
        right=None
        if skill=='join_csv':right,source=_source(root,args,completed_results or {},True);sources.append(source)
        frame=_guard(_transform(skill,args,frame,right))
    data=_csv_bytes(frame)
    # Validate the serialized contract before publication, including cell bounds.
    published_frame=read_frame(data)
    calculation = {}
    if skill == 'calculate_csv_columns':
        from .calculations import verify_calculation
        original = read_frame(read_bytes(root, sources[0]['path'], sources[0]['area']), ',' if args.source_step else args.delimiter)
        if not verify_calculation(original, published_frame, args):
            raise TabularError('Independent calculation verification failed before publication')
        calculation = {'calculation_arguments': args.model_dump(mode='json', exclude_none=True)}
    path=_publish(root,args.target_path,data)
    return {**calculation,'operation':skill,'data_contract':'table/csv-v1','sources':sources,'output':{'path':path,'sha256':hashlib.sha256(data).hexdigest()},**_preview(published_frame,10),'effects':'create_csv','execution_performed':True,'validation_performed':False,'warnings':['Geometry/CRS are not included in the exported attribute table.'] if skill=='vector_attributes_to_csv' else []}

def validate_output(result,settings):
    root=Path(settings.project_root).resolve()
    data=read_bytes(root,result['output']['path'],'output');frame=read_frame(data)
    checks={'output_sha256':hashlib.sha256(data).hexdigest()==result['output']['sha256'],'row_count':len(frame)==result['row_count'],'columns':list(frame.columns)==result['columns'],'source_identity':all(hashlib.sha256(read_bytes(root,s['path'],s['area'])).hexdigest()==s['sha256'] for s in result['sources'])}
    if 'text_transform_definition' in result:
        from geoagent_harness.operations.packages import installed_packages,package_sha
        from geoagent_harness.capabilities.text import verify_frame
        package=installed_packages(root).get(result['operation'])
        checks['installed_package_identity']=bool(package and package.text_transform is not None and package_sha(package)==result.get('package_sha256') and package.text_transform.model_dump(mode='json')==result['text_transform_definition'])
        source=result['sources'][0]
        original=read_frame(read_bytes(root,source['path'],source['area']),result.get('source_delimiter',','))
        checks['text_transform_values']=checks['installed_package_identity'] and verify_frame(original,frame,package.text_transform)
    if result.get('operation') == 'calculate_csv_columns':
        from .calculations import verify_calculation
        args = ARGUMENTS['calculate_csv_columns'].model_validate(result['calculation_arguments'])
        source = result['sources'][0]
        original = read_frame(read_bytes(root, source['path'], source['area']), ',' if args.source_step else args.delimiter)
        checks['calculation_values'] = verify_calculation(original, frame, args)
    return {'passed':all(checks.values()),'checks':checks,'target':result['output']['path'],'row_count':len(frame),'columns':list(frame.columns),'workflow_executed':True}
