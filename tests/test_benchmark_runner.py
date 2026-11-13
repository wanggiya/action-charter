"""B2/B3: actual governed fixture execution and negative evidence tests; no live DB/model."""
import hashlib
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from geoagent_harness.apps.benchmark.runner import run_suite
from geoagent_harness.apps.benchmark import checks
from geoagent_harness.contracts.benchmark import BenchmarkTask

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    import shutil
    shutil.copytree(ROOT/'benchmarks/tasks',tmp_path/'benchmarks/tasks')
    (tmp_path/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(tmp_path/'state')}))
    return tmp_path


def task(project):
    path=project/'benchmarks/tasks/s-csv-profile-001/task.yaml'
    return path,yaml.safe_load(path.read_text())


def test_fixture_executes_real_pipeline_without_model_or_owner_configuration(project,monkeypatch):
    monkeypatch.setenv('POSTGRES_PASSWORD','private-fixture-value')
    monkeypatch.setenv('GEOAGENT_INPUT_ROOT','/not/the/fixture')
    result,directory=run_suite(project,fixture=True)
    record=result['results'][0]
    assert record['status']=='passed',json.dumps(record)
    assert record['executed_operations']==1
    assert len(record['checks'])==2 and all(c['status']=='passed' for c in record['checks'])
    assert record['evidence_kind']=='fixture'
    assert record['metrics']['prompt_tokens'] is None
    assert 'private-fixture-value' not in (directory/'summary.json').read_text()
    job=json.loads((directory/'tasks/s-csv-profile-001/job.json').read_text())
    assert 'expected' not in job and 'checks' not in job and 'task' not in job
    assert not (project/'data').exists()
    assert (directory/'s-csv-profile-001.inputs.json').exists()
    assert (directory/'tasks/s-csv-profile-001/state').is_dir()


def test_wrong_expected_count_fails_instead_of_teaching_answer_to_fixture(project):
    path,value=task(project);value['expected']['checks'][1]['expected']=999
    path.write_text(yaml.safe_dump(value))
    result,_=run_suite(project,fixture=True)
    assert result['results'][0]['status']=='failed'
    assert result['results'][0]['checks'][1]['status']=='failed'
    assert result['results'][0]['reason_code']=='checks_failed'


def test_missing_or_non_opted_in_local_data_skips_before_model_or_execution(project):
    path,value=task(project);value.update(requires_local_data=True,inputs=['data/input/private.csv'])
    path.write_text(yaml.safe_dump(value))
    result,_=run_suite(project,fixture=True)
    record=result['results'][0]
    assert record['status']=='skipped' and record['metrics']['model_calls']==0 and record['executed_operations']==0
    (project/'data/input').mkdir(parents=True);(project/'data/input/private.csv').write_text('local fixture')
    skipped,_=run_suite(project,fixture=True)
    assert skipped['results'][0]['reason_code']=='local_data_not_enabled'


def test_tiny_wall_budget_stops_process_and_does_not_claim_refusal_or_success(project):
    path,value=task(project);value['limits']['wall_clock_s']=.001;value['expected']={'kind':'refusal'}
    path.write_text(yaml.safe_dump(value))
    result,directory=run_suite(project,fixture=True)
    record=result['results'][0]
    assert record['status']=='timeout' and record['executed_operations'] in {0,None}
    assert record['observed_outcome'] in {'unknown','not_dispatched'}
    assert record['metrics']['timeouts']==1
    assert (directory/'started.json').exists() and (directory/'summary.json').exists()


def test_explicit_fixture_write_requires_exact_normal_authorization(project):
    path,value=task(project);value['request']='Select order_id and amount from orders.csv and save to data/output/projected.csv. Prepare only.'
    value['expected']={'kind':'deterministic','checks':[{'type':'file_exists','path':'data/output/projected.csv'}]}
    path.write_text(yaml.safe_dump(value))
    plan={'summary':'Fixture column projection','steps':[{'step_id':'step_1','skill':'select_csv_columns','purpose':'Project columns',
        'arguments':{'path':'data/input/orders.csv','columns':['order_id','amount'],'target_path':'data/output/projected.csv'},
        'requires_approval':True,'validation_required':True}]}
    (path.parent/'fixture-plan.json').write_text(json.dumps(plan))
    blocked,blocked_dir=run_suite(project,fixture=True)
    assert blocked['results'][0]['executed_operations']==0
    assert not list((blocked_dir/'tasks/s-csv-profile-001/data/output').iterdir())
    result,directory=run_suite(project,fixture=True,allow_fixture_writes=True)
    record=result['results'][0]
    assert record['status']=='passed',json.dumps(record)
    assert record['metrics']['approvals_required']==1
    assert list((directory/'tasks/s-csv-profile-001/state/approvals').glob('*.json'))
    assert (path.parent/'input/orders.csv').read_bytes()==(ROOT/'benchmarks/tasks/s-csv-profile-001/input/orders.csv').read_bytes()


def run_evidence(outcome):
    return {'status':'completed','steps':[{'step_id':'step_1','skill_id':'inspect_csv','status':'completed','outcome':outcome}]}


@pytest.mark.parametrize('kind,value,wanted',[
    ('row_count',3,'passed'),('row_count',3.0,'failed'),('row_count',True,'error'),
    ('value_close',3.05,'passed'),('value_close',30,'failed'),('value_close',float('nan'),'error')])
def test_numeric_scorers_check_observed_values_with_tolerance(kind,value,wanted,project):
    _,definition=task(project)
    check={'type':kind,'field':'row_count','expected':3}
    if kind=='value_close':check['tolerance']=.1
    definition['expected']={'kind':'deterministic','checks':[check]}
    expected=BenchmarkTask.model_validate(definition).expected
    assert checks.score(expected,run_evidence({'row_count':value}),project)[0].status==wanted


def test_missing_ambiguous_and_unrelated_evidence_cannot_pass(project):
    _,value=task(project);expected=BenchmarkTask.model_validate(value).expected
    run=run_evidence({'row_count':3,'columns':['wrong']})
    assert checks.score(expected,run,project)[0].status=='failed'
    run['steps'].append({**run['steps'][0],'step_id':'step_2'})
    assert checks.score(expected,run,project)[1].status=='error'
    run['steps'][0]['status']='failed';run['steps'][1]['status']='queued'
    assert all(c.status!='passed' for c in checks.score(expected,run,project))


def test_file_check_requires_matching_receipt_and_rejects_tamper_and_links(project):
    _,value=task(project);value['expected']={'kind':'deterministic','checks':[{'type':'file_exists','path':'data/output/file.csv'}]}
    expected=BenchmarkTask.model_validate(value).expected
    out=project/'data/output/file.csv';out.parent.mkdir(parents=True);out.write_text('fixture')
    run=run_evidence({'output':{'path':'data/output/file.csv','sha256':hashlib.sha256(out.read_bytes()).hexdigest()}})
    assert checks.score(expected,run,project)[0].status=='passed'
    out.write_text('tampered');assert checks.score(expected,run,project)[0].status=='failed'
    out.unlink();out.symlink_to(project/'benchmarks/tasks/s-csv-profile-001/input/orders.csv')
    assert checks.score(expected,run,project)[0].status=='error'


def test_table_check_needs_verified_exact_target_and_never_connects(project):
    _,value=task(project);value['expected']={'kind':'deterministic','checks':[{'type':'table_exists','schema_name':'public','table':'fixture'}]}
    expected=BenchmarkTask.model_validate(value).expected
    run=run_evidence({'passed':True,'target':'public.fixture','committed':True,'workflow_executed':True})
    assert checks.score(expected,run,project)[0].status=='failed'
    run['steps'][0]['skill_id']='validate_postgres_import'
    assert checks.score(expected,run,project)[0].status=='passed'
    run['steps'][0]['outcome']['target']='public.other'
    assert checks.score(expected,run,project)[0].status=='failed'


@pytest.mark.parametrize('change',[{'observed_outcome':'error'},{'executed_operations':None},{'executed_operations':1},{'output_files':1}])
def test_refusal_requires_zero_execution_and_no_output(change):
    observation={'observed_outcome':'refused','executed_operations':0,'output_files':0};observation.update(change)
    assert not checks.refusal_passes(observation)


def test_cli_lists_and_runs_same_runner(project):
    from geoagent_harness.apps.cli.main import app
    runner=CliRunner()
    listed=runner.invoke(app,['benchmark','list','--project-root',str(project)])
    assert listed.exit_code==0 and json.loads(listed.stdout)[0]['id']=='s-csv-profile-001'
    invoked=runner.invoke(app,['benchmark','run','--fixture','--project-root',str(project)])
    assert invoked.exit_code==0,invoked.stdout
    assert json.loads(invoked.stdout)['tasks'][0]['status']=='passed'


def test_zero_call_budget_blocks_model_generation_without_dispatch(project):
    path,value=task(project);value['request']='Select order_id from orders.csv into data/output/limited.csv. Prepare only.'
    value['limits']['model_calls']=0;path.write_text(yaml.safe_dump(value))
    result,directory=run_suite(project,fixture=True,allow_fixture_writes=True)
    record=result['results'][0]
    assert record['status']=='failed' and record['executed_operations']==0
    assert record['metrics']['model_calls']==0
    assert record['reason_code']=='call_budget_exhausted'
    assert not list((directory/'tasks/s-csv-profile-001/data/output').iterdir())


def test_staging_collision_is_an_error_before_dispatch(project):
    path,value=task(project);value.update(requires_local_data=True,inputs=['input/orders.csv','data/input/orders.csv'])
    (project/'data/input').mkdir(parents=True);(project/'data/input/orders.csv').write_text('local fixture')
    path.write_text(yaml.safe_dump(value))
    result,_=run_suite(project,fixture=True,include_local_data=True)
    record=result['results'][0]
    assert record['status']=='error' and record['reason_code']=='benchmark_setup_error'
    assert record['metrics']['model_calls']==0


def test_remote_profile_is_rejected_before_any_worker_or_network(project,monkeypatch):
    monkeypatch.setenv('MODEL_NAME','fixture-model')
    monkeypatch.setenv('MODEL_BASE_URL','https://outside.invalid/v1')
    with pytest.raises(ValueError,match='loopback'):run_suite(project)
    assert not (project/'state/benchmark-runs').exists()


def test_cancellation_preserves_partial_state_and_stops_worker(project,monkeypatch):
    from geoagent_harness.apps.benchmark import runner
    def interrupted(_):raise KeyboardInterrupt()
    monkeypatch.setattr(runner,'_pause',interrupted)
    result,directory=run_suite(project,fixture=True)
    assert result['results'][0]['reason_code']=='cancelled'
    assert result['results'][0]['executed_operations'] is None
    assert (directory/'started.json').exists() and (directory/'summary.json').exists()
    assert result['complete'] is False


def test_local_endpoint_path_records_reported_usage_and_separates_critic_from_score(project,monkeypatch):
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    from threading import Thread
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            calls.append(payload)
            # Valid fixed planning proposal, intentionally invalid advisory reply.
            schema=payload.get('response_format',{}).get('json_schema',{}).get('schema',{})
            response={} if 'deterministic_status' in schema.get('properties',{}) else {'message':'Fixture proposal','plan':{'summary':'Inspect CSV','steps':[{'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect fixture','arguments':{'path':'data/input/orders.csv'}}]}}
            body=json.dumps({'choices':[{'message':{'content':json.dumps(response)},'finish_reason':'stop'}],
                'model':'mock-local-endpoint','usage':{'prompt_tokens':17,'completion_tokens':2}}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setenv('MODEL_NAME','mock-local-endpoint')
    monkeypatch.setenv('MODEL_BASE_URL',f'http://127.0.0.1:{server.server_port}/v1')
    try:
        result,_=run_suite(project)
        record=result['results'][0]
        assert record['status']=='passed',record
        assert record['advisory_status']=='unavailable'
        assert record['metrics']['model_calls']==len(calls)>=1
        assert record['metrics']['prompt_tokens']==17*len(calls) and record['metrics']['completion_tokens']==2*len(calls)
        assert record['metrics']['roles'][0]['role']=='critic'
    finally:
        server.shutdown();server.server_close();thread.join()


def test_postgis_receipt_requires_exact_target_and_observed_existence(project):
    _,value=task(project);value['expected']={'kind':'deterministic','checks':[{'type':'table_exists','schema_name':'public','table':'fixture'}]}
    expected=BenchmarkTask.model_validate(value).expected
    run=run_evidence({'passed':True,'table_exists':True,'target_schema':'public','target_table':'fixture'})
    run['steps'][0]['skill_id']='validate_postgis_layer'
    assert checks.score(expected,run,project)[0].status=='passed'
    run['steps'][0]['outcome']['table_exists']=False
    assert checks.score(expected,run,project)[0].status=='failed'


def test_run_staging_budget_is_checked_before_data_dispatch(project,monkeypatch):
    from geoagent_harness.apps.benchmark import runner
    monkeypatch.setattr(runner,'MAX_RUN_INPUT_BYTES',1)
    result,_=run_suite(project,fixture=True)
    record=result['results'][0]
    assert record['status']=='error' and record['metrics']['model_calls']==0


def test_columns_check_can_bind_exact_step_in_multistep_workflow(project):
    _,value=task(project);value['expected']={'kind':'deterministic','checks':[{'type':'report_contains_columns','columns':['amount'],'step_id':'step_2'}]}
    expected=BenchmarkTask.model_validate(value).expected
    run=run_evidence({'columns':['wrong']});run['steps'].append({'step_id':'step_2','skill_id':'select_csv_columns','status':'completed','outcome':{'columns':['amount']}})
    assert checks.score(expected,run,project)[0].status=='passed'
