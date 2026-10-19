"""Automatic successful records use real temp fixtures, never LLMs/live services."""
import json
from copy import deepcopy

import pytest
from typer.testing import CliRunner

from tests.test_reusable_recipes_and_runs import project, use, execution
from geoagent_harness.recipe_catalog import successful as saved
from geoagent_harness.recipe_catalog.composition import compose, RecipeRequest, recipe_action
from geoagent_harness.interface_api.workflow_runs import RunRequest, run_action
from geoagent_harness.cli import app


def execute(project, *, inspection=False, target='cleaned'):
    request=use(project, 'recipe_inspect_csv', path='data/input/orders.csv') if inspection else use(project)
    if not inspection:
        request.parameters.update(selected_path=f'data/output/{target}_selected.csv', target_path=f'data/output/{target}.csv')
    result,_=compose([request],project)
    return run_action(RunRequest(action='start',workflow=execution(project,result)),project_root=project,background=False)


def test_retention_is_automatic_private_metadata_without_model_calls(project,monkeypatch):
    from geoagent_harness.model import SharedModelClient
    monkeypatch.setattr(SharedModelClient,'complete',lambda *args:pytest.fail('Retention must not call a model'))
    record=execute(project)
    assert record['status']=='completed' and record['successful_recipe']['status']=='saved'
    methods=saved.inventory(project)
    assert len(methods)==1 and methods[0]['tags']==['cleaning','csv','workflow']
    assert len(methods[0]['operations'])==2
    assert methods[0]['sources'][0]['run_id']==record['run_id']
    text=json.dumps(methods)
    for private in ['data/input/orders.csv','data/output/cleaned.csv','Unknown','fill_values','approval_filename','authority_sha256','arguments','preview']:
        assert private not in text
    assert methods[0]['execution_authority_granted'] is False
    assert saved.inventory(project,conversation_id='a'*32)==[]
    assert saved.inventory(project,query='inspection')==[]
    assert saved.inventory(project,query='csv')==methods
    response=recipe_action(RecipeRequest(action='list',query='csv'),project_root=project)
    assert response['successful_records']==methods


def test_inspection_success_stays_metadata_and_dedup_is_idempotent(project):
    first=execute(project,inspection=True)
    assert first['successful_recipe']['status']=='saved'
    again=run_action(RunRequest(action='retain',run_id=first['run_id']),project_root=project)
    assert again['successful_recipe']==first['successful_recipe']
    second=execute(project,inspection=True)
    methods=saved.inventory(project)
    assert len(methods)==1 and len(methods[0]['sources'])==2
    assert first['run_id']!=second['run_id']
    assert methods[0]['operations'][0]['outputs']==['inspection_metadata']
    assert 'inspection' in methods[0]['tags']
    # Reopening in another process performs no execution and uses persisted metadata.
    result=CliRunner().invoke(app,['reusable-recipes','--project-root',str(project)])
    assert result.exit_code==0,result.output
    assert len(json.loads(result.output)['successful_records'][0]['sources'])==2


@pytest.mark.parametrize('status',['failed','cancelled','interrupted','validation_failed','running'])
def test_stopped_or_incomplete_runs_are_never_successful(project,status):
    record=execute(project)
    record['run_id']='a'*32
    record['status']=status
    assert saved.retain(project,record)['status']=='not_eligible'
    assert len(saved.inventory(project)[0]['sources'])==1


@pytest.mark.parametrize('damage',['validation','skipped','missing_outcome','missing_step'])
def test_missing_step_or_validation_evidence_rejects(project,damage):
    record=execute(project)
    record['run_id']='a'*32
    if damage=='validation':record['steps'][-1]['validation_outcome']={'passed':False}
    if damage=='skipped':record['steps'][-1]['status']='skipped'
    if damage=='missing_outcome':record['steps'][-1]['outcome']=None
    if damage=='missing_step':record['steps'].pop()
    assert saved.retain(project,record)['status']=='not_eligible'


def test_recording_failure_does_not_change_execution_and_retry_only_indexes(project,monkeypatch):
    real=saved.retain
    monkeypatch.setattr(saved,'retain',lambda *args:(_ for _ in ()).throw(OSError('private storage message')))
    record=execute(project)
    assert record['status']=='completed'
    assert record['successful_recipe']['status']=='unavailable'
    assert 'private storage message' not in json.dumps(record['successful_recipe'])
    before=(project/'data/output/cleaned.csv').read_bytes()
    monkeypatch.setattr(saved,'retain',real)
    # The operation executor must never be called by retry indexing.
    import geoagent_harness.interface_api.workflow as service
    monkeypatch.setattr(service,'execute_workflow',lambda *a,**k:pytest.fail('Indexing cannot execute'))
    retried=run_action(RunRequest(action='retain',run_id=record['run_id']),project_root=project)
    assert retried['successful_recipe']['status']=='saved'
    assert before==(project/'data/output/cleaned.csv').read_bytes()


def test_method_dedup_preserves_semantic_differences_and_source_evidence(project):
    first=execute(project,target='first')
    second=execute(project,target='second')
    assert first['retention_basis']['method_id']==second['retention_basis']['method_id']
    assert len(saved.inventory(project))==1
    assert len(saved.inventory(project)[0]['sources'])==2
    steps=[{'step_id':s['step_id'],'skill':s['skill_id'],'arguments':deepcopy(s['arguments']),'depends_on':s['depends_on']} for s in first['steps']]
    steps[-1]['arguments']['fill_values']['region']='Elsewhere'
    assert saved.capture_basis(project,steps)['method_id']!=first['retention_basis']['method_id']
    changed=deepcopy(first)
    changed['steps'][0]['outcome']['row_count']=999
    with pytest.raises(ValueError,match='evidence changed'):
        saved.retain(project,changed)


def test_contract_change_is_visible_without_relabelling_success(project,monkeypatch):
    execute(project)
    original=saved.contracts
    def changed(root):
        result=original(root)
        result['select_csv_columns']['contract_sha256']='f'*64
        return result
    monkeypatch.setattr(saved,'contracts',changed)
    assert saved.inventory(project)[0]['contract_status']=='changed_or_unavailable'


def test_other_chat_records_are_not_pooled_and_limits_fail_soft(project,monkeypatch):
    record=execute(project)
    other=deepcopy(record);other.update(run_id='b'*32,conversation_id='b'*32)
    saved.retain(project,other)
    assert len(saved.inventory(project)[0]['sources'])==1
    assert len(saved.inventory(project,conversation_id='b'*32)[0]['sources'])==1
    assert saved.inventory(project,conversation_id='c'*32)==[]
    monkeypatch.setattr(saved,'MAX_RECORDS',2)
    extra=deepcopy(record);extra['run_id']='c'*32
    with pytest.raises(ValueError,match='inventory is full'):
        saved.retain(project,extra)


def test_missing_snapshot_and_unsafe_storage_do_not_imply_success(project,tmp_path):
    record=execute(project)
    record['retention_basis']=None
    assert saved.retain(project,record)['status']=='unavailable'
    other=tmp_path/'unsafe';other.mkdir()
    (other/'workflow-state').symlink_to(project/'workflow-state',target_is_directory=True)
    with pytest.raises(ValueError,match='unsafe'):
        saved.inventory(other)


def test_spatial_inspection_is_retained_without_csv_claims(project):
    from geoagent_harness.planner.schemas import PlannerResult
    result=PlannerResult(model='fixture',original_request='Inspect vector only',context_references=[],plan={'summary':'Inspect vector','steps':[{'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect','arguments':{'path':'data/input/points.geojson'},'requires_approval':False,'validation_required':False}]})
    record=run_action(RunRequest(action='start',workflow=execution(project,result)),project_root=project,background=False)
    assert record['successful_recipe']['status']=='saved'
    method=saved.inventory(project)[0]
    assert 'geospatial' in method['tags'] and 'inspection' in method['tags']
    assert method['operations'][0]['outputs']==['inspection_metadata']
    assert list((project/'data/output').iterdir())==[]


def test_contract_capture_failure_is_fail_soft_and_does_not_fake_historical_version(project,monkeypatch):
    monkeypatch.setattr(saved,'capture_basis',lambda *args:(_ for _ in ()).throw(ValueError('contract unavailable')))
    record=execute(project)
    assert record['status']=='completed'
    assert record['successful_recipe']['status']=='unavailable'
    assert saved.inventory(project)==[]


def test_corrupt_index_does_not_hide_other_recipe_templates(project):
    execute(project)
    (project/'workflow-state/successful-workflows.sqlite3').write_bytes(b'not a sqlite database')
    response=recipe_action(RecipeRequest(action='list'),project_root=project)
    assert response['recipes'] and response['successful_records']==[]
    assert 'unavailable' in response['successful_records_finding']


def test_critic_timeout_does_not_block_automatic_retention(project,monkeypatch):
    from geoagent_harness.model import SharedModelClient
    monkeypatch.setenv('MODEL_NAME','offline-fixture')
    monkeypatch.setenv('MODEL_BASE_URL','http://127.0.0.1:1/v1')
    monkeypatch.setattr(SharedModelClient,'complete',lambda *args:(_ for _ in ()).throw(TimeoutError('fixture timeout')))
    plan,_=compose([use(project)],project)
    record=run_action(RunRequest(action='start',workflow=execution(project,plan),review_outcome=True),project_root=project,background=False)
    assert record['status']=='completed' and record['successful_recipe']['status']=='saved'
    assert record['critic_review']['status']=='unavailable'
    assert len(saved.inventory(project))==1


def test_separate_cli_process_reopens_persisted_records_without_execution(project):
    import subprocess,sys
    record=execute(project)
    before=(project/'data/output/cleaned.csv').read_bytes()
    script="from typer.testing import CliRunner; from geoagent_harness.cli import app; import sys; r=CliRunner().invoke(app,['reusable-recipes','--project-root',sys.argv[1]]); print(r.output); assert r.exit_code==0"
    result=subprocess.run([sys.executable,'-c',script,str(project)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['successful_records'][0]['sources'][0]['run_id']==record['run_id']
    assert before==(project/'data/output/cleaned.csv').read_bytes()
