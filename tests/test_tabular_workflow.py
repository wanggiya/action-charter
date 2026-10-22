"""Checkpoint 24: bounded pandas pipelines reuse exact workflow authority/evidence."""
import json
from pathlib import Path
from shutil import copyfile
import pytest
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.approvals import plan_sha256
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import EditRequest, WorkflowRequest, validate_edit, prepare_workflow, authorize_workflow, execute_workflow
from geoagent_harness.tabular.service import TabularError, inspect_csv, run_operation, read_frame, validate_output
from geoagent_harness.mcp_server.settings import load_settings

REPO=Path(__file__).parents[1]
@pytest.fixture
def project(tmp_path,monkeypatch):
    (tmp_path/'context').mkdir();copyfile(REPO/'context/SKILLS_INDEX.yaml',tmp_path/'context/SKILLS_INDEX.yaml')
    (tmp_path/'data/input').mkdir(parents=True);(tmp_path/'data/output').mkdir()
    for name in ['sample_orders.csv','sample_regions.csv','sample_points.geojson']:copyfile(REPO/'data/input'/name,tmp_path/'data/input'/name)
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('ENABLE_WRITE_TOOLS','true');monkeypatch.setenv('ALLOW_OVERWRITE','false')
    return tmp_path

def pipeline():
    definitions=[
        ('inspect_csv',{'path':'data/input/sample_orders.csv'}),
        ('select_csv_columns',{'path':'data/input/sample_orders.csv','columns':['order_id','region','amount'],'target_path':'data/output/selected.csv'}),
        ('handle_csv_missing',{'source_step':'step_2','method':'fill','fill_values':{'region':'unknown','amount':0},'target_path':'data/output/filled.csv'}),
        ('filter_csv_rows',{'source_step':'step_3','predicates':[{'column':'amount','operator':'ge','value':10,'value_type':'number'}],'target_path':'data/output/filtered.csv'}),
        ('join_csv',{'source_step':'step_4','right_path':'data/input/sample_regions.csv','keys':['region'],'how':'left','cardinality':'many_to_one','target_path':'data/output/joined.csv'}),
        ('aggregate_csv',{'source_step':'step_5','by':['region_name'],'aggregations':[{'column':'amount','function':'sum','output_column':'total'},{'column':'order_id','function':'count','output_column':'orders'}],'target_path':'data/output/grouped.csv'}),
        ('export_csv',{'source_step':'step_6','target_path':'data/output/final.csv'}),
    ]
    return PlannerResult(model='fixture',original_request='Produce regional totals through explicit table operations',context_references=[],plan={'summary':'Regional CSV totals','steps':[{'step_id':f'step_{i}','skill':skill,'purpose':skill,'arguments':args,'requires_approval':skill!='inspect_csv','validation_required':skill!='inspect_csv'} for i,(skill,args) in enumerate(definitions,1)]})

def saved(project,result):
    validated=validate_edit(EditRequest(action='validate_plan_edit',planner_result=result),project_root=project)
    record=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=result,confirmed_plan_sha256=validated['plan_sha256'],allowed_skill_ids=validated['allowed_skill_ids']),project_root=project)
    return WorkflowRequest(action='prepare_workflow',plan_filename=record['plan_filename'],confirmed_plan_sha256=record['plan_sha256'])

def run(project,proposal):
    request=saved(project,proposal);review=prepare_workflow(request,project_root=project)
    approval=authorize_workflow(WorkflowRequest(**{**request.model_dump(),'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Exact temporary CSV scope'}),project_root=project)
    assert not list((project/'data/output').iterdir())
    result=execute_workflow(WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,'plan_approval_filename':approval['plan_approval_filename'],'recipe_approval_filename':approval['recipe_approval_filename']}),project_root=project)
    return result

def test_all_operations_pipeline_exact_results_and_lineage(project):
    result=run(project,pipeline())
    assert result['status']=='validated_success'
    final=read_frame((project/'data/output/final.csv').read_bytes())
    assert final.to_dict(orient='records')==[{'region_name':'North region','total':'30','orders':'2'},{'region_name':'South region','total':'40','orders':'1'},{'region_name':'Unknown region','total':'30','orders':'1'}]
    assert len(result['step_results'])==7
    assert all(step['validation_outcome']['passed'] for step in result['step_results'][1:])
    evidence=json.loads(Path(result['evidence_path']).read_text())
    assert len(evidence['lineage'])==7 # each single-input transform plus the two-input join
    assert len({a['artifact_id'] for a in evidence['artifacts']})==len(evidence['artifacts'])

def test_inspection_preserves_ids_missing_semantics_and_bounded_preview(project):
    result=inspect_csv('sample_orders.csv',load_settings(),preview_rows=2)
    assert result['row_count']==6 and len(result['preview'])==2
    assert result['preview'][0]['order_id']=='001'
    assert result['missing_counts']['amount']==1
    assert not list((project/'data/output').iterdir())
    (project/'data/input/markers.csv').write_text('code,value\nNA,NULL\n001,\n')
    marker=inspect_csv('markers.csv',load_settings())
    assert marker['preview'][0]=={'code':'NA','value':'NULL'}
    assert marker['preview'][1]['value'] is None

def test_inspection_execution_needs_no_fabricated_approval(project):
    result=pipeline();result.plan.steps=result.plan.steps[:1]
    request=saved(project,result);review=prepare_workflow(request,project_root=project)
    assert review['approval_required_step_ids']==[]
    run=execute_workflow(WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True}),project_root=project)
    assert run['step_results'][0]['outcome']['row_count']==6
    assert not (project/'approvals').exists()

@pytest.mark.parametrize('content',['a,a\n1,2\n','a,b\n1,2,3\n','a\n'+('x'*5000)+'\n'])
def test_bad_csv_bounds_reject_without_writes(project,content):
    (project/'data/input/bad.csv').write_text(content)
    with pytest.raises(TabularError):inspect_csv('bad.csv',load_settings())
    assert not list((project/'data/output').iterdir())

@pytest.mark.parametrize('change',['cycle','wrong_contract','outside','expression','same_output'])
def test_invalid_plan_contracts_reject_before_approval(project,change):
    result=pipeline()
    if change=='cycle':result.plan.steps[1].depends_on=['step_7']
    elif change=='wrong_contract':result.plan.steps[2].arguments['source_step']='step_1'
    elif change=='outside':result.plan.steps[1].arguments['path']='data/output/arbitrary.csv'
    elif change=='expression':result.plan.steps[3].arguments['expression']='arbitrary pandas query'
    else:result.plan.steps[-1].arguments['target_path']='data/output/grouped.csv'
    with pytest.raises((ValueError,RuntimeError)):saved(project,result)
    assert not list((project/'data/output').iterdir())

def test_write_mode_symlinks_and_collision_prohibited(project,monkeypatch):
    args={'path':'sample_orders.csv','columns':['order_id'],'target_path':'data/output/ids.csv'}
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','false')
    with pytest.raises(TabularError,match='disabled'):run_operation('select_csv_columns',args,load_settings())
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    outcome=run_operation('select_csv_columns',args,load_settings())
    assert validate_output(outcome,load_settings())['passed']
    with pytest.raises(TabularError,match='exists'):run_operation('select_csv_columns',args,load_settings())
    (project/'data/input/link.csv').symlink_to(project/'data/input/sample_orders.csv')
    with pytest.raises(TabularError):inspect_csv('link.csv',load_settings())
    (project/'data/output/ids.csv').write_text('order_id\nforged\n')
    assert not validate_output(outcome,load_settings())['passed']

def test_cli_inspect_and_typed_plan_share_service(project):
    runner=CliRunner()
    inspected=runner.invoke(app,['inspect-csv','sample_orders.csv','--project-root',str(project),'--preview-rows','1'])
    assert inspected.exit_code==0,inspected.output
    assert json.loads(inspected.output)['row_count']==6
    config=project/'request.json';config.write_text(pipeline().plan.model_dump_json())
    planned=runner.invoke(app,['workflow-plan',str(config),'--project-root',str(project)])
    assert planned.exit_code==0,planned.output
    payload=json.loads(planned.output)
    assert not payload['approval_performed'] and not payload['execution_performed']
    assert not list((project/'data/output').iterdir())


def test_mixed_geojson_attributes_to_tabular_workflow(project):
    proposal=PlannerResult(model='fixture',original_request='Inspect vector, extract scalar attributes and select/export names',context_references=[],plan={'summary':'Compatible spatial to tabular workflow','steps':[
        {'step_id':'step_1','skill':'inspect_vector','purpose':'Inspect public vector','arguments':{'path':'data/input/sample_points.geojson'}},
        {'step_id':'step_2','skill':'vector_attributes_to_csv','purpose':'Export scalar attributes without geometry','arguments':{'path':'data/input/sample_points.geojson','target_path':'data/output/attributes.csv'},'requires_approval':True,'validation_required':True},
        {'step_id':'step_3','skill':'select_csv_columns','purpose':'Select names','arguments':{'source_step':'step_2','columns':['name'],'target_path':'data/output/names.csv'},'requires_approval':True,'validation_required':True},
        {'step_id':'step_4','skill':'export_csv','purpose':'Export names','arguments':{'source_step':'step_3','target_path':'data/output/names_final.csv'},'requires_approval':True,'validation_required':True},
    ]})
    result=run(project,proposal)
    assert result['status']=='validated_success'
    expected=json.loads((project/'data/input/sample_points.geojson').read_text())
    assert read_frame((project/'data/output/names_final.csv').read_bytes())['name'].tolist()==[feature['properties']['name'] for feature in expected['features']]
    assert 'geometry' not in read_frame((project/'data/output/attributes.csv').read_bytes()).columns


def test_join_declared_cardinality_rejects_before_publication(project):
    (project/'data/input/duplicate.csv').write_text('region,lookup\nnorth,a\nnorth,b\n')
    args={'path':'sample_orders.csv','right_path':'duplicate.csv','keys':['region'],'cardinality':'many_to_one','target_path':'data/output/invalid.csv'}
    # Missing keys must be handled explicitly before any join.
    with pytest.raises(TabularError):run_operation('join_csv',args,load_settings())
    assert not (project/'data/output/invalid.csv').exists()
    (project/'data/input/left.csv').write_text('region,amount\nnorth,10\n')
    args['path']='left.csv'
    with pytest.raises(TabularError,match='cardinality'):run_operation('join_csv',args,load_settings())
    assert not (project/'data/output/invalid.csv').exists()


def test_pending_intermediate_digest_and_nonancestor_references_fail_closed(project):
    from types import SimpleNamespace
    original=run_operation('select_csv_columns',{'path':'sample_orders.csv','columns':['order_id'],'target_path':'data/output/first.csv'},load_settings())
    prior=SimpleNamespace(validation_performed=True,validation_result={'passed':True},execution=SimpleNamespace(result=original))
    (project/'data/output/first.csv').write_text('order_id\nchanged\n')
    with pytest.raises(TabularError,match='digest'):run_operation('export_csv',{'source_step':'step_1','target_path':'data/output/second.csv'},load_settings(),{'step_1':prior})
    assert not (project/'data/output/second.csv').exists()
    with pytest.raises(TabularError,match='ancestor'):run_operation('export_csv',{'source_step':'step_1','target_path':'data/output/second.csv'},load_settings())


def test_cli_full_journey_uses_exact_review_authority_and_shared_results(project):
    runner=CliRunner();config=project/'request.json';config.write_text(pipeline().plan.model_dump_json())
    planned=runner.invoke(app,['workflow-plan',str(config),'--project-root',str(project)])
    record=json.loads(planned.output)['saved'];name=record['plan_filename'];sha=record['plan_sha256']
    reviewed=runner.invoke(app,['workflow-review',name,'--plan-sha',sha,'--project-root',str(project)])
    assert reviewed.exit_code==0,reviewed.output
    review=json.loads(reviewed.output)
    base=[name,'--plan-sha',sha,'--review-sha',review['review_sha256'],'--project-root',str(project)]
    unauthorized=runner.invoke(app,['workflow-execute',*base,'--confirm-execution'])
    assert unauthorized.exit_code==2 and not list((project/'data/output').iterdir())
    approved=runner.invoke(app,['workflow-authorize',*base,'--approver','fixture','--reason','Exact CSV scope'])
    assert approved.exit_code==0,approved.output
    authority=json.loads(approved.output)
    executed=runner.invoke(app,['workflow-execute',*base,'--confirm-execution','--plan-approval',authority['plan_approval_filename'],'--recipe-approval',authority['recipe_approval_filename']])
    assert executed.exit_code==0,executed.output
    assert json.loads(executed.output)['status']=='validated_success'
    assert len(read_frame((project/'data/output/final.csv').read_bytes()))==3

def test_serialized_attribute_bounds_fail_before_output_publication(project):
    (project/'data/input/large.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':None,'properties':{'name':'x'*5000}}]}))
    with pytest.raises(TabularError):
        run_operation('vector_attributes_to_csv',{'path':'large.geojson','target_path':'data/output/bad.csv'},load_settings())
    assert not list((project/'data/output').iterdir())


def test_missing_drop_tsv_any_filter_and_numeric_rejection(project):
    (project/'data/input/table.tsv').write_text('id\tamount\n001\t5\n002\t\n003\t20\n')
    dropped=run_operation('handle_csv_missing',{'path':'table.tsv','delimiter':'\t','method':'drop_rows','columns':['amount'],'target_path':'data/output/drop.csv'},load_settings())
    assert dropped['row_count']==2 and dropped['preview'][0]['id']=='001'
    filtered=run_operation('filter_csv_rows',{'path':'table.tsv','delimiter':'\t','match':'any','predicates':[{'column':'amount','operator':'is_missing'},{'column':'amount','operator':'gt','value':10,'value_type':'number'}],'target_path':'data/output/any.csv'},load_settings())
    assert [r['id'] for r in filtered['preview']]==['002','003']
    (project/'data/input/bad_numbers.csv').write_text('group,value\na,text\n')
    with pytest.raises(TabularError,match='non-numeric'):
        run_operation('aggregate_csv',{'path':'bad_numbers.csv','by':['group'],'aggregations':[{'column':'value','function':'sum','output_column':'total'}],'target_path':'data/output/bad.csv'},load_settings())
    assert not (project/'data/output/bad.csv').exists()


def test_late_failure_reports_completed_work_and_partial_csv_outputs(project):
    proposal=pipeline()
    proposal.plan.steps[3].arguments['predicates'][0]['column']='unknown_column'
    request=saved(project,proposal);review=prepare_workflow(request,project_root=project)
    authorization=authorize_workflow(WorkflowRequest(**{**request.model_dump(),'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Temporary failure recovery test'}),project_root=project)
    with pytest.raises((RuntimeError,ValueError)):
        execute_workflow(WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True,'plan_approval_filename':authorization['plan_approval_filename'],'recipe_approval_filename':authorization['recipe_approval_filename']}),project_root=project)
    states=[json.loads(p.read_text()) for p in (project/'workflow-state/interface-executions').glob('*.json')]
    assert len(states)==1
    state=states[0]
    assert state['status']=='failed' and state['failed_step_id']=='step_4'
    assert state['execution_performed'] is True
    assert {item['path'] for item in state['partial_outputs']}=={'data/output/selected.csv','data/output/filled.csv'}
    assert 'fresh target paths' in state['recovery_guidance']
    assert not (project/'data/output/final.csv').exists()


def test_explicit_null_source_defaults_and_numeric_overflow(project):
    proposal=pipeline()
    proposal.plan.steps[2].arguments['path']=None
    proposal.plan.steps[4].arguments['right_step']=None
    result=run(project,proposal)
    assert result['status']=='validated_success'
    (project/'data/input/overflow.csv').write_text('group,value\na,1e308\na,1e308\n')
    with pytest.raises(TabularError,match='finite'):
        run_operation('aggregate_csv',{'path':'overflow.csv','by':['group'],'aggregations':[{'column':'value','function':'sum','output_column':'total'}],'target_path':'data/output/overflow.csv'},load_settings())
    assert not (project/'data/output/overflow.csv').exists()


@pytest.mark.parametrize('case',['expired','changed_review'])
def test_table_authority_reverified_before_any_writes(project,monkeypatch,case):
    from datetime import datetime,timedelta,timezone
    request=saved(project,pipeline());review=prepare_workflow(request,project_root=project)
    authorization=authorize_workflow(WorkflowRequest(**{**request.model_dump(),'action':'authorize_workflow','confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':'fixture','reason':'Temporary authority test'}),project_root=project)
    review_sha=review['review_sha256']
    if case=='expired':
        verifier=api.verify_interface_plan_approval
        monkeypatch.setattr(api,'verify_interface_plan_approval',lambda request,**kwargs:verifier(request,**kwargs,now=datetime.now(timezone.utc)+timedelta(minutes=31)))
    else:
        review_sha='f'*64
    with pytest.raises(api.InterfaceApiError):
        execute_workflow(WorkflowRequest(**{**request.model_dump(),'action':'execute_workflow','confirmed_review_sha256':review_sha,'confirm_execution':True,'plan_approval_filename':authorization['plan_approval_filename'],'recipe_approval_filename':authorization['recipe_approval_filename']}),project_root=project)
    assert not list((project/'data/output').iterdir())
