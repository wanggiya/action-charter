"""Mode semantics, role isolation, immutable execution scope and truthful effort metrics."""
import json
from pathlib import Path
import shutil
import pytest
from geoagent_harness.model.schemas import ModelResult,ModelRequest,ChatMessage
from geoagent_harness.orchestrator.task_agents import Coordinator,finish_run
from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.planner.schemas import PlannerResult

ROOT=Path(__file__).parents[1];ID='a'*32
@pytest.fixture
def project(tmp_path):
 for name in ('context','agents'):shutil.copytree(ROOT/name,tmp_path/name)
 (tmp_path/'data/input').mkdir(parents=True);(tmp_path/'data/output').mkdir()
 shutil.copyfile(ROOT/'data/input/sample_orders.csv',tmp_path/'data/input/sample_orders.csv')
 return tmp_path

class Client:
 def __init__(self,*,tokens=True,revision=False):self.requests=[];self.tokens=tokens;self.revision=revision
 def complete(self,request):
  self.requests.append(request)
  control=json.loads(request.messages[0].content)['task_coordinator']
  if control['phase']=='planning':
   value={'message':'Proposed selection only.','plan':{'summary':'Select declared columns','steps':[{'step_id':'step_1','skill':'select_csv_columns','purpose':'Select region and amount','arguments':{'path':'data/input/sample_orders.csv','columns':['region','amount'],'target_path':'data/output/selected.csv'},'requires_approval':True,'validation_required':True}]}}
  else:
   value={'conclusion':'needs_revision' if self.revision and control['phase']=='preflight' else 'ready' if control['phase']=='preflight' else 'supported','summary':'Assess supplied facts only.','findings':[],'evidence_step_ids':['step_1'],'limitations':['Small fixture; not a domain assessment.']}
  return ModelResult(model='fixture',content=json.dumps(value),prompt_tokens=10 if self.tokens else None,completion_tokens=4 if self.tokens else None)


def generate(project,mode,client):
 return conversation_turn(TurnRequest(action='turn',conversation_id=ID,message='Select region and amount from sample_orders.csv; prepare only.',agent_mode=mode),project_root=project,model_client=client)

@pytest.mark.parametrize('mode,calls,actors',[('single',2,['primary','primary']),('three',3,['planner','executor','critic'])])
def test_actual_planning_uses_one_or_three_contexts(project,mode,calls,actors):
 client=Client();result=generate(project,mode,client)
 receipt=result['agent_coordination']
 assert receipt['mode']==mode and len(client.requests)==calls
 controls=[json.loads(r.messages[0].content)['task_coordinator'] for r in client.requests]
 assert [c['actor'] for c in controls]==actors
 assert bool(controls[1]['context_notes'])==(mode=='single')
 if mode=='three':assert not controls[2]['context_notes'] and 'executor_handoff' in client.requests[2].messages[1].content
 assert receipt['metrics']['prompt_tokens']==calls*10 and receipt['metrics']['completion_tokens']==calls*4
 assert receipt['authority_granted'] is False and not list((project/'data/output').iterdir())
 assert conversation_turn(TurnRequest(action='read',conversation_id=ID),project_root=project)['agent_mode']==mode
 assert len(client.requests)==calls


def test_missing_tokens_are_unknown_and_failed_review_does_not_authorize(project):
 client=Client(tokens=False);value=generate(project,'single',client)
 assert value['agent_coordination']['metrics']['prompt_tokens'] is None
 assert not value['agent_coordination']['metrics']['token_usage_complete']
 assert not (project/'approvals').exists()


def test_reviews_cannot_override_failed_execution_or_invent_steps():
 c=Coordinator('three',client=Client())
 receipt=c.review('critic','outcome',{'status':'failed','steps':[{'step_id':'step_1'}]})
 assert receipt['status']=='unavailable' and not receipt['authority_granted']
 c=Coordinator('single',client=Client())
 receipt=c.review('executor','preflight',{'steps':[{'step_id':'step_2'}]})
 assert receipt['status']=='unavailable'


def test_mode_changes_only_future_work_and_cannot_run_during_execution(project):
 first=generate(project,'single',Client())
 updated=conversation_turn(TurnRequest(action='configure_agent_mode',conversation_id=ID,expected_revision=first['revision'],agent_mode='three'),project_root=project)
 assert updated['agent_mode']=='three' and updated['agent_coordination']['mode']=='single'
 directory=project/'workflow-state/interface-runs';directory.mkdir(parents=True,exist_ok=True)
 (directory/('b'*32+'.json')).write_text(json.dumps({'conversation_id':ID,'status':'running'}))
 with pytest.raises(api.InterfaceApiError,match='run to stop'):
  conversation_turn(TurnRequest(action='configure_agent_mode',conversation_id=ID,expected_revision=updated['revision'],agent_mode='single'),project_root=project)


def test_review_identity_is_chat_scoped_even_for_same_plan(project):
 first=generate(project,'single',Client());proposal=first['planner_result']
 typed=PlannerResult.model_validate({k:proposal[k] for k in ('model','agent_id','original_request','context_references','plan','warnings')})
 stored=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=typed,confirmed_plan_sha256=proposal['plan_sha256'],allowed_skill_ids=['select_csv_columns']),project_root=project)
 a=prepare_workflow(WorkflowRequest(action='prepare_workflow',conversation_id=ID,plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256']),project_root=project)
 b=prepare_workflow(WorkflowRequest(action='prepare_workflow',conversation_id='c'*32,plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256']),project_root=project)
 assert a['agent_mode']=='single' and 'agent_mode' not in b and a['review_sha256']!=b['review_sha256']


def test_report_uses_saved_mode_and_bounded_original_context(project):
 first=generate(project,'single',Client())
 record={'agent_coordination':first['agent_coordination'],'run_id':'d'*32,'plan_sha256':first['planner_result']['plan_sha256'],'status':'completed','failed_step_id':None,'steps':[{'step_id':'step_1','skill_id':'select_csv_columns','status':'validated_success','outcome':{'row_count':6,'preview':[{'patient_nbr':'private identifier'}]},'validation_outcome':{'passed':True}}]}
 report=finish_run(project,record,model_client=Client())
 assert report['report']['mode']=='single' and report['report']['review_kind']=='self_review'
 assert 'private identifier' not in json.dumps(report['report'])
 assert report['report']['tool_calls']==1 and report['report']['evidence']['steps'][0]['facts']['row_count']==6
 assert report['report']['planning_metrics']['model_calls']==2
 assert 'Self-review is not independent' in report['report']['text']
 assert 'Recorded operations' in report['report']['text']


def test_legacy_assessment_cannot_replace_captured_single_mode(project,monkeypatch):
 from geoagent_harness.interface_api import workflow_runs,run_assessment
 record={'run_id':'e'*32,'status':'completed','agent_coordination':{'mode':'single'},'critic_review':{'status':'complete','finding':'Saved self-review'}}
 monkeypatch.setattr(workflow_runs,'_read',lambda directory,identity:record)
 class ForbiddenClient:
  def complete(self,request):raise AssertionError('Must not run another Critic')
 assert run_assessment.assess_run(project,record['run_id'],model_client=ForbiddenClient(),retry=True)==record


def test_preflight_correction_is_bounded_and_failed_attempt_preserves_plan(project):
 good=generate(project,'single',Client())
 bad=Client(revision=True)
 with pytest.raises(Exception):conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=good['revision'],message='Select region and amount; revise the current plan.',agent_mode='single'),project_root=project,model_client=bad)
 state=conversation_turn(TurnRequest(action='read',conversation_id=ID),project_root=project)
 assert state['planner_result']['plan_sha256']==good['planner_result']['plan_sha256']
 assert state['agent_attempt']['metrics']['model_calls']<=6
