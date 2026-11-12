"""Source-bound, repeatable assessment/report evidence; no live services."""
import hashlib
import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner
from tests.test_task_agents import project

from geoagent_harness.data.tabular.analytical_service import profile_table
from geoagent_harness.data.tabular.readiness import ReadinessAssessment, attach_assessment, build_assessment, compact_assessment


@pytest.fixture
def data(tmp_path):
    folder=tmp_path/'data/input';folder.mkdir(parents=True)
    (folder/'measurements.csv').write_text('observation_id,entity,region,value,code\n001,A,North,2,1\n002,A,North,4,2\n003,B,South,?,9\n004,C,South,6,1\n')
    (folder/'definitions.csv').write_text('code,description\n1,One\n2,Two\n')
    return tmp_path


def options():
    return {'codebook_path':'definitions.csv','missing_values':{'value':['?']},'duplicate_key':['observation_id'],
        'duplicate_rows':True,'distinct_columns':['entity'],'numeric_columns':['value'],'group_by':['region'],'limit':1}


def test_assessment_reconciles_missingness_keys_mapping_and_full_groups(data):
    source=data/'data/input/measurements.csv';before=source.read_bytes()
    r=profile_table(data,'measurements.csv',options());a=r['readiness_assessment']
    typed=ReadinessAssessment.model_validate(a)
    assert typed.source_rows==typed.matching_rows==4 and a['source_sha256']==hashlib.sha256(before).hexdigest()
    assert a['distinct_counts']=={'entity':3} and a['population_scope']=='unverified' and not a['possible_sample']
    fields={f['name']:f for f in a['fields']}
    assert fields['value']['missing']==1 and fields['value']['missing_percent']==25
    assert fields['value']['numeric_count']==3 and fields['value']['mean']==4
    assert a['mappings']==[{'field':'code','matched_rows':3,'unmatched_rows':1}]
    checks={c['name']:c for c in a['checks']}
    assert checks['Candidate observation key']['status']=='pass'
    assert checks['Whole-row duplicates']['status']=='pass'
    assert checks['Supplied codebook coverage']['status']=='attention'
    assert [g['percentage_total'] for g in a['groups']]==[50,50]
    assert [g['percentage_within_primary'] for g in a['groups']]==[100,100]
    assert len(r['table_analysis']['table']['preview'])==1 and sum(g['row_count'] for g in a['groups'])==4
    assert all(s in a['report_markdown'] for s in ['Numerical findings','Supplied definitions','not a clinical assessment','not preview rows'])
    assert source.read_bytes()==before and not (data/'data/output').exists()
    compact=compact_assessment(a)
    assert 'report_markdown' not in compact and 'groups' not in compact and 'fields' not in compact
    assert compact['source_sha256']==a['source_sha256']


def test_unknown_checks_filters_and_empty_denominators_are_explicit(data):
    r=profile_table(data,'measurements.csv',{'filters':[{'column':'region','value':'absent'}]})
    a=r['readiness_assessment'];assert a['source_rows']==4 and a['matching_rows']==0
    assert a['filters']==[{'column':'region','value':'absent'}]
    assert all(f['missing_percent'] is None for f in a['fields'])
    assert all(c['status']=='not_requested' for c in a['checks'][:4])
    assert a['execution_authority'] is False and a['data_written'] is False


def test_dataset_projection_and_saved_terminal_report_do_not_rescan(data,monkeypatch):
    from geoagent_harness.data.tabular.dataset_service import profile_dataset
    from geoagent_harness.apps.chat.views import saved_view, render_view
    monkeypatch.setenv('ACTIONCHARTER_ANALYTICAL_RUNTIME','local')
    r=profile_dataset(data,'measurements.csv',{'numeric_columns':['value'],'missing_values':{'value':['?']}},retain_artifact=False)
    a=r['readiness_assessment'];assert a['source_rows']==4
    assert next(f for f in a['fields'] if f['name']=='value')['standard_deviation']==2
    state={'conversation_id':'a'*32,'revision':1,'analytical_session':{'observations':[{'result':{'dataset_profile':r}}]}}
    (data/'data/input/measurements.csv').unlink()
    view=saved_view(state,'report');assert view['recorded_only'] and not view['execution_performed']
    assert a['report_markdown'].strip() in '\n'.join(render_view(view).splitlines()[4:])


def test_budget_omissions_never_discard_original_analysis_and_text_is_escaped(data):
    r=profile_table(data,'measurements.csv',options());r.pop('readiness_assessment')
    original=json.dumps(r['table_analysis'],sort_keys=True)
    attach_assessment(r,result_budget=len(json.dumps(r).encode())+1000)
    assert 'readiness_assessment' not in r and 'output budget' in r['readiness_status']
    assert json.dumps(r['table_analysis'],sort_keys=True)==original
    r['table_analysis']['profiles'][0]['name']='<script>|field'
    a=build_assessment(r)
    assert '<script>' not in a['report_markdown'] and '&lt;script&gt;&#124;field' in a['report_markdown']


def test_cli_and_mcp_share_same_readiness_evidence(data):
    from geoagent_harness.apps.cli.main import app
    from geoagent_harness.task_actions import data_tools as tools
    expected=profile_table(data,'measurements.csv',options())['readiness_assessment']
    mcp=tools.profile_table('measurements.csv',options(),settings=SimpleNamespace(project_root=data,input_root=data/'data/input'))
    assert mcp['readiness_assessment']==expected
    reply=CliRunner().invoke(app,['inspect-table','measurements.csv','--options',json.dumps(options()),'--report','--project-root',str(data)])
    assert reply.exit_code==0,reply.output
    assert reply.output.strip()==expected['report_markdown'].strip()


def test_critic_evidence_contains_scope_unknowns_and_no_report_rows(data):
    from geoagent_harness.task_actions.run_assessment import evidence
    outcome=profile_table(data,'measurements.csv',{})
    record={'run_id':'r','plan_sha256':'a'*64,'status':'completed','failed_step_id':None,'steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','outcome':outcome}]}
    value=evidence(record)['steps'][0]['metadata']['readiness']
    assert value['source_rows']==4 and value['population_scope']=='unverified'
    assert value['checks'][0]['status']=='not_requested' and 'report_markdown' not in value


def test_combined_report_retains_statistical_methods_and_source_binding(data):
    spec=options();spec['statistics']={'columns':['value'],'methods':['describe'],'missing_policy':'complete_cases'}
    r=profile_table(data,'measurements.csv',spec);a=r['readiness_assessment']
    assert r['table_analysis']['statistics']['report_markdown'] in a['report_markdown']
    assert a['omissions']['statistical_report']==0
    assert next(f for f in a['fields'] if f['name']=='value')['standard_deviation']==2
    assert a['source_sha256']==r['table_analysis']['statistics']['source']['sha256']


def test_group_rates_use_all_groups_before_report_truncation(data):
    folder=data/'data/input'
    (folder/'rates.csv').write_text('category,outcome\n'+''.join(f'{i//2},{i%2}\n' for i in range(40)))
    r=profile_table(data,'rates.csv',{'group_by':['category','outcome']})
    a=r['readiness_assessment']
    assert len(a['groups'])==30 and a['omissions']['groups']==10
    assert all(g['primary_denominator']==2 and g['percentage_within_primary']==50 for g in a['groups'])
    assert all(g['total_denominator']==40 and g['percentage_total']==2.5 for g in a['groups'])
    assert len(r['table_analysis']['groups'])==40


def test_readiness_planning_is_focused_without_omitting_requested_checks(project):
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
    from tests.test_planner_conversation import Client
    from jsonschema import Draft202012Validator
    folder=project/'data/input/test';folder.mkdir()
    (folder/'records.csv').write_text('encounter_id,patient_nbr,race,weight,payer_code,medical_specialty\n001,A,?,1,P,M\n')
    (folder/'codes.csv').write_text('race,description\nX,Defined category\n')
    arguments={'path':'data/input/test/records.csv','analysis':{'codebook_path':'data/input/test/codes.csv',
        'missing_values':{k:['?'] for k in ['race','weight','payer_code','medical_specialty']},
        'duplicate_key':['encounter_id'],'duplicate_rows':True,'distinct_columns':['patient_nbr']}}
    reply={'message':'Readiness inspection proposed; nothing executed.','plan':{'summary':'Inspect full source readiness','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect requested quality checks','arguments':arguments}]}}
    client=Client(reply)
    result=conversation_turn(TurnRequest(action='turn',conversation_id='f'*32,allowed_skill_ids=['inspect_csv'],
        message='Inspect test/records.csv with test/codes.csv. Use the whole file, not the sample. Treat ? as missing in race, weight, payer_code and medical_specialty. Check encounter_id as the record key and check whole-row duplicates. Count distinct patient_nbr. Prepare only; no writes.'),project_root=project,model_client=client)
    system=json.loads(client.requests[0].messages[0].content)
    assert system['prompt_profile']=='table-inspection-focused-v1'
    assert sum(len(m.content.encode()) for m in client.requests[0].messages)<12000
    assert list(system['operation_argument_schemas'])==['inspect_csv']
    assert 'conversion_arguments_example' not in system
    assert Draft202012Validator(client.requests[0].response_schema).is_valid(reply)
    actual=result['planner_result']['plan']['steps'][0]['arguments']['analysis']
    assert actual['duplicate_rows'] and actual['duplicate_key']==['encounter_id']
    assert actual['missing_values']==arguments['analysis']['missing_values']
    assert not result['execution_performed'] and not result['approval_performed']
    assert not (project/'approvals').exists()
    assert result['context_usage']['model_request']['prompt_profile']=='table-inspection-focused-v1'
    from geoagent_harness.platform.model_gateway.client import ModelClientError
    timed=Client(ModelClientError.timeout())
    with pytest.raises(ModelClientError) as failure:
        conversation_turn(TurnRequest(action='turn',conversation_id='f'*32,expected_revision=1,
            allowed_skill_ids=['inspect_csv'],message='Inspect test/records.csv with test/codes.csv. Check whole-row duplicates. No writes; prepare only.'),project_root=project,model_client=timed)
    assert len(timed.requests)==1
    assert failure.value.planner_diagnostics['prompt_profile']=='table-inspection-focused-v1'
    restored=conversation_turn(TurnRequest(action='read',conversation_id='f'*32),project_root=project)
    assert restored['revision']==result['revision'] and restored['planner_result']==result['planner_result']


def test_numerical_statistics_wording_keeps_analysis_and_focused_instructions(project):
    from tests.test_planner_conversation import Client,turn
    client=Client({'message':'Prepared numerical profile','plan':{'summary':'Inspect measurements','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect complete source','arguments':{'path':'sample_orders.csv','analysis':{'numeric_columns':['amount']}}}]}})
    result=turn(project,client,'Inspect sample_orders.csv. Return row count, column names and numerical statistics for amount. Use the complete file. No writes.')
    system=json.loads(client.requests[0].messages[0].content)
    assert system['prompt_profile']=='table-inspection-focused-v1'
    assert 'analysis' in system['operation_argument_schemas']['inspect_csv']['properties']
    assert result['context_usage']['model_request']['prompt_bytes']<18000
    assert result['planner_result']['plan']['steps'][0]['arguments']['analysis']['numeric_columns']==['amount']


def test_basic_metadata_inspection_uses_focused_profile_without_analysis(project):
    from tests.test_planner_conversation import Client,turn
    client=Client({'message':'Prepared inspection','plan':{'summary':'Inspect source','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect metadata','arguments':{'path':'sample_orders.csv'}}]}})
    turn(project,client,'Inspect sample_orders.csv. Return row count and column names. No writes.')
    system=json.loads(client.requests[0].messages[0].content)
    assert system['prompt_profile']=='table-inspection-focused-v1'
    assert 'analysis' not in system['operation_argument_schemas']['inspect_csv']['properties']


def test_report_metric_coverage_requires_calculated_evidence(data):
    r=profile_table(data,'measurements.csv',options())
    report=r['readiness_assessment']['report_markdown']
    assert '| Inferential P-values | Not calculated |' in report
    assert '| Predictive precision / recall / F1 | Not calculated |' in report
    r['table_analysis']['statistics']={'regression':{'residual_standard_error':0.4,'coefficients':[
        {'p_value':0.03,'standard_error':0.2,'confidence_lower':0.1,'confidence_upper':1.1}]}}
    report=build_assessment(r)['report_markdown']
    assert '| Inferential P-values | Calculated |' in report
    assert '| Regression standard errors / confidence intervals | Calculated |' in report
    assert '| Regression residual error / R-squared | Calculated |' in report
    assert '| Predictive precision / recall / F1 | Not calculated |' in report
    r['table_analysis']['statistics']['regression']['coefficients']=[{'p_value':None}]
    report=build_assessment(r)['report_markdown']
    assert '| Inferential P-values | Unavailable; inspect method diagnostics |' in report
