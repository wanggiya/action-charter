"""Bounded content-free request telemetry. Observations never grant authority."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime,timezone
import json
import logging
import math
import os
from pathlib import Path
import re
import threading
import time
from uuid import uuid4

_active=ContextVar('request_diagnostics',default=None)
_phase=ContextVar('diagnostic_phase',default=('unassigned','model_call'))
MAX_RECORDS=600
MAX_CALLS=6000
LIMITATIONS=['API RSS is sampled process memory shared by concurrent work, not exact per-chat allocation.',
    'CPU seconds cover this process during the interval, including concurrent work.',
    'System available RAM is machine-wide. Worker RAM and Ollama/GPU memory are not measured here.',
    'Missing token usage is unknown, never inferred from prompt bytes or recorded as zero.',
    'A completed model call is not a validated plan or successful execution.']

def now():return datetime.now(timezone.utc).isoformat()

def error_code(error):
    current=error;seen=set()
    while current is not None and id(current) not in seen and len(seen)<8:
        seen.add(id(current));message=str(current)
        if message.startswith(('Executor work-order review requests correction:','Critic plan review requests correction:')):
            return 'planner_review_needs_revision'
        current=current.__cause__
    code=getattr(error,'code',None)
    if code in {'planner_budget_exhausted','model_timeout','model_unavailable','model_authentication_failed','model_http_unavailable','model_http_error','model_invalid_response','model_response_format_rejected','model_data_class_blocked'}:return code
    from geoagent_harness.platform.model_settings import ModelSettingsError
    if isinstance(error,ModelSettingsError):
        from geoagent_harness.platform.model_gateway.diagnostics import model_failure
        return model_failure(error)['code']
    reason=getattr(error,'reason',None)
    if reason=='output_truncated':return 'planner_output_truncated'
    text=str(error).lower()
    for fragment,code in [('invalid plan schema','planner_invalid_schema'),('invalid json','planner_invalid_json'),('deterministic policy','planner_policy_rejected')]:
        if fragment in text:return code
    return 'request_failed'

def safe_diagnostics(error):
    raw=getattr(error,'planner_diagnostics',{}) or {}
    fields=('prompt_bytes','response_schema_bytes','supplied_schema_count','available_operation_count','elapsed_seconds','completion_tokens','response_bytes','discovery_rounds')
    return {key:raw[key] for key in fields if isinstance(raw.get(key),(int,float)) and not isinstance(raw[key],bool)}

def ticks(pid):
    try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
    except (OSError,IndexError):return None

def resources():
    result={'api_rss_bytes':None,'system_available_bytes':None}
    for path,key,field in [('/proc/self/status','api_rss_bytes','VmRSS:'),('/proc/meminfo','system_available_bytes','MemAvailable:')]:
        try:
            for line in Path(path).read_text().splitlines():
                if line.startswith(field):result[key]=int(line.split()[1])*1024;break
        except (OSError,ValueError):pass
    return result

class Samples:
    def __init__(self):
        self.stop=threading.Event();self.started=time.monotonic();self.cpu=time.process_time();self.first=resources();self.peak=self.first['api_rss_bytes'];self.minimum=self.first['system_available_bytes'];self.count=1
        self.thread=threading.Thread(target=self.sample,daemon=True);self.thread.start()
    def sample(self):
        while not self.stop.wait(.5):
            r=resources();self.count+=1
            if r['api_rss_bytes'] is not None:self.peak=max(self.peak or 0,r['api_rss_bytes'])
            if r['system_available_bytes'] is not None:self.minimum=min(self.minimum if self.minimum is not None else r['system_available_bytes'],r['system_available_bytes'])
    def finish(self):
        self.stop.set();self.thread.join(timeout=1);last=resources()
        return {'elapsed_seconds':round(time.monotonic()-self.started,4),'process_cpu_seconds':round(time.process_time()-self.cpu,4),
            'api_rss_start_bytes':self.first['api_rss_bytes'],'api_rss_end_bytes':last['api_rss_bytes'],
            'api_rss_sampled_peak_bytes':max([v for v in [self.peak,last['api_rss_bytes']] if v is not None],default=None),
            'system_available_min_bytes':min([v for v in [self.minimum,last['system_available_bytes']] if v is not None],default=None),
            'samples':self.count+1,'sample_interval_seconds':.5,'worker_rss_bytes':None,'model_rss_bytes':None,'gpu_vram_bytes':None}

def store(root,kind,value):
    try:
        from geoagent_harness.platform.storage.metadata import transaction as database
        with database(root,write=True) as c:
            encoded=json.dumps(value,separators=(',',':'))
            if len(encoded.encode())>12000:raise ValueError('Diagnostic record budget')
            c.records('request_diagnostics_v1').put(value['id'],encoded,owner=value['conversation_id'],kind=kind,parent=value.get('parent_id'))
            # Retention preserves the existing active-call and parent/child rules.
            c.prune_diagnostics(turns=MAX_RECORDS,calls=MAX_CALLS)
        return True
    except Exception:return False  # Monitoring must not retry or alter data execution.

@contextmanager
def phase(role,name):
    token=_phase.set((role,name))
    try:yield
    finally:_phase.reset(token)

@contextmanager
def scope(root,conversation_id,submission_id=None,*,independent=False):
    existing=_active.get()
    if not independent and existing is not None and existing['record']['conversation_id']==conversation_id and existing['root'].resolve()==Path(root).resolve():
        yield existing;return
    record={'schema_version':'request-diagnostics-v1','id':uuid4().hex,'conversation_id':conversation_id,'submission_id':submission_id,
        'status':'started','started_at':now(),'finished_at':None,'owner_pid':os.getpid(),'owner_start_ticks':ticks(os.getpid()),
        'error_code':None,'observed_model_calls':0,'storage_available':True}
    state={'root':Path(root),'record':record};record['storage_available']=store(root,'turn',record)
    sample=Samples();token=_active.set(state)
    try:
        yield state
        record['status']='completed'
    except BaseException as error:
        record.update(status='failed',error_code=error_code(error),failure_diagnostics=safe_diagnostics(error))
        raise
    finally:
        record.update(finished_at=now(),resources=sample.finish())
        store(root,'turn',record);_active.reset(token)

@contextmanager
def model_call(request,settings,*,decision=None):
    state=_active.get()
    standalone=state is None
    if standalone:
        # No synthetic chat/turn is created. Configured standalone calls reuse the
        # existing record store; embedders without a root receive a safe log event.
        state={'root':Path(settings.credential_root) if settings.credential_root else None,
            'record':{'id':None,'conversation_id':uuid4().hex,'submission_id':None,
                      'observed_model_calls':0,'storage_available':True}}
    role,name=_phase.get();parent=state['record'];parent['observed_model_calls']+=1
    record={'schema_version':'request-diagnostics-v1','id':uuid4().hex,'parent_id':parent['id'],
        'conversation_id':parent['conversation_id'],'submission_id':parent['submission_id'],'workflow_run_id':parent.get('workflow_run_id'),'role':role,'phase':name,
        'model':settings.model[:160],'timeout_seconds':min(settings.timeout_seconds,request.timeout_seconds or settings.timeout_seconds),
        'provider_profile_id':settings.provider_profile_id,'provider_kind':settings.provider_kind,'provider_location':settings.provider_location,
        'output_token_limit':settings.max_tokens,'reasoning_effort':settings.reasoning_effort,'response_format':settings.response_format,
        'prompt_bytes':sum(len(m.content.encode()) for m in request.messages),
        'schema_bytes':len(json.dumps(request.response_schema,separators=(',',':')).encode()) if request.response_schema else 0,
        'prompt_tokens':None,'completion_tokens':None,'status':'started','started_at':now(),'finished_at':None,
        'owner_pid':os.getpid(),'owner_start_ticks':ticks(os.getpid()),'error_code':None,
        'network_dispatch':'unknown' if decision is not None and decision.allowed else 'not_attempted'}
    if decision is not None:
        record.update(highest_data_class=decision.highest_class,data_allowed=decision.data_allowed,
            configured_data_allowed=decision.configured_data_allowed,
            egress_decision='allowed' if decision.allowed else 'blocked',
            unclassified_parts=decision.unclassified_parts,nonlocal_restricted=decision.nonlocal_restricted)
    if state['root'] is not None and not store(state['root'],'call',record):parent['storage_available']=False
    sample=Samples()
    try:
        yield record
        record['status']='completed'
    except BaseException as error:
        record.update(status='failed',error_code=error_code(error));raise
    finally:
        record.update(finished_at=now(),resources=sample.finish())
        if state['root'] is not None and not store(state['root'],'call',record):parent['storage_available']=False
        if standalone:
            logging.getLogger(__name__).info('model_egress',extra={'model_egress':{
                key:record[key] for key in ('provider_profile_id','provider_kind','provider_location',
                'model','highest_data_class','data_allowed','egress_decision','network_dispatch',
                'status','error_code') if key in record}})

def read(root,conversation_id):
    from geoagent_harness.platform.storage.metadata import transaction as database, validate_identity as _identity
    _identity(conversation_id)
    with database(root) as c:
        rows=[] if c is None else [(row.kind,row.content) for row in c.records('request_diagnostics_v1').entries(owner=conversation_id,limit=100)]
        retained=0 if c is None else c.records('request_diagnostics_v1').count(owner=conversation_id)
    records=[]
    for kind,raw in rows:
        v=json.loads(raw)
        if v['status']=='started':
            observed=ticks(v['owner_pid']);original=v.get('owner_start_ticks');dead=False
            if observed is not None and original is not None:dead=observed!=original
            elif observed is None and os.name=='posix':
                try:os.kill(v['owner_pid'],0)
                except ProcessLookupError:dead=True
                except (PermissionError,OSError):pass
            if dead:v['status']='interrupted';v['error_code']='process_interrupted'
        v.pop('owner_pid',None);v.pop('owner_start_ticks',None);v['kind']=kind;records.append(v)
    calls=[v for v in records if v['kind']=='call'];complete=all(v['status']=='completed' and v['prompt_tokens'] is not None and v['completion_tokens'] is not None for v in calls)
    return {'schema_version':'request-diagnostics-v1','conversation_id':conversation_id,'records':records,
        'returned_limit':100,'scope':'most_recent_records_in_this_chat','reported_prompt_tokens':sum(v['prompt_tokens'] for v in calls) if complete else None,
        'reported_completion_tokens':sum(v['completion_tokens'] for v in calls) if complete else None,'token_usage_complete':complete,
        'reported_model_usage':reported_model_usage(records,retained_records=retained),
        'limitations':LIMITATIONS,'execution_performed':False,'authority_granted':False}


def reported_model_usage(records,*,retained_records=None):
    """Pure, bounded summaries of visible observations, never lifetime billing.

    A call is counted once in a scope. Parent request durations are not added to
    nested model durations. Missing/blocked calls never fabricate token counts.
    Input and output stay separate; repeated context is counted per model call.
    """
    parents={r['id']:r for r in records if r.get('kind')=='turn'}
    calls=list({r['id']:r for r in records if r.get('kind')=='call'}.values())
    truncated=retained_records is not None and retained_records>len(records)
    def count(value):return type(value) is int and 0<=value<=2**31-1
    def seconds(value):return type(value) in {int,float} and math.isfinite(value) and value>=0
    def run_id(record):
        return record.get('workflow_run_id') or parents.get(record.get('parent_id'),{}).get('workflow_run_id')
    def metrics(items,roots=()):
        sent=[r for r in items if r.get('network_dispatch')!='not_attempted']
        expected=max(len(items),sum(r.get('observed_model_calls',0) for r in roots if count(r.get('observed_model_calls'))))
        missing=expected-len(items)
        inputs=[r['prompt_tokens'] for r in sent if count(r.get('prompt_tokens'))]
        outputs=[r['completion_tokens'] for r in sent if count(r.get('completion_tokens'))]
        paired=sum(count(r.get('prompt_tokens')) and count(r.get('completion_tokens')) for r in sent)
        timed=[r for r in sent if seconds((r.get('resources') or {}).get('elapsed_seconds'))]
        rate_calls=[r for r in timed if count(r.get('completion_tokens')) and r['resources']['elapsed_seconds']>0]
        duration=sum(r['resources']['elapsed_seconds'] for r in timed)
        rate_time=sum(r['resources']['elapsed_seconds'] for r in rate_calls)
        incomplete=missing>0 or any(r.get('storage_available') is False for r in [*roots,*items])
        return {'recorded_calls':len(items),'not_sent_calls':len(items)-len(sent),
            'calls_awaiting_or_attempting_response':sum(r.get('status')=='started' for r in sent),
            'calls_with_reported_input':len(inputs),'calls_with_reported_output':len(outputs),
            'calls_with_both_counts':paired,'calls_with_unknown_usage':len(sent)-paired+missing,
            'calls_expected_usage':len(sent)+missing,
            'missing_call_records':missing,'collection_incomplete':incomplete,
            'reported_input_tokens':sum(inputs) if inputs else None,
            'reported_output_tokens':sum(outputs) if outputs else None,
            'model_call_seconds':round(duration,4) if timed else None,'timed_calls':len(timed),
            'end_to_end_output_tokens_per_second':round(sum(r['completion_tokens'] for r in rate_calls)/rate_time,3) if rate_time else None,
            'rate_measured_calls':len(rate_calls),
            'model_call_failures':sum(r.get('status') in {'failed','interrupted'} for r in sent),
            'timeout_calls':sum(r.get('error_code')=='model_timeout' for r in sent),
            'correction_calls':sum(str(r.get('phase') or '').endswith('_correction') for r in sent),
            'coverage':'partial' if incomplete or paired<len(sent) else 'reported_for_visible_calls' if sent else 'not_sent' if items else 'no_recorded_calls'}
    def scope(identity,label,kind,items,roots):
        groups={}
        for call in items:
            key=(call.get('role') or 'unassigned',call.get('provider_profile_id') or 'unknown',call.get('model') or 'unknown')
            groups.setdefault(key,[]).append(call)
        return {'id':identity,'label':label,'kind':kind,**metrics(items,roots),
            'workflow_status':next((r['workflow_status'] for r in roots if r.get('workflow_status')),None),
            'by_role_model':[{'role':key[0],'provider_profile_id':key[1],'model':key[2],**metrics(value)} for key,value in sorted(groups.items())]}
    scopes=[scope('chat','Recent chat records','chat',calls,list(parents.values()))]
    for parent in parents.values():
        if parent.get('workflow_run_id') and not parent.get('submission_id'):continue
        submission=parent.get('submission_id')
        related=[c for c in calls if c.get('parent_id')==parent['id'] or (submission and c.get('submission_id')==submission)]
        identity='submission:'+(submission or parent['id'])
        if any(s['id']==identity for s in scopes):continue
        roots=[p for p in parents.values() if p['id']==parent['id'] or (submission and p.get('submission_id')==submission)]
        scopes.append(scope(identity,'Submission · '+str(parent.get('started_at','Unknown time')),'submission',related,roots))
    for identity in sorted({run_id(r) for r in records if run_id(r)}):
        related=[c for c in calls if run_id(c)==identity]
        roots=[p for p in parents.values() if run_id(p)==identity]
        scopes.append(scope('workflow:'+identity,'Workflow · '+identity[:8],'workflow',related,roots))
    return {'schema_version':'reported-model-tokens-v1','record_limit':100,
        'returned_records':len(records),'retained_records':retained_records,
        'records_truncated':truncated,'lifetime_usage':False,'scopes':scopes}


def recent_chats(root):
    """Keep failed first submissions discoverable without storing their prompts."""
    try:
        from geoagent_harness.platform.storage.metadata import transaction as database
        with database(root) as c:
            return c.recent_diagnostic_chats() if c else []
    except Exception:return []
