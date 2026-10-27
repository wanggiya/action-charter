"""Role-neutral input discovery and operation-specific read feasibility."""
from contextlib import ExitStack
import os
from pathlib import Path
import re
import stat
import time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.discovery.source import relative_path

class DiscoveryRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    directory:str=Field(max_length=960)

class AssessmentRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    path:str=Field(max_length=960)
    operation:Literal['profile','quality','group','select_csv_columns','join_csv','calculate_csv_columns','statistical_model']='profile'


def directory_path(value):
    if value=='data/input':return value
    return relative_path(value,'input')


def discover_inputs(root,directory):
    """One bounded directory, no symlinks, hidden files, recursion or raw rows."""
    directory=directory_path(directory)
    from geoagent_harness.discovery.source import _parent
    files=[];examined=0
    try:
        with ExitStack() as stack:
            parent,name=_parent(stack,Path(root),directory+'/.directory-entry')
            # _parent walks every directory with O_NOFOLLOW; .directory-entry is
            # a lexical sentinel, never opened or required to exist.
            with os.scandir(parent) as entries:
                for entry in entries:
                    examined+=1
                    if examined>200:raise ValueError('Directory exceeds 200 entries; use a smaller input folder')
                    if entry.name.startswith('.') or not entry.is_file(follow_symlinks=False):continue
                    suffix=Path(entry.name).suffix.lower()
                    if suffix not in {'.csv','.tsv','.geojson','.gpkg','.shp','.tif','.tiff'}:continue
                    if len(entry.name)>200 or len(directory+'/'+entry.name)>960:continue
                    info=entry.stat(follow_symlinks=False)
                    if not stat.S_ISREG(info.st_mode):continue
                    try:relative_path(directory+'/'+entry.name,'input')
                    except (ValueError,InterfaceApiError):continue
                    files.append({'path':directory+'/'+entry.name,'bytes':info.st_size,'format':suffix[1:],
                        'possible_sample':bool(re.search(r'(^|[_ .-])(sample|subset)([_ .-]|\d|$)',Path(entry.name).stem,re.I)),
                        'sample_provenance':'unverified'})
                    if len(files)>40:raise ValueError('Directory exceeds 40 supported files; use a smaller folder')
    except OSError as error:raise ValueError('Input directory unavailable or unsafe') from error
    files.sort(key=lambda f:f['path'])
    from geoagent_harness.interface_api.inspection_policy import bounded_read
    deadline=time.monotonic()+20
    from geoagent_harness.interface_api.server import InterfaceApiError
    for item in files[:8]:
        if item['format'] not in {'csv','tsv'}:continue
        try:
            probe=bounded_read(Path(root),action='csv_strategy_probe',path=item['path'],delimiter='\t' if item['format']=='tsv' else ',',max_seconds=max(.1,min(3,deadline-time.monotonic())))
            columns=probe['metadata']['columns']
            item.update(columns=columns,metadata_scope='bounded_header_and_sample',row_count=None,
                possible_codebook=len(columns)==2 and columns[1].casefold()=='description')
        except ValueError:
            item['metadata_status']='unavailable; inspect format or source changes'
    for item in files:
        if item['possible_sample'] and item.get('columns'):
            item['compatible_schema_sources']=[f['path'] for f in files if not f['possible_sample'] and not f.get('possible_codebook') and f.get('columns')==item['columns']][:3]
    return {'directory':directory,'files':files,'effects':'read_only','recursive':False,
        'header_probe_limit':8,'raw_rows_returned':False,'limitations':[
            'Filename hints and compatible headers do not establish sample provenance or representativeness.',
            'Rows are not counted or loaded into model context during discovery.']}


def assess_table(root,path,operation='profile'):
    request=AssessmentRequest(path=path,operation=operation)
    path=relative_path(request.path,'input')
    from geoagent_harness.discovery.csv import source
    with source(Path(root),path,max_bytes=None) as (_,path,identity):size=identity[2]
    streaming=request.operation in {'profile','quality','group'}
    supported=request.operation!='statistical_model'
    limit=1024**3 if streaming else 8*1024**2
    strategy='full_stream' if streaming else 'bounded_dataframe'
    if not supported:strategy='unavailable'
    elif size>limit:strategy='needs_alternative'
    return {'path':path,'operation':request.operation,'source_bytes':size,'strategy':strategy,
        'supported':supported,'within_byte_limit':supported and size<=limit,'byte_limit':limit if supported else None,
        'row_limit':None if streaming or not supported else 10000,'row_count':'not established',
        'runtime_state_checks_required':True,'sampling_required':supported and size>limit,
        'sample_creation_available':False,'sample_write_authority_granted':False,
        'reason':('Statistical model fitting is not registered in this slice.' if not supported else
            'Complete-source streaming is eligible; actual time, cardinality and memory limits still apply.' if streaming and size<=limit else
            'Input exceeds this operation byte limit. Consider a compatible sample or another supported strategy; no sample will be created automatically.' if size>limit else
            'Byte check passed; the dataframe operation must additionally enforce its row and memory limits.'),
        'effects':'read_only'}
