#!/usr/bin/env python3
"""Opt-in, synthetic M3c qualification. No owner config, dataset or secret loading.

Relays exercise transports against the SAME model, not independent providers.
Only the sanitized result is retained; temporary workflow state is removed.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from importlib.metadata import version
import os
from pathlib import Path
import secrets
import shutil
import socket
from socketserver import ThreadingMixIn, UnixStreamServer
import subprocess
import sys
import tempfile
from threading import Thread
import time
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'scripts'))
import httpx

from geoagent_harness.apps.benchmark.checks import score
from geoagent_harness.apps.benchmark.loader import load_task
from geoagent_harness.apps.benchmark.runner import _stage, _stop
from geoagent_harness.apps.benchmark.reporting import source_sha256
from geoagent_harness.contracts.model_providers import ProviderProfile, ProviderUpdate, ProviderSelection
from geoagent_harness.platform.model_gateway import SharedModelClient
from geoagent_harness.platform.model_gateway.profiles import save, select, capture, loopback
from geoagent_harness.platform.model_gateway.schemas import ModelRequest, ChatMessage
from geoagent_harness.platform.model_settings import ModelSettings

TASK = 's-csv-profile-001'
REQUEST = ('For the synthetic table orders.csv, propose a read-only workflow to report its row count '
           'and column names. Use only inspect_csv; do not write any output files.')
MODES = ('direct', 'compatible-relay', 'authenticated-relay', 'isolated', 'gateway', 'secondary')


def endpoint(value):
    # Strict literal loopback prevents a DNS/proxy hop from escaping this test scope.
    profile = ProviderProfile(id='qualification', base_url=value)
    if urlsplit(profile.base_url).hostname not in {'127.0.0.1', '::1'} or not loopback(value):
        raise ValueError('Qualification requires a literal loopback /v1 endpoint')
    return profile.base_url


class _UnixHTTP(ThreadingMixIn, UnixStreamServer):
    daemon_threads = True


class Relay:
    """Private fixed-destination HTTP broker, with no URL/tool/forward-proxy API."""
    def __init__(self, upstream, *, key=None, unix_socket=None, timeout=120):
        self.upstream = endpoint(upstream)
        self.key, self.unix_socket, self.timeout = key, unix_socket, timeout
        self.forwarded = self.rejected = 0

    def __enter__(self):
        relay = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                if self.path != '/v1/chat/completions':
                    self.send_error(404); return
                if relay.key and not secrets.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + relay.key):
                    relay.rejected += 1
                    self.send_error(401); return
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    if not 0 < size <= 1_000_000 or self.headers.get('Transfer-Encoding'):
                        self.send_error(413); return
                    body = self.rfile.read(size)
                    if len(body) != size:
                        self.send_error(400); return
                    # The synthetic gate key is consumed here, never sent upstream.
                    relay.forwarded += 1
                    with httpx.Client(timeout=relay.timeout, trust_env=False, follow_redirects=False) as client:
                        with client.stream('POST', relay.upstream + '/chat/completions',
                                           content=body, headers={'Content-Type': 'application/json'}) as response:
                            data = bytearray()
                            for part in response.iter_bytes():
                                data.extend(part)
                                if len(data) > 2_000_000:
                                    raise ValueError('Response budget')
                            status = response.status_code
                    self.send_response(status)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers(); self.wfile.write(data)
                except (OSError, ValueError, httpx.HTTPError):
                    try: self.send_error(502)
                    except OSError: pass

        if self.unix_socket:
            self.server = _UnixHTTP(self.unix_socket, Handler)
            os.chmod(self.unix_socket, 0o600)
            self.base_url = 'http://127.0.0.1/v1'
        else:
            self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            self.server.daemon_threads = True
            self.base_url = f'http://127.0.0.1:{self.server.server_port}/v1'
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=3)


def smoke(settings, *, transport=None):
    started = time.monotonic()
    request = ModelRequest(messages=[ChatMessage(role='user', content='Return exactly {"ok":true}.')],
        json_mode=True, response_schema={'type':'object','properties':{'ok':{'const':True}},'required':['ok'],'additionalProperties':False})
    try:
        result = SharedModelClient(replace(settings, max_tokens=64), transport=transport).complete(request)
        valid = json.loads(result.content) == {'ok': True}
        return {'status':'passed' if valid else 'failed', 'code':'valid_json' if valid else 'unexpected_content',
                'model':result.model, 'format':result.response_format, 'finish_reason':result.finish_reason,
                'prompt_tokens':result.prompt_tokens, 'completion_tokens':result.completion_tokens,
                'seconds':round(time.monotonic()-started, 3)}
    except Exception as error:
        from geoagent_harness.platform.model_gateway.profiles import ProviderError
        return {'status':'failed', 'code':getattr(error, 'code', None) or ('credential_configuration_invalid' if isinstance(error,ProviderError) else 'invalid_response'),
                'seconds':round(time.monotonic()-started, 3)}


def namespace_probe():
    identity = os.readlink('/proc/self/ns/net')
    names = sorted(name for _, name in socket.if_nameindex())
    blocked = False
    try:
        with socket.create_connection(('198.51.100.1', 9), timeout=.3):
            pass
    except OSError as error:
        # ENETUNREACH is stronger evidence than an arbitrary closed port/timeout.
        blocked = error.errno == 101
    return {'identity':identity, 'interfaces':names, 'external_network_unreachable':blocked}


def credential_rejection_checks(client,url,model,*,managed=False,upstream_calls=None):
    # Valid input prevents a malformed-request 400 from masquerading as an auth check.
    body={'model':model,'messages':[{'role':'user','content':'Return exactly {"ok":true}.'}],
          'max_tokens':64,'stream':False}
    missing=client.post(url+'/chat/completions',json=body)
    wrong=client.post(url+'/chat/completions',json=body,
                      headers={'Authorization':'Bearer sk-'+secrets.token_hex(32)})
    try:kind=wrong.json().get('error',{}).get('type')
    except (ValueError,AttributeError):kind=None
    # Pinned LiteLLM without its optional key database refuses non-master keys
    # as no_db_connection/400. Accept that ONLY with counted zero upstream calls;
    # the separate correct-key connection AND complete workflow must also pass.
    no_db=managed and wrong.status_code==400 and kind=='no_db_connection' and upstream_calls is not None and upstream_calls()==0
    return {'missing_status':missing.status_code,'wrong_status':wrong.status_code,
        'wrong_error_type':kind if kind in {'auth_error','no_db_connection'} else 'unclassified',
        'blocked':missing.status_code in {401,403} and (wrong.status_code in {401,403} or no_db),
        'upstream_calls_for_rejections':upstream_calls() if upstream_calls else None}


def environment(root, settings, credential=None):
    keep = ('PATH','LANG','LC_ALL','LD_LIBRARY_PATH','SYSTEMROOT')
    env = {k:os.environ[k] for k in keep if k in os.environ}
    home = root / 'home'; home.mkdir()
    env.update(HOME=str(home), XDG_CACHE_HOME=str(home/'cache'), PYTHONPATH=str(REPO/'src'),
        GEOAGENT_PROJECT_ROOT=str(root), ENABLE_WRITE_TOOLS='false', MODEL_NAME=settings.model,
        MODEL_BASE_URL=settings.base_url, MODEL_TIMEOUT_SECONDS=str(settings.timeout_seconds),
        MODEL_MAX_TOKENS=str(settings.max_tokens), MODEL_REASONING_EFFORT=settings.reasoning_effort or '',
        MODEL_RESPONSE_FORMAT=settings.response_format, MODEL_DATA_ALLOWED='raw',
        POSTGRES_HOST='127.0.0.1', POSTGRES_PORT='1', GEOSERVER_BASE_URL='http://127.0.0.1:1')
    if credential is not None: env['QUALIFICATION_KEY'] = credential
    return env


def workflow(root, settings, *, credential=None, model_socket=None, isolated=False,
             fixture_plan=None, wall_seconds=240, critic_timeout=15):
    loaded = load_task(REPO, TASK)
    inputs = _stage(REPO, loaded, root)
    if critic_timeout != 15:
        from geoagent_harness.platform.model_gateway.catalog import select_review_timeout, ReviewTimeoutSelection
        select_review_timeout(root,ReviewTimeoutSelection(seconds=critic_timeout,expected_revision=0))
    profile = ProviderProfile(id='qualification', kind='gateway' if credential else 'local',
        base_url=settings.base_url, model=settings.model, data_allowed='raw',
        credential_ref='env:QUALIFICATION_KEY' if credential else None,
        capabilities=settings.response_format,
        limits={'timeout_s':float(settings.timeout_seconds), 'max_tokens':settings.max_tokens})
    state = save(root, ProviderUpdate(profile=profile, expected_revision=0))
    select(root, ProviderSelection(profile_id=profile.id, expected_revision=state.revision))
    bound = capture(root, {'MODEL_REASONING_EFFORT':settings.reasoning_effort or ''}).settings()
    job = {'request':REQUEST, 'settings':asdict(bound), 'inputs':inputs, 'model_calls':3,
        'wall_clock_s':wall_seconds, 'allow_writes':False, 'allowed_skill_ids':['inspect_csv'],
        'qualification':True,
        'fixture_plan':fixture_plan, 'model_socket':model_socket}
    (root/'job.json').write_text(json.dumps(job))
    env = environment(root, bound, credential)
    command = [sys.executable, str(Path(__file__).resolve()),
               '--isolated-worker-root' if isolated else '--worker-root', str(root)]
    if isolated:
        command = ['unshare','--user','--map-current-user','--net', *command]
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=root, env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        process.wait(timeout=wall_seconds+5)
    except subprocess.TimeoutExpired:
        _stop(process)
    except BaseException:
        _stop(process)
        raise
    def read(name, default):
        try: return json.loads((root/name).read_text())
        except (OSError, ValueError): return default
    observed = read('observation.json', {})
    calls = read('calls.json', {}).get('calls', [])
    checks = score(loaded.task.expected, observed.get('run', {}), root)
    executed = observed.get('executed_operations', 0)
    no_outputs = not any((root/'data/output').rglob('*'))
    success = (observed.get('observed_outcome') == 'completed' and executed == 1
               and no_outputs and observed.get('approvals_required',0) == 0
               and bool(checks) and all(c.status == 'passed' for c in checks))
    critic = observed.get('critic_status', 'not_completed')
    planner_called = any(c['role']=='planner' for c in calls)
    result = {'status':'passed' if success and critic=='complete' and planner_called and fixture_plan is None else 'not_qualified',
        'planning':observed.get('planning_status','not_validated'), 'execution':'passed' if success else 'failed',
        'critic':critic, 'reason_code':observed.get('reason_code','worker_stopped'),
        'critic_reason_code':observed.get('critic_reason_code'),
        'model_planner_called':planner_called and fixture_plan is None, 'executed_operations':executed,
        'data_outputs':observed.get('output_files',0), 'checks':[c.model_dump() for c in checks],
        'calls':calls, 'seconds':round(time.monotonic()-started,3), 'exit_code':process.returncode}
    if isolated:
        probe=read('namespace.json', {})
        result['network']={'namespace_changed':probe.get('identity') != os.readlink('/proc/self/ns/net') if probe else False,
            'interfaces':probe.get('interfaces',[]), 'external_network_unreachable':probe.get('external_network_unreachable',False),
            'allowed_model_calls':len(calls)}
        if not (result['network']['namespace_changed'] and probe.get('interfaces')==['lo']
                and probe.get('external_network_unreachable') and success):
            result['status']='not_qualified'
    return result


def run(args):
    upstream = endpoint(args.base_url)
    settings = ModelSettings(base_url=upstream, model=args.model, timeout_seconds=args.timeout,
        max_tokens=1536, reasoning_effort=args.reasoning)
    ProviderProfile(id='qualification',base_url=upstream,model=args.model)
    gateway_key = os.environ.get(args.gateway_credential_env) if args.gateway_credential_env else None
    if args.gateway_url:
        endpoint(args.gateway_url)
        if not gateway_key: raise ValueError('An existing gateway requires a credential environment reference')
    output = Path(args.output)
    if output.exists() or output.is_symlink(): raise ValueError('Choose a new result path; results are never overwritten')
    report = {'schema_version':'1.0','task':'P1-M3c','evidence_kind':'real_model',
        'created_at':datetime.now(timezone.utc).isoformat(), 'model':args.model,
        'task_sha256':load_task(REPO,TASK).task_sha256,
        'runner_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'worker_sha256':sha256((REPO/'src/geoagent_harness/apps/benchmark/worker.py').read_bytes()).hexdigest(),
        'service_controller_sha256':sha256((REPO/'scripts/qualification_services.py').read_bytes()).hexdigest(),
        'windows_controller_sha256':sha256((REPO/'scripts/qualification_ollama.ps1').read_bytes()).hexdigest(),
        'source_sha256':source_sha256(REPO), 'source_unchanged':None,
        'versions':{'python':sys.version.split()[0],'httpx':version('httpx')},
        'same_backend_relays':True, 'results':{}, 'complete':False,
        'limits':{'model_calls_per_workflow':3,'workflow_wall_seconds':240,'request_timeout_seconds':args.timeout,
                  'max_output_tokens':1536,'critic_timeout_seconds':args.critic_timeout,
                  'product_critic_default_unchanged':True,'writes':False}}
    # Optional identification only: a gateway need not implement Ollama's API.
    try:
        with httpx.Client(timeout=3,trust_env=False,follow_redirects=False) as client:
            metadata=client.get(upstream.removesuffix('/v1')+'/api/version').json()
        value=metadata.get('version')
        if isinstance(value,str) and len(value)<=40 and all(c.isalnum() or c in '.-+' for c in value):
            report['versions']['ollama']=value
    except (httpx.HTTPError,ValueError,AttributeError): pass
    # Exclusive output contains no endpoints, credentials, prompts or raw replies.
    with output.open('x', encoding='utf-8') as stream:
        os.chmod(output, 0o600)
        def persist():
            stream.seek(0); json.dump(report,stream,indent=2); stream.truncate(); stream.flush(); os.fsync(stream.fileno())
        persist()
        for mode in args.modes:
            print(f'{mode}: starting', flush=True)
            with tempfile.TemporaryDirectory(prefix='ac-qual-') as temporary, ExitStack() as stack:
                private = Path(temporary); root=private/'workspace'; key=None; broker=None; model_socket=None; managed=None; secondary=None
                chosen=settings
                if mode=='gateway' and args.litellm_python:
                    from qualification_services import LiteLLMGateway
                    broker=stack.enter_context(Relay(upstream,timeout=args.timeout))
                    try:managed=stack.enter_context(LiteLLMGateway(args.litellm_python,broker.base_url,args.model,private/'gateway'))
                    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
                        report['results'][mode]={'status':'unavailable','reason_code':'managed_gateway_startup_failed'}
                        persist(); print('gateway: unavailable (managed startup failed)',flush=True); continue
                    key=managed.key
                    chosen=replace(settings,base_url=managed.base_url,model='qualification-model',
                        credential_ref='env:QUALIFICATION_KEY',provider_profile_id='qualification-gateway')
                elif mode=='gateway' and not args.gateway_url:
                    report['results'][mode]={'status':'unavailable','reason_code':'real_gateway_not_configured'}
                    persist(); print('gateway: unavailable (no existing gateway supplied)',flush=True); continue
                elif mode=='gateway':
                    key=gateway_key
                    chosen=replace(settings,base_url=args.gateway_url,model=args.gateway_model or args.model,
                        credential_ref='env:'+args.gateway_credential_env,provider_profile_id='qualification-gateway')
                elif mode=='secondary':
                    if args.ollama_executable:
                        from qualification_services import WindowsOllama
                        try:secondary=stack.enter_context(WindowsOllama(args.ollama_executable,args.ollama_models,private/'secondary'))
                        except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
                            report['results'][mode]={'status':'unavailable','reason_code':'secondary_runtime_startup_failed'}
                            persist(); print('secondary: unavailable (managed startup failed)',flush=True); continue
                    if not secondary and not args.secondary_url:
                        report['results'][mode]={'status':'unavailable','reason_code':'secondary_runtime_not_configured'}
                        persist(); print('secondary: unavailable',flush=True); continue
                    chosen=replace(settings,base_url=secondary.base_url if secondary else args.secondary_url,
                        model=args.secondary_model or args.model,provider_profile_id='qualification-secondary')
                elif mode in {'compatible-relay','authenticated-relay','isolated'}:
                    key='sk-'+secrets.token_hex(24) if mode=='authenticated-relay' else None
                    if mode=='isolated': model_socket=str(private/'model.sock')
                    broker=stack.enter_context(Relay(upstream,key=key,unix_socket=model_socket,timeout=args.timeout))
                    chosen=replace(settings,base_url=broker.base_url,
                        credential_ref='env:QUALIFICATION_KEY' if key else None,
                        provider_profile_id='qualification-relay')
                extra={}
                before=broker.forwarded if broker else None
                blocked=smoke(replace(chosen,data_allowed='none'))
                extra['egress']={'blocked_before_dispatch':blocked.get('code')=='model_data_class_blocked',
                    'upstream_calls':broker.forwarded-before if broker else None}
                if key:
                    before=broker.forwarded if broker else None
                    missing_reference=smoke(replace(chosen,credential_ref='secret:absent-qualification-key',credential_root=str(private)))
                    extra['missing_credential_reference']={'blocked':missing_reference['code']=='credential_configuration_invalid',
                        'upstream_calls':broker.forwarded-before if broker else None}
                    # Direct socket checks deliberately don't use the missing-key profile (which blocks pre-send).
                    before=broker.forwarded if broker else None
                    with httpx.Client(timeout=10,trust_env=False,follow_redirects=False) as client:
                        extra['authentication']=credential_rejection_checks(client,chosen.base_url,chosen.model,
                            managed=managed is not None,upstream_calls=(lambda:broker.forwarded-before) if broker else None)
                if mode=='isolated':
                    extra['connectivity']={'status':'tested_by_isolated_workflow'}
                else:
                    previous=os.environ.get('QUALIFICATION_KEY')
                    try:
                        if key: os.environ['QUALIFICATION_KEY']=key
                        extra['connectivity']=smoke(chosen)
                    finally:
                        if previous is None: os.environ.pop('QUALIFICATION_KEY',None)
                        else: os.environ['QUALIFICATION_KEY']=previous
                if mode=='isolated' and not shutil.which('unshare'):
                    result={'status':'unavailable','reason_code':'unshare_not_installed'}
                else:
                    result=workflow(root,chosen,credential=key,model_socket=model_socket,isolated=mode=='isolated',critic_timeout=args.critic_timeout)
                result.update(extra)
                result['model']=chosen.model
                if broker: result['broker']={'forwarded':broker.forwarded,'rejected':broker.rejected}
                if mode=='authenticated-relay': result['gateway_kind']='test_harness_not_LiteLLM'
                if managed:
                    managed.close()
                    result['gateway']={'software':'litellm','version':'1.109.1',
                        'managed_process_stopped':managed.stopped,'retries':0,'fallbacks':False,
                        'dependency_lock_sha256':sha256((REPO/'requirements/model-qualification.txt').read_bytes()).hexdigest()}
                    if not managed.stopped:result['status']='not_qualified'
                if secondary:
                    secondary.close()
                    result['runtime']={**secondary.provenance,'managed_process_stopped':secondary.stopped}
                    if not secondary.stopped or not secondary.provenance.get('cache_inventory_unchanged'):result['status']='not_qualified'
                elif mode=='secondary':result['runtime_independence']='operator_supplied_endpoint; verify process provenance separately'
                if extra.get('authentication',{}).get('blocked') is False: result['status']='not_qualified'
                if not extra['egress']['blocked_before_dispatch']: result['status']='not_qualified'
                if extra.get('connectivity',{}).get('status')=='failed': result['status']='not_qualified'
                # Scan transient state before deleting it; never export raw offending material.
                if key and any(key.encode() in p.read_bytes() for p in private.rglob('*') if p.is_file()):
                    result={'status':'not_qualified','reason_code':'credential_leak_detected'}
                report['results'][mode]=result
                persist(); print(f"{mode}: {result['status']}",flush=True)
        managed_gateway=report['results'].get('gateway',{}).get('gateway',{}).get('software')=='litellm'
        independent=report['results'].get('secondary',{}).get('runtime',{}).get('separately_started_process') is True
        report['complete']=(set(args.modes)==set(MODES) and managed_gateway and independent
                            and all(v['status']=='passed' for v in report['results'].values()))
        report['source_unchanged']=report['source_sha256']==source_sha256(REPO)
        persist()
    return report


def main():
    if len(sys.argv)==3 and sys.argv[1] in {'--worker-root','--isolated-worker-root'}:
        root=Path(sys.argv[2])
        if sys.argv[1]=='--isolated-worker-root':
            (root/'namespace.json').write_text(json.dumps(namespace_probe()))
        from geoagent_harness.apps.benchmark.worker import work
        work(root); return
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True)
    parser.add_argument('--base-url',default='http://127.0.0.1:11434/v1',type=endpoint)
    parser.add_argument('--output',required=True)
    parser.add_argument('--modes',nargs='+',choices=MODES,default=list(MODES))
    parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--reasoning',choices=('none','low','medium','high'),default='none')
    parser.add_argument('--critic-timeout',type=int,default=15,
                        help='Explicit temporary-workspace review budget (5–180 seconds); product default stays 15')
    parser.add_argument('--gateway-url',type=endpoint)
    parser.add_argument('--gateway-model')
    parser.add_argument('--gateway-credential-env')
    parser.add_argument('--litellm-python',type=Path,help='Use the optional pinned environment to start/stop a real local gateway')
    parser.add_argument('--secondary-url',type=endpoint,help='Separately operated model server; never a relay')
    parser.add_argument('--secondary-model',help='Installed model on the second server; recorded separately')
    parser.add_argument('--ollama-executable',type=Path,help='WSL: start an owned second Windows Ollama process')
    parser.add_argument('--ollama-models',type=Path,help='WSL: existing Windows model cache; no downloads')
    args=parser.parse_args()
    if not 0<args.timeout<=120: parser.error('timeout must be >0 and <=120 seconds')
    if not 5<=args.critic_timeout<=180: parser.error('critic-timeout must be 5–180 seconds')
    if len(set(args.modes))!=len(args.modes): parser.error('modes must be unique; no implicit repeat attempts')
    if args.litellm_python and (args.gateway_url or args.gateway_credential_env):
        parser.error('Choose managed LiteLLM or an external gateway configuration')
    if bool(args.ollama_executable)!=bool(args.ollama_models) or (args.ollama_executable and args.secondary_url):
        parser.error('Provide both Windows Ollama/cache paths or an external secondary URL')
    result=run(args)
    print('Result: '+str(Path(args.output).resolve()))
    raise SystemExit(0 if result['complete'] else 2)


if __name__=='__main__': main()
