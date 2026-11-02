"""Known-answer statistics, invalid designs, source contracts and shared entry points."""
import hashlib
import json
import math
from types import SimpleNamespace
import pytest
from typer.testing import CliRunner
from geoagent_harness.tabular.analytical_service import profile_table
from geoagent_harness.tabular.statistics import StatisticsSpec,StatisticsAccumulator,StatisticsError
from tests.test_task_agents import project

@pytest.fixture
def data(tmp_path):
    (tmp_path/'data/input').mkdir(parents=True)
    (tmp_path/'data/input/measures.csv').write_text('x,y,region,patient\n0,1,A,p1\n1,3,A,p1\n2,4,B,p2\n3,5,B,p2\n')
    return tmp_path

def run(root,spec,**options):
    return profile_table(root,'measures.csv',{'statistics':spec,**options})['table_analysis']['statistics']

def test_descriptive_grouped_full_file_and_source_bound_report(data):
    r=run(data,{'columns':['x','y'],'by':['region']})
    x=r['descriptive'][0]
    assert x['mean']==1.5 and x['variance']==pytest.approx(5/3) and x['standard_deviation']==pytest.approx(math.sqrt(5/3))
    assert x['percentiles']['25.0']==.75 and x['percentiles']['50.0']==1.5
    assert r['grouped_descriptive'][0]['descriptive'][1]['mean']==2
    assert r['grouped_descriptive'][1]['descriptive'][1]['variance']==.5
    assert r['source']['sha256']==hashlib.sha256((data/'data/input/measures.csv').read_bytes()).hexdigest()
    assert r['source']['sha256'] in r['report_markdown'] and r['analysis_rows']==4


def test_report_and_critic_share_question_scope_and_computed_facts_without_raw_rows(data):
    from geoagent_harness.tabular.statistics import statistical_evidence
    from geoagent_harness.interface_api.run_assessment import evidence
    question='How does x vary by region? <script>not instructions</script>'
    r=run(data,{'columns':['x'],'by':['region'],'question':question})
    assert '## Analysis definition' in r['report_markdown'] and '## Computed findings' in r['report_markdown']
    assert '&lt;script&gt;' in r['report_markdown'] and '<script>' not in r['report_markdown']
    e=statistical_evidence({'table_analysis':{'statistics':r}})
    assert e['question']==question and e['source']==r['source'] and e['source_rows']==4
    assert e['matching_rows']==e['analysis_rows']==4 and e['group_count']==2
    assert e['specification']['by']==['region'] and e['missing_counts']=={'x':0}
    assert e['grouped_descriptive'][1]['descriptive'][0]['mean']==2.5
    record={'run_id':'a'*32,'plan_sha256':'b'*64,'status':'completed','failed_step_id':None,'steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','outcome':{'table_analysis':{'statistics':r},'preview':[{'secret':'not-for-model'}]}}]}
    pack=evidence(record)
    assert pack['steps'][0]['metadata']['statistics']==e
    assert 'not-for-model' not in json.dumps(pack)


def test_critic_evidence_is_bounded_and_truncation_does_not_mutate_saved_report(data):
    from copy import deepcopy
    from geoagent_harness.tabular.statistics import statistical_evidence
    r=run(data,{'columns':['x','y'],'by':['region']})
    r['grouped_descriptive']=[deepcopy(r['grouped_descriptive'][0]) for _ in range(64)]
    for group in r['grouped_descriptive']:
        group['descriptive']*=12
    original=deepcopy(r)
    e=statistical_evidence({'table_analysis':{'statistics':r}})
    assert len(json.dumps(e).encode())<=6000
    assert e['group_count']==64 and e['group_summaries_omitted']==64
    assert e['source']==r['source'] and r==original
    with pytest.raises(ValueError):StatisticsSpec(columns=['x'],question='x'*401)


def test_critic_receives_measured_relationships_and_model_diagnostics(data):
    from geoagent_harness.tabular.statistics import statistical_evidence
    r=run(data,{'methods':['pearson','covariance','linear_regression'],'columns':['x','y'],'regression':{'outcome':'y','predictors':['x']}})
    e=statistical_evidence({'table_analysis':{'statistics':r}})
    pair=e['correlations'][0]['pairs'][0]
    assert pair['fields']==['x','y'] and pair['coefficient']==r['correlations'][0]['coefficients'][0][1]
    assert pair['p_value']==r['correlations'][0]['p_values'][0][1] and e['correlations'][0]['pairs_omitted']==0
    assert e['covariance']=={'columns':['x','y'],'rows':4,'ddof':1}
    assert e['regression']['diagnostics']==r['regression']['diagnostics']

def test_ols_matches_hand_calculation_and_independent_scipy_solver(data):
    from scipy.stats import linregress
    r=run(data,{'methods':['describe','pearson','spearman','linear_regression'],'columns':['x','y'],'regression':{'outcome':'y','predictors':['x']}})
    fit=r['regression'];reference=linregress([0,1,2,3],[1,3,4,5])
    assert fit['coefficients'][0]['coefficient']==pytest.approx(1.3)
    assert fit['coefficients'][1]['coefficient']==pytest.approx(reference.slope)
    assert fit['coefficients'][1]['standard_error']==pytest.approx(math.sqrt(.03))
    assert fit['coefficients'][1]['p_value']==pytest.approx(reference.pvalue)
    assert fit['r_squared']==pytest.approx(1-.3/8.75)
    assert fit['adjusted_r_squared']==pytest.approx(1-(1-fit['r_squared'])*3/2)
    assert r['correlations'][0]['coefficients'][0][1]==pytest.approx(reference.rvalue)
    assert r['correlations'][1]['coefficients'][0][1]==pytest.approx(1)
    assert fit['coefficients'][1]['confidence_lower']<1.3<fit['coefficients'][1]['confidence_upper']
    assert fit['rows']==4 and fit['degrees_of_freedom_residual']==2
    assert 'P-value' in r['report_markdown'] and 'causal' in r['report_markdown']

@pytest.mark.parametrize('covariance',['nonrobust','HC3','cluster'])
def test_multivariate_model_and_covariance_choices(data,covariance):
    import numpy as np
    from scipy.stats import t
    rows=[]
    for i in range(8):
        x1=1 if i&1 else -1;x2=1 if i&2 else -1;e=1 if i&4 else -1
        rows.append(f'{x1},{x2},{3+2*x1-x2+.5*e},g{i//2}\n')
    (data/'data/input/measures.csv').write_text('x1,x2,y,group\n'+''.join(rows))
    spec={'outcome':'y','predictors':['x1','x2'],'covariance':covariance}
    if covariance=='cluster':spec['cluster_column']='group'
    r=run(data,{'methods':['linear_regression'],'regression':spec})['regression']
    assert [c['coefficient'] for c in r['coefficients']]==pytest.approx([3,2,-1])
    assert r['r_squared']==pytest.approx(40/42)
    assert all(c['p_value'] is not None for c in r['coefficients'])
    if covariance=='cluster':assert r['clusters']==4 and r['degrees_of_freedom_inference']==3
    # Independent covariance formulas, not another call to the fitting library.
    x=np.array([[1,float(row.split(',')[0]),float(row.split(',')[1])] for row in rows])
    y=np.array([float(row.split(',')[2]) for row in rows]);bread=np.linalg.inv(x.T@x)
    residual=y-x@np.array([3,2,-1]);df=5
    if covariance=='nonrobust':cov=bread*(residual@residual)/df
    elif covariance=='HC3':
        leverage=np.einsum('ij,jk,ik->i',x,bread,x)
        cov=bread@((x.T*(residual/(1-leverage))**2)@x)@bread
    else:
        scores=np.array([(x[i:i+2]*residual[i:i+2,None]).sum(axis=0) for i in range(0,8,2)])
        cov=bread@(scores.T@scores)@bread*(4/3)*(7/5);df=3
    se=np.sqrt(np.diag(cov))
    assert [c['standard_error'] for c in r['coefficients']]==pytest.approx(se,abs=1e-14)
    for coefficient,error in zip(r['coefficients'],se):
        if error>1e-10:assert coefficient['p_value']==pytest.approx(2*t.sf(abs(coefficient['coefficient']/error),df))

def test_missing_policy_is_explicit_and_inputs_are_unchanged(data):
    path=data/'data/input/measures.csv';path.write_text('x,y\n0,1\n?,3\n2,4\n3,5\n');before=path.read_bytes()
    with pytest.raises(Exception,match='missing, invalid'):run(data,{'columns':['x','y']})
    r=run(data,{'columns':['x','y'],'missing_policy':'complete_cases'},missing_values={'x':['?']})
    assert r['matching_rows']==4 and r['analysis_rows']==3 and r['excluded_rows']==1
    assert r['missing_counts']['x']==1 and r['invalid_counts']['x']==0
    assert path.read_bytes()==before and not (data/'data/output').exists()

def test_filters_ddof_and_constant_correlation(data):
    r=run(data,{'columns':['x'],'ddof':0},filters=[{'column':'region','value':'A'}])
    assert r['source_rows']==4 and r['analysis_rows']==2 and r['descriptive'][0]['variance']==.25
    (data/'data/input/measures.csv').write_text('x,y\n1,2\n1,3\n1,5\n')
    r=run(data,{'methods':['pearson','spearman'],'columns':['x','y']})
    assert r['correlations'][0]['constant_columns']==['x']
    assert r['correlations'][0]['coefficients'][0][1] is None

def test_rank_deficient_design_and_non_numeric_fields_reject(data):
    (data/'data/input/measures.csv').write_text('x,z,y\n0,0,1\n1,2,3\n2,4,4\n3,6,5\n')
    with pytest.raises(Exception,match='rank-deficient'):run(data,{'methods':['linear_regression'],'regression':{'outcome':'y','predictors':['x','z']}})
    with pytest.raises(Exception,match='not present'):run(data,{'columns':['not_in_source']})

def test_perfect_fit_does_not_invent_inferential_certainty(data):
    (data/'data/input/measures.csv').write_text('x,y\n0,1\n1,3\n2,5\n3,7\n')
    r=run(data,{'methods':['linear_regression'],'regression':{'outcome':'y','predictors':['x']}})['regression']
    assert r['r_squared']==pytest.approx(1) and r['inference_status']=='unavailable_perfect_fit'
    assert all(c['p_value'] is None and c['standard_error'] is None for c in r['coefficients'])

def test_contracts_and_budgets_are_closed():
    for spec in ({'columns':['x'],'expression':'eval(1)'},{'methods':['pearson'],'columns':['x']},{'columns':['x'],'percentiles':[101]},
                 {'methods':['linear_regression'],'regression':{'outcome':'y','predictors':['y']}},
                 {'methods':['linear_regression'],'regression':{'outcome':'y','predictors':['x'],'covariance':'cluster'}}):
        with pytest.raises(ValueError):StatisticsSpec.model_validate(spec)
    accumulator=StatisticsAccumulator(StatisticsSpec(columns=['x'],by=['g']),['x','g'],{})
    with pytest.raises(StatisticsError,match='64 groups'):
        for i in range(65):accumulator.add({'x':'1','g':str(i)})
    accumulator=StatisticsAccumulator(StatisticsSpec(columns=['x']),['x'],{});accumulator.matched=200000
    with pytest.raises(StatisticsError,match='200,000'):accumulator.add({'x':'1'})

def test_mcp_and_cli_use_the_same_statistical_service(data,monkeypatch):
    from geoagent_harness.mcp_server.tools import table_statistics
    from geoagent_harness.cli import app
    spec={'columns':['x','y']}
    mcp=table_statistics('measures.csv',spec,settings=SimpleNamespace(project_root=data,input_root=data/'data/input'))
    cli=CliRunner().invoke(app,['table-statistics','measures.csv','--specification',json.dumps(spec),'--project-root',str(data)])
    assert cli.exit_code==0,cli.output
    assert json.loads(cli.output)['table_analysis']['statistics']==mcp['table_analysis']['statistics']
    import asyncio
    from geoagent_harness.mcp_server import tools
    from geoagent_harness.mcp_server.server import create_mcp_server
    monkeypatch.setattr(tools,'load_settings',lambda:SimpleNamespace(project_root=data,input_root=data/'data/input'))
    blocks=asyncio.run(create_mcp_server().call_tool('linear_regression',{'path':'measures.csv','specification':{'outcome':'y','predictors':['x']}}))
    recorded=json.loads(blocks[0].text)['table_analysis']['statistics']['regression']
    assert recorded['coefficients'][1]['coefficient']==pytest.approx(1.3)
    assert recorded['coefficients'][1]['p_value']==pytest.approx(.017292370176)


def test_statistics_are_registered_as_typed_read_only_mcp_tools():
    import asyncio
    from geoagent_harness.mcp_server.server import create_mcp_server
    from geoagent_harness.mcp_server.tools import TOOL_ALLOWLIST
    from geoagent_harness.mcp_client import READ_ONLY_TOOL_ALLOWLIST
    schemas={tool.name:tool.inputSchema for tool in asyncio.run(create_mcp_server().list_tools())}
    assert set(schemas)==set(TOOL_ALLOWLIST)
    for name in ('table_statistics','linear_regression'):
        assert name in READ_ONLY_TOOL_ALLOWLIST
        assert 'specification' in schemas[name]['properties']
    assert 'covariance' in json.dumps(schemas['linear_regression'])
    assert 'percentiles' in json.dumps(schemas['table_statistics'])

def test_complete_file_not_preview(data):
    (data/'data/input/measures.csv').write_text('x\n'+''.join(f'{i}\n' for i in range(200)))
    r=run(data,{'columns':['x']})
    assert r['analysis_rows']==200 and r['descriptive'][0]['mean']==99.5


@pytest.mark.parametrize('ddof',[0,1])
def test_covariance_matrix_and_report_have_independently_known_values(data,ddof):
    r=run(data,{'methods':['covariance'],'columns':['x','y'],'ddof':ddof})
    matrix=r['covariance_matrix']
    # Centered cross-products: xx=5, xy=6.5, yy=8.75 over all four rows.
    assert matrix['columns']==['x','y'] and matrix['rows']==4 and matrix['ddof']==ddof
    assert matrix['values'][0]==pytest.approx([5/(4-ddof),6.5/(4-ddof)])
    assert matrix['values'][1]==pytest.approx([6.5/(4-ddof),8.75/(4-ddof)])
    report=r['report_markdown']
    assert '## Covariance matrix' in report and '| Field | x | y |' in report
    assert r['source']['sha256'] in report and 'Runtime versions' in report


def test_report_tables_escape_data_and_retain_diagnostics(data):
    (data/'data/input/measures.csv').write_text('score|<x>\n1\n2\n3\n')
    report=run(data,{'columns':['score|<x>']})['report_markdown']
    assert 'score&#124;&lt;x&gt;' in report and 'score|<x>' not in report
    assert 'Minimum' in report and 'Maximum' in report and 'Percentile' in report


def test_covariance_single_observation_keeps_matrix_shape_and_ddof_policy(data):
    (data/'data/input/measures.csv').write_text('x,y\n1,2\n')
    r=run(data,{'methods':['covariance'],'columns':['x','y'],'ddof':0})
    assert r['covariance_matrix']['values']==[[0,0],[0,0]]
    with pytest.raises(Exception,match='more complete rows'):
        run(data,{'methods':['covariance'],'columns':['x','y'],'ddof':1})


def test_terminal_report_reads_recorded_evidence_without_recalculation(data):
    from geoagent_harness.chat.workspace import Workspace,HELP
    report=run(data,{'columns':['x']})
    class Client:
        def __init__(self):self.calls=[]
        def post(self,path,payload):
            self.calls.append((path,payload))
            assert payload=={'action':'read','run_id':'a'*32}
            return {'run_id':'a'*32,'conversation_id':'b'*32,'status':'completed','steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','outcome':{'table_analysis':{'statistics':report}}}]}
    client=Client();workspace=Workspace(client,'b'*32);workspace.state={'revision':1}
    assert workspace.execute('/statistics '+'a'*32)==report['report_markdown']
    assert len(client.calls)==1 and '/statistics' in HELP


def test_planner_proposes_actual_statistics_not_just_a_summary(project):
    from tests.test_planner_conversation import Client
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    from geoagent_harness.operations.registry import operation_catalog
    (project/'data/input/measures.csv').write_text('x,y\n0,1\n1,3\n2,4\n3,5\n')
    spec={'methods':['describe','pearson','linear_regression'],'columns':['x','y'],'regression':{'outcome':'y','predictors':['x']}}
    reply={'message':'Statistical workflow prepared; nothing executed.','plan':{'summary':'Fit explicit statistical methods','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Read statistics','arguments':{'path':'data/input/measures.csv','analysis':{'statistics':spec}},'requires_approval':False,'validation_required':False}]}}
    client=Client(reply)
    r=conversation_turn(TurnRequest(action='turn',conversation_id='e'*32,message='Fit linear regression of y on x in measures.csv. Return standard deviation and Pearson correlation of x and y. No writes.'),project_root=project,model_client=client)
    assert r['planner_result']['plan']['steps'][0]['arguments']['analysis']['statistics']==spec
    assert len(client.requests)==1 and not r['execution_performed']
    system=json.loads(client.requests[0].messages[0].content)
    assert system['prompt_profile']=='statistics-focused-v1'
    assert sum(len(m.content.encode()) for m in client.requests[0].messages)<16000
    assert 'conversion_arguments_example' not in system
    assert list(system['operation_argument_schemas'])==['inspect_csv']
    assert 'StatisticsSpec' in system['operation_argument_schemas']['inspect_csv']['$defs']
    assert operation_catalog(project,'linear_regression')['operations'][0]['id']=='inspect_csv'
    from copy import deepcopy
    from jsonschema import Draft202012Validator
    validator=Draft202012Validator(client.requests[0].response_schema)
    assert validator.is_valid(reply)
    metadata=deepcopy(reply);metadata['plan']['steps'][0]['arguments'].pop('analysis')
    assert not validator.is_valid(metadata)
    null=deepcopy(reply);null['plan']['steps'][0]['arguments']['analysis']['statistics']=None
    assert not validator.is_valid(null)
    omitted=deepcopy(reply);omitted['plan']['steps'][0]['arguments']['analysis']['statistics']['methods']=['describe']
    assert not validator.is_valid(omitted)
    assert validator.is_valid({'message':'Which numeric outcome should be fitted?','plan':None})


def test_repeated_statistics_omission_is_not_filled_in_or_executed(project):
    from tests.test_planner_conversation import Client
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    from geoagent_harness.planner.agent import PlannerAgentError
    (project/'data/input/measures.csv').write_text('x,y\n0,1\n1,3\n2,4\n3,5\n')
    reply={'message':'I will fit the regression.','plan':{'summary':'Only metadata','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect','arguments':{'path':'data/input/measures.csv'}}]}}
    client=Client(reply,reply)
    with pytest.raises(PlannerAgentError) as error:
        conversation_turn(TurnRequest(action='turn',conversation_id='f'*32,message='Fit linear regression of y on x in measures.csv with cluster covariance grouped by patient. No writes.'),project_root=project,model_client=client)
    assert error.value.reason=='request_coverage_incomplete' and len(client.requests)==2
    definitions=client.requests[0].response_schema['$defs']
    spec=definitions['operation_inspect_csv_StatisticsSpec']
    regression=definitions['operation_inspect_csv_RegressionSpec']
    assert spec['properties']['methods']['const']==['linear_regression']
    assert 'columns' not in spec['properties']
    assert regression['properties']['covariance']['const']=='cluster'
    assert 'cluster_column' in regression['required']
    assert not (project/'workflow-state/interface-runs').exists()
    saved=conversation_turn(TurnRequest(action='read',conversation_id='f'*32),project_root=project)
    assert saved['planner_result'] is None and not saved['execution_performed']


def test_covariance_matrix_is_available_to_planner_without_regression(project):
    from tests.test_planner_conversation import Client
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    (project/'data/input/measures.csv').write_text('x,y\n0,1\n1,3\n2,4\n3,5\n')
    spec={'methods':['covariance'],'columns':['x','y']}
    client=Client({'message':'Proposed matrix.','plan':{'summary':'Covariance matrix','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Measure covariance','arguments':{'path':'data/input/measures.csv','analysis':{'statistics':spec}}}]}})
    r=conversation_turn(TurnRequest(action='turn',conversation_id='e'*32,message='Compute a covariance matrix for x and y in measures.csv. No writes.'),project_root=project,model_client=client)
    assert r['planner_result']['plan']['steps'][0]['arguments']['analysis']['statistics']==spec
    definition=client.requests[0].response_schema['$defs']['operation_inspect_csv_StatisticsSpec']
    assert definition['properties']['methods']['const']==['covariance']
    assert 'regression' not in definition['properties'] and not r['execution_performed']

def test_statistical_omissions_fail_and_unused_schema_definitions_are_pruned():
    from geoagent_harness.planner.request_coverage import validate_statistics_coverage,RequestedOperationOmission,statistical_request_requirements
    from geoagent_harness.planner.schemas import WorkflowPlan,PlanStep
    from geoagent_harness.planner.prompt_scope import prune_definitions
    plan=WorkflowPlan(summary='Incomplete',steps=[PlanStep(step_id='step_1',skill='inspect_csv',purpose='Inspect',arguments={'path':'data/input/measures.csv'})])
    with pytest.raises(RequestedOperationOmission,match='linear_regression'):validate_statistics_coverage(plan,'Fit linear regression of y on x.')
    validate_statistics_coverage(plan,'Inspect measures.csv. No linear regression.')
    assert statistical_request_requirements('Fit linear regression with cluster covariance grouped by patient.')[0]=={'linear_regression'}
    schema={'properties':{'x':{'$ref':'#/$defs/A'}},'$defs':{'A':{'$ref':'#/$defs/B'},'B':{'type':'string'},'unused':{'type':'number'}}}
    assert set(prune_definitions(schema)['$defs'])=={'A','B'}
