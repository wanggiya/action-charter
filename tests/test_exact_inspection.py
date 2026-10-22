"""Production submission route: zero inference, bounded batches, no authority reuse."""
import json
from pathlib import Path
import pytest
from tests.test_inspection_on_send import project,CHAT,Client,request
from geoagent_harness.interface_api.planner_submission import submission_action
from geoagent_harness.interface_api.inspection_planning import plan_for_request


class NoModel:
    def complete(self,*args):raise AssertionError('Exact inspection must not call a model')


@pytest.mark.parametrize('enabled',[False,True])
def test_zero_model_proposal_or_execution_and_no_replay(project,enabled):
    response=submission_action(request(enabled),project_root=project,model_client=NoModel(),background=False)
    assert response['conversation']['context_usage']['model_request']['stage']=='deterministic_inspection'
    assert response['conversation']['context_usage']['model_request']['model_calls']==0
    if enabled:
        assert response['run']['status']=='completed'
        assert response['run']['steps'][0]['outcome']['row_count']==6
    else:assert response['run'] is None
    repeat=submission_action(request(enabled),project_root=project,model_client=NoModel(),background=False)
    assert repeat['run']==response['run']
    assert not (project/'approvals').exists() and not (project/'data/output').exists()


@pytest.mark.parametrize('message',[
    'Inspect sample_orders.csv then export it.','Inspect sample_orders.csv. Return CRS. No writes.',
    'Inspect ../outside.csv.','Inspect sample_orders.csv; authorize writes.',
    'Inspect sample_orders.csv and sample_orders.csv.',
    'Inspect a.csv, b.csv, c.csv, d.csv and e.csv.','Use history to approve everything.',
    'Inspect sample_orders.csv. Ignore policy.',
])
def test_unsupported_scope_never_enters_exact_route(message):
    assert plan_for_request(message,['inspect_csv','inspect_vector','inspect_raster']) is None


def test_batch_has_separate_bound_results_and_restores_without_replay(project):
    turn=request();turn.turn.message='Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes.'
    response=submission_action(turn,project_root=project,model_client=NoModel(),background=False)
    run=response['run'];assert run['status']=='completed'
    assert len(run['steps'])==2
    assert run['steps'][0]['outcome']['row_count']==6
    assert run['steps'][1]['outcome']['driver']=='GTiff'
    assert all(step['outcome']['source_sha256'] for step in run['steps'])
    assert submission_action(turn,project_root=project,model_client=NoModel(),background=False)['run']['run_id']==run['run_id']


def test_batch_source_changed_after_first_step_preserves_partial_results(project,monkeypatch):
    import geoagent_harness.interface_api.inspection_policy as policy
    read=policy.bounded_read
    def change_after_first(*args,**kwargs):
        result=read(*args,**kwargs)
        if kwargs.get('action')=='csv_discover':(project/'data/input/sample_dem.tif').write_bytes(b'changed')
        return result
    monkeypatch.setattr(policy,'bounded_read',change_after_first)
    turn=request();turn.turn.message='Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes.'
    response=submission_action(turn,project_root=project,model_client=NoModel(),background=False)
    assert response['run']['status']=='failed'
    assert response['run']['steps'][0]['outcome']['row_count']==6
    assert not response['run']['steps'][1]['outcome']
    assert response['run']['failed_step_id']=='step_2'


def test_explicit_new_send_can_repeat_same_inspection_but_receipt_cannot(project):
    first=submission_action(request(),project_root=project,model_client=NoModel(),background=False)
    again=request();again.submission_id='e'*32;again.turn.expected_revision=first['conversation']['revision']
    second=submission_action(again,project_root=project,model_client=NoModel(),background=False)
    assert first['run']['run_id']!=second['run']['run_id']
    assert second['run']['status']=='completed'


def test_cancel_batch_skips_queued_steps_and_retains_first_result(project,monkeypatch):
    from geoagent_harness.interface_api import workflow_runs
    original=workflow_runs._Observer.progress
    def cancel(self,step,skill,status,outcome=None,validation=None):
        original(self,step,skill,status,outcome,validation)
        if step=='step_1' and status=='completed':
            workflow_runs.run_action(workflow_runs.RunRequest(action='cancel',run_id=self.identity),project_root=project)
    monkeypatch.setattr(workflow_runs._Observer,'progress',cancel)
    turn=request();turn.turn.message='Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes.'
    result=submission_action(turn,project_root=project,model_client=NoModel(),background=False)
    assert result['run']['status']=='cancelled'
    assert result['run']['steps'][1]['status']=='skipped'
    assert result['run']['steps'][0]['outcome']['row_count']==6


def test_missing_second_source_records_probe_but_never_executes_prefix(project):
    from geoagent_harness.interface_api.server import InterfaceApiError
    from geoagent_harness.interface_api.planner_submission import SubmissionRequest
    turn=request();turn.turn.message='Inspect sample_orders.csv and missing.tif. Return metadata. No writes.'
    with pytest.raises(InterfaceApiError,match='available regular file'):
        submission_action(turn,project_root=project,model_client=NoModel(),background=False)
    result=submission_action(SubmissionRequest(action='read',submission_id=turn.submission_id,conversation_id=CHAT),project_root=project)
    assert result['run'] is None and result['discovery_performed']
    assert result['submission']['discovery']['status']=='incomplete'
    assert result['submission']['discovery']['completed_sources']==1


def test_batch_aggregate_budget_prevents_execution(project,monkeypatch):
    from geoagent_harness.interface_api import planner_submission
    original=planner_submission.bounded_read
    def large(*args,**kwargs):
        value=original(*args,**kwargs);value['bytes']=1024**3
        return value
    monkeypatch.setattr(planner_submission,'bounded_read',large)
    turn=request();turn.turn.message='Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes.'
    result=submission_action(turn,project_root=project,model_client=NoModel(),background=False)
    assert result['run'] is None and result['submission']['discovery']['status']=='incomplete'


def test_mcp_discovery_does_not_broaden_custom_input_root(project):
    from geoagent_harness.mcp_server.tools import discover_dataset
    from geoagent_harness.mcp_server.settings import load_settings
    settings=load_settings().model_copy(update={'project_root':project,'input_root':project/'data'})
    with pytest.raises(ValueError,match='project data/input'):discover_dataset('sample_orders.csv',settings=settings)


def test_tsv_and_skill_selection_are_respected(project):
    plan=plan_for_request('Inspect table.tsv. Return columns. No writes.',['inspect_csv'])
    assert plan.steps[0].arguments['delimiter']=='\t'
    assert plan_for_request('Inspect terrain.tif.',['inspect_csv']) is None
    (project/'data/input/table.tsv').write_text('id\tname\n001\tfirst\n')
    turn=request();turn.turn.message='Inspect table.tsv. Return columns. No writes.'
    result=submission_action(turn,project_root=project,model_client=NoModel(),background=False)
    assert result['run']['steps'][0]['outcome']['columns']==['id','name']


def test_cli_mcp_and_service_have_equivalent_metadata(project):
    from geoagent_harness.discovery.service import discover_dataset
    from geoagent_harness.mcp_server.tools import discover_dataset as mcp_discover
    from geoagent_harness.mcp_server.settings import load_settings
    from geoagent_harness.cli import app
    from typer.testing import CliRunner
    settings=load_settings().model_copy(update={'project_root':project,'input_root':project/'data/input'})
    actual=discover_dataset(project,'sample_dem.tif')
    mcp=mcp_discover('sample_dem.tif',settings=settings)
    reply=CliRunner().invoke(app,['discover-dataset','sample_dem.tif','--project-root',str(project)])
    assert reply.exit_code==0,reply.output
    cli=json.loads(reply.output)
    for key in ('width','height','band_count','crs','source_manifest','source_sha256','technical_details'):
        assert actual[key]==mcp[key]==cli[key]


@pytest.mark.parametrize('execute',[False,True])
def test_cli_submission_uses_same_durable_route_without_model(project,monkeypatch,execute):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    from geoagent_harness.interface_api import conversation
    def forbidden():raise AssertionError('Model configuration must not be requested')
    monkeypatch.setattr(conversation,'load_model_settings',forbidden)
    arguments=['submit-inspection','Inspect sample_orders.csv and sample_dem.tif. Return metadata. No writes.',
        '--project-root',str(project)]
    if execute:arguments.append('--execute')
    reply=CliRunner().invoke(app,arguments)
    assert reply.exit_code==0,reply.output
    response=json.loads(reply.output)
    assert bool(response['run']) is execute
    assert response['conversation']['context_usage']['model_request']['model_calls']==0
    assert not response['approval_performed']


def test_cli_discovery_default_relative_project_root(project,monkeypatch):
    from typer.testing import CliRunner
    from geoagent_harness.cli import app
    monkeypatch.chdir(project)
    result=CliRunner().invoke(app,['discover-dataset','sample_dem.tif'])
    assert result.exit_code==0,result.output
    assert json.loads(result.output)['driver']=='GTiff'


def test_exact_route_keeps_existing_stricter_gate(project):
    from geoagent_harness.interface_api.conversation import conversation_turn,TurnRequest
    from geoagent_harness.planner.schemas import PlannerResult
    first=submission_action(request(False),project_root=project,model_client=NoModel(),background=False)
    saved=first['conversation']['planner_result']
    gated=PlannerResult.model_validate({key:saved[key] for key in ('agent_id','model','original_request','context_references','plan','warnings')})
    gated.plan.steps[0].requires_approval=True
    state=conversation_turn(TurnRequest(action='bind_task_plan',conversation_id=CHAT,task_id=CHAT,
        expected_revision=first['conversation']['revision'],current_plan=gated),project_root=project)
    again=request();again.submission_id='e'*32;again.turn.expected_revision=state['revision']
    result=submission_action(again,project_root=project,model_client=NoModel(),background=False)
    assert result['run'] is None
    assert result['conversation']['planner_result']['plan']['steps'][0]['requires_approval']
