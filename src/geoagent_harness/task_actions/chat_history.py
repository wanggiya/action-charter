"""Immutable chat-scoped workflow/analysis snapshots; opening history grants no authority."""
from geoagent_harness.task_actions.planning_tasks import as_transaction
from geoagent_harness.platform.storage.chat_snapshots import _tables, _digest, archive
import hashlib,json
from datetime import datetime,timezone
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from geoagent_harness.platform.paths import runtime_store_path
from geoagent_harness.platform.storage.metadata import transaction as database
from geoagent_harness.task_actions.planning_tasks import _get, write_turn

class HistoryRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    action:Literal['list','read','continue']='list'
    conversation_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    entry_id:str|None=Field(default=None,pattern=r'^(?:[a-f0-9]{64}|run:[a-f0-9]{32})$')
    expected_revision:int|None=Field(default=None,ge=0)








def _entries(db,identity):
    db = as_transaction(db)
    if db is None:return []
    entries=[]
    for row in db.records('chat_history_v1').entries(owner=identity):
        key,raw=row.key,row.content
        value=json.loads(raw)
        if value.get('conversation_id')!=identity or value.get('id')!=key or _digest({'conversation_id':identity,'revision':value['revision'],**{k:value[k] for k in ['planner_result','analytical_session','view']}})!=key:raise ValueError('History record scope or digest changed')
        entries.append(value)
    return entries


def _blob(db,digest):
    db = as_transaction(db)
    if digest is None:return None
    raw=db.records('chat_history_blobs_v1').get(digest)
    if raw is None or len(raw.encode())>2_000_000:raise ValueError('Historical content is unavailable')
    value=json.loads(raw)
    if _digest(value)!=digest:raise ValueError('Historical content digest does not match')
    return value


def _runs(root,identity):
    directory=runtime_store_path(root, 'workflow-state', 'interface-runs')
    if not directory.exists():return []
    if directory.is_symlink() or directory.parent.is_symlink():raise ValueError('Unsafe execution history storage')
    from geoagent_harness.task_actions.workflow_runs import _read
    records=[]
    for path in sorted(directory.glob('*.json'),key=lambda p:p.lstat().st_mtime,reverse=True)[:200]:
        if path.is_symlink():continue
        import re
        if not re.fullmatch('[a-f0-9]{32}',path.stem):continue
        record=_read(directory,path.stem, project_root=root)
        if record.get('conversation_id')==identity:records.append(record)
    return records


def history_action(request:HistoryRequest,*,project_root):
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn, Conversation, _response
    root=project_root.resolve(strict=True)
    current=conversation_turn(TurnRequest(action='read',conversation_id=request.conversation_id),project_root=root)
    # Safely index the recoverable current baseline. Earlier overwritten states cannot be invented.
    with database(root,write=True) as db:
        stored=_get(db,'conversations',request.conversation_id)
        if stored:archive(db,stored)
    runs=_runs(root,request.conversation_id)
    with database(root) as db:
        entries=_entries(db,request.conversation_id)
        if request.action=='list':
            public=[{k:e[k] for k in ['id','conversation_id','revision','kind','summary','recorded_at']} for e in entries]
            public += [{'id':'run:'+r['run_id'],'conversation_id':request.conversation_id,'revision':None,'kind':'run','summary':r['status']+' · '+r['plan_sha256'][:12],'recorded_at':r['started_at']} for r in runs]
            return {'entries':sorted(public,key=lambda e:e['recorded_at'],reverse=True),'revision':current['revision'],'finding':'Recorded versions plus linked runs. Earlier overwritten versions may be unavailable. Reads never rerun work.','execution_performed':False,'approval_performed':False}
        if request.entry_id and request.entry_id.startswith('run:'):
            if request.action!='read':raise ValueError('Continue from a workflow version, not an execution attempt')
            record=next((r for r in runs if 'run:'+r['run_id']==request.entry_id),None)
            if not record:raise ValueError('Execution does not belong to this chat')
            return {'entry':{'id':request.entry_id,'kind':'run','revision':None,'summary':record['status']},'planner_result':None,'analytical_session':None,'view':None,'run':record,'execution_performed':False,'approval_performed':False}
        entry=next((e for e in entries if e['id']==request.entry_id),None)
        if not entry:raise ValueError('Historical item does not belong to this chat')
        plan=_blob(db,entry['planner_result']);analysis=_blob(db,entry['analytical_session']);view=_blob(db,entry['view'])
    if request.action=='continue':
        if request.expected_revision is None or request.expected_revision!=current['revision']:raise ValueError('Chat changed; refresh before continuing from history')
        from geoagent_harness.capabilities.workflow import _check
        from geoagent_harness.contracts.planning import PlannerResult
        if plan:_check(PlannerResult.model_validate(plan),root)
        raw={k:v for k,v in current.items() if k in Conversation.model_fields}
        if raw.get('planner_result'):raw['planner_result']={k:v for k,v in raw['planner_result'].items() if k in PlannerResult.model_fields}
        state=Conversation.model_validate(raw)
        state.planner_result=PlannerResult.model_validate(plan) if plan else None;state.analytical_session=analysis
        state.revision+=1
        from geoagent_harness.task_actions.conversation import Entry
        if len(state.messages)>98:raise ValueError('Chat is full; preserve/export history before continuing')
        state.messages.extend([Entry(role='user',content='Continue from saved version '+entry['id'][:12],task_id=state.conversation_id,conversation_id=state.conversation_id),Entry(role='assistant',content='Saved workflow/analysis restored as a new draft revision. No historical approval or execution was reused.',task_id=state.conversation_id,conversation_id=state.conversation_id)])
        state.context_usage={'history_enabled':True,'included_messages':0,'omitted_messages':len(state.messages),'excerpts_truncated':False,'prompt_bytes':0,'prompt_limit_bytes':64000,'model_request':{'stage':'analytical_history_restore' if analysis and entry['kind'] in {'analysis','view'} else 'history_restore','elapsed_seconds':0,'prompt_bytes':0,'supplied_schema_count':0,'available_operation_count':0,'retrieved_method_count':0,'model_calls':0}}
        write_turn(root,state.model_dump(mode='json'),expected_revision=request.expected_revision,expected_task_revision=request.expected_revision,restored_view=view)
        state.task_revision=state.revision
        response=_response(state,False,root=root)
        return {'conversation':response,'execution_performed':False,'approval_performed':False}
    public_plan=None
    if plan:
        from geoagent_harness.core.policy.approvals import plan_sha256
        from geoagent_harness.contracts.planning import PlannerResult
        public_plan={**plan,'schema_version':'1.0','status':'planned_not_saved','allowed_skill_ids':current['allowed_skill_ids'],'plan_sha256':plan_sha256(PlannerResult.model_validate(plan).plan),'plan_saved':False,'approval_performed':False,'execution_performed':False}
    return {'entry':entry,'planner_result':public_plan,'analytical_session':analysis,'view':view,'run':None,'execution_performed':False,'approval_performed':False}


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
history_action = _task_entrypoint(history_action, audit=lambda arguments: arguments["request"].action not in ['list', 'read'])
