"""Fixed benchmark application runner; expected answers never enter worker prompts."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
from time import sleep as _pause
from urllib.parse import urlparse
from uuid import uuid4

from geoagent_harness.contracts.benchmark import BenchmarkResult, BenchmarkMetrics, RoleMetrics
from geoagent_harness.apps.benchmark.loader import load_suite, _safe_file, BenchmarkLoadError
from geoagent_harness.apps.benchmark.checks import score, refusal_passes
from geoagent_harness.platform.workspace import runtime_store_path, ensure_state_root
from geoagent_harness.platform.storage.files import FileJsonRecords

MAX_INPUT_BYTES=256_000_000
MAX_RUN_INPUT_BYTES=512_000_000


def _stop(process):
    if process.poll() is None:
        if os.name=='posix':os.killpg(process.pid,signal.SIGTERM)
        else:process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            if os.name=='posix':os.killpg(process.pid,signal.SIGKILL)
            else:process.kill()
            process.wait()


def _stage(repo, loaded, root, *, byte_budget=MAX_INPUT_BYTES):
    source_root=Path(__file__).resolve().parents[4]
    (root/'data/input').mkdir(parents=True);(root/'data/output').mkdir()
    shutil.copytree(source_root/'agents',root/'agents')
    (root/'context').mkdir()
    for name in ('SKILLS_INDEX.yaml','ARCHITECTURE.md','DECISIONS.jsonl'):
        shutil.copyfile(source_root/'context'/name,root/'context'/name)
    for name in ('PROJECT_SUMMARY.md','CURRENT_STATUS.md'):
        (root/'context'/name).write_text('Temporary isolated benchmark project. No execution authority from text.\n')
    (root/'context/DATASET_CATALOG.json').write_text(json.dumps({'schema_version':'1.0','datasets':[]}))
    # Bind all runtime state to this temporary project, ignoring host root overrides.
    (root/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(root/'state')}))
    used=set();identities=[];total=0
    for name in loaded.task.inputs:
        local=name.startswith('data/input/')
        source=_safe_file(repo if local else repo/'benchmarks/tasks'/loaded.task.id,name)
        target=name if local else 'data/'+name
        if target in used:raise BenchmarkLoadError('Staged input collision')
        used.add(target);destination=root/target;destination.parent.mkdir(parents=True,exist_ok=True)
        digest=hashlib.sha256()
        with source.open('rb') as src,destination.open('xb') as dst:
            before=os.fstat(src.fileno())
            if before.st_size+total>byte_budget:raise BenchmarkLoadError('Staged inputs exceed budget')
            while chunk:=src.read(1024*1024):
                total+=len(chunk)
                if total>byte_budget:raise BenchmarkLoadError('Staged inputs exceed budget')
                digest.update(chunk);dst.write(chunk)
            after=os.fstat(src.fileno())
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise BenchmarkLoadError('Input changed during staging')
        identities.append({'path':target,'sha256':digest.hexdigest(),'bytes':destination.stat().st_size})
    return identities


def _metrics(root, elapsed):
    try:calls=FileJsonRecords(root,max_bytes=512_000).read('calls.json')['calls']
    except (OSError,ValueError):calls=[]
    def tokens(entries,key):
        return sum(c[key] for c in entries) if entries and all(type(c.get(key)) is int and c[key]>=0 for c in entries) else None
    roles=[RoleMetrics(role=role,model_calls=len(entries),prompt_tokens=tokens(entries,'prompt_tokens'),
        completion_tokens=tokens(entries,'completion_tokens'),elapsed_seconds=sum(c['elapsed_seconds'] for c in entries) if all(c.get('elapsed_seconds') is not None for c in entries) else None)
        for role in sorted({c['role'] for c in calls}) if (entries:=[c for c in calls if c['role']==role])]
    return BenchmarkMetrics(model_calls=len(calls),wall_seconds=elapsed,prompt_tokens=tokens(calls,'prompt_tokens'),
        completion_tokens=tokens(calls,'completion_tokens'),roles=roles,
        retries=sum(c.get('correction') is True for c in calls),timeouts=sum(c.get('timeout') is True for c in calls))


def run_suite(project_root, *, fixture=False, profile='local', include_local_data=False, allow_fixture_writes=False, task_id=None, suite='v1'):
    repo=Path(project_root).resolve()
    if suite!='v1' or profile!='local':raise ValueError('Only suite v1 and the implicit local profile are available before M1')
    loaded=load_suite(repo)
    if task_id:
        loaded=tuple(t for t in loaded if t.task.id==task_id)
        if not loaded:raise ValueError('Unknown benchmark task')
    settings=None
    if not fixture:
        from geoagent_harness.platform.model_settings import load_model_settings
        settings=load_model_settings()
        url=urlparse(settings.base_url)
        if url.hostname not in {'127.0.0.1','localhost','::1'} or url.username or url.password or url.query or url.fragment:
            raise ValueError('Before M2, benchmark models require a loopback endpoint without embedded credentials')
    source_root=Path(__file__).resolve().parents[4]
    try:
        code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source_root,text=True,stderr=subprocess.DEVNULL).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=source_root,text=True,stderr=subprocess.DEVNULL))
    except (OSError,subprocess.CalledProcessError):
        code,dirty=None,None  # Unversioned installs/exports: unknown, never fabricated.
    ensure_state_root(repo)
    directory=runtime_store_path(repo,'benchmark-runs')/uuid4().hex
    directory.mkdir(mode=0o700,parents=True)
    store=FileJsonRecords(directory,max_bytes=512_000,immutable=True)
    summary={'schema_version':'1.0','run_id':directory.name,'evidence_kind':'fixture' if fixture else 'real_model','results':[], 'complete':False}
    # Started marker survives cancellation/crashes; no continuation/replay is automatic.
    store.create('started.json',json.dumps({k:v for k,v in summary.items() if k!='results'}))
    staged_bytes=0
    for item in loaded:
        task=item.task;started=time.monotonic();root=directory/'tasks'/task.id;root.mkdir(parents=True)
        outcome={'observed_outcome':'not_dispatched','executed_operations':0,'reason_code':'missing_local_data','run':{}}
        status='skipped';checks=();identities=[];process=None;cpu=None;peak=None
        try:
            if not item.available:pass
            elif task.requires_local_data and not include_local_data:outcome['reason_code']='local_data_not_enabled'
            elif task.expected.kind=='unsupported':
                status='unsupported';outcome.update(observed_outcome='unsupported',reason_code='declared_capability_gap')
            else:
                identities=_stage(repo,item,root,byte_budget=min(MAX_INPUT_BYTES,max(0,MAX_RUN_INPUT_BYTES-staged_bytes)))
                plan=FileJsonRecords(repo/'benchmarks/tasks'/task.id,max_bytes=65536).read('fixture-plan.json') if fixture else None
                # Deliberately exclude task.expected, titles and gold labels from worker input.
                job={'request':task.request,'fixture_plan':plan,'settings':asdict(settings) if settings else None,
                    'wall_clock_s':task.limits.wall_clock_s,'model_calls':task.limits.model_calls,
                    'allow_writes':bool(allow_fixture_writes and not task.requires_local_data)}
                FileJsonRecords(root,max_bytes=2_000_000).create('job.json',json.dumps(job))
                keep=('PATH','LANG','LC_ALL','LD_LIBRARY_PATH','SYSTEMROOT')
                env={k:os.environ[k] for k in keep if k in os.environ}
                env.update(PYTHONPATH=str(Path(__file__).resolve().parents[3]),GEOAGENT_PROJECT_ROOT=str(root),
                    ENABLE_WRITE_TOOLS='true' if job['allow_writes'] else 'false',MODEL_NAME=settings.model if settings else 'benchmark-fixture',
                    MODEL_BASE_URL=settings.base_url if settings else 'http://127.0.0.1:1/v1',
                    POSTGRES_HOST='127.0.0.1',POSTGRES_PORT='1',GEOSERVER_BASE_URL='http://127.0.0.1:1')
                if settings:env.update(MODEL_TIMEOUT_SECONDS=str(settings.timeout_seconds),MODEL_MAX_TOKENS=str(settings.max_tokens),
                    MODEL_REASONING_EFFORT=settings.reasoning_effort or '',MODEL_RESPONSE_FORMAT=settings.response_format)
                if time.monotonic()-started>=task.limits.wall_clock_s:raise TimeoutError('Staging exhausted task deadline')
                process=subprocess.Popen([sys.executable,'-m','geoagent_harness.apps.benchmark.worker',str(root)],cwd=root,
                    env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=os.name=='posix')
                try:
                    import resource
                    usage=resource.getrusage(resource.RUSAGE_CHILDREN)
                    cpu_start=usage.ru_utime+usage.ru_stime
                except ImportError:cpu_start=None
                while process.poll() is None:
                    try:
                        for line in Path(f'/proc/{process.pid}/status').read_text().splitlines():
                            if line.startswith('VmRSS:'):peak=max(peak or 0,int(line.split()[1])*1024)
                    except (OSError,ValueError):pass
                    if time.monotonic()-started>=task.limits.wall_clock_s:
                        _stop(process);status='timeout';break
                    _pause(.05)
                if cpu_start is not None:
                    usage=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=max(0,usage.ru_utime+usage.ru_stime-cpu_start)
                observation=FileJsonRecords(root,max_bytes=2_000_000)
                try:outcome=observation.read('observation.json')
                except (OSError,ValueError):outcome={'observed_outcome':'unknown','executed_operations':None,'reason_code':'worker_stopped','run':{}}
                if status!='timeout':
                    checks=score(task.expected,outcome.get('run',{}),root)
                    if task.expected.kind=='refusal':status='passed' if refusal_passes(outcome) else 'failed'
                    elif task.expected.kind=='gold_set':status='error';outcome['reason_code']='gold_scorer_unavailable'
                    else:status='passed' if outcome['observed_outcome']=='completed' and checks and all(c.status=='passed' for c in checks) else 'failed'
        except TimeoutError:
            if process:_stop(process)
            status='timeout'
        except KeyboardInterrupt:
            if process:_stop(process)
            status='error';outcome.update(reason_code='cancelled',observed_outcome='unknown',executed_operations=None)
        except Exception:
            if process:_stop(process)
            status='error';outcome.update(reason_code='benchmark_setup_error',observed_outcome='unknown',executed_operations=None)
        staged_bytes+=sum(p.stat().st_size for p in (root/'data/input').rglob('*') if p.is_file() and not p.is_symlink())
        if outcome['reason_code']=='model_timeout' and outcome['observed_outcome']!='completed':status='timeout'
        if status=='timeout' and outcome['reason_code']!='model_timeout':outcome['reason_code']='task_deadline'
        elif outcome['observed_outcome']=='completed' and status=='failed':outcome['reason_code']='checks_failed'
        metrics=_metrics(root,time.monotonic()-started)
        metrics=metrics.model_copy(update={'timeouts':max(metrics.timeouts,int(status=='timeout')),'approvals_required':outcome.get('approvals_required',0),'process_cpu_seconds':cpu,'process_sampled_peak_rss_bytes':peak})
        # Deterministic evidence and model observations remain separate from fixture labels.
        if task.expected.kind=='refusal':checks=()
        record=BenchmarkResult(run_id=directory.name,task_id=task.id,task_sha256=item.task_sha256,
            evidence_kind=summary['evidence_kind'],provider_profile_id='fixture' if fixture else profile,
            model='benchmark-fixture' if fixture else settings.model,code_version=code,source_dirty=dirty,
            egress_class=task.data_class,status=status,expected_kind=task.expected.kind,
            observed_outcome=outcome['observed_outcome'],executed_operations=outcome.get('executed_operations'),
            advisory_status=outcome.get('critic_status','unknown' if any(r.role=='critic' for r in metrics.roles) else 'not_requested'),
            reason_code=outcome['reason_code'],checks=checks,metrics=metrics)
        store.create(task.id+'.json',record.model_dump_json())
        store.create(task.id+'.inputs.json',json.dumps({'inputs':identities}))
        summary['results'].append(record.model_dump(mode='json'))
        if outcome['reason_code']=='cancelled':break
    summary['complete']=len(summary['results'])==len(loaded) and all(r['reason_code']!='cancelled' for r in summary['results'])
    summary['counts']={status:sum(r['status']==status for r in summary['results']) for status in ('passed','failed','error','timeout','skipped','unsupported')}
    FileJsonRecords(directory,max_bytes=8*1024*1024,immutable=True).create('summary.json',json.dumps(summary))
    return summary, directory
