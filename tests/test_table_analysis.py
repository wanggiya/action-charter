import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from geoagent_harness.tabular.analytical_service import profile_table, recorded_analysis
from geoagent_harness.discovery.csv import inspect
from geoagent_harness.interface_api.inspection_planning import plan_for_request


@pytest.fixture
def dataset(tmp_path):
    directory = tmp_path / 'data/input/test'
    directory.mkdir(parents=True)
    with (directory/'visits.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id','patient','age','outcome','stay','code'])
        for i in range(15000):
            writer.writerow([f'{i:06}',str(i//2),'older' if i%2 else 'younger','<30' if i%3==0 else 'NO',str(i%5+1),str(i%2+1)])
    (tmp_path/'data/input/codes.csv').write_text('code,description\n1,Emergency\n2,Urgent\n,\nother,description\n0,Unbound\n')
    return tmp_path


def options():
    return {'codebook_path':'codes.csv','group_by':['age','outcome'],
            'numeric_columns':['stay'],'distinct_columns':['patient'], 'offset':20,'limit':20}


def test_full_source_profile_matches_independent_reference(dataset):
    r = profile_table(dataset,'test/visits.csv',options())
    a = r['table_analysis']
    assert r['row_count'] == a['source_row_count'] == a['matched_row_count'] == 15000
    assert a['distinct_counts']['patient'] == 7500
    assert a['codebook']['sections']['code']['1'] == 'Emergency'
    assert a['codebook']['unbound_sections'] == ['other']
    assert a['codebook']['coverage']['code']['matched_rows'] == 15000
    assert a['table']['preview'][0]['id'] == '000020'
    assert sum(g['row_count'] for g in a['groups']) == 15000
    # Independent dataframe oracle, not the service/grouping implementation.
    import pandas as pd
    raw = pd.read_csv(dataset/'data/input/test/visits.csv')
    expected = raw.groupby(['age','outcome']).agg(n=('id','size'),mean=('stay','mean'))
    for g in a['groups']:
        reference = expected.loc[(g['age'],g['outcome'])]
        assert g['row_count'] == reference['n']
        assert g['stay_mean'] == pytest.approx(reference['mean'])
    assert r['table_reference']['sources'][1]['sha256'] == hashlib.sha256((dataset/'data/input/codes.csv').read_bytes()).hexdigest()
    assert len(json.dumps(r).encode()) < 128000


def test_exact_profile_plan_and_safe_nested_path(dataset):
    message='Profile test/visits.csv using codes.csv. Group by age, outcome. Summarize stay. Count distinct patient. No writes.'
    plan = plan_for_request(message,['inspect_csv'])
    assert len(plan.steps) == 1 and not plan.steps[0].requires_approval
    assert plan.steps[0].arguments['analysis']['codebook_path'] == 'data/input/codes.csv'
    assert plan.steps[0].arguments['path'] == 'data/input/test/visits.csv'
    from geoagent_harness.intent.input import check_task_input
    assert check_task_input(project_root=dataset,input_path='test/visits.csv') == 'data/input/test/visits.csv'
    for path in ['../visits.csv','test/../visits.csv','test//visits.csv','/etc/passwd','test\\visits.csv']:
        with pytest.raises(ValueError): profile_table(dataset,path)


def test_filter_and_source_bound_recorded_page(dataset):
    r = profile_table(dataset,'test/visits.csv',options())
    record={'run_id':'a'*32,'plan_sha256':'b'*64,'conversation_id':'c'*32,
            'steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','arguments':{},'outcome':r}]}
    q={**options(),'filters':[{'column':'outcome','value':'<30'}], 'offset':0}
    request=SimpleNamespace(confirmed_plan_sha256='b'*64, conversation_id='c'*32, step_id='step_1', table_options=__import__('geoagent_harness.tabular.analysis_contracts',fromlist=['AnalysisOptions']).AnalysisOptions.model_validate(q))
    page=recorded_analysis(dataset,record,request)
    assert page['table_analysis']['matched_row_count'] == 5000
    assert page['table_analysis']['table']['preview'][0]['id'] == '000000'
    assert page['data_written'] is False
    request.conversation_id='d'*32
    with pytest.raises(ValueError,match='matching'): recorded_analysis(dataset,record,request)
    request.conversation_id='c'*32
    (dataset/'data/input/codes.csv').write_text('code,description\n1,Changed\n')
    with pytest.raises(ValueError,match='Codebook changed'): recorded_analysis(dataset,record,request)


def test_missing_codes_are_explicit_and_identifiers_preserved(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/values.csv').write_text('id,value\n001,?\n002,None\n003,\n004,4\n')
    r=profile_table(tmp_path,'values.csv',{'missing_values':{'value':['?']},'profile_columns':['id','value']})
    p=r['table_analysis']['profiles'][1]
    assert p['missing_count'] == 2
    assert any(c['value']=='None' for c in p['categories'])
    assert r['table_analysis']['table']['preview'][0]['id']=='001'
    assert r['missing_counts']['value'] == 1  # Legacy raw empty-count contract unchanged.


@pytest.mark.parametrize('content',[
    'code,description\n1,A\n1,B\n',
    'code,label\n1,A\n',
    'code,description\n1,A,extra\n',
])
def test_ambiguous_codebook_rejects_without_fabricating_labels(dataset,content):
    (dataset/'data/input/codes.csv').write_text(content)
    with pytest.raises(Exception): profile_table(dataset,'test/visits.csv',options())


def test_source_replacement_and_cardinality_limits(dataset):
    r=profile_table(dataset,'test/visits.csv')
    with (dataset/'data/input/test/visits.csv').open('a') as stream: stream.write('extra,p,older,NO,1,1\n')
    with pytest.raises(ValueError,match='changed'): profile_table(dataset,'test/visits.csv',expected_sha256=r['source_sha256'])
    with pytest.raises(Exception): profile_table(dataset,'test/visits.csv',{'group_by':['id']})


def test_full_file_aggregate_export_and_validation(dataset):
    from geoagent_harness.tabular.service import run_operation, validate_output
    settings=SimpleNamespace(project_root=dataset,enable_write_tools=True,allow_overwrite=False)
    r=run_operation('aggregate_csv',{'path':'test/visits.csv','streaming':True,'by':['age','outcome'],
        'aggregations':[{'column':'id','function':'count','output_column':'encounters'},
                        {'column':'stay','function':'mean','output_column':'mean_stay'}],
        'target_path':'data/output/summary.csv'},settings)
    assert r['streaming_aggregation']['source_row_count'] == 15000
    assert validate_output(r,settings)['passed']
    with (dataset/'data/output/summary.csv').open() as f:
        assert sum(int(row['encounters']) for row in csv.DictReader(f)) == 15000
    with pytest.raises(Exception,match='exists'):
        run_operation('aggregate_csv',{'path':'test/visits.csv','streaming':True,'by':['age'],
            'aggregations':[{'column':'id','function':'count','output_column':'n'}],
            'target_path':'data/output/summary.csv'},settings)


def test_quality_repetitions_duplicates_and_group_distinct(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/q.csv').write_text('id,patient,group,value\n1,p,A,2\n2,p,A,?\n3,q,B,\n3,q,B,\n,p,B,None\n')
    a=profile_table(tmp_path,'q.csv',{'quality_columns':['id','patient','value'],
        'duplicate_rows':True,'duplicate_key':['id'],'group_by':['group'],
        'distinct_columns':['patient'],'missing_values':{'value':['?']}})['table_analysis']
    quality=a['quality']
    assert quality['columns']['patient']=={'status':'exact','distinct_count':2,'once_only_values':0,
        'repeated_values':2,'rows_in_repeated_groups':5,'excess_occurrences':3}
    assert quality['duplicate_rows']['excess_occurrences']==1
    assert quality['duplicate_key']['missing_key_rows']==1
    assert quality['duplicate_key']['excess_occurrences']==1
    assert not quality['duplicate_key']['candidate_key']
    assert [g['patient_distinct'] for g in a['groups']]==[1,2]
    assert sum(g['patient_distinct'] for g in a['groups'])>a['distinct_counts']['patient']
    value=next(p for p in a['profiles'] if p['name']=='value')
    assert (value['empty_count'],value['declared_missing_count'],value['missing_count'])==(2,1,3)
    assert value['frequency']['once_only_values']==2  # literal None remains a value
    assert a['quality']['scope']=='matching_rows'
    filtered=profile_table(tmp_path,'q.csv',{'duplicate_key':['id'],'filters':[{'column':'group','value':'A'}]})['table_analysis']
    assert filtered['quality']['duplicate_key']['candidate_key']


def test_quality_zero_matches_and_reserved_group_output(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/q.csv').write_text('id,id_distinct\n1,a\n')
    a=profile_table(tmp_path,'q.csv',{'quality_columns':['id'],'duplicate_key':['id'],
        'duplicate_rows':True,'filters':[{'column':'id','value':'absent'}]})['table_analysis']
    assert a['quality']['duplicate_rows']['distinct_count']==0
    assert not a['quality']['duplicate_key']['candidate_key']
    with pytest.raises(Exception,match='conflict'):
        profile_table(tmp_path,'q.csv',{'group_by':['id_distinct'],'distinct_columns':['id']})


def test_exact_quality_budget_never_returns_partial_metrics(tmp_path):
    from geoagent_harness.tabular.analysis import Accumulator
    acc=Accumulator(tmp_path,['id'],{'quality_columns':['id']})
    acc.exact_entries=500000
    with pytest.raises(ValueError,match='No partial checks'):
        acc.add(['one'])


def test_quality_mcp_cli_share_contract_and_results(tmp_path):
    import asyncio
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    from geoagent_harness.mcp_server import tools
    from geoagent_harness.mcp_server.server import mcp
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/q.csv').write_text('id,group\n1,A\n1,A\n2,B\n')
    opts={'quality_columns':['id'],'duplicate_key':['id'],'group_by':['group'],'distinct_columns':['id']}
    direct=profile_table(tmp_path,'q.csv',opts)['table_analysis']
    settings=SimpleNamespace(project_root=tmp_path,input_root=tmp_path/'data/input')
    through_mcp=tools.profile_table('q.csv',opts,settings=settings)['table_analysis']
    options_file=tmp_path/'options.json';options_file.write_text(json.dumps(opts))
    result=CliRunner().invoke(app,['profile-csv','q.csv','--project-root',str(tmp_path),'--options',str(options_file)])
    assert result.exit_code==0,result.output
    assert json.loads(result.output)['table_analysis']==through_mcp==direct
    registered=asyncio.run(mcp.list_tools())
    schema=next(t.inputSchema for t in registered if t.name=='profile_table')
    assert 'quality_columns' in json.dumps(schema) and 'duplicate_key' in json.dumps(schema)
    with pytest.raises(Exception):tools.profile_table('q.csv',{'arbitrary_python':'import os'},settings=settings)


def test_exact_quality_recovers_high_cardinality_distribution(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/q.csv').write_text('id\n'+''.join(f'{i}\n' for i in range(300))+'0\n')
    p=profile_table(tmp_path,'q.csv',{'quality_columns':['id']})['table_analysis']['profiles'][0]
    assert p['distinct_count']==300 and p['frequency']['once_only_values']==299
    assert p['categories'][0]['value']=='0' and p['categories'][0]['count']==2
    assert p['categories_status']=='exact_counts_top_12'
