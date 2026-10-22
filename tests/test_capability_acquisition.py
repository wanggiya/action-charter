"""Optional data-only acquisition: private preparation, tests, promotion, execution."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from tests.test_planner_conversation import project,Client,turn,read,ID
from geoagent_harness.capabilities.service import CapabilityProposal,make_package,prepare,promote
from geoagent_harness.capabilities.text import TextTransform,reference_value
from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.operations.packages import package_sha,canonical,parse_package,test_package as package_test,installed_packages,execute_projection,PackageError
from geoagent_harness.planner.agent import PlannerAgentError
from geoagent_harness.planner.effort_budget import EffortBudget

REQUEST='Inspect sample_orders.csv. Trim whitespace and uppercase region into a NEW region_clean column, preserving original columns, then save a fresh CSV. Do not execute.'
DEFINITION={'source_column':'region','output_column':'region_clean','steps':[{'kind':'strip'},{'kind':'upper'}]}
PROPOSAL={'gap_reason':'Registered CSV operations have no string normalization transform.','definition':DEFINITION}
REPLY={'message':'Prepare a bounded text capability.','plan':None,'capability_request':PROPOSAL}
CRITIC={'assessment':'suitable','reason':'The definition matches the requested trim then uppercase transform.','limitations':['Synthetic evidence only.']}

def configure(root,enabled=True,revision=0,identity=ID):
    return conversation_turn(TurnRequest(action='configure_acquisition',conversation_id=identity,expected_revision=revision,acquisition_enabled=enabled),project_root=root)

def candidate(root):
    configure(root)
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message=REQUEST),project_root=root,model_client=Client(REPLY),critic_client=Client(CRITIC))
    return result,result['capability_candidate']

def install(root,record,revision=2,identity=ID,sha=None):
    return conversation_turn(TurnRequest(action='install_capability',conversation_id=identity,expected_revision=revision,confirmed_candidate_sha256=sha or record['candidate_sha256']),project_root=root)

def test_defaults_private_switch_persistence_and_stale_configuration(project):
    assert not read(project)['acquisition_enabled']
    enabled=configure(project)
    assert enabled['revision']==1 and enabled['acquisition_enabled']
    assert read(project)['acquisition_enabled']
    other=conversation_turn(TurnRequest(action='read',conversation_id='c'*32),project_root=project)
    assert not other['acquisition_enabled'] and other['capability_candidate'] is None
    with pytest.raises(InterfaceApiError):configure(project,False,0)
    assert not configure(project,False,1)['acquisition_enabled']
    assert not (project/'operation-packages').exists()


def test_off_rejects_candidate_with_bounded_repair_and_no_tests(project,monkeypatch):
    called=[]
    monkeypatch.setattr('geoagent_harness.capabilities.service.prepare',lambda *a,**k:called.append(1))
    with pytest.raises(PlannerAgentError):turn(project,Client(REPLY,REPLY),REQUEST)
    assert called==[] and read(project)['revision']==0
    assert not (project/'operation-packages').exists()


def test_on_existing_operation_plan_never_starts_acquisition(project,monkeypatch):
    configure(project)
    monkeypatch.setattr('geoagent_harness.capabilities.service.prepare',lambda *a,**k:pytest.fail('Unneeded acquisition'))
    reply={'message':'Inspect','plan':{'summary':'Inspect CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Read metadata','arguments':{'path':'sample_orders.csv'}}]}}
    client=Client(reply)
    result=turn(project,client,'Inspect sample_orders.csv. No writes.',revision=1)
    assert len(client.requests)==1 and result['capability_candidate'] is None
    assert result['context_usage']['effort_budget']['fixture_batches']==0


def test_prepare_install_restart_reuse_no_execution_authority(project):
    result,record=candidate(project)
    assert record['status']=='tested' and record['tests']['passed']
    assert record['critic']['assessment']=='suitable'
    assert record['tests']['arbitrary_python_executed'] is False
    assert len(record['tests']['negative_cases'])>=7
    assert result['context_usage']['effort_budget']['model_calls']==2
    assert result['context_usage']['effort_budget']['fixture_batches']==1
    assert result['context_usage']['effort_budget']['tool_calls']==1
    assert not result['execution_performed'] and not result['approval_performed']
    assert not (project/'operation-packages').exists() and not (project/'data/output').exists()
    installed=install(project,record)
    assert installed['capability_candidate']['installed']
    assert not installed['execution_performed'] and not installed['approval_performed']
    assert read(project)['capability_candidate']['installed']
    packages=installed_packages(project);assert record['operation_id'] in packages
    assert not (project/'data/output').exists()
    # Exact compatible installed definitions bypass all fixture/Critic work.
    reused=prepare(CapabilityProposal.model_validate(PROPOSAL),root=project,conversation_id=ID,revision=3,message=REQUEST,budget=EffortBudget(),critic_client=Client())
    assert reused['status']=='use_existing' and reused['fixture_batches']==0 and reused['model_calls']==0
    from geoagent_harness.operations.registry import operation_catalog
    item=next(op for op in operation_catalog(project)['operations'] if op['id']==record['operation_id'])
    assert item['approval_required'] and item['validation_required']
    assert item['adapter_configuration']['text_transform']['output_column']=='region_clean'
    public=(project/'operation-packages'/f"{record['operation_id']}.json").read_text()
    assert REQUEST not in public and ID not in public and 'sample_orders.csv' not in public


def test_promotion_rejects_wrong_digest_other_chat_and_changed_revision(project):
    _,record=candidate(project)
    with pytest.raises(ValueError):install(project,record,sha='0'*64)
    with pytest.raises(InterfaceApiError):install(project,record,identity='c'*32,revision=0)
    with pytest.raises(InterfaceApiError):install(project,record,revision=1)
    configure(project,False,2)
    with pytest.raises(InterfaceApiError):install(project,record,revision=3)
    assert not (project/'operation-packages').exists()


@pytest.mark.parametrize('bad',[{'steps':[{'kind':'python','code':'print(1)'}]}, {'steps':[{'kind':'replace_literal','old':'.*','new':'X','regex':True}]}, {'source_column':'../region'}, {'output_column':'region'}])
def test_closed_family_rejects_code_regex_paths_and_replacement(bad):
    with pytest.raises(ValidationError):TextTransform.model_validate({**DEFINITION,**bad})


def test_cell_expansion_is_rejected_before_vectorization():
    definition=TextTransform(source_column='region',output_column='result',steps=[{'kind':'replace_literal','old':'x','new':'x'*128}])
    with pytest.raises(ValueError):reference_value('x'*4096,definition)


def test_worker_has_deadline_and_scrubbed_environment(project,monkeypatch):
    import subprocess
    from geoagent_harness.capabilities.testing import test_text_package
    package=make_package(CapabilityProposal.model_validate(PROPOSAL))
    seen=[]
    def timeout(*args,**kwargs):seen.append((args,kwargs));raise subprocess.TimeoutExpired(args[0],20)
    monkeypatch.setenv('POSTGRES_PASSWORD','not-for-the-worker')
    monkeypatch.setattr(subprocess,'run',timeout)
    with pytest.raises(PackageError):test_text_package(package)
    command,kwargs=seen[0]
    assert '-I' in command[0] and '-B' in command[0]
    assert kwargs['timeout']==20 and 'POSTGRES_PASSWORD' not in kwargs['env']


def test_legacy_projection_manifest_digest_is_unchanged():
    path=Path(__file__).parents[1]/'examples/checkpoint25/order_identity.operation.json'
    old=json.loads(path.read_text());old.setdefault('runtime','pandas==3.0.5');old.setdefault('candidate_function','pandas.core.indexing.IndexingMixin.loc')
    expected=hashlib.sha256(json.dumps(old,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    package=parse_package(json.loads(path.read_text()))
    assert package_sha(package)==expected and b'text_transform' not in canonical(package)


def test_promoted_adapter_obeys_write_policy_and_verifies_exact_values(project):
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.tabular.service import validate_output,read_frame
    _,record=candidate(project);install(project,record)
    settings=load_settings({}).model_copy(update={'project_root':project,'enable_write_tools':False})
    args={'path':'data/input/sample_orders.csv','target_path':'data/output/cleaned.csv','package_sha256':record['package_sha256']}
    with pytest.raises(ValueError):execute_projection(record['operation_id'],args,settings)
    settings=settings.model_copy(update={'enable_write_tools':True})
    output=execute_projection(record['operation_id'],args,settings)
    checks=validate_output(output,settings)
    assert checks['passed'] and checks['checks']['text_transform_values']
    frame=read_frame((project/args['target_path']).read_bytes())
    original=read_frame((project/args['path']).read_bytes())
    assert len(frame)==len(original) and list(frame.columns)==[*original.columns,'region_clean']
    with pytest.raises(ValueError):execute_projection(record['operation_id'],args,settings)
    with pytest.raises(ValueError):execute_projection(record['operation_id'],{**args,'package_sha256':'0'*64},settings)
    tampered=copy.deepcopy(output);tampered['text_transform_definition']['steps'][0]['kind']='lower'
    assert not validate_output(tampered,settings)['passed']


def test_cli_controls_share_the_chat_service_and_require_confirmation(project):
    from geoagent_harness.cli import app
    runner=CliRunner()
    output=runner.invoke(app,['capability-acquisition',ID,'--enabled','--expected-revision','0','--project-root',str(project)])
    assert output.exit_code==0,output.output
    assert json.loads(output.output)['acquisition_enabled']
    rejected=runner.invoke(app,['install-chat-capability',ID,'--candidate-sha','0'*64,'--expected-revision','1','--project-root',str(project)])
    assert rejected.exit_code==2 and '--confirm-install' in rejected.output


def test_critic_rejection_and_failed_fixture_never_install(project,monkeypatch):
    configure(project)
    critic=Client({'assessment':'not_suitable','reason':'Fixture criticism','limitations':[]})
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message=REQUEST),project_root=project,model_client=Client(REPLY),critic_client=critic)
    record=result['capability_candidate'];assert record['status']=='rejected'
    with pytest.raises(ValueError):install(project,record)
    assert not (project/'operation-packages').exists()
    monkeypatch.setattr('geoagent_harness.capabilities.service.test_package',lambda value,**kwargs:{'passed':False,'finding':'Synthetic mismatch','scope':'temporary_fixtures_only'})
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=2,message=REQUEST),project_root=project,model_client=Client(REPLY),critic_client=Client())
    assert result['capability_candidate']['status']=='rejected' and result['capability_candidate']['critic']['status']=='not_requested'
    assert result['context_usage']['effort_budget']['model_calls']==1


def test_capability_workflow_uses_existing_exact_authorization_and_downstream_csv(project,monkeypatch):
    from geoagent_harness.planner.schemas import PlannerResult
    from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow,authorize_workflow,execute_workflow
    from tests.test_operation_discovery import stored
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    _,record=candidate(project);install(project,record)
    plan=PlannerResult(model='fixture',original_request=REQUEST,context_references=[],plan={'summary':'Normalize then select','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/sample_orders.csv'}},
        {'step_id':'step_2','skill':record['operation_id'],'purpose':'Clean strings','arguments':{'path':'data/input/sample_orders.csv','target_path':'data/output/cleaned.csv','package_sha256':record['package_sha256']},'depends_on':['step_1'],'requires_approval':True,'validation_required':True},
        {'step_id':'step_3','skill':'select_csv_columns','purpose':'Select cleaned values','arguments':{'source_step':'step_2','columns':['region_clean'],'target_path':'data/output/selected.csv'},'depends_on':['step_2'],'requires_approval':True,'validation_required':True}]})
    scope=stored(project,plan);review=prepare_workflow(scope,project_root=project)
    assert review['steps'][1]['adapter_configuration']['text_transform']['steps'][1]['kind']=='upper'
    execute={**scope.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True}
    with pytest.raises(InterfaceApiError):execute_workflow(WorkflowRequest(**execute),project_root=project)
    authorization=authorize_workflow(WorkflowRequest(**{**scope.model_dump(),'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Only temporary text transform outputs'}),project_root=project)
    result=execute_workflow(WorkflowRequest(**{**execute,'plan_approval_filename':authorization['plan_approval_filename'],'recipe_approval_filename':authorization['recipe_approval_filename']}),project_root=project)
    assert result['status']=='validated_success'
    assert result['step_results'][1]['validation_outcome']['checks']['text_transform_values']
    assert (project/'data/output/selected.csv').read_text().startswith('region_clean\nNORTH\n')


def test_fixture_and_model_deadlines_are_shared_and_bounded(monkeypatch):
    from geoagent_harness.model.schemas import ModelRequest,ChatMessage,ModelResult
    monkeypatch.setenv('PLANNER_TURN_TIMEOUT_SECONDS','60')
    budget=EffortBudget();client=Client({'message':'ok'})
    request=ModelRequest(timeout_seconds=15,messages=[ChatMessage(role='user',content='Fixture')])
    budget.complete(client,request,lambda r:7)
    assert client.requests[0].timeout_seconds<=15
    budget.fixture_batch()
    with pytest.raises(Exception) as stopped:budget.fixture_batch()
    assert stopped.value.code=='planner_budget_exhausted'
    assert budget.receipt()['fixture_batches']==1


def test_budget_failure_preserves_chat_and_keeps_private_attempt_receipt(project,monkeypatch):
    from geoagent_harness.capabilities.service import attempts
    from geoagent_harness.model import ModelClientError
    configure(project)
    def exhausted(self):self.reject('fixture_batch_limit')
    monkeypatch.setattr(EffortBudget,'fixture_batch',exhausted)
    with pytest.raises(ModelClientError) as error:
        conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message=REQUEST),project_root=project,model_client=Client(REPLY))
    assert error.value.code=='planner_budget_exhausted'
    assert error.value.planner_diagnostics['effort_budget']['model_calls']==1
    assert read(project)['revision']==1 and read(project)['capability_candidate'] is None
    history=attempts(project,ID)['attempts'];assert len(history)==1
    assert history[0]['status']=='preparation_failed' and history[0]['committed_turn'] is False
    assert attempts(project,'c'*32)['attempts']==[]
    assert not (project/'operation-packages').exists()


def test_unavailable_critic_is_explicit_and_cannot_fabricate_success(project):
    from geoagent_harness.model import ModelClientError
    configure(project)
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message=REQUEST),project_root=project,model_client=Client(REPLY),critic_client=Client(ModelClientError.timeout()))
    record=result['capability_candidate']
    assert record['status']=='tested' and record['tests']['passed']
    assert record['critic']['status']=='unavailable' and record['critic']['assessment'] is None
    assert record['critic']['code']=='model_timeout'
    assert not result['context_usage']['effort_budget']['token_usage_complete']
    assert result['context_usage']['effort_budget']['model_calls']==2
    assert not (project/'operation-packages').exists()


@pytest.mark.parametrize('enabled',[False,True])
@pytest.mark.parametrize('typed_operations',[False,True])
def test_known_gap_decoder_supports_plain_and_operation_branch_schemas(enabled,typed_operations):
    from geoagent_harness.interface_api.conversation import Reply,AcquisitionReply
    from geoagent_harness.planner.decoder_schema import decoder_schema
    from geoagent_harness.capabilities.service import gap_decoder
    from geoagent_harness.tabular.schemas import InspectCSV
    schema=(AcquisitionReply if enabled else Reply).model_json_schema()
    schema['$defs']['PlanStep']['properties']['skill']['enum']=['inspect_csv']
    decoder=decoder_schema(schema,{'inspect_csv':InspectCSV.model_json_schema()} if typed_operations else {})
    bounded=gap_decoder(decoder,enabled)
    assert 'properties' not in bounded and 'WorkflowPlan' not in bounded['$defs']
    assert len(bounded['anyOf'])==(2 if enabled else 1)
    assert all(branch['properties']['plan']=={'type':'null'} for branch in bounded['anyOf'])
    assert all('workflow_action' not in branch['properties'] for branch in bounded['anyOf'])


def test_known_gap_cannot_be_disguised_as_numeric_calculation(project):
    configure(project)
    wrong={'message':'Normalize using arithmetic','plan':{'summary':'Wrong family','steps':[{'step_id':'step_1','skill':'calculate_csv_columns','purpose':'Uppercase','arguments':{'path':'data/input/sample_orders.csv'}}]}}
    client=Client(wrong,REPLY)
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message=REQUEST),project_root=project,model_client=client,critic_client=Client(CRITIC))
    assert len(client.requests)==2 and result['capability_candidate']['status']=='tested'
    system=json.loads(client.requests[0].messages[0].content)
    assert system['known_capability_gap']['registered_text_family'] is False
    assert system['known_capability_gap']['plan_must_be_null']
    assert json.loads(client.requests[1].messages[-1].content)['failure_kind']=='capability_gap'
    assert result['context_usage']['effort_budget']['model_calls']==3


def test_explicit_negative_text_request_is_not_a_gap():
    from geoagent_harness.capabilities.service import explicit_text_gap
    assert not explicit_text_gap('Inspect x.csv. Do not uppercase region.',[],{})
    assert explicit_text_gap('Inspect x.csv. Trim whitespace and uppercase region.',[],{})
    assert not explicit_text_gap('Inspect points.geojson. Uppercase region.',[],{})
    assert not explicit_text_gap('Inspect x.csv. Uppercase region.',[],{'ext_text':SimpleNamespace(text_transform=DEFINITION)})


def test_explicit_constraints_bind_only_supplied_simple_semantics():
    from geoagent_harness.capabilities.service import explicit_text_constraints
    assert explicit_text_constraints(REQUEST)==TextTransform.model_validate(DEFINITION)
    negative='Inspect x.csv. Do not strip whitespace. Uppercase region into a new region_clean column.'
    assert [step.kind for step in explicit_text_constraints(negative).steps]==['upper']
    assert explicit_text_constraints('Strip trailing whitespace and uppercase region into a new region_clean column.') is None
    assert explicit_text_constraints('Uppercase region into a new region_clean column then lowercase region.') is None


def test_explicit_complete_text_request_cannot_become_unneeded_clarification(project):
    configure(project)
    client=Client({'message':'Would you like me to prepare this capability?','plan':None},REPLY)
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message=REQUEST),project_root=project,model_client=client,critic_client=Client(CRITIC))
    assert result['capability_candidate']['status']=='tested' and len(client.requests)==2
    schema=client.requests[0].response_schema
    assert len(schema['anyOf'])==1
    assert schema['$defs']['TextTransform']['properties']['source_column']['const']=='region'
    assert schema['$defs']['TextTransform']['properties']['steps']['maxItems']==2


def test_package_limit_rejects_before_fixture_work(project,monkeypatch):
    from geoagent_harness.operations.packages import install_package
    sample=json.loads((Path(__file__).parents[1]/'examples/checkpoint25/order_identity.operation.json').read_text())
    directory=project/'operation-packages';directory.mkdir()
    for index in range(20):
        value={**sample,'id':f'ext_fixture_{index}'};package=parse_package(value)
        (directory/f'{package.id}.json').write_text(json.dumps({'package':package.model_dump(mode='json'),'package_sha256':package_sha(package)}))
    monkeypatch.setattr('geoagent_harness.operations.packages.test_package',lambda *a,**k:pytest.fail('No tests after the install limit'))
    package=make_package(CapabilityProposal.model_validate(PROPOSAL))
    with pytest.raises(PackageError,match='limit'):install_package(package.model_dump(mode='json'),package_sha(package),root=project,confirm=True)
    assert len(installed_packages(project))==20


def test_exact_installed_text_request_binds_csv_source_dependency_and_rejects_wrong_inspector(project):
    _,record=candidate(project);install(project,record)
    wrong={'message':'Wrong inspection','plan':{'summary':'Normalize','steps':[
        {'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect','arguments':{'path':'data/input/sample_orders.csv'}},
        {'step_id':'step_2','skill':record['operation_id'],'purpose':'Normalize','arguments':{'path':'data/input/sample_orders.csv','package_sha256':record['package_sha256']},'depends_on':['step_1']}]}}
    correct=copy.deepcopy(wrong);correct['plan']['steps'][0]['skill']='inspect_csv'
    client=Client(wrong,correct)
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=2,message=REQUEST),project_root=project,model_client=client,critic_client=Client())
    assert result['capability_candidate'] is None and len(client.requests)==2
    assert [step['skill'] for step in result['planner_result']['plan']['steps']]==['inspect_csv',record['operation_id']]
    schema=client.requests[0].response_schema
    steps=schema['$defs']['WorkflowPlan']['properties']['steps']['prefixItems']
    assert len(schema['anyOf'])==1
    assert steps[0]['properties']['skill']['const']=='inspect_csv'
    assert steps[0]['properties']['arguments']['properties']['path']['const']=='data/input/sample_orders.csv'
    assert 'depends_on' not in steps[0]['required']
    assert steps[1]['properties']['depends_on']['items']['const']=='step_1'
    assert result['context_usage']['effort_budget']['fixture_batches']==0
    assert not (project/'data/output').exists()


def test_candidate_preparation_preserves_a_preexisting_inspection(project):
    first=turn(project,Client({'message':'Inspect','plan':{'summary':'Inspect CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/sample_orders.csv','preview_rows':2}}]}}),'Inspect sample_orders.csv.')
    configure(project,revision=1)
    result=conversation_turn(TurnRequest(action='turn',conversation_id=ID,expected_revision=2,message=REQUEST),project_root=project,model_client=Client(REPLY),critic_client=Client(CRITIC))
    assert result['planner_result']==first['planner_result']
    assert not result['proposal_changed']
    assert result['capability_candidate']['source_revision']==3


def test_bounded_column_names_have_a_bounded_readable_package_name():
    proposal=CapabilityProposal(gap_reason='String normalization gap',definition={'source_column':'a'*100,'output_column':'b'*100,'steps':[{'kind':'upper'}]})
    package=make_package(proposal)
    assert len(package.name)==100 and package.text_transform.source_column=='a'*100
