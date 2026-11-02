"""Analytical report views and explicitly requested evidence-file operations differ."""
import json
from tests.test_planner_conversation import project,Client,turn


def inspect():return {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect source','arguments':{'path':'sample_orders.csv','analysis':{'numeric_columns':['amount']}}}

def test_summary_report_uses_inspection_without_extra_file_operation(project):
    extra={'step_id':'step_2','skill':'generate_report','purpose':'Report','arguments':{}}
    client=Client({'message':'Report','plan':{'summary':'Inspect and report','steps':[inspect(),extra]}},
                  {'message':'Recorded inspection report','plan':{'summary':'Inspect and report','steps':[inspect()]}})
    result=turn(project,client,'Inspect sample_orders.csv and return a data-quality report. No writes.')
    assert len(client.requests)==2 and [s['skill'] for s in result['planner_result']['plan']['steps']]==['inspect_csv']
    system=json.loads(client.requests[0].messages[0].content)
    assert any('Do not add generate_report' in rule for rule in system['mandatory_rules'])
    schema=json.dumps(client.requests[0].response_schema)
    assert 'generate_report' not in schema
    assert not result['execution_performed'] and not result['approval_performed']


def test_explicit_evidence_operation_binds_current_task_before_review(project):
    client=Client({'message':'Proposed evidence persistence','plan':{'summary':'Persist workflow evidence','steps':[
      {'step_id':'step_1','skill':'validate_postgis_layer','purpose':'Validate existing layer','arguments':{'target_schema':'agent_sandbox','target_table':'fixture_table'},'validation_required':True},
      {'step_id':'step_2','skill':'generate_report','purpose':'Persist evidence report','arguments':{},'depends_on':['step_1']}]}})
    result=turn(project,client,'Prepare generate_report to persist an evidence report file for this task. Do not execute.')
    step=result['planner_result']['plan']['steps'][-1]
    assert step['arguments']['task_id']=='b'*32 and step['requires_approval']
    assert not result['execution_performed'] and not result['approval_performed']
