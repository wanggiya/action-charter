"""Bounded content-free request telemetry. Observations never grant authority."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime,timezone
import json
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
    if code in {'planner_budget_exhausted','model_timeout','model_unavailable','model_authentication_failed','model_http_unavailable','model_http_error','model_invalid_response','model_response_format_rejected'}:return code
    from .settings import ModelSettingsError
    if isinstance(error,ModelSettingsError):
        from .diagnostics import model_failure
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
        from geoagent_harness.task_actions.planning_tasks import transaction as database
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
def model_call(request,settings):
    state=_active.get()
    if state is None:yield None;return
    role,name=_phase.get();parent=state['record'];parent['observed_model_calls']+=1
    record={'schema_version':'request-diagnostics-v1','id':uuid4().hex,'parent_id':parent['id'],
        'conversation_id':parent['conversation_id'],'submission_id':parent['submission_id'],'workflow_run_id':parent.get('workflow_run_id'),'role':role,'phase':name,
        'model':settings.model[:160],'timeout_seconds':min(settings.timeout_seconds,request.timeout_seconds or settings.timeout_seconds),
        'output_token_limit':settings.max_tokens,'reasoning_effort':settings.reasoning_effort,'response_format':settings.response_format,
        'prompt_bytes':sum(len(m.content.encode()) for m in request.messages),
        'schema_bytes':len(json.dumps(request.response_schema,separators=(',',':')).encode()) if request.response_schema else 0,
        'prompt_tokens':None,'completion_tokens':None,'status':'started','started_at':now(),'finished_at':None,
        'owner_pid':os.getpid(),'owner_start_ticks':ticks(os.getpid()),'error_code':None}
    if not store(state['root'],'call',record):parent['storage_available']=False
    sample=Samples()
    try:
        yield record
        record['status']='completed'
    except BaseException as error:
        record.update(status='failed',error_code=error_code(error));raise
    finally:
        record.update(finished_at=now(),resources=sample.finish())
        if not store(state['root'],'call',record):parent['storage_available']=False

def read(root,conversation_id):
    from geoagent_harness.task_actions.planning_tasks import transaction as database, _identity
    _identity(conversation_id)
    with database(root) as c:
        rows=[] if c is None else [(row.kind,row.content) for row in c.records('request_diagnostics_v1').entries(owner=conversation_id,limit=100)]
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
        'limitations':LIMITATIONS,'execution_performed':False,'authority_granted':False}


def recent_chats(root):
    """Keep failed first submissions discoverable without storing their prompts."""
    try:
        from geoagent_harness.task_actions.planning_tasks import transaction as database
        with database(root) as c:
            return c.recent_diagnostic_chats() if c else []
    except Exception:return []
