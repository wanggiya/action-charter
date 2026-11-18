"""B6 profile pinning and comparisons use fake HTTP, synthetic keys and temp state."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread

import pytest
import yaml
from typer.testing import CliRunner

from tests.test_benchmark_runner import project
from geoagent_harness.apps.benchmark.runner import run_suite,_profile_snapshot
from geoagent_harness.apps.benchmark.reporting import build_report
from geoagent_harness.apps.benchmark.comparison import compare_runs,markdown_comparison
from geoagent_harness.contracts.model_providers import ProviderProfile,ProviderUpdate,ProviderSelection
from geoagent_harness.platform.model_gateway import profiles


@pytest.fixture
def endpoint():
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            calls.append({'payload':payload,'authorization':self.headers.get('Authorization')})
            system=json.loads(payload['messages'][0]['content'])
            if 'deterministic_status' in system.get('required_json_schema',{}).get('properties',{}):
                reply={'deterministic_status':'completed','conclusion':'supported','summary':'Fixture review.',
                       'findings':[],'limitations':['Fake HTTP test, not real model evidence.']}
            else:
                reply={'message':'Inspection proposed.','plan':{'summary':'Inspect table','steps':[
                    {'step_id':'step_1','skill':'inspect_csv','purpose':'Inspect source',
                     'arguments':{'path':'data/input/orders.csv'}}]}}
            body=json.dumps({'model':payload['model'],'choices':[{'message':{'content':json.dumps(reply)},'finish_reason':'stop'}],
                             'usage':{'prompt_tokens':11,'completion_tokens':7}}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_port}/v1',calls
    finally:server.shutdown();server.server_close();thread.join(timeout=3)


def save(root,url,**kwargs):
    profile=ProviderProfile.model_validate({'id':'candidate','base_url':url,'model':'small','data_allowed':'raw',**kwargs})
    profiles.save(root,ProviderUpdate(profile=profile,expected_revision=profiles.read(root).revision))
    return profile


def measure(root,url,**kwargs):
    save(root,url,**kwargs)
    path=root/'benchmarks/tasks/s-csv-profile-001/task.yaml'
    task=yaml.safe_load(path.read_text())
    task['request']='For the supplied table orders.csv, propose a read-only workflow returning row count and column names.'
    path.write_text(yaml.safe_dump(task))
    return run_suite(root,profile='candidate')


def test_explicit_snapshot_preserves_active_selection_and_project_reasoning(project,endpoint,monkeypatch):
    from geoagent_harness.platform.model_gateway.catalog import select_reasoning,ReasoningSelection
    url,_=endpoint;save(project,url)
    select_reasoning(project,ReasoningSelection(selection='none',expected_revision=0))
    before=profiles.store(project).read('model-providers.json')
    settings,binding,review,credentials=_profile_snapshot(project,'candidate')
    assert settings.model=='small' and settings.reasoning_effort=='none' and review==15
    assert binding['profile_id']=='candidate' and binding['provider_revision']==1
    assert binding['reasoning_selection_revision']==1
    assert credentials=={} and 'base_url' not in binding and 'credential_ref' not in binding
    assert profiles.store(project).read('model-providers.json')==before
    save(project,url,model='later')
    assert settings.model=='small' and binding['provider_revision']==1
    monkeypatch.setenv('MODEL_NAME','launcher');monkeypatch.setenv('MODEL_BASE_URL',url)
    profiles.select(project,ProviderSelection(profile_id='candidate',expected_revision=2))
    assert _profile_snapshot(project,'local')[0].model=='launcher'
    assert profiles.read(project).selected=='candidate'


@pytest.mark.parametrize('capabilities',['json_schema','text'])
def test_saved_profile_reaches_all_worker_calls_and_public_report_stays_private(project,endpoint,monkeypatch,capabilities):
    url,calls=endpoint;key='SYNTHETIC_B6_AUTH_KEY_987654'
    monkeypatch.setenv('B6_TEST_KEY',key);monkeypatch.setenv('B6_UNRELATED_SECRET','DO_NOT_FORWARD')
    from geoagent_harness.apps.benchmark import runner
    original=runner.subprocess.Popen;environments=[]
    def spawn(*args,**kwargs):
        if 'env' in kwargs:environments.append(kwargs['env'].copy())
        return original(*args,**kwargs)
    monkeypatch.setattr(runner.subprocess,'Popen',spawn)
    summary,directory=measure(project,url,credential_ref='env:B6_TEST_KEY',capabilities=capabilities)
    assert summary['counts']['passed']==1,summary
    assert calls and all(v['payload']['model']=='small' and v['authorization']=='Bearer '+key for v in calls)
    assert all('B6_UNRELATED_SECRET' not in e for e in environments)
    assert summary['context']['provider_binding']['profile_id']=='candidate'
    assert summary['context']['model_configuration']['response_format']==capabilities
    job=json.loads((directory/'tasks/s-csv-profile-001/job.json').read_text())
    assert job['settings']['model']=='small' and job['review_timeout_seconds']==15
    report=build_report(project,directory.name)
    assert report['results'][0]['metrics']['prompt_tokens']==11*len(calls)
    public=json.dumps(report)
    assert key not in public and url not in public and str(project) not in public
    assert profiles.read(project).selected=='local'
    for path in directory.rglob('*'):
        if path.is_file():assert key.encode() not in path.read_bytes()


def test_secret_file_resolves_privately_after_gate_without_copying_secret(project,endpoint):
    url,calls=endpoint;(project/'.secrets').mkdir();(project/'.secrets/model').write_text('SYNTHETIC_B6_FILE_KEY')
    summary,directory=measure(project,url,credential_ref='secret:model')
    assert summary['counts']['passed']==1
    assert all(c['authorization']=='Bearer SYNTHETIC_B6_FILE_KEY' for c in calls)
    assert not list(directory.rglob('.secrets'))


def test_profile_policy_refusal_does_not_dispatch_or_forward_credential(project,endpoint,monkeypatch):
    url,calls=endpoint;monkeypatch.setenv('B6_TEST_KEY','SYNTHETIC_BLOCKED_KEY')
    summary,_=measure(project,url,data_allowed='none',credential_ref='env:B6_TEST_KEY')
    assert summary['results'][0]['reason_code']=='model_data_class_blocked'
    assert calls==[]
    assert _profile_snapshot(project,'candidate')[3]=={}


def test_unknown_remote_and_fixture_profiles_fail_before_staging(project):
    with pytest.raises(ValueError,match='Unknown'):run_suite(project,profile='missing')
    save(project,'https://outside.invalid/v1')
    with pytest.raises(ValueError,match='loopback'):run_suite(project,profile='candidate')
    with pytest.raises(ValueError,match='Fixture'):run_suite(project,profile='candidate',fixture=True)
    assert not (project/'state/benchmark-runs').exists()


def test_changed_profile_during_staging_does_not_change_worker_settings(project,endpoint,monkeypatch):
    from geoagent_harness.apps.benchmark import runner
    url,calls=endpoint;original=runner._stage
    def stage(*args,**kwargs):
        value=original(*args,**kwargs);save(project,url,model='changed-after-snapshot');return value
    monkeypatch.setattr(runner,'_stage',stage)
    summary,_=measure(project,url)
    assert summary['results'][0]['model']=='small' and all(c['payload']['model']=='small' for c in calls)
    assert profiles.read(project).profiles[0].model=='changed-after-snapshot'


def test_comparison_is_read_only_flags_mismatch_and_rejects_tampered_inputs(project,endpoint):
    url,calls=endpoint
    first,a=measure(project,url,model='first')
    second,b=measure(project,url,model='second')
    before=len(calls)
    value=compare_runs(project,a.name,b.name)
    assert value['matched_recorded_conditions'] and value['performance_winner'] is None
    assert value['tasks'][0]['both_passed'] and value['tasks'][0]['right_minus_left_on_matched_passes'] is not None
    assert len(calls)==before and not value['execution_performed'] and not value['model_called']
    assert 'not established' in markdown_comparison(value)
    assert url not in json.dumps(value)
    from geoagent_harness.apps.cli.main import app
    result=CliRunner().invoke(app,['benchmark','compare',a.name,b.name,'--project-root',str(project),'--format','json'])
    assert result.exit_code==0,result.output
    assert json.loads(result.stdout)==value
    # Raw fixture bytes change without changing the YAML task definition.
    (project/'benchmarks/tasks/s-csv-profile-001/input/orders.csv').write_text('order_id,region,amount\n4,West,12\n')
    _,c=measure(project,url,model='third')
    mismatch=compare_runs(project,a.name,c.name)
    assert not mismatch['matched_recorded_conditions']
    assert 'different_input_identity' in mismatch['tasks'][0]['findings']
    assert mismatch['tasks'][0]['right_minus_left_on_matched_passes'] is None
    manifest=b/'s-csv-profile-001.inputs.json';data=json.loads(manifest.read_text());data['inputs'][0]['sha256']='0'*64
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='input manifest'):compare_runs(project,a.name,b.name)


def test_comparison_does_not_infer_efficiency_from_different_conditions_or_failed_work(project,endpoint):
    url,calls=endpoint;_,a=measure(project,url,model='first');_,b=measure(project,url,model='second')
    before=len(calls);originals={p:p.read_text() for p in b.glob('*.json')}
    for change,expected in [('configuration','different_model_configuration'),
                            ('source','unverified_stable_source'),('legacy','unrecorded_provider_binding'),
                            ('review','unrecorded_review_timeout'),('packages','different_package_versions'),
                            ('definition','different_task_definition'),('failure',None)]:
        for p,text in originals.items():p.write_text(text)
        summary=json.loads((b/'summary.json').read_text());started=json.loads((b/'started.json').read_text())
        if change=='configuration':summary['context']['model_configuration']['max_tokens']=513
        elif change=='source':summary['source_unchanged']=False
        elif change=='legacy':
            summary['context'].pop('provider_binding');summary['context'].pop('review_timeout_seconds')
            summary['results'][0].pop('input_manifest_sha256')
        elif change=='review':summary['context']['review_timeout_seconds']=None
        elif change=='packages':summary['context']['package_versions']['test-package']='1.0'
        elif change=='definition':summary['results'][0]['task_sha256']='1'*64
        else:
            summary['results'][0].update(status='failed',reason_code='checks_failed')
            summary['results'][0]['checks'][0]['status']='failed'
            summary['counts'].update(passed=0,failed=1)
        started['context']=summary['context']
        (b/'summary.json').write_text(json.dumps(summary));(b/'started.json').write_text(json.dumps(started))
        (b/'s-csv-profile-001.json').write_text(json.dumps(summary['results'][0]))
        result=compare_runs(project,a.name,b.name)
        assert result['performance_winner'] is None
        if expected:
            assert expected in [*result['findings'],*result['tasks'][0]['findings']]
            assert not result['matched_recorded_conditions']
        else:assert not result['tasks'][0]['both_passed']
        assert result['tasks'][0]['right_minus_left_on_matched_passes'] is None
    assert len(calls)==before


def test_report_rejects_malformed_root_records_without_echoing_input(project,endpoint):
    from geoagent_harness.apps.cli.main import app
    url,_=endpoint;_,directory=measure(project,url)
    for name in ('summary.json','started.json','s-csv-profile-001.inputs.json'):
        path=directory/name;original=path.read_text();path.write_text('[{"private":"DO_NOT_ECHO"}]')
        result=CliRunner().invoke(app,['benchmark','report',directory.name,'--project-root',str(project)])
        assert result.exit_code==2 and 'DO_NOT_ECHO' not in result.output
        path.write_text(original)


def test_prepared_worker_profile_is_verified_without_overwrite(project,endpoint,monkeypatch):
    from dataclasses import replace
    from geoagent_harness.apps.benchmark.worker import bind_profile
    url,calls=endpoint;save(project,url)
    profiles.select(project,ProviderSelection(profile_id='candidate',expected_revision=1))
    settings=profiles.capture(project).settings();before=profiles.store(project).read('model-providers.json')
    bind_profile(project,settings)
    assert profiles.store(project).read('model-providers.json')==before
    with pytest.raises(ValueError,match='differs'):bind_profile(project,replace(settings,model='different'))
    assert profiles.store(project).read('model-providers.json')==before and calls==[]
