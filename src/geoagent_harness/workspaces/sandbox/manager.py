"""Trusted fixed Docker launcher, selected-file staging and immutable report artifacts."""
import hashlib,json,os,selectors,subprocess,tempfile,time,uuid
from pathlib import Path
from geoagent_harness.data.discovery.csv import source, identity
from geoagent_harness.contracts.paths import relative_path

IMAGE='actioncharter-analytical-worker:local'
class SandboxError(ValueError):pass


def docker(*args,timeout=10):
    try:
        r=subprocess.run(['docker',*args],capture_output=True,timeout=timeout,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:raise SandboxError('Docker unavailable. Start Docker and build the analytical worker; no host fallback was used.') from e
    if r.returncode:raise SandboxError('Docker command failed. Check daemon access and build scripts/build_analytical_worker.sh; no host fallback was used.')
    return r.stdout


def snapshot(root,path,destination,check=None):
    digest=hashlib.sha256()
    with source(root,path) as (fd,normalized,before),destination.open('xb') as output:
        while chunk:=os.read(fd,65536):
            if check:check()
            output.write(chunk);digest.update(chunk)
        if identity(os.fstat(fd))!=before:raise SandboxError('Input changed while staging')
        with source(root,path) as (_,_,after):
            if before!=after:raise SandboxError('Input path changed while staging')
    destination.chmod(0o444)
    return normalized,digest.hexdigest()


def launch_command(name,image_id,mounts):
    """Fixed trusted worker boundary; never receives agent-supplied Docker flags."""
    return ['docker','run','--name',name,'--label','org.actioncharter.job=profile-v1','--read-only','--network','none',
            '--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges:true','--pids-limit','64',
            '--memory','512m','--memory-swap','512m','--cpus','1','--ulimit','nofile=64:64',
            '--tmpfs','/scratch:rw,noexec,nosuid,nodev,size=128m,mode=1777','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=32m,mode=1777',
            *mounts,'-i',image_id]


def run_profile(root,path,options,*,delimiter=',',checkpoint=None,max_seconds=120):
    started=time.monotonic()
    def check():
        if checkpoint:checkpoint()
        if time.monotonic()-started>max_seconds:raise SandboxError('Sandbox deadline exceeded; nothing retried')
    check()
    image=docker('image','inspect',IMAGE)
    metadata=json.loads(image)[0]
    if metadata.get('Config',{}).get('Labels',{}).get('org.actioncharter.worker.protocol')!='dataset-profile-v1':raise SandboxError('Worker protocol mismatch; rebuild the analytical worker')
    image_id=metadata['Id'];name='actioncharter-profile-'+uuid.uuid4().hex
    job_options=dict(options)
    with tempfile.TemporaryDirectory(prefix='actioncharter-job-') as directory:
        workspace=Path(directory)
        original,source_sha=snapshot(root,path,workspace/'source.csv',check)
        bindings=[{'path':original,'sha256':source_sha}]
        mounts=['--mount',f'type=bind,src={workspace}/source.csv,dst=/job/data/input/source.csv,readonly']
        if options.get('codebook_path'):
            book,book_sha=snapshot(root,options['codebook_path'],workspace/'codebook.csv',check)
            bindings.append({'path':book,'sha256':book_sha});job_options['codebook_path']='data/input/codebook.csv'
            mounts+=['--mount',f'type=bind,src={workspace}/codebook.csv,dst=/job/data/input/codebook.csv,readonly']
        command=launch_command(name,image_id,mounts)
        payload=json.dumps({'options':job_options,'delimiter':delimiter}).encode()
        if len(payload)>16384:raise SandboxError('Profile options exceed job limit')
        stdout=bytearray();stderr=bytearray();process=None;state={};created=False
        try:
            # Create synchronously before attachment: cancellation cannot race container creation.
            command[1]='create'
            docker(*command[1:]);created=True
            check()
            process=subprocess.Popen(['docker','start','-a','-i',name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            process.stdin.write(payload);process.stdin.close()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout,selectors.EVENT_READ,'out');selector.register(process.stderr,selectors.EVENT_READ,'err')
                while selector.get_map():
                    if checkpoint:checkpoint()
                    if time.monotonic()-started>max_seconds:raise SandboxError('Sandbox deadline exceeded; job stopped, nothing retried')
                    for key,_ in selector.select(.1):
                        chunk=os.read(key.fileobj.fileno(),65536)
                        if not chunk:selector.unregister(key.fileobj);continue
                        target=stdout if key.data=='out' else stderr;target.extend(chunk)
                        if len(target)>(1024**2 if key.data=='out' else 16384):raise SandboxError('Sandbox output budget exceeded')
            process.wait(timeout=2)
            state=json.loads(docker('inspect','--format','{{json .State}}',name))
            if process.returncode:raise SandboxError('Calculation worker failed or exceeded resources; no partial result published')
            result=json.loads(stdout)
            if result.get('source_sha256')!=source_sha or result.get('schema_version')!='dataset-profile-v1':raise SandboxError('Worker source/result binding mismatch')
            if len(result.get('profiles',[]))!=len(result.get('columns',[])):raise SandboxError('Worker profile coverage mismatch')
            if len(bindings)>1 and (result.get('codebook') or {}).get('sha256')!=bindings[1]['sha256']:raise SandboxError('Worker codebook binding mismatch')
            result['source']=original;result['query']=options
            if result.get('field_guidance'):result['field_guidance']['source']=original
            if result.get('codebook'):result['codebook']['path']=bindings[1]['path']
            result['runtime']={'mode':'docker','job_id':name,'image_id':image_id,'protocol':'dataset-profile-v1',
                'network':'none','root_read_only':True,'user':'65534:65534','memory_bytes':512*1024**2,
                'scratch_bytes':128*1024**2,'pids_limit':64,'exit_code':state.get('ExitCode'),'oom_killed':state.get('OOMKilled'),
                'elapsed_seconds':round(time.monotonic()-started,3),'input_bindings':bindings}
            return result
        finally:
            # Container identity is generated here, never supplied by an agent.
            cleanup_error=None
            try:
                if created:docker('rm','-f',name)
            except SandboxError as error:cleanup_error=error
            if process:
                if process.poll() is None:process.kill()
                process.wait(timeout=5)
                for pipe in (process.stdin,process.stdout,process.stderr):
                    if pipe and not pipe.closed:pipe.close()
            if cleanup_error:raise SandboxError('Worker cleanup could not be verified. Inspect containers labelled org.actioncharter.job=profile-v1 before retrying.') from cleanup_error


def record_artifact(root,result,owner=None):
    root=Path(root).resolve(strict=True)
    from geoagent_harness.platform.workspace import runtime_store_path
    directory=runtime_store_path(root, 'workflow-state', 'analytical-artifacts')
    if directory.parent.is_symlink() or directory.is_symlink():raise SandboxError('Unsafe analytical artifact storage')
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    payload=json.dumps({'owner':owner,'result':result},sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if len(payload)>1024**2:raise SandboxError('Dataset profile exceeds artifact limit')
    digest=hashlib.sha256(payload).hexdigest();path=directory/(digest+'.json')
    if path.is_symlink():raise SandboxError('Unsafe artifact reference')
    if not path.exists():
        files=list(directory.glob('*.json'))
        if len(files)>=128 or sum(f.stat().st_size for f in files)+len(payload)>128*1024**2:raise SandboxError('Analytical artifact quota reached; retain/export or clean older artifacts explicitly')
        fd,temporary=tempfile.mkstemp(dir=directory,prefix='.artifact-')
        try:
            with os.fdopen(fd,'wb') as output:output.write(payload);output.flush();os.fsync(output.fileno())
            os.replace(temporary,path)
        finally:
            if os.path.exists(temporary):os.unlink(temporary)
    return {'sha256':digest,'kind':'dataset_profile','owner':owner,'scope':'project_and_owning_conversation','bytes':len(payload),'execution_authority':False}
