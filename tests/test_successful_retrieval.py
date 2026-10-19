"""Own-chat methods assist proposals; they never bypass policy or authority."""
import json
import pytest

from tests.test_planner_conversation import project, Client, turn, as_base, ID
from tests.test_reusable_recipes_and_runs import execution, use
from geoagent_harness.recipe_catalog.composition import compose
from geoagent_harness.interface_api.workflow_runs import RunRequest,run_action
from geoagent_harness.interface_api.conversation import TurnRequest,conversation_turn
from geoagent_harness.planner.successful_retrieval import retrieve
from geoagent_harness.model import ModelClientError


@pytest.fixture
def completed(project,monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    (project/'data/output').mkdir(parents=True,exist_ok=True)
    request=use(project)
    request.parameters['source']='data/input/sample_orders.csv'
    planned,_=compose([request],project)
    reply=turn(project,Client({'message':'Clean CSV','plan':planned.plan.model_dump(mode='json')}),'Clean sample_orders.csv; keep region and amount and fill missing regions with Unknown')
    run=run_action(RunRequest(action='start',conversation_id=ID,workflow=execution(project,as_base(reply['planner_result']))),project_root=project,background=False)
    assert run['successful_recipe']['status']=='saved' and run['conversation_id']==ID
    return project,run,reply


def test_own_method_retrieval_proposes_fresh_bindings_without_execution(completed):
    root,run,reply=completed
    adapted=json.loads(json.dumps(reply['planner_result']['plan']))
    for step in adapted['steps']:step['arguments'].pop('target_path',None)
    client=Client({'message':'Adapted saved method','plan':adapted})
    before=(root/'data/output/cleaned.csv').read_bytes()
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message='Repeat cleaning the CSV with fresh outputs',current_plan=as_base(reply['planner_result'])),project_root=root,model_client=client)
    payload=json.loads(client.requests[0].messages[1].content)
    methods=payload['successful_method_examples']
    assert len(methods)==1 and methods[0]['source_run_id']==run['run_id']
    assert all('target_path' not in step['arguments'] for step in methods[0]['historical_operations'])
    assert 'authority' not in json.dumps(methods[0]['historical_operations'])
    assert result['context_usage']['successful_methods']['count']==1
    assert result['planner_result']['plan']['steps'][-1]['arguments']['target_path']!='data/output/cleaned.csv'
    assert (root/'data/output/cleaned.csv').read_bytes()==before
    assert not result['execution_performed'] and not result['approval_performed']


def test_history_off_and_other_chats_do_not_silently_retrieve(completed):
    root,run,_=completed
    skills=[s['skill_id'] for s in run['steps']]
    assert retrieve(root,'c'*32,'clean csv',skills)[0]==[]
    assert retrieve(root,ID,'clean csv',skills,use_history=False)[1]['status']=='history_disabled'
    selected,receipt=retrieve(root,ID,'Use saved successful method '+run['retention_basis']['method_id'],skills,use_history=False)
    assert len(selected)==1 and receipt['explicit_selection']
    assert retrieve(root,'c'*32,'Use saved successful method '+run['retention_basis']['method_id'],skills)[1]['status']=='selection_unavailable'


def test_changed_source_evidence_and_restricted_skills_cannot_be_reused(completed):
    root,run,_=completed
    skills=[s['skill_id'] for s in run['steps']]
    explicit='Use saved successful method '+run['retention_basis']['method_id']
    assert retrieve(root,ID,explicit,['inspect_csv'])[0]==[]
    path=root/'workflow-state/interface-runs'/f"{run['run_id']}.json"
    record=json.loads(path.read_text());record['steps'][0]['outcome']['row_count']=12345;path.write_text(json.dumps(record))
    assert retrieve(root,ID,explicit,skills)[1]['status']=='selection_unavailable'


def test_timeout_reports_safe_request_diagnostics_without_retry(project):
    client=Client(ModelClientError.timeout())
    with pytest.raises(ModelClientError) as caught:
        turn(project,client,'Clean sample_orders.csv; fill missing regions with Unknown')
    assert len(client.requests)==1
    diagnostic=caught.value.planner_diagnostics
    assert diagnostic['stage']=='planner_generation'
    assert diagnostic['prompt_bytes']<28000
    assert diagnostic['supplied_schema_count']<diagnostic['available_operation_count']
    assert 'sample_orders' not in json.dumps(diagnostic)


def test_schema_focus_preserves_allowlist_and_property_named_title():
    from geoagent_harness.planner.prompt_scope import compact_schema,schema_scope
    schema={'title':'Root','type':'object','properties':{'title':{'title':'Title','type':'string'}},'required':['title']}
    result=compact_schema(schema)
    assert result['properties']['title']=={'type':'string'}
    assert result['required']==['title']
    allowed=['inspect_csv','select_csv_columns','inspect_vector']
    assert schema_scope('Inspect x.csv',allowed)==allowed[:2]
    assert schema_scope('Inspect x.csv',allowed,['inspect_vector'])==allowed
    assert schema_scope('Inspect vector and CSV',allowed)==allowed


def test_cli_adaptation_uses_the_same_service_and_never_executes(completed,monkeypatch):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    import geoagent_harness.interface_api.conversation as service
    root,run,reply=completed
    adapted=json.loads(json.dumps(reply['planner_result']['plan']))
    for step in adapted['steps']:step['arguments'].pop('target_path',None)
    client=Client({'message':'Adapted via shared service','plan':adapted})
    original=service.conversation_turn
    monkeypatch.setattr(service,'conversation_turn',lambda request,*,project_root:original(request,project_root=project_root,model_client=client))
    request_file=root/'adaptation-request.json'
    request_file.write_text(json.dumps({'action':'turn','conversation_id':ID,'message':'Repeat cleaning the CSV with fresh outputs','expected_revision':1}))
    result=CliRunner().invoke(app,['planning-conversation-turn','--request-file',str(request_file),'--project-root',str(root)])
    assert result.exit_code==0,result.output
    payload=json.loads(result.output)
    assert payload['context_usage']['successful_methods']['count']==1
    assert not payload['approval_performed'] and not payload['execution_performed']
    assert len(list((root/'workflow-state/interface-runs').glob('*.json')))==1


def test_structured_selection_keeps_ids_out_of_user_text_and_checks_scope(completed):
    from geoagent_harness.interface_api.server import InterfaceApiError
    root,run,reply=completed
    adapted=json.loads(json.dumps(reply['planner_result']['plan']))
    for step in adapted['steps']:step['arguments'].pop('target_path',None)
    client=Client({'message':'Adapted selected workflow','plan':adapted})
    method=run['retention_basis']['method_id']
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message='Adapt the selected CSV workflow with fresh outputs',use_history=False,successful_method_id=method),project_root=root,model_client=client)
    assert result['context_usage']['successful_methods']['explicit_selection']
    assert result['context_usage']['successful_methods']['count']==1
    payload=json.loads(client.requests[0].messages[1].content)
    assert method not in payload['latest_message']
    assert payload['selected_successful_method_id']==method
    untouched=Client({'message':'Unused','plan':None})
    with pytest.raises(InterfaceApiError,match='outside this chat'):
        conversation_turn(TurnRequest(action='turn',conversation_id='c'*32,message='Adapt selected workflow',successful_method_id=method),project_root=root,model_client=untouched)
    assert untouched.requests==[]
