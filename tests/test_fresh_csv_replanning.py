"""Fresh-output requests do not need model-generated filenames or overwrite."""
import copy
from tests.test_planner_conversation import project, Client, ID, turn, read
from geoagent_harness.planner.bindings import refresh_inherited_csv_targets
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
import pytest


def proposal(target='data/output/prior_selection.csv'):
    return {'message':'Proposed selection','plan':{'summary':'Inspect and select CSV','steps':[
        {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect CSV','arguments':{'path':'sample_orders.csv'}},
        {'step_id':'step_2','skill':'select_csv_columns','purpose':'Select columns','arguments':{'path':'sample_orders.csv','columns':['order_id','region'],'target_path':target},'depends_on':['step_1']}]}}


def test_fresh_request_allocates_inherited_occupied_name_before_policy(project):
    initial=turn(project,Client(proposal()),'Inspect sample_orders.csv and select order_id and region to a fresh CSV.')
    target=project/'data/output/prior_selection.csv';target.parent.mkdir(exist_ok=True);target.write_text('previous bytes')
    result=turn(project,Client(proposal()),'Repeat the CSV selection with fresh outputs. Do not execute.',revision=1)
    new=result['planner_result']['plan']['steps'][1]['arguments']['target_path']
    assert new.startswith('data/output/result_') and new!=str(target.relative_to(project))
    assert target.read_text()=='previous bytes' and not (project/new).exists()
    assert 'allocated automatically' in result['messages'][-1]['content']
    assert not result['execution_performed'] and not result['approval_performed']


@pytest.mark.parametrize('message',[
    'Explain the current workflow.',
    'Use data/output/prior_selection.csv as the fresh CSV target.',
    'Use prior_selection.csv as the fresh CSV target.',
    'Do not create fresh outputs; explain the workflow.',
])
def test_explicit_names_and_nonfresh_requests_are_never_remapped(project,message):
    initial=turn(project,Client(proposal()),'Select columns in sample_orders.csv.')
    value=PlannerResult.model_validate({k:v for k,v in initial['planner_result'].items() if k in PlannerResult.model_fields})
    target=project/'data/output/prior_selection.csv';target.parent.mkdir(exist_ok=True);target.write_text('preserve')
    revised=value.plan.model_copy(deep=True)
    assert refresh_inherited_csv_targets(revised,value,project,message)==[]
    assert revised==value.plan and target.read_text()=='preserve'
