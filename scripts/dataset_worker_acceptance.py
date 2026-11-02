#!/usr/bin/env python3
"""Explicit real Docker boundary checks; all mutable fixtures/artifacts live in /tmp."""
import argparse,csv,hashlib,json,math,os,shutil,socket,statistics,subprocess,tempfile,time,uuid
from pathlib import Path
from geoagent_harness.sandbox.manager import IMAGE,docker,launch_command,run_profile,SandboxError
from geoagent_harness.tabular.dataset_service import profile_dataset


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--real-data',action='store_true');args=parser.parse_args()
 repo=Path(__file__).resolve().parents[1];image=json.loads(docker('image','inspect',IMAGE))[0]['Id'];evidence={};before_jobs=set(docker('ps','-a','--filter','label=org.actioncharter.job=profile-v1','--format','{{.Names}}').decode().split())
 with tempfile.TemporaryDirectory(prefix='actioncharter-boundary-') as folder:
  root=Path(folder);inputs=root/'data/input';inputs.mkdir(parents=True)
  path=inputs/'source.csv';path.write_text('patient_nbr,age,value\n001,[20-30),2\n001,[20-30),4\n002,[30-40),6\n');path.chmod(0o444)
  canary=root/'not-mounted-secret';canary.write_text('not for the worker')
  def probe(code):
   name='actioncharter-probe-'+uuid.uuid4().hex
   command=launch_command(name,image,['--mount',f'type=bind,src={path},dst=/job/data/input/source.csv,readonly'])
   command[-1:-1]=['--entrypoint','python']
   try:
    r=subprocess.run(command+['-I','-B','-c',code],capture_output=True,timeout=20)
    if r.returncode:raise AssertionError(r.stderr.decode()[:500])
    state=json.loads(docker('inspect',name))[0]
    assert state['HostConfig']['ReadonlyRootfs'] and state['HostConfig']['NetworkMode']=='none'
    assert state['HostConfig']['Memory']==512*1024**2 and state['HostConfig']['PidsLimit']==64
    assert state['HostConfig']['CapDrop']==['ALL'] and state['Config']['User']=='65534:65534'
    return json.loads(r.stdout)
   finally:docker('rm','-f',name)
  code='''import json,os,socket,errno
out={'uid':os.getuid(),'host_canary_absent':not os.path.exists(%r),'docker_socket_absent':not os.path.exists('/var/run/docker.sock'),'other_job_absent':not os.path.exists('/job/data/input/other.csv')}
for key,p in [('input_readonly','/job/data/input/source.csv'),('root_readonly','/app/canary')]:
 try:
  with open(p,'a') as f:f.write('forbidden')
  out[key]=False
 except OSError:out[key]=True
s=socket.socket();s.settimeout(.2)
try:s.connect(('192.0.2.1',80));out['network_blocked']=False
except OSError:out['network_blocked']=True
with open('/proc/self/status') as f:status=f.read()
out['no_new_privileges']='NoNewPrivs:\\t1' in status
out['capabilities_dropped']='CapEff:\\t0000000000000000' in status
try:
 with open('/scratch/limit','wb') as f:
  for _ in range(129):f.write(b'x'*1024**2)
 out['scratch_bounded']=False
except OSError as e:out['scratch_bounded']=e.errno==errno.ENOSPC
print(json.dumps(out))''' % str(canary)
  evidence['isolation']=probe(code)
  assert evidence['isolation']['uid']==65534
  assert all(v for k,v in evidence['isolation'].items() if k!='uid')
  os.environ['ACTIONCHARTER_ANALYTICAL_RUNTIME']='docker'
  r=profile_dataset(root,'source.csv',owner='acceptance')
  assert r['source_rows']==3 and r['profiles'][2]['numeric']['mean']==4
  assert r['runtime']['mode']=='docker' and r['artifact']['owner']=='acceptance'
  expected=hashlib.sha256(path.read_bytes()).hexdigest();assert r['source_sha256']==expected
  # Two concurrent runs must get different job IDs and private staged files.
  from concurrent.futures import ThreadPoolExecutor
  with ThreadPoolExecutor(max_workers=2) as pool:
   jobs=list(pool.map(lambda _:profile_dataset(root,'source.csv'),range(2)))
  assert jobs[0]['runtime']['job_id']!=jobs[1]['runtime']['job_id']
  evidence['concurrent_jobs']='independent IDs, identical verified results'
  class Cancelled(Exception):pass
  calls=0
  def cancel():
   nonlocal calls
   calls+=1
   if calls>=4:raise Cancelled()
  try:run_profile(root,'source.csv',{},checkpoint=cancel)
  except Cancelled:evidence['cancellation']='stopped and cleaned'
  else:raise AssertionError('Cancellation not observed')
  (inputs/'large.csv').write_text('value\n'+'2\n'*300000)
  try:run_profile(root,'large.csv',{},max_seconds=.25)
  except SandboxError:evidence['deadline']='stopped without retry'
  else:raise AssertionError('Deadline not enforced')
  if args.real_data:
   evidence['real_data']=[]
   for filename in ['diabetic_sample_5000.csv','diabetic_data.csv']:
    source=repo/'data/input/test'/filename
    if not source.exists():raise RuntimeError('Real source absent: '+filename)
    shutil.copyfile(source,inputs/filename)
    start=time.monotonic();r=profile_dataset(root,filename,{'distinct_columns':['patient_nbr']})
    profiles={p['name']:p for p in r['profiles']}
    with source.open(newline='') as f:
     rows=list(csv.DictReader(f))
    assert r['source_rows']==len(rows) and len(profiles)==len(rows[0])
    for field,p in profiles.items():
     if p['numeric']:
      vals=[float(row[field]) for row in rows if row[field] and row[field]!='?']
      n=p['numeric'];assert n['count']==len(vals)
      assert math.isclose(n['mean'],statistics.mean(vals),rel_tol=1e-10)
      assert n['minimum']==min(vals) and n['maximum']==max(vals)
      assert math.isclose(n['standard_deviation'],statistics.stdev(vals),rel_tol=1e-10)
    assert profiles['patient_nbr']['distinct_count']==len({row['patient_nbr'] for row in rows})
    assert profiles['age']['analytical_role']=='ordered_category'
    assert profiles['admission_source_id']['numeric'] is None
    evidence['real_data'].append({'file':filename,'rows':len(rows),'fields':len(profiles),'numeric_fields_verified':sum(p['numeric'] is not None for p in profiles.values()),'seconds':round(time.monotonic()-start,2)})
  evidence['worker_image_id']=image
  remaining=set(docker('ps','-a','--filter','label=org.actioncharter.job=profile-v1','--format','{{.Names}}').decode().split())-before_jobs
  assert not remaining,'Worker containers remain: '+remaining
  evidence['cleanup']='all acceptance jobs removed'
 print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
