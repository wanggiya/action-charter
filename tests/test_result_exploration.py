"""Full bounded artifact exploration, not preview-only transformations."""
import json
from pathlib import Path
import pytest
from typer.testing import CliRunner
from tests.test_tabular_workflow import project
from tests.test_result_preview import recorded
from geoagent_harness.interface_api.exploration_contracts import ExplorationQuery, ChartAnalysis, ResultViewSpec
from geoagent_harness.interface_api.workflow_runs import RunRequest, run_action
from geoagent_harness.interface_api.server import InterfaceApiError
from geoagent_harness.cli import app


def explore(project, content=b'id,region,amount\n001,North,10\n002,South,\n003,North,20\n', **query):
    path, record, request = recorded(project, content)
    request.action = 'explore'
    request.query = ExplorationQuery(**query)
    return path, record, request, run_action(request, project_root=project)


def test_query_uses_full_artifact_and_preserves_identity_beyond_preview(project):
    content = ('id,region,amount\n' + ''.join(f'{i:04},North,{i}\n' for i in range(1500))).encode()
    _, _, request, _ = explore(project, content, filters=[{'column':'amount','operator':'ge','value_type':'number','value':1200}],
        sort={'column':'amount','value_type':'number','descending':True})
    result = run_action(request, project_root=project)
    assert result['row_count'] == 1500 and result['matched_row_count'] == 300
    assert result['preview'][0]['id'] == '1499' and result['row_ids'][0] == 1499
    assert result['next_offset'] == 25
    request.query.offset = result['next_offset']
    next_page = run_action(request, project_root=project)
    assert next_page['row_ids'][0] == 1474
    assert not set(next_page['row_ids']) & set(result['row_ids'])
    assert not result['execution_performed'] and not result['approval_performed']


def test_profiles_describe_complete_source_not_filtered_page(project):
    _, _, _, result = explore(project, filters=[{'column':'region','operator':'eq','value':'North'}])
    profiles = {item['name']:item for item in result['column_profiles']}
    assert profiles['amount']['missing_count'] == 1
    assert profiles['amount']['observed_type'] == 'numeric-compatible text'
    assert profiles['amount']['minimum'] == 10 and profiles['amount']['maximum'] == 20
    assert profiles['id']['storage_type'] == 'string'
    assert result['matched_row_count'] == 2 and result['preview'][0]['id'] == '001'


def test_filtered_chart_summary_matches_all_filtered_rows(project):
    _, _, request, _ = explore(project, filters=[{'column':'amount','operator':'not_missing'}])
    request.analysis = ChartAnalysis(group_by='region',value='amount',aggregation='sum')
    result = run_action(request, project_root=project)
    assert result['chart_analysis']['preview'] == [{'category':'North','value':30.0}]
    assert result['chart_analysis']['scope'] == 'complete_filtered_artifact'
    assert result['chart_analysis']['source_total_row_count'] == 3
    assert result['chart_analysis']['source_row_count'] == 2


def test_nulls_sort_last_and_identifier_strings_are_not_rewritten(project):
    _, _, _, result = explore(project, sort={'column':'amount','value_type':'number','descending':True})
    assert result['row_ids'] == [2,0,1]
    assert result['preview'][0]['id'] == '003'


def test_contains_is_literal_not_regular_expression(project):
    _, _, _, result = explore(project, b'id,text\n01,a.b\n02,axb\n', filters=[{'column':'text','operator':'contains','value':'.'}])
    assert result['matched_row_count'] == 1 and result['row_ids'] == [0]


@pytest.mark.parametrize('query', [
    {'filters':[{'column':'unknown','operator':'eq','value':'x'}]},
    {'sort':{'column':'region','value_type':'number'}},
    {'columns':['id','id']},
    {'columns':['missing']},
])
def test_invalid_semantic_query_rejected(project,query):
    with pytest.raises(InterfaceApiError):
        explore(project, **query)


def test_missing_chat_and_changed_source_rejected(project):
    path, _, request, _ = explore(project)
    request.conversation_id = None
    with pytest.raises(InterfaceApiError,match='conversation'):
        run_action(request,project_root=project)
    request.conversation_id = 'c'*32
    path.write_text('id,region,amount\n001,Other,999\n')
    with pytest.raises(InterfaceApiError,match='changed since execution'):
        run_action(request,project_root=project)


def test_response_budget_paging_does_not_skip_rows(project):
    columns = [f'c{i}' for i in range(32)]
    content = (','.join(columns)+'\n'+''.join(','.join(['x'*500]*32)+'\n' for _ in range(150))).encode()
    _, _, request, first = explore(project, content, limit=100)
    assert first['cells_truncated'] and first['next_offset'] == len(first['row_ids']) < 100
    request.query.offset = first['next_offset']
    second = run_action(request,project_root=project)
    assert second['row_ids'][0] == first['row_ids'][-1] + 1
    assert len(json.dumps(first['preview'],ensure_ascii=False).encode()) <= 128000


def test_cli_shares_exploration_contract(project,tmp_path):
    _, _, request, result = explore(project)
    path = tmp_path/'explore.json';path.write_text(request.model_dump_json())
    response = CliRunner().invoke(app,['workflow-runs','--project-root',str(project),'--request-file',str(path)])
    assert response.exit_code == 0, response.output
    assert json.loads(response.stdout) == result
    assert not (project/'approvals').exists()


def test_view_spec_excludes_paths_and_map_table_filtering():
    base = dict(run_id='a'*32,plan_sha256='b'*64,step_id='step_1',view='Table')
    with pytest.raises(ValueError):
        ResultViewSpec(**base,path='/etc/passwd')
    with pytest.raises(ValueError):
        ResultViewSpec(**{**base,'view':'Map'},query={'filters':[{'column':'x','operator':'eq','value':'1'}]})
