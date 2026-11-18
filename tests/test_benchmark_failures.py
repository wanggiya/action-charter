"""Benchmark findings expose trusted schema/rule metadata, never parser inputs."""
import json
import pytest
import yaml
from pydantic import BaseModel,ConfigDict,ValidationError
from tests.test_benchmark_runner import project
from geoagent_harness.agents.roles.planner.agent import PlannerAgentError
from geoagent_harness.apps.benchmark.worker import failure_details
from geoagent_harness.apps.benchmark.runner import run_suite
from geoagent_harness.apps.benchmark.reporting import build_report,markdown_report


def test_schema_findings_are_bounded_and_exclude_names_values_and_exception_text():
    class Input(BaseModel):
        model_config=ConfigDict(extra='forbid')
        columns:list[str]
    try:
        Input.model_validate({'columns':[{'private':'PRIVATE_VALUE'}],
                              'PRIVATE_FIELD_NAME':'PRIVATE_SECRET'})
    except ValidationError as cause:
        error=PlannerAgentError('Planner plan failed deterministic policy after one correction attempt PRIVATE_EXCEPTION',
                                correction_attempted=True,reason='PRIVATE_REASON')
        error.__cause__=cause
    value=failure_details(error,{})
    assert value['stage']=='planning' and value['category']=='planner_policy_rejected'
    assert value['correction_attempted'] and value['planner_reason'] is None
    assert value['schema_findings'] and len(value['schema_findings'])<=6
    assert 'columns' in json.dumps(value)
    assert 'PRIVATE_' not in json.dumps(value)


def test_fixed_policy_code_and_stage_preserve_unknown_details():
    cause=ValueError('Referenced operation must produce a CSV table')
    error=PlannerAgentError('Planner plan failed deterministic policy after one correction attempt')
    error.__cause__=cause
    value=failure_details(error,{})
    assert value['policy_rule']=='csv_producer_required'
    unknown=failure_details(RuntimeError('PRIVATE_SECRET at /private/file'),{'planning_status':'validated'})
    assert unknown['stage']=='execution' and unknown['policy_rule'] is None
    assert unknown['schema_findings']==[] and 'PRIVATE_' not in json.dumps(unknown)
    assert failure_details(error,{'planning_status':'validated','observed_outcome':'completed'})['stage']=='advisory_review'


def test_deep_schema_locations_cannot_exceed_findings_budget():
    cause=ValidationError.from_exception_data('BoundedInput',[{'type':'missing','loc':('columns',)*200,'input':{'private':'PRIVATE_VALUE'}}])
    error=PlannerAgentError('Planner model returned an invalid plan schema');error.__cause__=cause
    value=failure_details(error,{})
    assert len(value['schema_findings'][0])==1024
    assert 'PRIVATE_VALUE' not in json.dumps(value)


def test_failed_fixture_records_safe_findings_in_shared_report(project):
    folder=project/'benchmarks/tasks/s-csv-profile-001'
    task=yaml.safe_load((folder/'task.yaml').read_text())
    task['request']='Propose inspection of orders.csv using inspect_csv; do not write files.'
    (folder/'task.yaml').write_text(yaml.safe_dump(task))
    plan=json.loads((folder/'fixture-plan.json').read_text())
    plan['steps'][0]['arguments']['PRIVATE_FIELD_NAME']='PRIVATE_VALUE'
    (folder/'fixture-plan.json').write_text(json.dumps(plan))
    summary,path=run_suite(project,fixture=True)
    assert summary['counts']['failed']==1,summary
    report=build_report(project,path.name)
    details=report['results'][0]['failure_details']
    assert details['stage']=='planning' and details['schema_findings']
    assert 'PRIVATE_' not in json.dumps(report)+markdown_report(report)
    assert report['results'][0]['executed_operations']==0
