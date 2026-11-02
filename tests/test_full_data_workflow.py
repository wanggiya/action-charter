"""Qualified full-file preparation, preflight and recorded handoff boundaries."""
import csv
import hashlib
import json
from types import SimpleNamespace

import pytest
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.tabular.service import run_operation,validate_output,TabularError


@pytest.fixture
def settings(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True);(tmp_path/'data/output').mkdir()
    (tmp_path/'data/input/rows.csv').write_text('id,region,amount,code\n'+''.join(f'{i:06d},{"A" if i%2 else "B"},{"" if i%7==0 else i},1\n' for i in range(700)))
    (tmp_path/'data/input/book.csv').write_text('code,description\n1,Defined\n')
    return MCPSettings(project_root=tmp_path,input_root=tmp_path/'data/input',output_root=tmp_path/'data/output',enable_write_tools=True)


@pytest.mark.parametrize('skill,arguments',[
    ('select_csv_columns',{'columns':['id','amount']}),
    ('filter_csv_rows',{'predicates':[{'column':'amount','operator':'gt','value':300,'value_type':'number'}]}),
    ('handle_csv_missing',{'method':'fill','fill_values':{'amount':0}}),
    ('decode_csv_codes',{'codebook_path':'book.csv','columns':['code']}),
    ('export_csv',{}),
])
def test_chunked_semantics_equal_existing_operations_across_batches(settings,skill,arguments):
    base={'path':'rows.csv',**arguments}
    small=run_operation(skill,{**base,'target_path':'data/output/small.csv'},settings)
    streamed=run_operation(skill,{**base,'target_path':'data/output/streamed.csv','streaming':True},settings)
    assert (settings.output_root/'small.csv').read_bytes()==(settings.output_root/'streamed.csv').read_bytes()
    assert small['row_count']==streamed['row_count']
    assert validate_output(streamed,settings)['passed']
    assert streamed['preview'][0]['id'].startswith('000')


def prior(result,settings):
    return SimpleNamespace(validation_performed=True,validation_result=validate_output(result,settings),execution=SimpleNamespace(result=result))


def test_large_preparation_ancestor_and_aggregation(settings):
    (settings.input_root/'large.csv').write_text('id,region,value\n'+''.join(f'{i:06d},A,2\n' for i in range(10001)))
    selected=run_operation('select_csv_columns',{'path':'large.csv','columns':['id','region','value'],'target_path':'data/output/selected.csv','streaming':True},settings)
    assert selected['row_count']==10001 and prior(selected,settings).validation_result['passed']
    aggregate=run_operation('aggregate_csv',{'source_step':'step_1','by':['region'],'aggregations':[{'column':'value','function':'sum','output_column':'total'}],
        'target_path':'data/output/aggregate.csv','streaming':True},settings,{'step_1':prior(selected,settings)})
    assert aggregate['preview'][0]['total']=='20002.0' and validate_output(aggregate,settings)['passed']
    (settings.output_root/'selected.csv').write_text('id,region,value\nchanged,A,2\n')
    with pytest.raises(TabularError):validate_output(selected,settings)


def test_streaming_failure_cancellation_and_collision_never_publish_partial(settings,monkeypatch):
    from geoagent_harness.tabular import streaming
    args={'path':'rows.csv','columns':['id'],'target_path':'data/output/target.csv','streaming':True}
    def stop():raise RuntimeError('cancelled')
    monkeypatch.setattr(streaming,'checkpoint',stop)
    with pytest.raises(RuntimeError,match='cancelled'):run_operation('select_csv_columns',args,settings)
    assert not list(settings.output_root.iterdir())
    monkeypatch.setattr(streaming,'checkpoint',lambda:None)
    monkeypatch.setattr(streaming,'MAX_OUTPUT_BYTES',32)
    with pytest.raises(TabularError,match='64 MiB'):run_operation('select_csv_columns',args,settings)
    assert not list(settings.output_root.iterdir())
    monkeypatch.setattr(streaming,'MAX_OUTPUT_BYTES',64*1024**2)
    run_operation('select_csv_columns',args,settings)
    before=(settings.output_root/'target.csv').read_bytes()
    with pytest.raises(TabularError,match='exists'):run_operation('select_csv_columns',args,settings)
    assert (settings.output_root/'target.csv').read_bytes()==before


def import_args(settings,data):
    from geoagent_harness.postgres.service import connection_sha256
    (settings.input_root/'mapped.csv').write_bytes(data)
    return {'path':'mapped.csv','source_sha256':hashlib.sha256(data).hexdigest(),'connection_sha256':connection_sha256(settings),
        'target_schema':'agent_sandbox','target_table':'fresh','columns':[
            {'source':'id','name':'id','type':'text','nullable':False},
            {'source':'value','name':'value','type':'numeric','null_values':['','?']},
            {'source':'label','name':'label','type':'text'}],'key_columns':['id']}


def test_complete_preflight_null_mapping_and_schema_without_connection(settings,monkeypatch):
    from geoagent_harness.postgres import service
    def forbidden(*a,**k):raise AssertionError('No database connection in mapping preflight')
    monkeypatch.setattr(service,'_transaction',forbidden)
    args=import_args(settings,b'id,value,label\n001,?,?\n002,1.50,text\n')
    r=service.inspect('validate_postgres_import',args,settings)
    assert r['passed'] and r['row_count']==2 and r['column_findings']['value']['null_rows']==1
    assert r['column_findings']['label']['null_rows']==0
    assert 'PRIMARY KEY ("id")' in r['proposed_ddl'] and not r['database_written'] and not r['execution_authority']
    bad=import_args(settings,b'id,value,label\n001,not_numeric,text\n001,2,text\n,3,text\n')
    r=service.inspect('validate_postgres_import',bad,settings)
    assert not r['passed'] and r['column_findings']['value']['invalid_cast_rows']==1
    assert r['column_findings']['id']['not_null_violations']==1
    assert r['key_findings']['excess_occurrences']==1
    with pytest.raises(service.PostgresError,match='preflight rejected'):service.run_operation('import_csv_to_postgres',bad,settings)


def test_handoff_uses_actual_schema_status_and_does_not_read_sources():
    from geoagent_harness.recipes.handoff import handoff
    record={'run_id':'r','plan_sha256':'a'*64,'status':'failed','steps':[{'step_id':'step_1','skill_id':'import_csv_to_postgres','status':'validated_success',
        'outcome':{'target_schema':'agent_sandbox','target_table':'fresh','column_metadata':[{'name':'id','type':'text','nullable':False}],
        'key_constraints':[{'kind':'primary','columns':['id']}],'row_count':10001,'table_sha256':'b'*64,'committed':True,
        'sources':[{'path':'data/input/absent.csv','sha256':'c'*64}],'arguments':{'password':'private-test-password'}}}]}
    r=handoff(record)
    assert r['status']=='failed' and not r['execution_performed'] and not r['authority_granted']
    assert '| id | text | False |' in r['technical_markdown'] and '10001' in r['technical_markdown']
    assert 'private-test-password' not in r['technical_markdown'] and 'uncertain commit' in r['technical_markdown']
    assert 'No source-bound' in r['analytical_markdown']


def test_streaming_strategy_bound_only_before_review_and_explicit_false_preserved(settings):
    from geoagent_harness.planner.bindings import bind_streaming_preparation
    from geoagent_harness.planner.schemas import WorkflowPlan,PlanStep
    from geoagent_harness.tabular.strategy import assess_table
    path=settings.input_root/'large.csv'
    with path.open('wb') as f:
        f.write(b'id,value\n');f.truncate(9*1024**2)
    steps=[PlanStep(step_id='step_1',skill='select_csv_columns',purpose='select',arguments={'path':'data/input/large.csv','columns':['id']}),
           PlanStep(step_id='step_2',skill='export_csv',purpose='export',arguments={'source_step':'step_1'}),
           PlanStep(step_id='step_3',skill='select_csv_columns',purpose='explicit bounded',arguments={'path':'data/input/large.csv','columns':['id'],'streaming':False})]
    plan=WorkflowPlan(summary='Qualified strategy',steps=steps)
    assert bind_streaming_preparation(plan,settings.project_root)==['step_1','step_2']
    assert plan.steps[2].arguments['streaming'] is False
    assert not list(settings.output_root.iterdir())
    assessed=assess_table(settings.project_root,'data/input/large.csv','select_csv_columns')
    assert assessed['strategy']=='full_stream' and assessed['row_limit']==200000
    assert assessed['required_arguments']=={'streaming':True} and assessed['within_byte_limit']
    assert assess_table(settings.project_root,'data/input/large.csv','join_csv')['strategy']=='needs_alternative'


def test_database_receipt_trims_preview_before_dropping_schema():
    from geoagent_harness.interface_api.workflow_runs import fit_database_receipt
    schema=[{'name':'id','type':'text','nullable':False}]
    value={'column_metadata':schema,'executed_ddl':'CREATE TABLE test (id text);',
           'preview':[{'id':'x'*1000} for _ in range(20)]}
    result=fit_database_receipt(value,limit=1000)
    assert result['column_metadata']==schema and result['executed_ddl']==value['executed_ddl']
    assert result['preview_truncated'] and not result['preview']
    assert len(value['preview'])==20


def test_terminal_report_follows_selected_historical_run_without_execution():
    from geoagent_harness.chat.workspace import Workspace
    calls=[]
    class Client:
        def post(self,path,payload):
            calls.append((path,payload))
            assert path=='/api/v1/workflow/runs' and payload['action']=='report'
            return {'handoff':{'analytical_markdown':payload['run_id'],'technical_markdown':'Recorded only'}}
    workspace=Workspace(Client(),'c'*32);workspace.state={'revision':1}
    workspace.last_run={'run_id':'b'*32};workspace.historical={'run':{'run_id':'a'*32}}
    assert 'a'*32 in workspace.execute('/report')
    assert calls[-1][1]['run_id']=='a'*32
    assert 'b'*32 in workspace.execute('/report '+'b'*32)
    workspace.historical=None
    assert 'b'*32 in workspace.execute('/report')
