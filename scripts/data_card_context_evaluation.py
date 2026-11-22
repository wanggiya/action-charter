"""Two bounded synthetic Planner observations, no workflow dispatch or owner state.

Read-only Git export supplies pre-change Python. Both conditions receive identical
synthetic input/context, model and limits. One observation/condition cannot establish
an efficiency or reliability improvement. Existing model weights must be installed.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import urlparse

MESSAGE = 'Inspect facts.csv and prepare a read-only inspection workflow. Return row count and column names when executed. Do not execute yet.'
CHILD = r'''
import json,sys,time
from pathlib import Path
from geoagent_harness.platform.model_gateway import SharedModelClient,ModelSettings
from geoagent_harness.task_actions.conversation import TurnRequest
from geoagent_harness.task_actions.planner_submission import SubmissionRequest,submission_action
root=Path(sys.argv[1]);config=json.loads(sys.argv[2]);calls=[]
client=SharedModelClient(ModelSettings(base_url=config['base_url'],model=config['model'],timeout_seconds=config['timeout'],max_tokens=512,reasoning_effort='none'))
class Bounded:
 def complete(self,request):
  if calls:raise RuntimeError('comparison_call_limit')
  item={'prompt_bytes':sum(len(m.content.encode()) for m in request.messages),'input_tokens':None,'output_tokens':None}
  calls.append(item);started=time.monotonic()
  try:
   result=client.complete(request)
   item.update(input_tokens=result.prompt_tokens,output_tokens=result.completion_tokens)
   return result
  finally:item['seconds']=round(time.monotonic()-started,3)
started=time.monotonic();record={}
try:
 result=submission_action(SubmissionRequest(action='submit',submission_id='a'*32,conversation_id='b'*32,
   inspect_on_send=True,turn=TurnRequest(action='turn',conversation_id='b'*32,message=config['message'],use_history=False,allowed_skill_ids=['inspect_csv'])),project_root=root,model_client=Bounded(),background=False)
 chat=result['conversation'];steps=((chat.get('planner_result') or {}).get('plan') or {}).get('steps',[])
 correct=len(steps)==1 and steps[0]['skill']=='inspect_csv' and steps[0]['arguments'].get('path')=='data/input/facts.csv' and not steps[0]['requires_approval']
 record={'status':'proposal' if steps else 'clarification','correct_inspection_proposal':correct,
   'context_statuses':[item['status'] for item in (chat.get('context_usage') or {}).get('dataset_context',[])],
   'workflow_dispatch':bool(result.get('run')),'approval_performed':result['approval_performed']}
except Exception as error:
 record={'status':'failed','error_code':getattr(error,'code',None) or ('comparison_call_limit' if str(error)=='comparison_call_limit' else type(error).__name__),
         'correct_inspection_proposal':False,'workflow_dispatch':False,'approval_performed':False}
record.update(seconds=round(time.monotonic()-started,3),model_calls=calls)
if config['candidate'] and record['status']!='failed':
 from geoagent_harness.data.discovery.context import prepare
 tick=time.monotonic();warm=prepare(root,'facts.csv',owner='b'*32,allow_read=True,preliminary=True)
 record['subsequent_context_check']={'status':warm['status'],'reader_performed':warm['reader_performed'],'seconds':round(time.monotonic()-tick,3)}
print(json.dumps(record))
'''


def source_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*.py')):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', default='f237372')
    parser.add_argument('--model', default='qwen3:4b-instruct')
    parser.add_argument('--base-url', default='http://127.0.0.1:11434/v1')
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if urlparse(args.base_url).hostname not in {'127.0.0.1','localhost','::1'}:
        parser.error('This synthetic local comparison requires a loopback endpoint')
    if not 0 < args.timeout <= 90:
        parser.error('Choose a timeout in (0,90] seconds')
    repo = Path(__file__).resolve().parents[1]
    archive = subprocess.check_output(['git','archive',args.baseline_ref,'src'],cwd=repo)
    with tempfile.TemporaryDirectory(prefix='actioncharter-card-comparison-') as directory:
        base = Path(directory)
        before = base/'before-code';before.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            source.extractall(before,filter='data')
        after = base/'after-code'
        shutil.copytree(repo/'src',after/'src',ignore=shutil.ignore_patterns('__pycache__'))
        common = base/'common-guidance'
        for folder in ('context','agents'):
            shutil.copytree(repo/folder,common/folder)
        observations=[]
        for name, code in [('before',before),('after',after)]:
            root=base/(name+'-project');root.mkdir()
            for folder in ('context','agents'):
                shutil.copytree(common/folder,root/folder)
            (root/'data/input').mkdir(parents=True)
            (root/'data/input/facts.csv').write_text('id,group,value\n001,A,2\n002,B,4\n003,A,6\n')
            config={'base_url':args.base_url,'model':args.model,'timeout':args.timeout,'message':MESSAGE,'candidate':name=='after'}
            environment={'PATH':os.environ.get('PATH',''),'LANG':'C.UTF-8',
                'PYTHONPATH':str(code/'src'),'MODEL_NAME':args.model,'MODEL_BASE_URL':args.base_url,
                'ENABLE_WRITE_TOOLS':'false','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
            try:
                completed=subprocess.run([sys.executable,'-c',CHILD,str(root),json.dumps(config)],cwd=root,
                    env=environment,capture_output=True,text=True,timeout=args.timeout+30)
                result=json.loads(completed.stdout) if completed.returncode==0 else {'status':'harness_failed','returncode':completed.returncode}
            except subprocess.TimeoutExpired:
                result={'status':'harness_deadline','workflow_dispatch':False,'approval_performed':False}
            observations.append({'condition':name,'python_source_sha256':source_digest(code/'src'),**result})
            print(json.dumps(observations[-1]),flush=True)
        report={'schema_version':'data-card-context-comparison-v1','baseline_ref':args.baseline_ref,
            'model':args.model,'reasoning_effort':'none','max_tokens':512,'timeout_seconds':args.timeout,
            'model_call_limit_per_condition':1,'message':MESSAGE,'order':['before','after'],
            'input_sha256':hashlib.sha256((root/'data/input/facts.csv').read_bytes()).hexdigest(),
            'observations':observations,'limitations':['One observation per condition, fixed before-then-after order; load/warmup may affect timing.',
                'Identical current project guidance copied into both synthetic projects; only Python versions differ.',
                'Not the full benchmark, a statistical reliability result, a speed claim or a domain-data test.'],
            'owner_state_changed':False,'data_files_written_by_workflow':False}
        with args.output.open('x') as stream:
            json.dump(report,stream,indent=2)


if __name__ == '__main__':
    main()
