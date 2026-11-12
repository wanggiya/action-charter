"""Natural-language orchestration owns mechanics, never execution authority."""
import json

import pytest

from tests.test_reusable_recipes_and_runs import project, use, execution, Model
from geoagent_harness.task_actions import recipe_catalog as recipes
from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action, _directory, _read, _write
from geoagent_harness.task_actions.run_assessment import assess_run, evidence, review_conversation_run
from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
from geoagent_harness.data.tabular.bindings import allocate_csv_outputs, refresh_automatic_targets
from geoagent_harness.platform.model_gateway.client import ModelClientError


def run(project):
    plan,_=recipes.compose([use(project)],project)
    record=run_action(RunRequest(action='start',workflow=execution(project,plan)),project_root=project,background=False)
    return plan,record


def assessment(record,**changes):
    return {'deterministic_status':record['status'],'conclusion':'supported','summary':'The recorded CSV operations completed with passing validation.',
            'findings':[],'limitations':['Synthetic observations do not establish suitability for other datasets.'],'reusable_method':None,**changes}


def test_compose_omitted_csv_targets_is_shared_and_creates_no_files(project):
    item=use(project)
    del item.parameters['selected_path'];del item.parameters['target_path']
    result=recipes.recipe_action(recipes.RecipeRequest(action='compose',uses=[item]),project_root=project)
    paths=[s['arguments']['target_path'] for s in result['plan']['steps']]
    assert len(set(paths))==2 and all(p.startswith('data/output/result_') for p in paths)
    assert not list((project/'data/output').iterdir())
    assert not (project/'approvals').exists()
    del item.parameters['columns']
    with pytest.raises(ValueError,match='parameters'):
        recipes.compose([item],project)


def test_automatic_targets_preserve_explicit_scope_and_refresh_occupied_auto_paths(project):
    plan,_=recipes.compose([use(project)],project)
    assert allocate_csv_outputs(plan.plan)==[]
    del plan.plan.steps[0].arguments['target_path']
    assert allocate_csv_outputs(plan.plan)==['step_1']
    old=plan.model_copy(deep=True)
    target=plan.plan.steps[0].arguments['target_path']
    (project/target).write_text('occupied\n')
    plan.plan.summary='Revised objective'
    assert refresh_automatic_targets(plan.plan,old,project)==['step_1']
    assert plan.plan.steps[0].arguments['target_path']!=target
    assert plan.plan.steps[1].arguments['target_path']=='data/output/cleaned.csv'
    assert (project/target).read_text()=='occupied\n'


def test_critic_summary_is_cached_and_never_reexecutes(project):
    _,record=run(project)
    model=Model(assessment(record,reusable_method={'title':'Clean columns','purpose':'Select columns and fill missing cells.',
        'operations':['select_csv_columns','handle_csv_missing'],'limitations':['Requires explicit column names and replacement values.']}))
    result=assess_run(project,record['run_id'],model_client=model)
    assert result['critic_review']['status']=='complete'
    assert result['critic_review']['assessment']['deterministic_status']=='completed'
    assert result['status']=='completed'
    assert assess_run(project,record['run_id'],model_client=model)==result
    assert len(model.calls)==1
    assert model.calls[0].timeout_seconds==15 and model.calls[0].response_schema
    assert len(list(_directory(project).glob('*.json')))==1
    source=json.loads(model.calls[0].messages[1].content)
    assert source['evidence_kind']=='recorded_run_observations'
    assert all('preview' not in step['metadata'] and 'arguments' not in step for step in source['steps'])


@pytest.mark.parametrize('kind',['timeout','schema','false_status','invented_operation'])
def test_critic_failure_never_changes_execution_or_retries(project,kind):
    _,record=run(project)
    class Failing:
        calls=0
        def complete(self,request):
            self.calls+=1
            if kind=='timeout':raise ModelClientError.timeout()
            from geoagent_harness.platform.model_gateway.schemas import ModelResult
            value={} if kind=='schema' else assessment(record,deterministic_status='failed') if kind=='false_status' else assessment(record,reusable_method={
                'title':'Invented','purpose':'Unavailable method','operations':['arbitrary_python'],'limitations':['Unverified.']})
            return ModelResult(model='fixture',content=json.dumps(value))
    model=Failing()
    result=assess_run(project,record['run_id'],model_client=model)
    assert result['status']=='completed' and result['critic_review']['status']=='unavailable'
    assess_run(project,record['run_id'],model_client=model)
    assert model.calls==1
    assert (project/'data/output/cleaned.csv').exists()


def test_stopped_run_cannot_be_reported_as_supported_or_reusable(project):
    _,record=run(project)
    record.update(status='cancelled',result=None)
    _write(_directory(project),record)
    result=assess_run(project,record['run_id'],model_client=Model(assessment(record)))
    assert result['critic_review']['status']=='unavailable'
    assert result['status']=='cancelled'


def test_interrupted_critic_read_never_makes_a_model_call(project):
    _,record=run(project)
    record['critic_review']={'status':'running','source_sha256':'0'*64}
    _write(_directory(project),record)
    reopened=_read(_directory(project),record['run_id'])
    assert reopened['critic_review']['status']=='unavailable'
    assert reopened['status']=='completed'


def test_chat_outcome_context_requires_own_matching_run(project):
    plan,record=run(project)
    model=Model()
    assert 'No execution is recorded' in review_conversation_run(project,'a'*32,plan,model_client=model)
    assert not model.calls
    record['conversation_id']='a'*32
    _write(_directory(project),record)
    model=Model(assessment(record))
    assert 'Recorded run status: completed' in review_conversation_run(project,'a'*32,plan,model_client=model)
    assert len(model.calls)==1
    other=Model()
    assert 'No execution is recorded' in review_conversation_run(project,'b'*32,plan,model_client=other)
    assert not other.calls


def test_critic_discards_assessment_if_evidence_changes(project):
    _,record=run(project)
    class Changing(Model):
        def complete(self,request):
            latest=_read(_directory(project),record['run_id'])
            latest['steps'][0]['status']='failed'
            _write(_directory(project),latest)
            return super().complete(request)
    result=assess_run(project,record['run_id'],model_client=Changing(assessment(record)))
    assert result['critic_review']['status']=='unavailable'
    assert 'discarded' in result['critic_review']['finding']


def test_planner_recipe_schema_feedback_is_bounded(project):
    from geoagent_harness.agents.roles.planner.recipe_authoring import prepare_recipe
    plan,_=recipes.compose([use(project)],project)
    candidate=recipes.catalog(project)['recipe_clean_csv'].model_dump(mode='json')
    author=Model({},candidate)
    critic=Model({'conclusion':'supported','findings':[],'limitations':['One synthetic fixture only.']})
    result=prepare_recipe(plan,project,model_client=author,critic_client=critic)
    assert result['test_report']['status']=='fixture_verified' and len(author.calls)==2
    feedback=json.loads(author.calls[1].messages[-1].content)
    assert feedback['findings']


def test_backend_reviews_enabled_runs_without_browser_or_execution_lease(project,monkeypatch):
    from geoagent_harness.task_actions import run_assessment
    from geoagent_harness.task_actions.workflow_runs import _lease
    from geoagent_harness.platform.model_gateway.schemas import ModelResult
    import os
    calls=[]
    class Critic:
        def complete(self,request):
            fd=_lease(_directory(project))  # No operation lease is held during inference.
            os.close(fd)
            calls.append(request)
            source=json.loads(request.messages[1].content)
            return ModelResult(model='fixture',content=json.dumps(assessment({'status':source['deterministic_status']})))
    monkeypatch.setenv('MODEL_NAME','fixture')
    monkeypatch.setattr(run_assessment,'SharedModelClient',lambda settings:Critic())
    plan,_=recipes.compose([use(project)],project)
    record=run_action(RunRequest(action='start',workflow=execution(project,plan),review_outcome=True),project_root=project,background=False)
    assert record['status']=='completed' and record['critic_review']['status']=='complete'
    assert len(calls)==1
    run_action(RunRequest(action='read',run_id=record['run_id']),project_root=project)
    assert len(calls)==1


def test_execution_only_links_matching_conversation_scope(project):
    plan,_=recipes.compose([use(project)],project)
    identity='c'*32
    conversation_turn(TurnRequest(action='bind_task_plan',conversation_id=identity,task_id=identity,current_plan=plan),project_root=project)
    request=execution(project,plan)
    record=run_action(RunRequest(action='start',workflow=request,conversation_id=identity),project_root=project,background=False)
    assert record['conversation_id']==identity
    record['critic_review']={'status':'queued'}
    record['finished_at']='2000-01-01T00:00:00+00:00'
    _write(_directory(project),record)
    loaded=_read(_directory(project),record['run_id'])
    assert loaded['critic_review']['status']=='unavailable'


def test_only_explicit_critic_retry_repeats_inference_not_operations(project):
    _,record=run(project)
    bad=Model({})
    assert assess_run(project,record['run_id'],model_client=bad)['critic_review']['status']=='unavailable'
    good=Model(assessment(record))
    assess_run(project,record['run_id'],model_client=good)
    assert not good.calls
    result=assess_run(project,record['run_id'],model_client=good,retry=True)
    assert result['critic_review']['status']=='complete' and len(good.calls)==1
    assert len(list(_directory(project).glob('*.json')))==1



def test_critic_annotation_enriches_own_success_without_changing_baseline(project):
    from geoagent_harness.capabilities.recipes.catalog import successful
    _,record=run(project)
    before=successful.inventory(project)[0]
    model=Model(assessment(record,reusable_method={'title':'Clean columns','purpose':'Select and fill missing values.',
        'operations':['select_csv_columns','handle_csv_missing'],'limitations':['Only observed fixture bindings were validated.']}))
    reviewed=assess_run(project,record['run_id'],model_client=model)
    assert reviewed['critic_review']['annotation_status']=='saved'
    after=successful.inventory(project)[0]
    annotation=after.pop('critic_annotation')
    assert after==before
    assert annotation['run_id']==record['run_id'] and annotation['execution_authority_granted'] is False
    assert annotation['evidence_kind']=='model_annotation_not_validation'
    assert successful.inventory(project,conversation_id='a'*32)==[]
    from geoagent_harness.capabilities.recipes.retrieval import retrieve
    snippets,_=retrieve(project,None,'clean csv',{'select_csv_columns','handle_csv_missing'})
    assert snippets[0]['advisory_method_note']['execution_authority_granted'] is False
    assert snippets[0]['advisory_method_note']['evidence_kind']=='model_annotation_not_validation'
    changed=json.loads(json.dumps(reviewed))
    changed['steps'][0]['outcome']['output']['path']='data/output/different.csv'
    assert successful.annotate(project,changed)=='not_eligible'
    assert assess_run(project,record['run_id'],model_client=model)==reviewed and len(model.calls)==1


def test_critic_annotation_index_failure_preserves_assessment_and_baseline(project,monkeypatch):
    from geoagent_harness.capabilities.recipes.catalog import successful
    _,record=run(project)
    before=successful.inventory(project)
    monkeypatch.setattr(successful,'annotate',lambda *args:(_ for _ in ()).throw(OSError('sensitive storage message')))
    result=assess_run(project,record['run_id'],model_client=Model(assessment(record)))
    assert result['status']=='completed' and result['critic_review']['status']=='complete'
    assert result['critic_review']['annotation_status']=='unavailable'
    assert 'sensitive storage message' not in json.dumps(result)
    assert successful.inventory(project)==before


def test_selected_vector_export_includes_its_declared_inspection_dependency(project):
    from pathlib import Path
    from shutil import copytree
    copytree(Path(__file__).parents[1]/'context',project/'context',dirs_exist_ok=True)
    from geoagent_harness.capabilities.registry.registry import planning_dependencies
    assert planning_dependencies(['vector_attributes_to_csv','aggregate_csv'],project)==['vector_attributes_to_csv','aggregate_csv','inspect_vector']
    plan={'summary':'Inspect, extract attributes and aggregate regions','assumptions':[],'steps':[
        {'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect the source','arguments':{'path':'data/input/points.geojson'},'requires_approval':False,'validation_required':False,'expected_artifacts':[]},
        {'step_id':'step_2','skill':'vector_attributes_to_csv','purpose':'Extract attributes without geometry','arguments':{'path':'data/input/points.geojson','target_path':'data/output/attributes.csv'},'requires_approval':True,'validation_required':True,'expected_artifacts':[],'depends_on':['step_1']},
        {'step_id':'step_3','skill':'aggregate_csv','purpose':'Sum amount by region','arguments':{'source_step':'step_2','target_path':'data/output/totals.csv','by':['region'],'aggregations':[{'column':'amount','function':'sum','output_column':'total_amount'}]},'requires_approval':True,'validation_required':True,'expected_artifacts':[],'depends_on':['step_2']}]}
    model=Model({'message':'Proposed inspected attribute export and aggregation.','plan':plan})
    reply=conversation_turn(TurnRequest(action='turn',conversation_id='d'*32,message='Extract points.geojson attributes and group amount by region.',allowed_skill_ids=['vector_attributes_to_csv','aggregate_csv']),project_root=project,model_client=model)
    assert reply['planner_result'] is not None
    assert 'inspect_vector' in reply['allowed_skill_ids']
    system=json.loads(model.calls[0].messages[0].content)
    assert system['source_reference_checks']['existing_supplied_paths']==['data/input/points.geojson']
    assert not system['source_reference_checks']['content_inspected']
    assert not reply['execution_performed'] and not reply['approval_performed']
    assert not list((project/'data/output').iterdir())



def test_planner_input_grounding_checks_only_supplied_safe_references(project,tmp_path):
    from geoagent_harness.task_actions.conversation import _input_references
    secret=tmp_path/'outside.csv';secret.write_text('private')
    (project/'data/input/linked.csv').symlink_to(secret)
    result=_input_references('Inspect points.geojson, linked.csv, ../../outside.csv and missing.csv.',project)
    assert result['existing_supplied_paths']==['data/input/points.geojson']
    assert result['content_inspected'] is False and result['execution_authority_granted'] is False



def test_explicit_inspection_cannot_be_silently_omitted_from_a_transform_proposal():
    from types import SimpleNamespace
    from geoagent_harness.agents.roles.planner.request_coverage import validate_calculation_coverage, RequestedOperationOmission
    plan=SimpleNamespace(steps=[SimpleNamespace(skill='calculate_csv_columns')])
    with pytest.raises(RequestedOperationOmission,match='inspect_csv'):
        validate_calculation_coverage(plan,'Inspect orders.csv, then calculate doubled = amount * 2.')
    validate_calculation_coverage(plan,'Do not inspect orders.csv. Calculate doubled = amount * 2.')



def test_repeated_source_path_question_receives_one_bounded_correction(project):
    from pathlib import Path
    from shutil import copytree
    copytree(Path(__file__).parents[1]/'context',project/'context',dirs_exist_ok=True)
    reply={'message':'Proposed inspection.','plan':{'summary':'Inspect orders','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Read metadata','arguments':{'path':'data/input/orders.csv'},'requires_approval':False,'validation_required':False,'expected_artifacts':[]}]}}
    model=Model({'message':'Which file should I inspect?','plan':None},reply)
    result=conversation_turn(TurnRequest(action='turn',conversation_id='f'*32,message='Inspect orders.csv. No writes.',allowed_skill_ids=['inspect_csv']),project_root=project,model_client=model)
    assert len(model.calls)==2 and result['planner_result'] is not None
    assert 'already supplied' in json.loads(model.calls[1].messages[-1].content)['deterministic_findings'][0]
    assert not result['execution_performed'] and not result['approval_performed']


def test_occupied_model_csv_target_is_corrected_before_review_without_overwrite(project):
    from pathlib import Path
    from shutil import copytree
    from copy import deepcopy
    copytree(Path(__file__).parents[1]/'context',project/'context',dirs_exist_ok=True)
    occupied=project/'data/output/existing.csv';occupied.write_text('keep this exact content')
    reply={'message':'Proposed projection.','plan':{'summary':'Select region and amount','steps':[{'step_id':'step_1','skill':'select_csv_columns','purpose':'Select the requested columns','arguments':{'path':'data/input/orders.csv','columns':['region','amount'],'target_path':'data/output/existing.csv'},'requires_approval':True,'validation_required':True,'expected_artifacts':[]}]}}
    corrected=deepcopy(reply);corrected['plan']['steps'][0]['arguments'].pop('target_path')
    model=Model(reply,corrected)
    result=conversation_turn(TurnRequest(action='turn',conversation_id='e'*32,message='Select region and amount from orders.csv into a fresh CSV.',allowed_skill_ids=['select_csv_columns']),project_root=project,model_client=model)
    assert len(model.calls)==2
    assert result['planner_result']['plan']['steps'][0]['arguments']['target_path'].startswith('data/output/result_')
    assert occupied.read_text()=='keep this exact content'
    assert len(list((project/'data/output').iterdir()))==1
    assert not result['execution_performed'] and not result['approval_performed']


@pytest.mark.parametrize('failure',['timeout','invalid'])
def test_review_diagnostics_are_critic_and_preserve_durable_execution(project,failure):
    import httpx
    from geoagent_harness.platform.model_gateway.client import SharedModelClient
    from geoagent_harness.platform.model_settings import ModelSettings
    from geoagent_harness.platform.model_gateway.telemetry import scope, read
    from geoagent_harness.platform.model_gateway.catalog import select_review_timeout, ReviewTimeoutSelection
    _,record=run(project)
    before_outputs={p.name:p.read_bytes() for p in (project/'data/output').glob('*.csv')}
    select_review_timeout(project,ReviewTimeoutSelection(seconds=30,expected_revision=0))
    calls=[]
    def handler(request):
        calls.append(request)
        if failure=='timeout':raise httpx.ReadTimeout('private provider detail',request=request)
        return httpx.Response(200,json={'model':'fixture','choices':[{'message':{'content':'{}'},'finish_reason':'stop'}]})
    model=SharedModelClient(ModelSettings(base_url='http://localhost:11434/v1',model='fixture',timeout_seconds=60,max_tokens=1024),transport=httpx.MockTransport(handler))
    identity='f'*32
    with scope(project,identity) as diagnostic:
        diagnostic['record']['workflow_run_id']=record['run_id']
        reviewed=assess_run(project,record['run_id'],model_client=model)
    assert reviewed['status']=='completed' and reviewed['steps']==record['steps']
    assert reviewed['critic_review']['status']=='unavailable'
    assert reviewed['critic_review']['timeout_seconds']==30
    if failure=='timeout':assert reviewed['critic_review']['error_code']=='model_timeout'
    assert assess_run(project,record['run_id'],model_client=model)==reviewed and len(calls)==1
    assert {p.name:p.read_bytes() for p in (project/'data/output').glob('*.csv')}==before_outputs
    records=read(project,identity)['records'];call=next(r for r in records if r['kind']=='call')
    assert (call['role'],call['phase'],call['workflow_run_id'],call['timeout_seconds'])==('critic','outcome_review',record['run_id'],30)
    assert 'private provider detail' not in json.dumps(records)


@pytest.mark.parametrize('execution_fails',[False,True])
def test_worker_keeps_execution_status_separate_from_review_timeout(project,monkeypatch,execution_fails):
    import os,httpx
    from geoagent_harness.task_actions import workflow_runs, workflow, run_assessment
    from geoagent_harness.platform.model_gateway.client import SharedModelClient
    from geoagent_harness.platform.model_settings import ModelSettings
    from geoagent_harness.platform.model_gateway.telemetry import read
    _,record=run(project)
    record['conversation_id']='e'*32
    _write(_directory(project),record)
    calls=[]
    def execute(*a,**kw):
        calls.append('execution')
        if execution_fails:raise ValueError('Synthetic operation failure')
        return record['result']
    def timeout(request):
        calls.append('review');raise httpx.ReadTimeout('private',request=request)
    settings=ModelSettings(base_url='http://localhost:11434/v1',model='fixture',timeout_seconds=60,max_tokens=1024)
    model=SharedModelClient(settings,transport=httpx.MockTransport(timeout))
    monkeypatch.setattr(workflow,'execute_workflow',execute)
    monkeypatch.setattr(run_assessment,'load_model_settings',lambda:settings)
    monkeypatch.setattr(run_assessment,'SharedModelClient',lambda settings:model)
    fd=os.open(project/'worker-test.lock',os.O_CREAT|os.O_RDWR,0o600)
    workflow_runs._worker(project,_directory(project),record['run_id'],object(),fd,review_outcome=True)
    final=_read(_directory(project),record['run_id'])
    assert final['status']==('failed' if execution_fails else 'completed')
    assert final['critic_review']['status']=='unavailable'
    assert calls==['execution','review']
    diagnostics=read(project,'e'*32)['records']
    turn=next(r for r in diagnostics if r['kind']=='turn')
    assert turn['workflow_status']==final['status'] and turn['outcome_review']['error_code']=='model_timeout'
    assert set(turn['outcome_review'])=={'status','error_code','timeout_seconds'}
    call=next(r for r in diagnostics if r['kind']=='call')
    assert (call['role'],call['phase'])==('critic','outcome_review')
