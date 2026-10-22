"""Planner proposes bounded result views without replacing or executing workflows."""
import hashlib
import json
import pytest
from tests.test_planner_conversation import project, Client, turn, read, ID
from geoagent_harness.interface_api.workflow_runs import _directory, _write
from geoagent_harness.planner.agent import PlannerAgentError


def seed(project):
    reply={'message':'Ready','plan':{'summary':'Inspect orders','steps':[{'step_id':'step_1','skill':'inspect_csv',
        'purpose':'Inspect CSV','arguments':{'path':'sample_orders.csv'},'requires_approval':False}]}}
    state=turn(project,Client(reply),'Inspect sample_orders.csv. Return row count and column names. No writes.')
    source=project/'data/input/sample_orders.csv'
    record={'run_id':'a'*32,'plan_sha256':state['planner_result']['plan_sha256'],'conversation_id':ID,'status':'completed',
        'steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','arguments':{'path':'data/input/sample_orders.csv'},
            'outcome':{'source':'data/input/sample_orders.csv','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'columns':['order_id','region','amount'],'preview':[],'row_count':6}}]}
    _write(_directory(project),record)
    spec={'run_id':record['run_id'],'plan_sha256':record['plan_sha256'],'step_id':'step_1','view':'Chart',
          'chart':{'group_by':'region','value':'amount','aggregation':'sum'},'chart_kind':'bar'}
    return state,spec


def test_planner_view_preserves_workflow_and_receives_no_row_values(project,monkeypatch):
    original,spec=seed(project)
    from geoagent_harness.interface_api import result_preview
    monkeypatch.setattr(result_preview,'read_bytes',lambda *a,**kw:pytest.fail('Preparing a view must not read dataset content'))
    client=Client({'message':'Show totals by region.','plan':None,'result_view':spec})
    result=turn(project,client,'Show total amount by region as a bar chart.',revision=1)
    assert result['planner_result']==original['planner_result'] and not result['proposal_changed']
    assert result['context_usage']['result_view']['chart']['aggregation']=='sum'
    context=json.loads(client.requests[0].messages[0].content)['result_view_context']
    assert context['results'][0]['columns']==['order_id','region','amount']
    assert 'preview' not in context['results'][0]
    assert not result['approval_performed'] and not result['execution_performed']
    assert len(list((project/'workflow-state/interface-runs').glob('*.json')))==1


@pytest.mark.parametrize('change',[
    {'run_id':'d'*32}, {'plan_sha256':'d'*64}, {'step_id':'step_2'},
    {'chart':{'group_by':'invented','value':'amount','aggregation':'sum'}},
])
def test_planner_view_cannot_invent_scope_or_fields(project,change):
    original,spec=seed(project)
    invalid={**spec,**change}
    client=Client({'message':'Chart.','plan':None,'result_view':invalid},{'message':'Chart.','plan':None,'result_view':invalid})
    with pytest.raises(PlannerAgentError):
        turn(project,client,'Show totals by region.',revision=1)
    assert read(project)['planner_result']==original['planner_result']
    assert read(project)['revision']==1
    assert len(client.requests)==2


def test_result_query_schema_not_sent_when_no_recorded_result(project):
    client=Client({'message':'Which result?','plan':None})
    turn(project,client,'Show a chart of results.')
    system=json.loads(client.requests[0].messages[0].content)
    assert 'result_view_context' not in system
    assert 'result_view' not in system['required_json_schema']['properties']
    assert 'ResultViewSpec' not in system['required_json_schema']['$defs']


def test_explicit_view_has_focused_schema_and_cannot_replace_workflow(project):
    original,spec=seed(project)
    wrong={'message':'Inspect again.','plan':original['planner_result']['plan']}
    client=Client(wrong,{'message':'Chart.','plan':None,'result_view':spec})
    result=turn(project,client,'Show total amount by region as a bar chart.',revision=1)
    assert len(client.requests)==2 and not result['proposal_changed']
    assert result['planner_result']==original['planner_result']
    system=json.loads(client.requests[0].messages[0].content)
    assert 'operation_argument_schemas' not in system
    assert 'WorkflowPlan' not in system['required_json_schema'].get('$defs',{})
    assert client.requests[0].response_schema['properties']['plan']['type']=='null'


def test_processing_request_does_not_use_view_only_route():
    from geoagent_harness.interface_api.result_exploration import requests_result_view
    assert not requests_result_view('Show a workflow that joins the CSV files and writes the result.')
    assert not requests_result_view('Inspect sample_orders.csv. Return row count and column names. No writes.')
    assert requests_result_view('Show the recorded result as a table.')


@pytest.mark.parametrize('message',[
    'Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.',
    'Replace the current workflow with this new task. Inspect sample_points.geojson. Return feature count, fields and CRS. No writes.',
])
def test_explicit_new_workflow_does_not_offer_recorded_view_fields(project,message):
    original,_=seed(project)
    from tests.test_planner_conversation import plan
    client=Client({'message':'New inspection prepared.','plan':plan()})
    result=turn(project,client,message,revision=1)
    system=json.loads(client.requests[0].messages[0].content)
    assert 'result_view_context' not in system
    assert 'ResultViewSpec' not in client.requests[0].response_schema.get('$defs',{})
    assert result['planner_result']['plan']['steps'][0]['skill']=='inspect_vector'
    assert result['proposal_changed'] and result['context_usage']['result_view'] is None
    assert not result['execution_performed']


def test_stale_inspection_summary_is_repaired_instead_of_satisfying_chart_request(project):
    original,spec=seed(project)
    client=Client({'message':'Inspection found 6 rows.','plan':None},
                  {'message':'Chart requested.','plan':None,'result_view':spec})
    result=turn(project,client,'Show total amount by region as a bar chart.',revision=1)
    assert len(client.requests)==2
    assert result['context_usage']['result_view']['chart']['aggregation']=='sum'
    assert result['planner_result']==original['planner_result']
    system=json.loads(client.requests[0].messages[0].content)
    assert 'query' not in system['required_json_schema']['$defs']['ResultViewSpec']['properties']


def test_genuine_missing_field_question_preserves_workflow(project):
    original,_=seed(project)
    client=Client({'message':'Which value column should be grouped by region?','plan':None})
    result=turn(project,client,'Show a bar chart by region.',revision=1)
    assert result['context_usage']['result_view'] is None
    assert result['planner_result']==original['planner_result']
    assert len(client.requests)==1



def test_explanation_uses_recorded_facts_not_model_numbers_and_reads_no_source(project,monkeypatch):
    original,spec=seed(project)
    from geoagent_harness.interface_api import result_preview
    monkeypatch.setattr(result_preview,'read_bytes',lambda *a,**kw:pytest.fail('An explanation must not read source data'))
    spec.update(view='Table',chart=None,explanation_fields=['row_count'])
    client=Client({'message':'There are 99999 rows with improved patient outcomes.','plan':None,'result_view':spec})
    result=turn(project,client,'Explain the current result row count.',revision=1)
    text=result['messages'][-1]['content']
    assert 'Row count: 6.' in text
    assert '99999' not in text and 'improved patient' not in text
    assert 'not a fresh source check' in text
    assert result['planner_result']==original['planner_result']
    assert not result['execution_performed']
    assert not client.requests
    assert result['context_usage']['model_request']['stage']=='recorded_evidence'
    assert result['context_usage']['included_messages']==0


def test_unknown_explanation_fact_cannot_be_promoted_to_verified_evidence(project):
    original,spec=seed(project)
    spec.update(view='Table',chart=None,explanation_fields=['mortality_cause'])
    reply={'message':'A claim','plan':None,'result_view':spec}
    with pytest.raises(PlannerAgentError):turn(project,Client(reply,reply),'Explain the current result mortality cause.',revision=1)
    assert read(project)['planner_result']==original['planner_result']


def test_spatial_display_contract_validates_kind_layer_and_band():
    from geoagent_harness.interface_api.exploration_contracts import ResultViewSpec
    from geoagent_harness.interface_api.result_exploration import validate_view
    context={'run_id':'a'*32,'plan_sha256':'b'*64,'results':[{'step_id':'step_1','views':['Map'],'spatial_kind':'raster','band_count':2}]}
    base={'run_id':'a'*32,'plan_sha256':'b'*64,'step_id':'step_1','view':'Map'}
    validate_view(ResultViewSpec(**base,spatial={'mode':'raster','bands':[2],'render':'ramp'}),context)
    for options in [{'mode':'raster','bands':[3]},{'mode':'vector','layer':'secret'},{'mode':'pixel','row':0,'column':0}]:
        with pytest.raises(ValueError):validate_view(ResultViewSpec(**base,spatial=options),context)
    context['results'][0].update(spatial_kind='vector',layers=['boundaries'])
    validate_view(ResultViewSpec(**base,spatial={'mode':'vector','layer':'boundaries'}),context)
    with pytest.raises(ValueError):validate_view(ResultViewSpec(**base,spatial={'mode':'vector','layer':'invented'}),context)



def test_raster_decoder_does_not_offer_vector_layer_as_a_band():
    from geoagent_harness.interface_api.exploration_contracts import ResultViewReply
    from geoagent_harness.interface_api.result_exploration import bind_view_schema
    context={'run_id':'a'*32,'plan_sha256':'b'*64,'results':[{'step_id':'step_1','views':['Map'],'spatial_kind':'raster','band_count':2,'recorded_facts':{'band_count':2}}]}
    schema=bind_view_schema(ResultViewReply.model_json_schema(),context)
    spatial=schema['$defs']['SpatialViewOptions']
    assert not {'layer','row','column'} & spatial['properties'].keys()
    assert {'mode','bands','render'}.issubset(spatial['required'])



def test_local_explanation_needs_no_model_configuration(project,monkeypatch):
    seed(project)
    import geoagent_harness.interface_api.conversation as service
    monkeypatch.setattr(service,'load_model_settings',lambda:pytest.fail('Recorded facts do not require a model'))
    result=service.conversation_turn(service.TurnRequest(action='turn',conversation_id=ID,expected_revision=1,message='Explain the current result row count.'),project_root=project)
    assert 'Row count: 6.' in result['messages'][-1]['content']
    assert result['context_usage']['model_request']['model_calls']==0
