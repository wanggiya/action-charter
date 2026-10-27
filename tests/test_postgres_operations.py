"""Known-answer database contracts and authority checks without live connections."""
from pathlib import Path
import hashlib
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from geoagent_harness.postgres.schemas import ARGUMENTS,ImportCSV,ExportCSV,ChangeRows
from geoagent_harness.postgres import service
from geoagent_harness.postgres.policy import validate_steps
from geoagent_harness.mcp_server.settings import MCPSettings

ROOT=Path(__file__).parents[1]
@pytest.fixture
def settings(tmp_path):
 (tmp_path/'data/input').mkdir(parents=True);(tmp_path/'data/output').mkdir()
 return MCPSettings(project_root=tmp_path,input_root=tmp_path/'data/input',output_root=tmp_path/'data/output',enable_write_tools=True)

def args(settings):
 data=b'id,amount\n001,1.50\n';(settings.input_root/'sample.csv').write_bytes(data)
 return {'connection_sha256':service.connection_sha256(settings),'target_schema':'agent_sandbox','target_table':'visits','path':'data/input/sample.csv','source_sha256':hashlib.sha256(data).hexdigest(),'columns':[{'source':'id','name':'id','type':'text'},{'source':'amount','name':'amount','type':'numeric'}]}

def test_registry_and_exact_gates(settings):
 from geoagent_harness.operations.registry import operation_catalog,argument_models
 from geoagent_harness.skill_registry import load_skill_registry
 from geoagent_harness.recipes.dispatcher import _validate_registered_skill
 registry=load_skill_registry(ROOT);catalog={o['id']:o for o in operation_catalog(ROOT)['operations']}
 for id in ARGUMENTS:
  assert id in argument_models(ROOT)
  skill=_validate_registered_skill(skill_id=id,registry=registry)
  assert skill.approval_required==(id not in service.READ_IDS)
  assert catalog[id]['workflow_supported']
  assert catalog[id]['runtime_requirements'][0]['distribution']=='psycopg'


def test_source_paths_hashes_and_profiles_fail_before_database(settings,monkeypatch):
 a=args(settings)
 def no_connection(*a,**kw):raise AssertionError('Rejected before connection')
 monkeypatch.setattr(service,'_transaction',no_connection)
 for changes in [{'source_sha256':'0'*64},{'path':'data/input/../sample.csv'},{'connection_sha256':'0'*64},{'target_schema':'public'}]:
  with pytest.raises(ValueError):service.run_operation('import_csv_to_postgres',{**a,**changes},settings)
 disabled=settings.model_copy(update={'enable_write_tools':False})
 with pytest.raises(ValueError):service.run_operation('import_csv_to_postgres',a,disabled)


def test_closed_arguments_and_snapshot_requirements(settings):
 a=args(settings)
 for patch in [{'soft_delete_marker':'id'},{'sql':'SELECT 1'},{'mode':'replace'},{'columns':[{'source':'id','name':'x;drop','type':'text'}]},{'source_step':'step_1'},{'source_sha256':None}]:
  with pytest.raises(ValidationError):ImportCSV.model_validate({**a,**patch})
 base={'target_schema':'agent_sandbox','target_table':'visits','columns':['id'],'target_path':'data/output/result.csv'}
 with pytest.raises(ValidationError):ExportCSV.model_validate(base)
 with pytest.raises(ValidationError):ExportCSV.model_validate({**base,'expected_table_sha256':'a'*64,'source_step':'step_1'})
 marker={'target_schema':'agent_sandbox','target_table':'visits','expected_table_sha256':'a'*64,'key_column':'id','keys':['1','1'],'expected_affected_rows':2}
 with pytest.raises(ValidationError):ChangeRows.model_validate(marker)
 with pytest.raises(ValidationError):ChangeRows.model_validate({**marker,'keys':['1'],'expected_affected_rows':2})


def test_reference_contracts_and_false_authority(settings):
 a=args(settings)
 step=SimpleNamespace(step_id='step_1',skill='import_csv_to_postgres',arguments=a,requires_approval=False,validation_required=True)
 with pytest.raises(ValueError,match='approval'):validate_steps([step],{'step_1':[]})
 step.requires_approval=True
 wrong=SimpleNamespace(step_id='step_2',skill='export_postgres_to_csv',requires_approval=True,validation_required=True,arguments={'target_schema':'agent_sandbox','target_table':'other','source_step':'step_1','columns':['id'],'target_path':'data/output/export.csv'})
 with pytest.raises(ValueError,match='same table'):validate_steps([step,wrong],{'step_1':[],'step_2':['step_1']})


def test_exact_numeric_mapping_and_no_silent_id_coercion():
 assert service._value('001','text')=='001'
 assert service._value('001','bigint')=='1'
 assert service._value('100.00','numeric')=='100'
 assert service._value('-0.000','numeric')=='0'
 assert service._value('FALSE','boolean')=='false'
 assert service._row_digest(['001','1.500'],['text','numeric'])==service._row_digest(['001','1.5'],['text','numeric'])
 for value,kind in [('1.1','bigint'),('yes','boolean'),('NaN','numeric'),('Inf','numeric'),('9'*50,'bigint')]:
  with pytest.raises(ValueError):service._value(value,kind)


def test_export_file_boundary_and_semantic_validation(settings):
 from geoagent_harness.postgres.files import publish,read_output
 data=b'id,amount\n001,\\N\n002,2.50\n';path='data/output/selected.csv'
 publish(settings.project_root,path,data)
 assert read_output(settings.project_root,path)==data
 with pytest.raises(ValueError):publish(settings.project_root,path,data)
 digest=hashlib.sha256(b''.join(sorted(hashlib.sha256(__import__('json').dumps(r,ensure_ascii=False,separators=(',',':')).encode()).digest() for r in [['001',None],['002','2.50']]))).hexdigest()
 result={'operation':'export_postgres_to_csv','arguments':{'target_schema':'agent_sandbox','target_table':'visits','expected_table_sha256':'a'*64,'columns':['id','amount'],'target_path':path},'output':{'path':path,'sha256':hashlib.sha256(data).hexdigest()},'semantic_sha256':digest,'row_count':2,'committed':False}
 assert service.validate_output(result,settings)['passed']
 (settings.output_root/'selected.csv').write_bytes(data.replace(b'002',b'003'))
 assert not service.validate_output(result,settings)['passed']
 (settings.output_root/'link.csv').symlink_to(settings.output_root/'selected.csv')
 with pytest.raises(ValueError):read_output(settings.project_root,'data/output/link.csv')


def test_database_read_only_workflow_uses_shared_adapter(tmp_path,monkeypatch):
 import shutil
 from geoagent_harness.interface_api import server as api
 from geoagent_harness.interface_api.workflow import WorkflowRequest,prepare_workflow,execute_workflow
 from geoagent_harness.planner.schemas import PlannerResult
 from geoagent_harness.approvals import plan_sha256
 (tmp_path/'context').mkdir();shutil.copyfile(ROOT/'context/SKILLS_INDEX.yaml',tmp_path/'context/SKILLS_INDEX.yaml')
 monkeypatch.setenv('ENABLE_WRITE_TOOLS','false')
 plan=PlannerResult(agent_id='planner',model='fixture',original_request='Discover configured sandbox tables',context_references=[],plan={'summary':'Discover tables','steps':[{'step_id':'step_1','skill':'discover_postgres_tables','purpose':'Discover ordinary tables','arguments':{'target_schema':'agent_sandbox'},'requires_approval':False,'validation_required':False}]})
 saved=api.save_interface_reviewed_plan(api.InterfaceReviewedPlanSaveRequest(action='save_reviewed_plan',planner_result=plan,confirmed_plan_sha256=plan_sha256(plan.plan),allowed_skill_ids=['discover_postgres_tables']),project_root=tmp_path)
 req=WorkflowRequest(action='prepare_workflow',plan_filename=saved['plan_filename'],confirmed_plan_sha256=saved['plan_sha256'])
 review=prepare_workflow(req,project_root=tmp_path)
 assert not review['approval_required_step_ids'] and review['execution_available']
 monkeypatch.setattr(service,'inspect',lambda *a,**kw:{'tables':['visits'],'execution_performed':True,'database_written':False})
 run=execute_workflow(req.model_copy(update={'action':'execute_workflow','confirmed_review_sha256':review['review_sha256'],'confirm_execution':True}),project_root=tmp_path)
 assert run['status']=='completed' and run['step_results'][0]['outcome']['tables']==['visits']


def test_same_chat_bindings_and_authority_attempts(settings):
 from geoagent_harness.postgres.bindings import bind
 arguments=args(settings);digest=arguments.pop('source_sha256');arguments.pop('connection_sha256')
 step=SimpleNamespace(step_id='step_1',skill='import_csv_to_postgres',arguments=arguments)
 state={'analytical_session':{'observations':[{'result':{'dataset_profile':{'source':'data/input/sample.csv','source_sha256':digest}}}]}}
 assert bind(SimpleNamespace(steps=[step]),state,settings)==['step_1']
 assert step.arguments['source_sha256']==digest
 assert step.arguments['connection_sha256']==service.connection_sha256(settings)
 service.claim_authority(settings,'approval-fixture','step_1')
 with pytest.raises(ValueError,match='already has an attempt'):service.claim_authority(settings,'approval-fixture','step_1')
 service.claim_authority(settings,'fresh-approval','step_1')


def test_postgres_schema_focus_does_not_bloat_unrelated_csv():
 from geoagent_harness.planner.prompt_scope import schema_scope
 available=list(ARGUMENTS)+['inspect_csv','calculate_csv_columns','join_csv']
 assert schema_scope('Import visits.csv into PostgreSQL',available)==['import_csv_to_postgres','inspect_csv']
 assert schema_scope('Soft delete the selected PostgreSQL rows',available)==['inspect_postgres_table','soft_delete_postgres_rows']
 assert 'import_csv_to_postgres' not in schema_scope('Calculate a column in visits.csv',available)
