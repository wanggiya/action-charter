"""Qualified chunked row-local preparation; no joins, aggregation or generated code."""
from contextlib import ExitStack
import hashlib
import json
import os
import uuid

import pandas as pd

from geoagent_harness.data.discovery.csv import source, Reader, text_reader, records, header, row_values, identity
from geoagent_harness.contracts.table_sources import TableRow, row_batches
from geoagent_harness.platform.execution_control import checkpoint
from geoagent_harness.contracts.paths import TabularError
from geoagent_harness.data.tabular.service import _guard, _transform, _csv_bytes, _preview, source_binding
from geoagent_harness.contracts.paths import relative_path
from geoagent_harness.data.discovery.source import _parent

MAX_ROWS=200000
MAX_OUTPUT_BYTES=64*1024**2
IDS={'select_csv_columns','filter_csv_rows','handle_csv_missing','decode_csv_codes','export_csv'}


def frames(root,binding,delimiter,receipt):
    with source(root,binding['path'],area=binding['area']) as (fd,path,before):
        reader=Reader(fd,limit=1024**3,checkpoint=checkpoint)
        with text_reader(reader) as text:
            parsed=records(text,delimiter);names=header(parsed)
            yield _guard(pd.DataFrame(columns=names,dtype='string'))
            def rows():
                count=0
                for row in parsed:
                    if not row:continue
                    row_values(row,names);count+=1
                    if count>MAX_ROWS:raise TabularError('Streaming preparation exceeds 200,000 input rows')
                    values=tuple(row);yield TableRow(values,values,('string',)*len(names))
                receipt['source_row_count']=count
            for batch in row_batches(rows(),checkpoint=checkpoint):
                frame=pd.DataFrame([r.analytical for r in batch.rows],columns=names,dtype='string')
                yield _guard(frame.replace('',pd.NA))
        if identity(os.fstat(fd))!=before or reader.bytes!=before[2]:raise TabularError('Streaming source changed during read')
        with source(root,path,area=binding['area']) as (_,_,after):
            if before!=after:raise TabularError('Streaming source was replaced')
        digest=reader.sha.hexdigest()
        if binding.get('sha256') and digest!=binding['sha256']:raise TabularError('Validated streaming source changed')
        receipt['source']={**binding,'sha256':digest}


def emit(root,skill,args,binding,sink):
    receipt={};metadata=None;size=0;digest=hashlib.sha256();coverage={};book=None
    if skill=='decode_csv_codes':
        from geoagent_harness.data.tabular.analysis import codebook
        book=codebook(root,args.codebook_path)
    for frame in frames(root,binding,',' if args.source_step else args.delimiter,receipt):
        if book:
            from geoagent_harness.data.tabular.decoding import decode, verify
            output,part=decode(frame,args,book)
            if not verify(frame,output,args,book):raise TabularError('Streaming decode verification failed')
            for name,value in part.items():
                total=coverage.setdefault(name,{**value,'matched_rows':0,'unmatched_rows':0})
                for key in ('matched_rows','unmatched_rows'):total[key]+=value[key]
        else:output=_transform(skill,args,frame)
        _guard(output)
        first=metadata is None
        if first:
            metadata=_preview(output,10);metadata.update(row_count=0,missing_counts=dict.fromkeys(output.columns,0))
        data=_csv_bytes(output) if first else output.to_csv(index=False,header=False,lineterminator='\n',na_rep='').encode()
        size+=len(data)
        if size>MAX_OUTPUT_BYTES or metadata['row_count']+len(output)>MAX_ROWS:raise TabularError('Streaming output exceeds 64 MiB / 200,000 rows')
        digest.update(data);sink(data)
        metadata['row_count']+=len(output)
        for name in output:metadata['missing_counts'][name]+=int(output[name].isna().sum())
        if len(metadata['preview'])<10:
            for item in _preview(output,10)['preview']:
                if len(metadata['preview'])>=10 or len(json.dumps(metadata['preview']+[item]).encode())>4096:break
                metadata['preview'].append(item)
    metadata['preview_truncated']=len(metadata['preview'])<metadata['row_count']
    sources=[receipt['source']]
    if book:
        from geoagent_harness.data.tabular.analysis import codebook
        current=codebook(root,args.codebook_path)
        if current['sha256']!=book['sha256']:raise TabularError('Codebook changed during streaming preparation')
        sources.append({'path':book['path'],'sha256':book['sha256'],'area':'input','source_step':None})
    return {**metadata,'sources':sources,'sha256':digest.hexdigest(),'source_row_count':receipt['source_row_count'],
            'codebook_coverage':coverage}


def run(skill,args,settings,completed):
    root=settings.project_root;binding=source_binding(root,args,completed)
    target=relative_path(args.target_path,'output')
    if not target.endswith('.csv'):raise TabularError('Streaming output requires a fresh CSV')
    with ExitStack() as stack:
        parent,name=_parent(stack,root,target,create=True);temporary='.'+uuid.uuid4().hex+'.csv.tmp'
        fd=os.open(temporary,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
        try:
            with os.fdopen(fd,'w+b') as handle:
                observed=emit(root,skill,args,binding,handle.write);handle.flush();os.fsync(handle.fileno())
                handle.seek(0);actual=hashlib.sha256()
                while data:=handle.read(65536):checkpoint();actual.update(data)
                replay=emit(root,skill,args,{**binding,'sha256':observed['sources'][0]['sha256']},lambda _:None)
                if actual.hexdigest()!=observed['sha256'] or replay!=observed:raise TabularError('Streaming output replay failed before publication')
                checkpoint()
                os.link(temporary,name,src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False);os.fsync(parent)
        except FileExistsError as error:raise TabularError('Output exists; choose a fresh path. Overwrite is prohibited') from error
        finally:os.unlink(temporary,dir_fd=parent)
    return {**{k:v for k,v in observed.items() if k not in {'sha256','source_row_count'}},'operation':skill,'data_contract':'table/csv-v1',
        'output':{'path':target,'sha256':observed['sha256']},'streaming_preparation':{'schema_version':'1.0',
        'source_row_count':observed['source_row_count'],'scope':'complete_parsed_file','arguments':args.model_dump(mode='json',exclude_none=True)},
        'effects':'create_csv','execution_performed':True,'validation_performed':False,'warnings':[]}


def validate(result,settings):
    from geoagent_harness.contracts.tabular import ARGUMENTS
    skill=result['operation']
    if skill not in IDS:raise TabularError('Unknown streaming preparation operation')
    args=ARGUMENTS[skill].model_validate(result['streaming_preparation']['arguments'])
    replay=emit(settings.project_root,skill,args,result['sources'][0],lambda _:None)
    output={};binding={'path':result['output']['path'],'area':'output','sha256':result['output']['sha256'],'source_step':None}
    for _ in frames(settings.project_root,binding,',',output):pass
    checks={'output_sha256':output['source']['sha256']==result['output']['sha256']==replay['sha256'],
        'row_count':output['source_row_count']==result['row_count']==replay['row_count'],
        'columns':replay['columns']==result['columns'],'source_identity':replay['sources']==result['sources'],
        'codebook_coverage':replay['codebook_coverage']==result.get('codebook_coverage',{})}
    return {'passed':all(checks.values()),'checks':checks,'target':result['output']['path'],'row_count':result['row_count'],
            'columns':result['columns'],'workflow_executed':True}


def aggregate(root,args,completed):
    from geoagent_harness.data.tabular.analysis import Accumulator
    binding=source_binding(root,args,completed);receipt={};consumer=None
    numeric=list(dict.fromkeys(a.column for a in args.aggregations if a.function!='count'))
    counts=list(dict.fromkeys(a.column for a in args.aggregations if a.function=='count'))
    for frame in frames(root,binding,',',receipt):
        if consumer is None:consumer=Accumulator(root,list(frame.columns),{'group_by':args.by,'numeric_columns':numeric,'count_columns':counts})
        for row in frame.fillna('').itertuples(index=False,name=None):consumer.add(list(row))
    analysis=consumer.result(receipt['source_row_count'])
    if any(p.get('numeric') and p['numeric']['invalid_count'] for p in analysis['profiles']):raise TabularError('Numeric aggregation contains non-numeric values')
    outputs=[a.output_column for a in args.aggregations]
    if len(set(outputs))!=len(outputs) or set(outputs).intersection(args.by):raise TabularError('Aggregation outputs must be unique and distinct from group keys')
    rows=[{**{n:g[n] or pd.NA for n in args.by},**{a.output_column:g[f'{a.column}_{a.function}'] for a in args.aggregations}} for g in analysis['groups']]
    return _guard(pd.DataFrame(rows,columns=args.by+outputs).astype('string')),[receipt['source']],{
        'source_row_count':receipt['source_row_count'],'scope':'complete_parsed_file','group_count_reconciles':analysis['checks']['group_count_reconciles']}
