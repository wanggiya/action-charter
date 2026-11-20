"""Bounded same-model synthetic D3 comparison; no execution or owner setting changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

from data_card_context_evaluation import CHILD, source_digest

TASKS = [
    'Profile facts.csv and check its structure and data quality. Prepare only.',
    'Inspect facts.csv and suggest useful health-table analysis questions. Prepare only.',
]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-code',required=True,type=Path)
    parser.add_argument('--model',default='qwen3:4b-instruct')
    parser.add_argument('--base-url',default='http://127.0.0.1:11434/v1')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scope',choices=['automatic','inspect-only'],default='automatic')
    parser.add_argument('--task-index',type=int,choices=[0,1])
    parser.add_argument('--max-calls',type=int,choices=[1,2],default=2)
    parser.add_argument('--condition',choices=['both','before','after'],default='both')
    parser.add_argument('--private-responses',type=Path,help='New private file under the temporary directory; synthetic response bodies only')
    args=parser.parse_args()
    if urlparse(args.base_url).hostname not in {'127.0.0.1','localhost','::1'}:
        parser.error('Synthetic qualification requires an existing loopback model endpoint')
    if args.output.exists():parser.error('Choose a new output; preserve previous evidence')
    if args.private_responses:
        private=args.private_responses.absolute()
        if not private.parent.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
            parser.error('Private synthetic responses must stay under the temporary directory')
        fd=os.open(private,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.close(fd)
    repo=Path(__file__).resolve().parents[1]
    child=CHILD.replace("'input_tokens':None,'output_tokens':None", "'input_tokens':None,'output_tokens':None,'schema_count':len(json.loads(request.messages[0].content).get('operation_argument_schemas',{})),'knowhow_ids':[item['id'] for item in json.loads(request.messages[0].content).get('agent_knowhow',[])]")
    if args.scope=='automatic':child=child.replace(",allowed_skill_ids=['inspect_csv']",'')
    child=child.replace('if calls:raise RuntimeError', "if len(calls)>=config['max_calls']:raise RuntimeError")
    child=child.replace('result=client.complete(request)', """result=client.complete(request)
   if config.get('private_responses'):
    fd=os.open(config['private_responses'],os.O_WRONLY|os.O_APPEND|os.O_NOFOLLOW)
    with os.fdopen(fd,'a') as stream:stream.write(json.dumps({'condition':config['condition'],'content':result.content[:16000]})+'\\n')""")
    child=child.replace('import json,sys,time','import json,sys,time,os')
    child=child.replace("record.update(seconds=round(time.monotonic()-started,3),model_calls=calls)",
        """if record.get('status')=='failed':
 record.update(reason=locals().get('safe_reason'),schema_findings=locals().get('safe_findings',[]),correction_attempted=locals().get('safe_correction'))
record.update(seconds=round(time.monotonic()-started,3),model_calls=calls)""")
    child=child.replace("except Exception as error:\n record=", """except Exception as error:
 safe_reason=getattr(error,'reason',None)
 safe_findings=[str(item)[:1024] for item in (getattr(error,'findings',None) or [])[:6]]
 safe_correction=getattr(error,'correction_attempted',None)
 record=""")
    compile(child,'bounded-comparison-child','exec')
    with tempfile.TemporaryDirectory(prefix='actioncharter-focused-comparison-') as directory:
        base=Path(directory);candidate=base/'candidate';candidate.mkdir()
        shutil.copytree(repo/'src',candidate/'src',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(repo/'agent-skills',candidate/'agent-skills')
        common=base/'common'
        for name in ('context','agents'):shutil.copytree(repo/name,common/name)
        observations=[]
        source='id,patient_nbr,age,measurement,readmitted\n001,p1,40,2,NO\n002,p1,40,4,YES\n003,p2,55,6,NO\n'
        for index,message in enumerate(TASKS):
            if args.task_index is not None and index!=args.task_index:continue
            for condition,code in [('before',args.before_code.resolve()),('after',candidate)]:
                if args.condition!='both' and condition!=args.condition:continue
                root=base/f'task-{index}-{condition}';root.mkdir()
                for name in ('context','agents'):shutil.copytree(common/name,root/name)
                (root/'data/input').mkdir(parents=True);(root/'data/input/facts.csv').write_text(source)
                config={'base_url':args.base_url,'model':args.model,'timeout':60,'message':message,'candidate':False,'max_calls':args.max_calls,
                        'condition':condition,'private_responses':str(private) if args.private_responses else None}
                env={'PATH':os.environ.get('PATH',''),'LANG':'C.UTF-8','PYTHONPATH':str(code/'src'),
                     'MODEL_NAME':args.model,'MODEL_BASE_URL':args.base_url,'ENABLE_WRITE_TOOLS':'false',
                     'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
                try:
                    completed=subprocess.run([sys.executable,'-c',child,str(root),json.dumps(config)],
                        cwd=root,env=env,capture_output=True,text=True,timeout=args.max_calls*60+30)
                    record=json.loads(completed.stdout) if completed.returncode==0 else {'status':'harness_failed','returncode':completed.returncode}
                except subprocess.TimeoutExpired:
                    record={'status':'harness_deadline','workflow_dispatch':False,'approval_performed':False}
                item={'task':index,'message':message,'condition':condition,'python_source_sha256':source_digest(code/'src'),**record}
                observations.append(item);print(json.dumps(item),flush=True)
        report={'schema_version':'focused-planning-observation-v1','model':args.model,'reasoning_effort':'none',
            'planning_scope':args.scope,
            'condition_selection':args.condition,
            'timeout_seconds':60,'max_tokens':512,'call_limit_per_condition':args.max_calls,'input_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'observations':observations,'owner_settings_changed':False,'workflow_execution_requested':False,
            'limitations':['Fixed synthetic tasks and bounded calls; declared before-then-after order, or one explicitly selected diagnostic condition.',
                'Common guidance and synthetic source; candidate changes schema focus and instruction context together.',
                'Returned question is not a demonstrated analysis or a correct inspection proposal.',
                'Not per-skill reliability qualification, full benchmark, private-data analysis or a statistical speed result.']}
        with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')


if __name__=='__main__':main()
