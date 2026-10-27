"""Compare actual coordinator paths on real data in a disposable database.

A local HTTP model fixture supplies proposals/reviews. This validates role routing,
not the quality/speed of a real Ollama model or clinical reasoning.
"""
import csv
from collections import Counter
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
from threading import Thread
import time
import uuid
import psycopg
from postgres_workflow_acceptance import docker
from diabetes_reference import read_book,sha,CODES
from diabetes_test_flow import make_plan,SELECTED,EXPORTED
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow,authorize_workflow
from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.write_policy import session

REPO=Path(__file__).resolve().parents[1]
def main():
 name='actioncharter-agent-modes-'+uuid.uuid4().hex[:12];created=False;provider=None
 source=REPO/'data/input/test/diabetic_sample_5000.csv';book_path=REPO/'data/input/test/IDS_mapping.csv';before=(sha(source),sha(book_path));book=read_book(book_path)
 with source.open(newline='') as stream:original=list(csv.DictReader(stream))
 expected=Counter(tuple([r[c] for c in SELECTED]+[book[c][r[c]] for c in CODES]+['false']) for r in original)
 old=os.environ.copy()
 with tempfile.TemporaryDirectory(prefix='actioncharter-task-modes-') as directory:
  root=Path(directory)
  for d in ('context','agents'):shutil.copytree(REPO/d,root/d)
  (root/'data/input/test').mkdir(parents=True);(root/'data/output').mkdir()
  shutil.copyfile(source,root/'data/input/test/diabetic_sample_5000.csv');shutil.copyfile(book_path,root/'data/input/test/IDS_mapping.csv')
  password=secrets.token_hex(24);secret=root/'throwaway-password';secret.write_text(password);secret.chmod(0o600)
  try:
   docker('run','--detach','--rm','--name',name,'--publish','127.0.0.1::5432','--tmpfs','/var/lib/postgresql/data:rw','--env','POSTGRES_PASSWORD='+password,'postgres:17');created=True
   port=int(docker('port',name,'5432/tcp').split(':')[-1])
   for _ in range(100):
    try:
     with psycopg.connect(host='127.0.0.1',port=port,dbname='postgres',user='postgres',password=password,connect_timeout=1) as db:db.execute('CREATE SCHEMA agent_sandbox')
     break
    except psycopg.Error:time.sleep(.1)
   else:raise AssertionError('Temporary database did not start')
   settings=MCPSettings(project_root=root,input_root=root/'data/input',output_root=root/'data/output',postgres_host='127.0.0.1',postgres_port=port,postgres_database='postgres',postgres_user='postgres',postgres_password_file=secret,enable_write_tools=True)
   calls=[];current={}
   class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_POST(self):
     body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
     control=json.loads(body['messages'][0]['content'])['task_coordinator'];calls.append(control)
     if control['phase']=='planning':value={'message':'Exact temporary workflow proposed. Nothing executed.','plan':current['plan'].plan.model_dump(mode='json')}
     else:value={'conclusion':'ready' if control['phase']=='preflight' else 'supported','summary':'Assess the supplied fixed evidence only.','findings':[],'evidence_step_ids':[f'step_{n}' for n in range(1,7)],'limitations':['Fixture response; not real-model capability evidence.']}
     encoded=json.dumps({'model':'fixture','choices':[{'message':{'content':json.dumps(value)},'finish_reason':'stop'}],'usage':{'prompt_tokens':10,'completion_tokens':5}}).encode()
     self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(encoded)));self.end_headers();self.wfile.write(encoded)
   provider=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=provider.serve_forever,daemon=True).start()
   os.environ.update(ENABLE_WRITE_TOOLS='true',GEOAGENT_PROJECT_ROOT=str(root),POSTGRES_HOST='127.0.0.1',POSTGRES_PORT=str(port),POSTGRES_DB='postgres',POSTGRES_USER='postgres',POSTGRES_PASSWORD_FILE=str(secret),ALLOWED_SCHEMAS='agent_sandbox',MODEL_NAME='fixture',MODEL_BASE_URL=f'http://127.0.0.1:{provider.server_port}/v1',MODEL_REASONING_EFFORT='none')
   for key,suffix in {'INPUT':'data/input','OUTPUT':'data/output','TRACE':'traces','REPORT':'reports','PLAN':'plans','APPROVAL':'approvals','STATE':'workflow-state','RECIPE':'workflow-recipes','RECIPE_RUN':'recipe-runs','RECIPE_EVIDENCE':'recipe-evidence','SPATIAL_CONTRACT':'spatial-contracts'}.items():os.environ['GEOAGENT_'+key+'_ROOT']=str(root/suffix)
   comparisons=[]
   with session(root,enabled=True):
    for mode in ('three','single'):
     identity=uuid.uuid4().hex;current['plan']=make_plan(settings,table='diabetes_'+mode,output='data/output/'+mode);start=len(calls)
     state=conversation_turn(TurnRequest(action='turn',conversation_id=identity,agent_mode=mode,message='Prepare the declared diabetes CSV readiness, selection, codebook decoding, aggregation and PostgreSQL import/export workflow. No execution yet.'),project_root=root)
     r=state['planner_result'];typed=PlannerResult.model_validate({k:r[k] for k in ('agent_id','model','original_request','context_references','plan','warnings')})
     stored=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=typed,confirmed_plan_sha256=r['plan_sha256'],allowed_skill_ids=r['allowed_skill_ids']),project_root=root)
     request=WorkflowRequest(action='prepare_workflow',conversation_id=identity,plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256']);review=prepare_workflow(request,project_root=root)
     assert review['agent_mode']==mode
     approved=authorize_workflow(request.model_copy(update={'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Disposable database and temporary data only'}),project_root=root)
     workflow=request.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,'plan_approval_filename':approved['plan_approval_filename'],'recipe_approval_filename':approved['recipe_approval_filename']})
     record=run_action(RunRequest(action='start',conversation_id=identity,workflow=workflow),project_root=root,background=False)
     assert record['status']=='completed',record.get('finding')
     with (root/f'data/output/{mode}_roundtrip.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
     assert Counter(tuple(r[c] for c in EXPORTED) for r in rows)==expected
     report=run_action(RunRequest(action='report',run_id=record['run_id']),project_root=root)
     assert report['mode']==mode and report['assessment']['status']=='complete'
     assert report['review_kind']==('self_review' if mode=='single' else 'separate_critic_context')
     total=len(calls);run_action(RunRequest(action='read',run_id=record['run_id']),project_root=root);run_action(RunRequest(action='report',run_id=record['run_id']),project_root=root);assert len(calls)==total
     actors=[c['actor'] for c in calls[start:]]
     assert actors==(['primary']*3 if mode=='single' else ['planner','executor','critic','critic']),actors
     comparisons.append({'mode':mode,'rows':len(rows),'values_match':True,'actors':actors,'planning_metrics':report['planning_metrics'],'outcome_metrics':report['metrics'],'operation_attempts':report['tool_calls']})
   print(json.dumps({'status':'passed','source_rows':len(original),'modes':comparisons,'model':'local HTTP fixture, not an actual Ollama evaluation','database':'disposable postgres:17','live_services_touched':False},indent=2))
  finally:
   if provider:provider.shutdown();provider.server_close()
   os.environ.clear();os.environ.update(old)
   if created:docker('rm','--force',name)
   assert (sha(source),sha(book_path))==before
if __name__=='__main__':main()
