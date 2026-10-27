"""Source-bound interactive views over a saved chat profile; no LLM or workflow dispatch."""
import json
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from geoagent_harness.interface_api.planning_tasks import database,_get
from .dataset_service import profile_dataset

class DatasetViewRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    action:Literal['read','calculate']='read'
    conversation_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    expected_revision:int=Field(ge=0)
    source_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    profile_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    view:Literal['groups','table']='groups'
    columns:list[str]=Field(default_factory=list,min_length=0,max_length=2)
    offset:int=Field(default=0,ge=0,le=1000000)
    limit:int=Field(default=20,ge=1,le=100)

    @model_validator(mode='after')
    def fields(self):
        if self.action=='calculate' and (not self.columns or len(set(self.columns))!=len(self.columns)):raise ValueError('Choose one or two different fields')
        return self


def percentages(groups,keys,matched):
    totals={}
    for row in groups:totals[row[keys[0]]]=totals.get(row[keys[0]],0)+row['row_count']
    return [{**{k:r[k] for k in keys},'row_count':r['row_count'],'total_denominator':matched,'primary_denominator':totals[r[keys[0]]],
        'percentage_total':100*r['row_count']/matched if matched else None,
        'percentage_within_primary':100*r['row_count']/totals[r[keys[0]]] if totals[r[keys[0]]] else None} for r in groups]


def _bound(root,request):
    with database(root) as connection:state=_get(connection,'conversations',request.conversation_id) if connection else None
    if not state or state['revision']!=request.expected_revision:raise ValueError('Chat changed or is unavailable; refresh saved chat before calculating a view')
    profiles=[o['result'].get('dataset_profile') for o in (state.get('analytical_session') or {}).get('observations',[]) if isinstance(o.get('result'),dict)]
    matches=[p for p in profiles if p and p.get('source_sha256')==request.source_sha256 and (p.get('artifact') or {}).get('sha256')==request.profile_sha256]
    if len(matches)!=1:raise ValueError('Profile does not belong to this chat; reopen its recorded outcome')
    return state,matches[0]


def dataset_view(request:DatasetViewRequest,*,project_root):
    root=project_root.resolve(strict=True);state,original=_bound(root,request)
    # Different views have distinct slots, preserving both last table page and grouped result.
    slot=request.conversation_id+':'+request.view
    with database(root) as connection:
        exists=connection and connection.execute("SELECT 1 FROM sqlite_master WHERE name='dataset_views_v1'").fetchone()
        raw=connection.execute('SELECT value FROM dataset_views_v1 WHERE id=?',(slot,)).fetchone() if exists else None
        saved=json.loads(raw[0]) if raw else None
    if request.action=='read':
        if saved and saved['profile_sha256']==request.profile_sha256 and saved['source_sha256']==request.source_sha256:
            return {'result':saved,'recorded_only':True,'execution_performed':False,'approval_performed':False}
        return {'result':None,'recorded_only':True,'execution_performed':False,'approval_performed':False}
    if set(request.columns)-set(original['columns']):raise ValueError('Choose fields present in the recorded profile')
    if request.view=='groups' and any(p['analytical_role']=='identifier' and p['name'] in request.columns for p in original['profiles']):raise ValueError('Individual identifier grouping is unavailable; use aggregate distinct counts')
    if request.view=='groups' and set(request.columns)&{'row_count','total_denominator','primary_denominator','percentage_total','percentage_within_primary'}:raise ValueError('Grouping field conflicts with summary measure names')
    options={k:v for k,v in original['query'].items() if k in {'codebook_path','missing_values','role_overrides','filters'}}
    options.update(group_by=request.columns if request.view=='groups' else [],numeric_columns=[],distinct_columns=[],preview_columns=request.columns,preview_offset=request.offset,preview_limit=request.limit)
    result=profile_dataset(root,original['source'],options,delimiter='\t' if original['source'].endswith('.tsv') else ',',owner=request.conversation_id,
        expected_sha256=original['source_sha256'],retain_artifact=False)
    old_book=original.get('codebook');new_book=result.get('codebook')
    if old_book and (not new_book or old_book['sha256']!=new_book['sha256']):raise ValueError('Codebook changed since the recorded result; inspect again')
    keys=request.columns if request.view=='groups' else []
    rows=percentages(result['groups'],keys,result['matching_rows']) if keys else []
    value={'conversation_id':request.conversation_id,'revision':request.expected_revision,'source':original['source'],
        'source_sha256':request.source_sha256,'profile_sha256':request.profile_sha256,'view':request.view,
        'columns':request.columns,'group_by':keys,'source_rows':result['source_rows'],'matching_rows':result['matching_rows'],
        'groups':rows,'table':result['table'],'query':options,'runtime':result['runtime'],'verified_at_read':True,
        'checks':{'group_count_reconciles':not keys or sum(r['row_count'] for r in rows)==result['matching_rows']},
        'percentage_policy':'All matching rows, or all rows within the first grouping field. Empty/marker groups retained. Not distinct-patient percentages.'}
    encoded=json.dumps(value,separators=(',',':'),allow_nan=False)
    if len(encoded.encode())>1000000:raise ValueError('View exceeds its saved-result budget; refine grouping')
    with database(root,write=True) as connection:
        latest=_get(connection,'conversations',request.conversation_id)
        if not latest or latest['revision']!=request.expected_revision:raise ValueError('Chat changed during calculation; previous view is preserved. Refresh before retrying.')
        connection.execute('CREATE TABLE IF NOT EXISTS dataset_views_v1 (id TEXT PRIMARY KEY,value TEXT NOT NULL)')
        connection.execute('INSERT INTO dataset_views_v1 VALUES (?,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value',(slot,encoded))
        from geoagent_harness.interface_api.chat_history import archive
        archive(connection,latest,kind='view',view=value)
    return {'result':value,'recorded_only':False,'execution_performed':False,'approval_performed':False,'data_written':False}
