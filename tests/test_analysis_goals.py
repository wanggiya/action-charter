"""Evidence-bound goal advice is distinct from analysis results and authority."""
import json
import pytest
from tests.test_task_agents import project
from tests.test_planner_conversation import Client
from geoagent_harness.tabular.analysis_goals import AnalysisGoal,validate,requested
from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest


def context():
 return {'run_id':'b'*32,'plan_sha256':'c'*64,'results':[{'step_id':'step_1','field_guidance':{
 'source':'data/input/measures.csv','source_sha256':'d'*64,'source_rows':4,'matching_rows':4,
 'field_evidence':[{'name':name,'role':role} for name,role in [('x','numerical'),('y','numerical'),('entity_id','identifier'),('group','categorical')]]}}]}


def goal(**kwargs):return AnalysisGoal(title='Explore variation',question='How variable is x?',method='describe',fields=['x'],rationale='Observed measurement candidate',**kwargs)


def test_goals_validate_fields_and_keep_metrics_uncomputed():
 r=validate([goal()], 'd'*64,context())
 assert r['goals'][0]['metrics']==['count','mean','percentiles','variance','standard deviation']
 assert r['goals'][0]['status']=='proposal_not_calculated' and not r['computed'] and not r['authority_granted']
 with pytest.raises(ValueError,match='observed fields'):validate([goal().model_copy(update={'fields':['invented']})],'d'*64,context())
 with pytest.raises(ValueError,match='identifiers'):validate([goal().model_copy(update={'fields':['entity_id']})],'d'*64,context())
 with pytest.raises(ValueError,match='exact recorded'):validate([goal()],'0'*64,context())
 assert validate([],None,None) is None
 with pytest.raises(ValueError,match='at least one'):validate([],'d'*64,context())


def test_unavailable_classification_and_large_source_are_explicit():
 g=goal().model_copy(update={'method':'classification_evaluation','fields':['group','x'],'target_candidate':'group'})
 result=validate([g],'d'*64,context())['goals'][0]
 assert result['availability']=='not_available' and 'held-out precision' in result['metrics']
 assert any('leakage' in text for text in result['prerequisites'])
 c=context();c['results'][0]['field_guidance']['matching_rows']=200001
 assert validate([goal()],'d'*64,c)['goals'][0]['availability']=='needs_scope'


def test_goal_advice_preserves_saved_workflow_and_cannot_execute(project,monkeypatch):
 identity='a'*32
 p={'summary':'Inspect measurements','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'sample_orders.csv'}}]}
 initial=conversation_turn(TurnRequest(action='turn',conversation_id=identity,message='Inspect sample_orders.csv.'),project_root=project,model_client=Client({'message':'Proposed','plan':p}))
 c=context();c['plan_sha256']=initial['planner_result']['plan_sha256']
 monkeypatch.setattr('geoagent_harness.interface_api.result_exploration.view_context',lambda *a,**k:c)
 response={'message':'Consider a distribution question.','plan':None,'source_sha256':'d'*64,'analysis_goals':[goal().model_dump()]}
 client=Client(response)
 request=TurnRequest(action='turn',conversation_id=identity,expected_revision=initial['revision'],message='Propose analysis goals from the recorded inspection. Suggestions only.')
 state=conversation_turn(request,project_root=project,model_client=client)
 assert state['planner_result']['plan_sha256']==initial['planner_result']['plan_sha256']
 assert state['context_usage']['analysis_goals']['goals'][0]['fields']==['x']
 assert not state['execution_performed'] and not state['approval_performed']
 system=json.loads(client.requests[0].messages[0].content)
 assert system['operation_argument_schemas']=={} and client.requests[0].response_schema['properties']['plan']=={'type':'null'}
 numeric_branch=client.requests[0].response_schema['$defs']['AnalysisGoal']['anyOf'][1]
 assert numeric_branch['properties']['fields']['items']['enum']==['x','y']
 assert 'linear_regression' in numeric_branch['properties']['method']['enum']
 assert requested(request.message) and not requested('Prepare a workflow for the selected analysis goal; do not execute.')
 saved=conversation_turn(TurnRequest(action='read',conversation_id=identity),project_root=project)
 assert saved['context_usage']['analysis_goals']==state['context_usage']['analysis_goals']


def test_wrong_source_and_identifier_inference_receive_bounded_goal_correction(project,monkeypatch):
 identity='e'*32;p={'summary':'Inspect','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'sample_orders.csv'}}]}
 initial=conversation_turn(TurnRequest(action='turn',conversation_id=identity,message='Inspect sample_orders.csv.'),project_root=project,model_client=Client({'message':'Proposed','plan':p}))
 c=context();c['plan_sha256']=initial['planner_result']['plan_sha256']
 monkeypatch.setattr('geoagent_harness.interface_api.result_exploration.view_context',lambda *a,**k:c)
 bad={'message':'Advice','plan':None,'source_sha256':'d'*64,'analysis_goals':[goal().model_copy(update={'fields':['entity_id']}).model_dump()]}
 good={**bad,'analysis_goals':[goal().model_dump()]};client=Client(bad,good)
 state=conversation_turn(TurnRequest(action='turn',conversation_id=identity,expected_revision=initial['revision'],message='Suggest analysis goals from inspection.'),project_root=project,model_client=client)
 assert len(client.requests)==2 and state['context_usage']['analysis_goals']['goals'][0]['fields']==['x']
 assert 'structured analysis_goals' in client.requests[1].messages[-1].content


def test_goal_schema_findings_name_trusted_fields_without_content():
 from geoagent_harness.interface_api.conversation import AnalysisGoalsReply
 from geoagent_harness.planner.agent import _schema_findings
 from pydantic import ValidationError
 with pytest.raises(ValidationError) as caught:
  AnalysisGoalsReply.model_validate({'message':'Advice','plan':None,'analysis_goals':[goal().model_dump()|{'rationale':'sensitive value '*30}]})
 findings=_schema_findings(caught.value)
 assert any('analysis_goals.0.rationale' in f and 'maximum text length' in f for f in findings)
 assert all('sensitive value' not in f for f in findings)
