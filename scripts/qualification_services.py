"""Opt-in development services. No owner config, credentials or databases."""
from __future__ import annotations

import json
from hashlib import sha256
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import time

import httpx

LITELLM_VERSION='1.109.1'


def clean_environment(directory):
    directory=Path(directory)
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    env={k:os.environ[k] for k in ('PATH','LANG','LC_ALL','LD_LIBRARY_PATH','SYSTEMROOT') if k in os.environ}
    env.update(HOME=str(directory),XDG_CACHE_HOME=str(directory/'cache'),
        PYTHON_DOTENV_DISABLED='1',LITELLM_LOCAL_MODEL_COST_MAP='True',
        LITELLM_TELEMETRY_DISABLED='true',LITELLM_TELEMETRY='False',
        DO_NOT_TRACK='1',OTEL_SDK_DISABLED='true',LITELLM_LOG='ERROR',
        LITELLM_SUPPRESS_STARTUP_OUTPUT='true',DISABLE_ADMIN_UI='true')
    return env


def free_port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0))
        return listener.getsockname()[1]


def gateway_configuration(upstream, model):
    from urllib.parse import urlsplit
    u=urlsplit(upstream)
    if u.scheme not in {'http','https'} or u.hostname not in {'127.0.0.1','::1'} or u.path!='/v1' or u.query or u.fragment or u.username or u.password:
        raise ValueError('Managed gateway requires a fixed literal-loopback upstream')
    return {'model_list':[{'model_name':'qualification-model','litellm_params':{
        'model':'openai/'+model,'api_base':upstream,'api_key':'synthetic-upstream',
        'max_retries':0,'timeout':125}}],
        'general_settings':{'master_key':'os.environ/QUALIFICATION_GATEWAY_KEY'},
        'litellm_settings':{'num_retries':0,'cache':False,'turn_off_message_logging':True,
            'suppress_startup_output':True,'success_callback':[],'failure_callback':[],
            'callbacks':[],'service_callback':[]},
        'router_settings':{'num_retries':0,'fallbacks':[]}}


class LiteLLMGateway:
    """A real optional LiteLLM process with bounded lifetime and private logs."""
    def __init__(self,python,upstream,model,directory,*,startup_seconds=60):
        self.python=Path(python).absolute();self.directory=Path(directory).absolute()
        self.config=gateway_configuration(upstream,model)
        self.startup_seconds=startup_seconds
        self.key='sk-'+secrets.token_hex(32)
        self.process=None;self.log=None;self.stopped=False
        self.port=free_port();self.base_url=f'http://127.0.0.1:{self.port}/v1'

    def __enter__(self):
        self.directory.mkdir(mode=0o700,parents=True,exist_ok=True)
        env=clean_environment(self.directory/'home')
        try:
            result=subprocess.run([str(self.python),'-c','from importlib.metadata import version; print(version("litellm"))'],
                env=env,cwd=self.directory,capture_output=True,text=True,timeout=10,check=True)
            if result.stdout.strip()!=LITELLM_VERSION:
                raise ValueError('Managed qualification gateway version does not match its lock')
            executable=self.python.parent/'litellm'
            if not executable.is_file() or not shutil.which('timeout'):
                raise ValueError('Install the optional gateway environment and coreutils timeout')
            config=self.directory/'gateway.json';config.write_text(json.dumps(self.config))
            os.chmod(config,0o600)
            env['QUALIFICATION_GATEWAY_KEY']=self.key
            self.log=(self.directory/'gateway.log').open('xb')
            # The external watchdog also bounds the service if the parent dies.
            self.process=subprocess.Popen(['timeout','--signal=TERM','--kill-after=3s','420s',
                str(executable),'--config',str(config),'--host','127.0.0.1',
                '--port',str(self.port),'--num_workers','1','--telemetry','False'],
                env=env,cwd=self.directory,stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.monotonic()+self.startup_seconds
            with httpx.Client(timeout=.5,trust_env=False,follow_redirects=False) as client:
                while time.monotonic()<deadline and self.process.poll() is None:
                    try:
                        if client.get(self.base_url.removesuffix('/v1')+'/health/liveliness').status_code==200:
                            return self
                    except httpx.HTTPError: pass
                    time.sleep(.1)
            raise RuntimeError('Managed LiteLLM gateway did not become ready; private startup log retained until cleanup')
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.process is not None and self.process.poll() is None:
            os.killpg(self.process.pid,signal.SIGTERM)
            try:self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid,signal.SIGKILL);self.process.wait()
        self.stopped=self.process is None or self.process.poll() is not None
        if self.log is not None and not self.log.closed:self.log.close()

    def __exit__(self,*args):
        self.close()


class WindowsOllama:
    """WSL-only, owned second Windows process; existing cached weights, no pull API."""
    def __init__(self,executable,models,directory,*,startup_seconds=30):
        self.executable=Path(executable).absolute();self.models=Path(models).absolute();self.directory=Path(directory).absolute()
        self.port=free_port();self.base_url=f'http://127.0.0.1:{self.port}/v1'
        self.startup_seconds=startup_seconds;self.process=None;self.log=None;self.stopped=False
        self.provenance={}

    def __enter__(self):
        self.directory.mkdir(mode=0o700,parents=True,exist_ok=True)
        if not self.executable.is_file() or not self.models.is_dir():raise ValueError('Installed Windows Ollama and cache are required')
        self.cache_before=self.cache_inventory()
        self.shell=Path('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
        def win(path):
            return subprocess.check_output(['wslpath','-w',str(Path(path).absolute())],text=True,timeout=3).strip()
        self.control=[str(self.shell),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
            '-File',win(Path(__file__).with_name('qualification_ollama.ps1')),'-PrivateHome',win(self.directory)]
        try:
            self.log=(self.directory/'server.log').open('xb')
            self.process=subprocess.Popen([*self.control,'-Action','Start','-Executable',win(self.executable),
                '-Models',win(self.models),'-Port','0'],env=clean_environment(self.directory/'linux-home'),
                stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.monotonic()+self.startup_seconds
            with httpx.Client(timeout=.5,trust_env=False,follow_redirects=False) as client:
                while time.monotonic()<deadline and self.process.poll() is None:
                    try:
                        owned=json.loads((self.directory/'owned-process.json').read_text(encoding='utf-8-sig'))
                        self.port=int(owned['port']);self.base_url=f'http://127.0.0.1:{self.port}/v1'
                        response=client.get(self.base_url.removesuffix('/v1')+'/api/version')
                        if response.status_code==200:
                            self.provenance={'software':'ollama','version':response.json()['version'],
                                'binary_sha256':owned['binary_sha256'],'separately_started_process':True,
                                'same_model_cache':True,'new_model_downloads':False}
                            return self
                    except (httpx.HTTPError,OSError,ValueError,KeyError):pass
                    time.sleep(.1)
            raise RuntimeError('Second Windows Ollama process did not become ready')
        except BaseException:
            self.close();raise

    def close(self):
        if hasattr(self,'control') and (self.directory/'owned-process.json').is_file():
            subprocess.run([*self.control,'-Action','Stop'],env=clean_environment(self.directory/'linux-home'),
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,check=True)
        if self.process is not None:
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid,signal.SIGTERM);self.process.wait(timeout=5)
        self.stopped=self.process is None or self.process.poll() is not None
        if hasattr(self,'cache_before'):
            self.provenance['cache_inventory_unchanged']=self.cache_before==self.cache_inventory()
        if self.log is not None and not self.log.closed:self.log.close()

    def __exit__(self,*args):self.close()

    def cache_inventory(self):
        # Do not reread gigabytes of weights: bind blob size/mtime plus exact small manifests.
        records=[]
        for path in sorted(self.models.rglob('*')):
            if path.is_file():
                info=path.stat();relative=path.relative_to(self.models)
                digest=sha256(path.read_bytes()).hexdigest() if relative.parts[0]=='manifests' else None
                records.append([relative.as_posix(),info.st_size,info.st_mtime_ns,digest])
        return sha256(json.dumps(records,separators=(',',':')).encode()).hexdigest()
