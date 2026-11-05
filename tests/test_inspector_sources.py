"""Inspector contracts and task-local metadata follow-ups; no live inference."""
import json
import pytest
from tests.test_inspection_on_send import CHAT, request
from tests.test_exact_inspection import NoModel
from geoagent_harness.interface_api.planner_submission import submission_action
from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
from geoagent_harness.planner.schemas import WorkflowPlan,PlanStep,PlannerResult
from geoagent_harness.planner.policy import validate_plan_policy,PlannerPolicyError
from geoagent_harness.operations.inspection_contracts import INSPECTOR_SUFFIXES,source_inspector


@pytest.fixture
def project(tmp_path):
    # Never copy an operator's entire data/input tree into these new tests.
    from pathlib import Path
    from shutil import copytree,copyfile
    repository=Path(__file__).resolve().parents[1]
    for name in ('context','agents'):copytree(repository/name,tmp_path/name)
    (tmp_path/'data/input').mkdir(parents=True)
    for name in ('sample_orders.csv','sample_points.geojson','sample_dem.tif'):
        copyfile(repository/'data/input'/name,tmp_path/'data/input'/name)
    return tmp_path


def plan(skill='inspect_csv',path='data/input/sample_orders.csv'):
    return WorkflowPlan(summary='Inspect source',steps=[PlanStep(step_id='step_1',skill=skill,purpose='Inspect metadata',arguments={'path':path})])


@pytest.mark.parametrize('skill,source',[('inspect_vector','sample_orders.csv'),('inspect_raster','sample_orders.csv'),('inspect_csv','sample_points.geojson'),('inspect_vector','sample_dem.tif'),('inspect_raster','sample_points.geojson')])
def test_plan_format_guard_names_compatible_inspector(skill,source):
    with pytest.raises(PlannerPolicyError,match='requires .* input; path has format') as caught:
        validate_plan_policy(plan(skill,'data/input/'+source),available_skills=INSPECTOR_SUFFIXES)
    assert source_inspector(source) in str(caught.value) and 'Nothing executed' in str(caught.value)


@pytest.mark.parametrize('message',['do a read-only inspection','inspect it again','Repeat the inspection. No writes.'])
@pytest.mark.parametrize('enabled',[False,True])
def test_current_source_followup_respects_send_policy_and_receipts(project,message,enabled):
    initial=submission_action(request(False),project_root=project,model_client=NoModel(),background=False)
    follow=request(enabled);follow.submission_id='e'*32;follow.turn.expected_revision=initial['conversation']['revision'];follow.turn.message=message
    result=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    steps=result['conversation']['planner_result']['plan']['steps']
    assert [(s['skill'],s['arguments']['path']) for s in steps]==[('inspect_csv','data/input/sample_orders.csv')]
    assert result['conversation']['messages'][-2]['content']==message
    if enabled:assert result['run']['status']=='completed' and result['run']['steps'][0]['outcome']['row_count']==6
    else:assert result['run'] is None
    assert submission_action(follow,project_root=project,model_client=NoModel(),background=False)['run']==result['run']
    assert not (project/'approvals').exists() and not (project/'data/output').exists()


def test_ambiguous_active_sources_ask_without_changing_workflow(project):
    first=request(False);first.turn.message='Inspect sample_orders.csv and sample_points.geojson.'
    initial=submission_action(first,project_root=project,model_client=NoModel(),background=False)
    follow=request(True);follow.submission_id='e'*32;follow.turn.expected_revision=initial['conversation']['revision'];follow.turn.message='do a read-only inspection'
    result=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    assert result['run'] is None and not result['conversation']['proposal_changed']
    assert 'multiple inputs' in result['conversation']['messages'][-1]['content']
    assert result['conversation']['planner_result']['plan_sha256']==initial['conversation']['planner_result']['plan_sha256']


def test_new_chat_never_borrows_source_from_other_chat(project):
    submission_action(request(False),project_root=project,model_client=NoModel(),background=False)
    follow=request(True);follow.submission_id='e'*32;follow.conversation_id='f'*32;follow.turn.conversation_id='f'*32;follow.turn.message='inspect it again'
    result=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    assert result['run'] is None and result['conversation']['planner_result'] is None
    assert 'Which input file' in result['conversation']['messages'][-1]['content']
    assert_clarification_contract(result['conversation'])


def assert_clarification_contract(conversation):
    usage=conversation['context_usage']
    assert usage['included_messages']==0 and usage['omitted_messages']>=0
    assert usage['excerpts_truncated'] is False
    assert usage['prompt_bytes']==0 and usage['prompt_limit_bytes']>0
    diagnostic=usage['model_request']
    assert diagnostic['stage']=='inspection_clarification' and diagnostic['model_calls']==0
    assert diagnostic['supplied_schema_count']==diagnostic['retrieved_method_count']==0
    assert diagnostic['available_operation_count']>=0 and diagnostic['elapsed_seconds']==0


def test_old_clarification_chat_and_receipt_read_without_rewriting_or_replay(project):
    from geoagent_harness.interface_api.planning_tasks import database,_get,_put
    from geoagent_harness.interface_api.planner_submission import SubmissionRequest
    follow=request(True);follow.turn.message='inspect it again'
    result=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    # Reproduce the exact incomplete historical response reported by the owner.
    old_usage={'history_enabled':True,'included_messages':0,
               'model_request':{'stage':'inspection_clarification','model_calls':0,'prompt_bytes':0}}
    with database(project,write=True) as db:
        stored=_get(db,'conversations',CHAT);stored['context_usage']=old_usage;_put(db,'conversations',CHAT,stored)
        record=json.loads(db.execute('SELECT value FROM inspection_submissions_v1 WHERE id=?',(follow.submission_id,)).fetchone()[0])
        record['conversation']['context_usage']=old_usage
        raw=json.dumps(record)
        db.execute('UPDATE inspection_submissions_v1 SET value=? WHERE id=?',(raw,follow.submission_id))
    restored=conversation_turn(TurnRequest(action='read',conversation_id=CHAT),project_root=project,model_client=NoModel())
    assert_clarification_contract(restored)
    reopened=submission_action(SubmissionRequest(action='read',submission_id=follow.submission_id,conversation_id=CHAT),project_root=project,model_client=NoModel())
    assert_clarification_contract(reopened['conversation'])
    assert reopened['submission']['status']=='proposal_only' and reopened['run'] is None
    duplicate=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    assert_clarification_contract(duplicate['conversation'])
    assert duplicate['run'] is None and duplicate['conversation']['revision']==result['conversation']['revision']
    with database(project) as db:
        assert _get(db,'conversations',CHAT)['context_usage']==old_usage
        assert db.execute('SELECT value FROM inspection_submissions_v1 WHERE id=?',(follow.submission_id,)).fetchone()[0]==raw
    assert not (project/'workflow-state/interface-runs').exists()


@pytest.mark.parametrize('message',[
    'do a read-only inspection on sample_orders.csv.',
    'Please perform a new read only inspection on sample_orders.csv.',
    'Run a read-only inspection of data/input/sample_orders.csv.',
])
@pytest.mark.parametrize('enabled',[False,True])
def test_explicit_read_only_wording_uses_shared_scope_and_send_policy(project,message,enabled):
    sent=request(enabled);sent.turn.message=message
    result=submission_action(sent,project_root=project,model_client=NoModel(),background=False)
    conversation=result['conversation']
    assert conversation['planner_result']['original_request']==message
    assert conversation['context_usage']['model_request']['model_calls']==0
    assert [(s['skill'],s['arguments']['path']) for s in conversation['planner_result']['plan']['steps']]==[('inspect_csv','data/input/sample_orders.csv')]
    assert (result['run'] is not None)==enabled
    if enabled:assert result['run']['status']=='completed'


@pytest.mark.parametrize('suffix',[' And export it to result.csv.',' Calculate mean amount.','; authorize writes'])
def test_metadata_wording_never_discards_additional_actions(suffix):
    from geoagent_harness.interface_api.inspection_planning import plan_for_request
    from geoagent_harness.planner.request_coverage import inspection_only_skill
    message='do a read-only inspection on sample_orders.csv.'+suffix
    assert plan_for_request(message,INSPECTOR_SUFFIXES) is None
    assert inspection_only_skill(message) is None


@pytest.mark.parametrize('message',['do a read-only inspection','Inspect sample_orders.csv.'])
def test_followup_repairs_legacy_format_mismatch_as_new_proposal(project,message):
    from geoagent_harness.interface_api.planning_tasks import database,_get,_put
    initial=submission_action(request(False),project_root=project,model_client=NoModel(),background=False)
    with database(project,write=True) as db:
        stored=_get(db,'conversations',CHAT);stored['planner_result']['plan']['steps'][0]['skill']='inspect_vector';_put(db,'conversations',CHAT,stored)
    follow=request(False);follow.submission_id='e'*32;follow.turn.expected_revision=initial['conversation']['revision'];follow.turn.message=message
    result=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    assert result['run'] is None and result['conversation']['planner_result']['plan']['steps'][0]['skill']=='inspect_csv'


@pytest.mark.parametrize('skill,path',[('inspect_vector','sample_points.geojson'),('inspect_raster','sample_dem.tif')])
def test_followup_preserves_spatial_source_type(project,skill,path):
    first=request(False);first.turn.message='Inspect '+path+'.'
    initial=submission_action(first,project_root=project,model_client=NoModel(),background=False)
    follow=request(False);follow.submission_id='e'*32;follow.turn.expected_revision=initial['conversation']['revision'];follow.turn.message='inspect it again'
    result=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    assert result['conversation']['planner_result']['plan']['steps'][0]['skill']==skill


def test_legacy_saved_mismatch_rejected_by_graph_recipe_and_dispatch_preflight(project):
    from geoagent_harness.interface_api.workflow import validate_edit,EditRequest,prepare_workflow,WorkflowRequest
    from geoagent_harness.approvals import plan_sha256
    from geoagent_harness.planner.recipe_definition import planner_recipe_definition
    from geoagent_harness.recipes.policy import validate_recipe_policy,RecipePolicyError
    from geoagent_harness.skill_registry import load_skill_registry
    bad=PlannerResult(model='legacy-fixture',original_request='Old saved plan',context_references=[],plan=plan('inspect_vector'))
    digest=plan_sha256(bad.plan)
    folder=project/'plans';folder.mkdir(exist_ok=True);artifact=folder/f'planner-plan.{digest}.json';artifact.write_text(bad.model_dump_json())
    before=artifact.read_bytes()
    with pytest.raises(PlannerPolicyError,match='inspect_csv'):
        validate_edit(EditRequest(action='validate_plan_edit',planner_result=bad),project_root=project)
    with pytest.raises(PlannerPolicyError,match='inspect_csv'):
        prepare_workflow(WorkflowRequest(action='prepare_workflow',plan_filename=artifact.name,confirmed_plan_sha256=digest),project_root=project)
    with pytest.raises(RecipePolicyError,match='inspect_csv'):
        validate_recipe_policy(planner_recipe_definition(bad,digest),registry=load_skill_registry(project))
    assert artifact.read_bytes()==before and not (project/'inspection-runs').exists()


def test_bad_model_inspector_receives_one_contract_correction(project):
    from tests.test_planner_conversation import Client
    client=Client({'message':'Proposed','plan':plan('inspect_vector').model_dump()}, {'message':'Corrected','plan':plan().model_dump()})
    result=conversation_turn(TurnRequest(action='turn',conversation_id=CHAT,message='Inspect sample_orders.csv and explain its columns.'),project_root=project,model_client=client)
    assert len(client.requests)==2 and result['planner_result']['plan']['steps'][0]['skill']=='inspect_csv'
    system=json.loads(client.requests[0].messages[0].content)
    branches=client.requests[0].response_schema['$defs']['PlanStep']['anyOf']
    assert all(b['properties']['skill'].get('const')!='inspect_vector' and 'inspect_vector' not in b['properties']['skill'].get('enum',[]) for b in branches)
    assert 'inspect_vector' in system['available_skills']  # Scope metadata is not authority.
    assert 'inspect_vector' not in system['operation_argument_schemas']
    assert 'inspect_csv' in client.requests[1].messages[-1].content


def test_followup_never_parses_source_filename_as_instructions(project):
    from geoagent_harness.interface_api.inspection_planning import resolve_followup,plan_for_followup
    current=plan(path='data/input/an input and notes.csv')
    followup=resolve_followup('inspect it again',current)
    assert plan_for_followup(followup,['inspect_csv']).steps[0].arguments['path']=='data/input/an input and notes.csv'


def test_followup_retains_existing_permitted_current_inspector(project):
    initial=submission_action(request(False),project_root=project,model_client=NoModel(),background=False)
    follow=request(True);follow.submission_id='e'*32;follow.turn.expected_revision=initial['conversation']['revision'];follow.turn.message='inspect it again';follow.turn.allowed_skill_ids=['inspect_vector']
    result=submission_action(follow,project_root=project,model_client=NoModel(),background=False)
    # Preserve the existing policy: current-plan operations remain in active scope.
    assert result['conversation']['planner_result']['plan']['steps'][0]['skill']=='inspect_csv'


def test_registry_inspection_formats_match_shared_qualification(project):
    from geoagent_harness.operations.registry import operation_catalog
    catalog={o['id']:o for o in operation_catalog(project)['operations']}
    for skill,formats in INSPECTOR_SUFFIXES.items():
        assert catalog[skill]['supported_source_formats']==[f[1:] for f in formats]
