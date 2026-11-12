"""Initial statistical field advice is bounded, source-bound and non-executing."""
import hashlib,json
from types import SimpleNamespace
import pytest
from typer.testing import CliRunner
from geoagent_harness.data.discovery.csv import inspect
from geoagent_harness.data.tabular.field_guidance import requests_field_guidance, compact_guidance, guidance_context
from geoagent_harness.data.tabular.dataset_profile import inspect_dataset
from tests.test_task_agents import project

@pytest.fixture
def data(tmp_path):
 (tmp_path/'data/input').mkdir(parents=True)
 rows=['patient_nbr,measurement,admission_source_id,age,constant,flag,number_visits,notes']
 for i in range(30):rows.append(f'{i//2:03d},{"?" if i==0 else i+.5},{1+i%3},[50-60),5,{i%2},{i%3},{"x"*200}')
 (tmp_path/'data/input/measures.csv').write_text('\n'.join(rows)+'\n')
 return tmp_path

def test_initial_inspection_advises_from_all_rows_without_changing_values(data):
 path=data/'data/input/measures.csv';before=path.read_bytes()
 r=inspect(data,'measures.csv',preview_rows=1);g=r['field_guidance'];c=g['candidates'];fields={f['name']:f for f in g['fields']}
 assert g['source_sha256']==hashlib.sha256(before).hexdigest() and g['matching_rows']==30
 assert 'measurement' in c['measurement'] and 'number_visits' in c['measurement']
 assert 'patient_nbr' in c['identifier'] and 'patient_nbr' not in c['measurement']
 assert 'constant' in c['review'] and 'flag' in c['review'] and 'notes' in c['review']
 assert fields['age']['role']=='ordered_category' and fields['admission_source_id']['kind']=='grouping'
 assert fields['measurement']['numeric_count']==29 and fields['measurement']['missing_count']==0
 assert any('marker' in text for text in fields['measurement']['cautions'])
 assert r['preview'][0]['measurement']=='?' and path.read_bytes()==before
 assert g['advisory_only'] and not (data/'data/output').exists()
 opportunities={o['id']:o for o in g['analysis_opportunities']}
 assert {'quality','distribution','frequencies','entities'}==set(opportunities)
 assert all(o['operation']=='inspect_csv' and o['requirements'] for o in opportunities.values())
 assert 'patient_nbr' in opportunities['entities']['fields'] and 'patient_nbr' not in opportunities['distribution']['fields']
 assert compact_guidance(g)['analysis_opportunities']==g['analysis_opportunities']

def test_comprehensive_profile_reuses_candidate_roles_and_declared_missingness(data):
 r=inspect_dataset(data,'measures.csv',{'missing_values':{'measurement':['?']}})
 fields={f['name']:f for f in r['field_guidance']['fields']}
 assert fields['measurement']['missing_count']==1
 assert not any('definitions need review' in text for text in fields['measurement']['cautions'])
 assert all(fields[p['name']]['role']==p['analytical_role'] for p in r['profiles'])
 assert fields['patient_nbr']['numeric_count'] is None

def test_worker_response_remains_bounded_and_does_not_sample_guidance(data):
 from geoagent_harness.data.tabular.analytical_service import recommend_fields
 names=[f'field_{i}' for i in range(100)]
 (data/'data/input/wide.csv').write_text(','.join(names)+'\n'+','.join(str(i) for i in range(100))+'\n')
 r=inspect(data,'wide.csv');g=r['field_guidance']
 assert len(json.dumps(r,separators=(',',':')).encode())<16000
 assert g['field_count']==100 and g['omitted_fields']==100-len(g['fields'])
 assert g['source_rows']==g['matching_rows']==1
 assert recommend_fields(data,'wide.csv')['source_sha256']==g['source_sha256']


def test_ordinary_guidance_honors_supplied_codebook_without_converting_values(data):
 (data/'data/input/ward.csv').write_text('ward\n1\n2\n1\n')
 (data/'data/input/ward_codes.csv').write_text('ward,description\n1,First ward\n2,Second ward\n')
 r=inspect(data,'ward.csv',analysis={'codebook_path':'ward_codes.csv'})
 f=r['field_guidance']['fields'][0]
 assert f['role']=='categorical' and f['kind']=='grouping'
 assert r['preview'][0]['ward']=='1'

def test_cli_and_registered_mcp_share_guidance_and_reject_unsafe_paths(data):
 import asyncio
 from geoagent_harness.apps.cli.main import app
 from geoagent_harness.task_actions import data_tools as tools
 from geoagent_harness.apps.mcp.server import create_mcp_server
 from geoagent_harness.platform.internal_mcp.client import READ_ONLY_TOOL_ALLOWLIST
 value=tools.recommend_table_fields('measures.csv',settings=SimpleNamespace(project_root=data,input_root=data/'data/input'))
 reply=CliRunner().invoke(app,['table-guidance','measures.csv','--project-root',str(data)])
 assert reply.exit_code==0,reply.output
 assert json.loads(reply.output)==value
 names={t.name:t.inputSchema for t in asyncio.run(create_mcp_server().list_tools())}
 assert 'recommend_table_fields' in READ_ONLY_TOOL_ALLOWLIST
 assert names['recommend_table_fields']['properties']['path']['type']=='string'
 with pytest.raises(ValueError):tools.recommend_table_fields('../measures.csv',settings=SimpleNamespace(project_root=data,input_root=data/'data/input'))


def test_analysis_starters_are_typed_bounded_and_exclude_ambiguous_or_incomplete_fields(data):
 from geoagent_harness.contracts.analysis_options import AnalysisOptions
 from geoagent_harness.data.tabular.field_guidance import analysis_starters
 g=inspect(data,'measures.csv')['field_guidance']
 assert [s['column'] for s in g['analysis_starters']]==['number_visits']
 for s in g['analysis_starters']:
  options=AnalysisOptions.model_validate(s['analysis'])
  assert options.statistics.columns==[s['column']]
  assert options.statistics.methods==['describe'] and options.statistics.missing_policy=='error'
 assert analysis_starters(g['fields'],source_rows=30,matching_rows=29)==[]
 assert analysis_starters(g['fields'],source_rows=200001,matching_rows=200001)==[]
 (data/'data/input/large_values.csv').write_text('measurement\n1000000000001\n1000000000002\n')
 assert inspect(data,'large_values.csv')['field_guidance']['analysis_starters']==[]
 (data/'data/input/small.csv').write_text('measurement\n1\n2\n')
 assert inspect(data,'small.csv')['field_guidance']['analysis_starters']==[]  # fewer than three observations


def test_inspection_to_grouped_analysis_matches_independent_reference_and_cli_mcp(data):
 import statistics
 from geoagent_harness.data.tabular.analytical_service import profile_table
 from geoagent_harness.task_actions.data_tools import table_statistics
 from geoagent_harness.apps.cli.main import app
 (data/'data/input/unrelated.csv').write_text('record_id,temperature,region\n001,12.5,North\n002,17.5,South\n003,20.5,North\n004,25.5,South\n')
 g=inspect(data,'unrelated.csv',preview_rows=1)['field_guidance']
 starter=next(s for s in g['analysis_starters'] if s['column']=='temperature')
 spec={**starter['analysis']['statistics'],'by':['region']}
 r=profile_table(data,'unrelated.csv',{'statistics':spec})['table_analysis']['statistics']
 assert r['analysis_rows']==4 and r['excluded_rows']==0
 observed=r['descriptive'][0]
 assert observed['mean']==statistics.mean([12.5,17.5,20.5,25.5])
 assert observed['variance']==pytest.approx(statistics.variance([12.5,17.5,20.5,25.5]))
 assert {g['group']['region']:g['descriptive'][0]['mean'] for g in r['grouped_descriptive']}=={'North':16.5,'South':21.5}
 assert r['source']['sha256']==g['source_sha256'] and g['source_sha256'] in r['report_markdown']
 assert 'North' in r['report_markdown'] and 'South' in r['report_markdown']
 settings=SimpleNamespace(project_root=data,input_root=data/'data/input')
 mcp=table_statistics('unrelated.csv',spec,settings=settings)['table_analysis']['statistics']
 cli=CliRunner().invoke(app,['table-statistics','unrelated.csv','--specification',json.dumps(spec),'--project-root',str(data)])
 assert cli.exit_code==0,cli.output
 assert json.loads(cli.output)['table_analysis']['statistics']['descriptive']==mcp['descriptive']==r['descriptive']
 # No hint grants an exclusion policy when selected data changes.
 (data/'data/input/unrelated.csv').write_text('record_id,temperature,region\n001,12.5,North\n002,?,South\n')
 from geoagent_harness.contracts.errors import InterfaceApiError
 with pytest.raises(InterfaceApiError,match='missing, invalid'):
  profile_table(data,'unrelated.csv',{'statistics':spec})


@pytest.mark.parametrize('question',['Which fields are suitable for statistics? Suggestions only; preserve the workflow.','What statistical analysis should I do next? Suggestions only; preserve the workflow.'])
def test_agent_field_question_uses_recorded_advice_and_preserves_workflow(project,monkeypatch,question):
 from tests.test_planner_conversation import Client
 from geoagent_harness.task_actions.conversation import conversation_turn, TurnRequest
 (project/'data/input/measures.csv').write_text('x,y\n0,1\n1,3\n2,4\n3,5\n')
 plan={'summary':'Inspect source','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/measures.csv'}}]}
 identity='a'*32
 first=conversation_turn(TurnRequest(action='turn',conversation_id=identity,message='Inspect measures.csv.'),project_root=project,model_client=Client({'message':'Proposed.','plan':plan}))
 advice=compact_guidance(inspect(project,'measures.csv')['field_guidance'])
 context={'run_id':'b'*32,'plan_sha256':first['planner_result']['plan_sha256'],'results':[{'step_id':'step_1','views':['Table','Chart'],'columns':['x','y'],'recorded_facts':{'row_count':4},'field_guidance':advice}]}
 monkeypatch.setattr('geoagent_harness.task_actions.result_exploration.view_context',lambda *a:context)
 client=Client({'message':'x and y are candidate measurements; inspect their spread and confirm the question before choosing an outcome.','plan':None})
 result=conversation_turn(TurnRequest(action='turn',conversation_id=identity,expected_revision=first['revision'],message=question),project_root=project,model_client=client)
 assert result['planner_result']['plan_sha256']==first['planner_result']['plan_sha256']
 system=json.loads(client.requests[0].messages[0].content)
 assert system['operation_argument_schemas']=={}
 assert any('at most three' in rule for rule in system['mandatory_rules'])
 assert system['result_view_context']['results'][0]['field_guidance']==advice
 assert client.requests[0].response_schema['properties']['plan']=={'type':'null'}
 assert guidance_context('Which fields in other.csv are suitable for statistics?',context) is None
 assert guidance_context('Which fields for statistics? source SHA-256: '+'0'*64,context) is None
 assert len(client.requests)==1 and not result['execution_performed'] and not result['approval_performed']
 assert requests_field_guidance('Which fields should I use for statistics?')
 assert not requests_field_guidance('Which fields should I use, then fit a regression?')
 assert not requests_field_guidance('What statistical analysis should I do next? Compute Pearson correlation now.')
 from geoagent_harness.agents.roles.planner.agent import PlannerAgentError
 bad=Client({'message':'Changing workflow.','plan':plan},{'message':'Changing workflow.','plan':plan})
 with pytest.raises(PlannerAgentError):
  conversation_turn(TurnRequest(action='turn',conversation_id=identity,expected_revision=result['revision'],message='Which fields are suitable for statistics?'),project_root=project,model_client=bad)
 assert len(bad.requests)==2
 saved=conversation_turn(TurnRequest(action='read',conversation_id=identity),project_root=project)
 assert saved['planner_result']['plan_sha256']==first['planner_result']['plan_sha256']
 from geoagent_harness.task_actions.planner_submission import SubmissionRequest, submission_action
 receipt=submission_action(SubmissionRequest(action='submit',submission_id='c'*32,conversation_id=identity,inspect_on_send=True,turn=TurnRequest(action='turn',conversation_id=identity,expected_revision=saved['revision'],message='Which fields are suitable for statistics?')),project_root=project,model_client=Client({'message':'Use the recorded candidates; confirm the objective.','plan':None}),background=False)
 assert receipt['submission']['run_id'] is None and not receipt['execution_performed']
 assert 'current workflow is unchanged' in receipt['submission']['finding']
