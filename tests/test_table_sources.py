"""Equivalent table formats, exact original identity and explicit selection contracts."""
import hashlib
import json
from types import SimpleNamespace
import pytest
from typer.testing import CliRunner
from geoagent_harness.data.discovery.csv import inspect
from geoagent_harness.data.tabular.analytical_service import profile_table, recorded_analysis
from geoagent_harness.contracts.analysis_options import AnalysisOptions
from geoagent_harness.data.tabular.table_sources import inspect as inspect_records
from tests.test_task_agents import project

@pytest.fixture
def tables(tmp_path):
    from openpyxl import Workbook
    folder=tmp_path/'data/input';folder.mkdir(parents=True)
    rows=[{'record_id':'001','x':1.5,'region':'A'},{'record_id':'002','x':2.5,'region':'A'},{'record_id':'003','x':4.5,'region':'B'}]
    (folder/'rows.csv').write_text('record_id,x,region\n001,1.5,A\n002,2.5,A\n003,4.5,B\n')
    (folder/'rows.json').write_text(json.dumps(rows))
    for suffix in ('jsonl','ndjson'):(folder/f'rows.{suffix}').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    book=Workbook();sheet=book.active;sheet.title='Data';sheet.append(list(rows[0]))
    for row in rows:sheet.append(list(row.values()))
    book.save(folder/'rows.xlsx')
    return tmp_path

@pytest.mark.parametrize('suffix',['json','jsonl','ndjson','xlsx'])
def test_formats_reconcile_full_analysis_and_preserve_original_identity(tables,suffix):
    options={'statistics':{'columns':['x'],'by':['region']},'distinct_columns':['record_id']}
    csv=profile_table(tables,'rows.csv',options)['table_analysis']
    r=profile_table(tables,f'rows.{suffix}',options)
    assert r['row_count']==3 and r['preview'][0]['record_id']=='001'
    assert r['table_analysis']['statistics']['descriptive']==csv['statistics']['descriptive']
    assert r['table_analysis']['statistics']['grouped_descriptive']==csv['statistics']['grouped_descriptive']
    assert r['table_analysis']['distinct_counts']=={'record_id':3}
    sha=hashlib.sha256((tables/f'data/input/rows.{suffix}').read_bytes()).hexdigest()
    assert r['source_sha256']==r['table_reference']['sources'][0]['sha256']==sha
    assert r['table_analysis']['statistics']['source']['sha256']==sha
    assert not (tables/'data/output').exists()

def test_sheet_and_record_selection_are_explicit_and_persist_in_guidance(tables):
    from openpyxl import load_workbook
    path=tables/'data/input/rows.xlsx';book=load_workbook(path);book.create_sheet('Other');book.save(path)
    with pytest.raises(ValueError,match='Choose source_options.sheet'):inspect_records(tables,'rows.xlsx')
    r=inspect_records(tables,'rows.xlsx',analysis={'source_options':{'sheet':'Data'}})
    assert r['source_selection']['sheet']=='Data'
    assert r['field_guidance']['source_options']['sheet']=='Data'
    assert r['field_guidance']['analysis_starters'][0]['analysis']['source_options']['sheet']=='Data'
    with pytest.raises(ValueError,match='absent'):inspect_records(tables,'rows.xlsx',analysis={'source_options':{'sheet':'missing'}})
    (tables/'data/input/wrapper.json').write_text(json.dumps({'records':[{'x':1},{'x':2}]}))
    with pytest.raises(ValueError,match='record array'):inspect_records(tables,'wrapper.json')
    assert inspect_records(tables,'wrapper.json',analysis={'source_options':{'records_key':'records'}})['row_count']==2
    r=inspect_records(tables,'rows.xlsx',analysis={'source_options':{'sheet':'Data','cell_range':'A1:C3'},'statistics':{'columns':['x']}})
    assert r['row_count']==2 and r['table_analysis']['statistics']['descriptive'][0]['mean']==2
    assert 'A1:C3' in r['table_analysis']['statistics']['report_markdown']

@pytest.mark.parametrize('text',['[{"x":{"nested":1}}]','[{"x":1,"x":2}]','[{"x":1},{"x":2,"new":3}]','[{"x":1},]','[{"x":NaN}]','[]'])
def test_ambiguous_json_never_flattens_or_silently_discards(tables,text):
    (tables/'data/input/bad.json').write_text(text)
    with pytest.raises(ValueError):inspect_records(tables,'bad.json')

def test_native_types_null_and_empty_policy_are_visible(tables):
    (tables/'data/input/types.json').write_text('[{"id":"001","flag":true,"v":null},{"id":"002","flag":false,"v":""}]')
    r=inspect_records(tables,'types.json',analysis={})
    assert r['preview'][0]['flag'] is True and r['preview'][1]['v']==''
    assert r['column_types']['flag']=='boolean' and r['missing_counts']['v']==1 and r['empty_string_counts']['v']==1
    assert r['table_analysis']['profiles'][2]['missing_count']==2
    assert any('null and empty' in w for w in r['warnings'])

def test_formula_unsafe_path_and_changed_source_reject(tables):
    from openpyxl import load_workbook
    path=tables/'data/input/rows.xlsx';book=load_workbook(path);book.active['B2']='=1+2';book.save(path)
    with pytest.raises(ValueError,match='Formula'):inspect_records(tables,'rows.xlsx')
    with pytest.raises(ValueError):inspect_records(tables,'../rows.json')
    (tables/'data/input/link.json').symlink_to(tables/'data/input/rows.json')
    with pytest.raises(OSError):inspect_records(tables,'link.json')
    changed=False
    def checkpoint():
        nonlocal changed
        if not changed:
            changed=True;(tables/'data/input/rows.json').write_text('[{"x":1}]')
    with pytest.raises(ValueError,match='changed'):inspect_records(tables,'rows.json',checkpoint=checkpoint)


def test_external_packages_and_reader_budgets_reject_without_partial_success(tables,monkeypatch):
    import zipfile
    from geoagent_harness.data.tabular import table_sources
    path=tables/'data/input/rows.xlsx'
    with zipfile.ZipFile(path,'a') as archive:archive.writestr('xl/externalLinks/externalLink1.xml','<externalLink/>')
    with pytest.raises(ValueError,match='external'):inspect_records(tables,'rows.xlsx')
    monkeypatch.setattr(table_sources,'MAX_ROWS',2)
    with pytest.raises(ValueError,match='rows'):inspect_records(tables,'rows.json')
    monkeypatch.setattr(table_sources,'MAX_BYTES',10)
    with pytest.raises(ValueError,match='16 MiB'):inspect_records(tables,'rows.json')

def test_cli_mcp_selection_and_readonly_policy(tables):
    from geoagent_harness.apps.cli.main import app
    from geoagent_harness.task_actions import data_tools as tools
    spec={'columns':['x']};settings=SimpleNamespace(project_root=tables,input_root=tables/'data/input')
    mcp=tools.table_statistics('rows.xlsx',spec,settings=settings,source_options={'sheet':'Data'})
    reply=CliRunner().invoke(app,['table-statistics','rows.xlsx','--specification',json.dumps(spec),'--source-options','{"sheet":"Data"}','--project-root',str(tables)])
    assert reply.exit_code==0,reply.output
    assert json.loads(reply.output)['table_analysis']['statistics']['descriptive']==mcp['table_analysis']['statistics']['descriptive']
    from geoagent_harness.core.policy.table import validate_steps
    from geoagent_harness.contracts.planning import PlanStep
    with pytest.raises(ValueError,match='requires .csv'):
        validate_steps([PlanStep(step_id='step_1',skill='select_csv_columns',purpose='invalid',arguments={'path':'rows.xlsx','columns':['x'],'target_path':'data/output/new.csv'},requires_approval=True,validation_required=True)],{'step_1':[]})

def test_recorded_view_preserves_sheet_and_rejects_selection_change(tables):
    options={'source_options':{'sheet':'Data'}}
    r=profile_table(tables,'rows.xlsx',options)
    record={'conversation_id':'a'*32,'plan_sha256':'b'*64,'run_id':'c'*32,'steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','arguments':{'path':'rows.xlsx','analysis':options},'outcome':r}]}
    request=SimpleNamespace(conversation_id='a'*32,confirmed_plan_sha256='b'*64,step_id='step_1',table_options=AnalysisOptions(group_by=['region']))
    viewed=recorded_analysis(tables,record,request)
    assert viewed['table_analysis']['request']['source_options']['sheet']=='Data'
    request.table_options=AnalysisOptions(source_options={'sheet':'Other'})
    with pytest.raises(ValueError,match='selection requires'):recorded_analysis(tables,record,request)


def test_new_formats_use_governed_workflow_and_never_run_on_send(project):
    from geoagent_harness.task_actions.planner_submission import SubmissionRequest, submission_action
    from geoagent_harness.task_actions.conversation import TurnRequest
    from tests.test_planner_conversation import Client
    from scripts.statistical_planner_evaluation import execute
    (project/'data/input/rows.json').write_text('[{"id":"001","x":1},{"id":"002","x":2}]')
    client=Client()
    receipt=submission_action(SubmissionRequest(action='submit',submission_id='d'*32,conversation_id='e'*32,inspect_on_send=True,turn=TurnRequest(action='turn',conversation_id='e'*32,message='Inspect rows.json. Return row count and column names. No writes.')),project_root=project,model_client=client,background=False)
    assert not client.requests and receipt['submission']['run_id'] is None
    assert not receipt['execution_performed'] and not receipt['approval_performed']
    assert 'nothing was read' in receipt['submission']['finding']
    run=execute(project,receipt['conversation'])
    assert run['status']=='completed'
    assert run['steps'][0]['outcome']['row_count']==2
    assert run['steps'][0]['outcome']['preview'][0]['id']=='001'


def test_planner_binds_explicit_sheet_and_repairs_provider_omission(project):
    from copy import deepcopy
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
    from tests.test_planner_conversation import Client
    from geoagent_harness.agents.roles.planner.request_coverage import requested_source_options
    from jsonschema import Draft202012Validator
    from openpyxl import Workbook
    book=Workbook();book.active.title='Data';book.active.append(['x','region']);book.active.append([1,'A']);book.save(project/'data/input/rows.xlsx')
    good={'message':'I will analyze historical_y from the old file.','plan':{'summary':'Describe x by region','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Describe','arguments':{'path':'data/input/rows.xlsx','analysis':{'source_options':{'sheet':'Data'},'statistics':{'columns':['x'],'by':['region'],'methods':['describe']}}}}]}}
    bad=deepcopy(good);bad['plan']['steps'][0]['arguments']['analysis'].pop('source_options')
    client=Client(bad,good)
    message='Compute descriptive statistics for x grouped by region in rows.xlsx, worksheet Data. Set analysis.source_options.sheet to Data. No writes. Prepare only.'
    result=conversation_turn(TurnRequest(action='turn',conversation_id='f'*32,message=message),project_root=project,model_client=client)
    assert len(client.requests)==2 and not result['execution_performed'] and not result['approval_performed']
    from geoagent_harness.contracts.table_sources import table_format_catalog
    system=json.loads(client.requests[0].messages[0].content)
    capability=system['table_source_capability']
    assert capability['operation_id']=='inspect_csv' and capability['execution_authority'] is False
    assert capability['formats']==[item for item in table_format_catalog()['formats'] if item['id']=='xlsx']
    assert 'historical_y' not in result['messages'][-1]['content']
    assert 'data/input/rows.xlsx' in result['messages'][-1]['content']
    assert 'historical_y' in result['context_usage']['model_request']['unverified_model_explanation']
    schema=client.requests[0].response_schema;validator=Draft202012Validator(schema)
    assert validator.is_valid(good) and not validator.is_valid(bad)
    extra=deepcopy(good);extra['plan']['steps'][0]['arguments']['analysis']['statistics']['columns'].append('historical_y')
    assert not validator.is_valid(extra)
    wrong=deepcopy(good);wrong['plan']['steps'][0]['arguments']['analysis']['source_options']['sheet']='Other'
    assert not validator.is_valid(wrong)
    wrong_source=deepcopy(good);wrong_source['plan']['steps'][0]['arguments']['path']='data/input/sample_orders.csv'
    assert not validator.is_valid(wrong_source)
    assert not validator.is_valid({'message':'CSV conversion is required.','plan':None})
    assert requested_source_options('JSON Lines, not a worksheet; omit spreadsheet source options.')=={}
    assert requested_source_options('Do not set source_options.sheet to Data.')=={}
    assert requested_source_options('Use worksheet "Data sheet".')=={'sheet':'Data sheet'}
    assert requested_source_options('Use source_options.header_row=2.')=={'header_row':2}
    assert requested_source_options('Use source_options.cell_range="B3:E8".')=={'cell_range':'B3:E8'}
    with pytest.raises(ValueError):AnalysisOptions(source_options={'header_row':2,'cell_range':'B3:E8'})
