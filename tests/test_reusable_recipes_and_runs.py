"""Reusable subworkflows and safe run lifecycle use real temporary CSV data."""
import json
from pathlib import Path
from shutil import copyfile, copytree
from threading import Event

import pytest
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import WorkflowRequest, prepare_workflow, authorize_workflow
from geoagent_harness.interface_api.workflow_runs import RunRequest, run_action
from geoagent_harness.recipe_catalog import composition as recipes
from geoagent_harness.planner.recipe_authoring import prepare_recipe
from geoagent_harness.model.schemas import ModelResult

REPO=Path(__file__).parents[1]


@pytest.fixture
def project(tmp_path,monkeypatch):
    (tmp_path/'context').mkdir()
    copyfile(REPO/'context/SKILLS_INDEX.yaml',tmp_path/'context/SKILLS_INDEX.yaml')
    copytree(REPO/'agents',tmp_path/'agents')
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/output').mkdir()
    (tmp_path/'data/input/orders.csv').write_text('region,amount,unused\nNorth,10,x\n,20,y\n')
    copyfile(REPO/'data/input/sample_points.geojson',tmp_path/'data/input/points.geojson')
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    return tmp_path


def use(project,id='recipe_clean_csv',alias='clean',**parameters):
    recipe=recipes.catalog(project)[id]
    if id=='recipe_clean_csv' and not parameters:
        parameters={'source':'data/input/orders.csv','columns':['region','amount'],'fill_values':{'region':'Unknown'},'selected_path':'data/output/selected.csv','target_path':'data/output/cleaned.csv'}
    return recipes.RecipeUse(recipe_id=id,recipe_sha256=recipes.recipe_digest(recipe),alias=alias,parameters=parameters)


def execution(project,result,authorize=True):
    stored=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=result,
        confirmed_plan_sha256=plan_sha256(result.plan),allowed_skill_ids=list({s.skill for s in result.plan.steps})),project_root=project)
    base=WorkflowRequest(action='prepare_workflow',plan_filename=stored['plan_filename'],confirmed_plan_sha256=stored['plan_sha256'])
    review=prepare_workflow(base,project_root=project)
    auth={}
    if authorize and review['approval_required_step_ids']:
        auth=authorize_workflow(WorkflowRequest(**{**base.model_dump(),'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],
            'approve_required_steps':True,'approver':'isolated-test','reason':'Temporary fixture outputs only'}),project_root=project)
    return WorkflowRequest(**{**base.model_dump(),'action':'execute_workflow','confirm_execution':True,'confirmed_review_sha256':review['review_sha256'],
        'plan_approval_filename':auth.get('plan_approval_filename'),'recipe_approval_filename':auth.get('recipe_approval_filename')})


def test_builtin_fixtures_are_real_and_do_not_touch_project_data(project):
    before=list((project/'data/output').iterdir())
    for recipe in recipes.catalog(project).values():
        if recipe.tests:
            assert recipes.test_recipe(recipe,project)['status']=='fixture_verified'
    assert list((project/'data/output').iterdir())==before
    assert not (project/'approvals').exists()


def test_shipped_composition_example_matches_current_hashes(project):
    request=recipes.RecipeRequest.model_validate_json((REPO/'examples/recipe-composition/spatial_csv_request.json').read_text())
    request.uses[0].parameters['path']='data/input/points.geojson'
    result=recipes.recipe_action(request,project_root=project)
    assert len(result['plan']['steps'])==4
    assert result['plan']['steps'][2]['arguments']['source_step']=='step_2'
    assert not result['execution_performed'] and not result['approval_performed']


def test_composition_checks_contracts_and_remaps_dependencies(project):
    first=use(project,'recipe_vector_attributes','attributes',path='data/input/points.geojson',target_path='data/output/attributes.csv')
    second=use(project)
    second.parameters.update(source={'recipe_output':'attributes'},columns=['name'],fill_values={'name':'Unknown'})
    plan,groups=recipes.compose([first,second],project)
    assert len(plan.plan.steps)==4
    assert plan.plan.steps[2].arguments['source_step']=='step_2'
    assert plan.plan.steps[3].arguments['source_step']=='step_3'
    assert plan.plan.steps[2].depends_on==['step_2']
    assert groups[1]['step_ids']==['step_3','step_4']
    assert all(s.requires_approval for s in plan.plan.steps[1:])
    assert 'sha256=' in plan.plan.assumptions[0]
    run=run_action(RunRequest(action='start',workflow=execution(project,plan)),project_root=project,background=False)
    assert run['status']=='completed'
    assert (project/'data/output/cleaned.csv').read_text()=='name\nBoston Common\nDowntown Crossing\n'
    assert all(s['validation_outcome']['passed'] for s in run['steps'][1:])


def test_metadata_cannot_be_connected_as_a_csv_artifact(project):
    first=use(project,'recipe_inspect_csv','metadata',path='data/input/orders.csv')
    second=use(project)
    second.parameters['source']={'recipe_output':'metadata'}
    with pytest.raises(ValueError,match='CSV artifact'):
        recipes.compose([first,second],project)


def test_literal_step_references_cannot_silently_bind_another_recipe(project):
    definition=recipes.catalog(project)['recipe_clean_csv'].model_dump(mode='json')
    definition['steps'][1]['arguments']['source_step']='step_1'
    with pytest.raises(ValueError,match='local'):
        recipes.ReusableRecipe.model_validate(definition)


def test_append_preserves_base_scope_and_remaps_local_references(project):
    base,_=recipes.compose([use(project,'recipe_inspect_csv',path='data/input/orders.csv')],project)
    base.plan.risks=['Fixture risk']
    base.context_references=['README.md']
    base.warnings=['Fixture warning']
    result,_=recipes.compose([use(project)],project,base=base)
    assert result.plan.steps[0]==base.plan.steps[0]
    assert result.plan.steps[2].arguments['source_step']=='step_2'
    assert result.plan.risks==base.plan.risks and result.warnings==base.warnings
    assert result.context_references==base.context_references


@pytest.mark.parametrize('change',['digest','missing','extra','type','unsafe','collision','alias'])
def test_invalid_bindings_never_become_plans(project,change):
    item=use(project)
    items=[item]
    if change=='digest':item.recipe_sha256='0'*64
    elif change=='missing':del item.parameters['columns']
    elif change=='extra':item.parameters['shell']='anything'
    elif change=='type':item.parameters['columns']='region'
    elif change=='unsafe':item.parameters['source']='../private.csv'
    elif change=='collision':item.parameters['selected_path']=item.parameters['target_path']
    else:items=[item,item]
    with pytest.raises((ValueError,RuntimeError)):
        recipes.compose(items,project)
    assert not list((project/'data/output').iterdir())


def test_registration_retests_exact_definition_and_survives_reload(project):
    definition=recipes.catalog(project)['recipe_clean_csv'].model_copy(deep=True)
    definition.id='recipe_fixture_clean'
    digest=recipes.recipe_digest(definition)
    with pytest.raises(ValueError,match='Confirm'):
        recipes.recipe_action(recipes.RecipeRequest(action='register',definition=definition),project_root=project)
    result=recipes.recipe_action(recipes.RecipeRequest(action='register',definition=definition,confirmed_recipe_sha256=digest,confirm_register=True),project_root=project)
    assert result['registered'] and not result['execution_performed']
    assert recipes.recipe_digest(recipes.catalog(project)[definition.id])==digest
    assert not list((project/'data/output').iterdir())
    request=definition.model_copy(deep=True)
    request.tests[0].expected_csv['data/output/cleaned.csv']='wrong\n'
    with pytest.raises(ValueError,match='differs'):
        recipes.test_recipe(request,project)
    path=project/'reusable-recipes'/f'{definition.id}.json'
    record=json.loads(path.read_text())
    record['operation_contracts_sha256']='0'*64
    path.write_text(json.dumps(record))
    assert definition.id not in recipes.catalog(project)
    inventory=recipes.recipe_action(recipes.RecipeRequest(action='list'),project_root=project)
    assert inventory['unavailable'][0]['id']==definition.id
    assert 'contracts changed' in inventory['unavailable'][0]['finding']
    assert 'recipe_inspect_csv' in recipes.catalog(project)  # unrelated planning stays usable


def test_registration_rejects_symlink_and_database_fixture(project):
    definition=recipes.catalog(project)['recipe_clean_csv'].model_copy(deep=True)
    definition.steps[0].skill='load_vector_to_postgis'
    with pytest.raises(ValueError,match='isolated'):
        recipes.test_recipe(definition,project)
    (project/'reusable-recipes').symlink_to(project/'data/input',target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):
        recipes.catalog(project)


def test_actual_run_has_intermediate_previews_and_durable_result(project):
    plan,_=recipes.compose([use(project)],project)
    run=run_action(RunRequest(action='start',workflow=execution(project,plan)),project_root=project,background=False)
    assert run['status']=='completed'
    assert [s['status'] for s in run['steps']]==['validated_success']*2
    assert run['steps'][0]['outcome']['row_count']==2
    assert run['steps'][0]['validation_outcome']['passed']
    assert (project/'data/output/cleaned.csv').read_text()=='region,amount\nNorth,10\nUnknown,20\n'
    loaded=run_action(RunRequest(action='read',run_id=run['run_id']),project_root=project)
    assert loaded==run
    inventory=run_action(RunRequest(action='list'),project_root=project)
    assert inventory['records'][0]['result'] is None
    assert inventory['records'][0]['steps'][0]['outcome'] is None
    assert inventory['records'][0]['source_paths']==['data/input/orders.csv']
    assert all(step['arguments']=={} and step['validation_outcome'] is None for step in inventory['records'][0]['steps'])


def test_progress_stays_active_until_final_state_is_durable(project,monkeypatch):
    original=api._persist_execution_progress
    observed=[]
    def persist(root,state,**kwargs):
        if state['status']=='validated_success':
            assert state['execution_preview_sha256'] in api._ACTIVE_PROGRESS
            observed.append(state['execution_preview_sha256'])
        return original(root,state,**kwargs)
    monkeypatch.setattr(api,'_persist_execution_progress',persist)
    plan,_=recipes.compose([use(project)],project)
    record=run_action(RunRequest(action='start',workflow=execution(project,plan)),project_root=project,background=False)
    assert record['status']=='completed' and len(observed)==1
    assert observed[0] not in api._ACTIVE_PROGRESS


def test_missing_authority_records_failure_without_writes(project):
    plan,_=recipes.compose([use(project)],project)
    run=run_action(RunRequest(action='start',workflow=execution(project,plan,authorize=False)),project_root=project,background=False)
    assert run['status']=='failed' and not run['execution_performed']
    assert not list((project/'data/output').iterdir())


def test_cancellation_finishes_current_validation_and_skips_next_write(project,monkeypatch):
    from geoagent_harness.interface_api import workflow_runs
    original=workflow_runs._Observer.progress
    def cancel_after_first(self,step,skill,status,outcome=None,validation=None):
        original(self,step,skill,status,outcome,validation)
        if step=='step_1' and status=='validated_success':
            run_action(RunRequest(action='cancel',run_id=self.identity),project_root=project)
    monkeypatch.setattr(workflow_runs._Observer,'progress',cancel_after_first)
    plan,_=recipes.compose([use(project)],project)
    request=execution(project,plan)
    run=run_action(RunRequest(action='start',workflow=request),project_root=project,background=False)
    assert run['status']=='cancelled'
    assert run['steps'][0]['status']=='validated_success' and run['steps'][0]['validation_outcome']['passed']
    assert run['steps'][1]['status']=='skipped'
    assert (project/'data/output/selected.csv').exists() and not (project/'data/output/cleaned.csv').exists()
    with pytest.raises(api.InterfaceApiError,match='already has an attempt'):
        run_action(RunRequest(action='start',workflow=request.model_copy(update={'reason':'changed irrelevant field'})),project_root=project,background=False)
    recovery=run_action(RunRequest(action='recover',run_id=run['run_id']),project_root=project)
    targets=[s['arguments']['target_path'] for s in recovery['plan']['steps']]
    assert all('_retry_' in p for p in targets)
    assert not recovery['approval_performed'] and not recovery['execution_performed']
    monkeypatch.setattr(workflow_runs._Observer,'progress',original)
    from geoagent_harness.planner.schemas import PlannerResult
    recovered=PlannerResult(**{k:recovery[k] for k in ('agent_id','model','original_request','context_references','plan','warnings')})
    fresh=run_action(RunRequest(action='start',workflow=execution(project,recovered)),project_root=project,background=False)
    assert fresh['status']=='completed'
    assert (project/'data/output/selected.csv').exists()


def test_active_verifier_is_not_aborted_and_concurrent_run_is_blocked(project,monkeypatch):
    from geoagent_harness.recipes import runner
    entered,release=Event(),Event()
    original=runner.validate_tabular_output
    def blocked(*args,**kwargs):
        entered.set()
        assert release.wait(10)
        return original(*args,**kwargs)
    monkeypatch.setattr(runner,'validate_tabular_output',blocked)
    plan,_=recipes.compose([use(project)],project)
    request=execution(project,plan)
    run=run_action(RunRequest(action='start',workflow=request),project_root=project)
    try:
        assert entered.wait(5)
        with pytest.raises(api.InterfaceApiError,match='already active'):
            run_action(RunRequest(action='start',workflow=request),project_root=project)
        cancelled=run_action(RunRequest(action='cancel',run_id=run['run_id']),project_root=project)
        assert cancelled['status']=='cancelling'
    finally:
        release.set()
    # The worker lease is released only after final durable state is stored.
    import time
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        current=run_action(RunRequest(action='read',run_id=run['run_id']),project_root=project)
        if current['status']=='cancelled':break
        time.sleep(.01)
    assert current['status']=='cancelled'
    assert current['steps'][0]['validation_outcome']['passed']
    assert current['steps'][1]['status']=='skipped'


def test_restart_marks_orphan_interrupted_without_replaying(project):
    from geoagent_harness.interface_api.workflow_runs import _write,_directory
    plan,_=recipes.compose([use(project,'recipe_inspect_csv',path='data/input/orders.csv')],project)
    record=run_action(RunRequest(action='start',workflow=execution(project,plan)),project_root=project,background=False)
    record.update(status='running',finished_at=None,result=None)
    record['steps'][0]['status']='running'
    _write(_directory(project),record)
    reopened=run_action(RunRequest(action='read',run_id=record['run_id']),project_root=project)
    assert reopened['status']=='interrupted' and reopened['failed_step_id']=='step_1'
    assert len(list((project/'inspection-runs').glob('*.json')))==1
    assert not list((project/'data/output').iterdir())


def test_read_only_resume_excludes_completed_steps(project):
    from geoagent_harness.interface_api.workflow_runs import _write,_directory
    from geoagent_harness.planner.schemas import PlanStep
    plan,_=recipes.compose([use(project,'recipe_inspect_csv',path='data/input/orders.csv')],project)
    plan.plan.steps.append(PlanStep(step_id='step_2',skill='inspect_csv',purpose='Inspect again for fixture',arguments={'path':'data/input/orders.csv'},depends_on=['step_1']))
    record=run_action(RunRequest(action='start',workflow=execution(project,plan)),project_root=project,background=False)
    record.update(status='interrupted',result=None)
    record['steps'][1]['status']='interrupted'
    _write(_directory(project),record)
    recovered=run_action(RunRequest(action='recover',run_id=record['run_id']),project_root=project)
    assert len(recovered['plan']['steps'])==1
    assert recovered['plan']['steps'][0]['step_id']=='step_1'
    assert recovered['plan']['steps'][0]['depends_on']==[]
    assert not recovered['execution_performed'] and not recovered['approval_performed']


def test_cancelled_inspection_remains_readable_in_existing_history(project,monkeypatch):
    from geoagent_harness.interface_api import workflow_runs
    from geoagent_harness.interface_api.workflow import inspection_inventory
    from geoagent_harness.planner.schemas import PlanStep
    original=workflow_runs._Observer.progress
    def cancel_first(self,step,skill,status,outcome=None,validation=None):
        original(self,step,skill,status,outcome,validation)
        if step=='step_1' and status=='completed':
            run_action(RunRequest(action='cancel',run_id=self.identity),project_root=project)
    monkeypatch.setattr(workflow_runs._Observer,'progress',cancel_first)
    plan,_=recipes.compose([use(project,'recipe_inspect_csv',path='data/input/orders.csv')],project)
    plan.plan.steps.append(PlanStep(step_id='step_2',skill='inspect_csv',purpose='Inspect again',arguments={'path':'data/input/orders.csv'},depends_on=['step_1']))
    run=run_action(RunRequest(action='start',workflow=execution(project,plan)),project_root=project,background=False)
    assert run['status']=='cancelled' and run['steps'][1]['status']=='skipped'
    records=inspection_inventory(project_root=project)['records']
    assert records[0]['status']=='cancelled' and len(records[0]['step_results'])==1
    assert not (project/'approvals').exists()


def test_http_routes_and_origin_guard(project):
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from threading import Thread
    server=ThreadingHTTPServer(('127.0.0.1',0),api._handler(project))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        for path in ('/api/v1/reusable-recipes','/api/v1/workflow/runs'):
            connection=HTTPConnection('127.0.0.1',server.server_port)
            connection.request('POST',path,json.dumps({'action':'list'}),{'Content-Type':'application/json'})
            response=connection.getresponse()
            assert response.status==200
            assert not json.loads(response.read())['execution_performed']
            connection.close()
            connection=HTTPConnection('127.0.0.1',server.server_port)
            connection.request('POST',path,json.dumps({'action':'list'}),{'Content-Type':'application/json','Origin':'https://untrusted.invalid'})
            response=connection.getresponse()
            assert response.status==403
            response.read();connection.close()
    finally:
        server.shutdown();server.server_close()


def test_expired_authority_cannot_start_a_later_write(project,monkeypatch):
    from geoagent_harness.recipes import runner
    from geoagent_harness.recipes.execution import RecipeExecutionPolicyError
    plan,_=recipes.compose([use(project)],project)
    request=execution(project,plan)
    original=runner.build_recipe_execution_envelope
    calls=[]
    def expires(**kwargs):
        calls.append(1)
        if len(calls)>1:raise RecipeExecutionPolicyError('expired')
        return original(**kwargs)
    monkeypatch.setattr(runner,'build_recipe_execution_envelope',expires)
    record=run_action(RunRequest(action='start',workflow=request),project_root=project,background=False)
    assert record['status']=='failed'
    assert not list((project/'data/output').iterdir())


class Model:
    def __init__(self,*values):self.values=list(values);self.calls=[]
    def complete(self,request):
        self.calls.append(request)
        return ModelResult(model='fixture',content=json.dumps(self.values.pop(0)))


def test_planner_authors_and_critic_reviews_without_builder_or_registration(project):
    plan,_=recipes.compose([use(project)],project)
    candidate=recipes.catalog(project)['recipe_clean_csv'].model_dump(mode='json')
    candidate['id']='recipe_generated_clean'
    from shutil import rmtree
    rmtree(project/'agents/builder')  # The normal recipe path does not depend on this role.
    planner=Model(candidate)
    critic=Model({'conclusion':'supported','findings':[],'limitations':['One synthetic fixture does not prove suitability for every CSV.']})
    result=prepare_recipe(plan,project,model_client=planner,critic_client=critic)
    assert result['test_report']['status']=='fixture_verified'
    assert result['critic']['conclusion']=='supported' and not result['registered']
    assert len(planner.calls)==1 and len(critic.calls)==1
    assert json.loads(planner.calls[0].messages[0].content)['agent']['id']=='planner'
    assert not (project/'reusable-recipes').exists() and not list((project/'data/output').iterdir())


def test_cli_catalog_and_run_inventory_share_services(project):
    cli=CliRunner()
    result=cli.invoke(app,['reusable-recipes','--project-root',str(project)])
    assert result.exit_code==0
    assert len(json.loads(result.stdout)['recipes'])==3
    result=cli.invoke(app,['workflow-runs','--project-root',str(project)])
    assert result.exit_code==0 and json.loads(result.stdout)['records']==[]


def test_run_inventory_source_labels_are_bounded_safe_local_paths():
    from geoagent_harness.interface_api.workflow_runs import _source_paths
    record={'steps':[{'arguments':{'path':value,'password':'not-an-inventory-field'}} for value in [
        'data/input/orders.csv','data/input/orders.csv','data/output/intermediate.csv',
        '/etc/passwd','data/input/../secret','data/input//bad.csv','data/input/bad\\name.csv',
        'data/input/bad\nname.csv','https://example.invalid/file.csv','data/input/'+('x'*960)]]}
    assert _source_paths(record)==['data/input/orders.csv','data/output/intermediate.csv']
    assert len(_source_paths({'steps':[{'arguments':{'path':f'data/input/{i}.csv'}} for i in range(30)]}))==20
