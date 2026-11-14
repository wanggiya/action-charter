"""Suite v1 manifests and shared-service fixture journeys; no owner data/live DB."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from geoagent_harness.apps.benchmark.loader import load_suite
from geoagent_harness.apps.benchmark.runner import run_suite
from geoagent_harness.apps.benchmark.checks import score
from geoagent_harness.contracts.benchmark import BenchmarkTask

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    shutil.copytree(ROOT/'benchmarks/tasks',tmp_path/'benchmarks/tasks')
    (tmp_path/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(tmp_path/'state')}))
    return tmp_path


def test_suite_inventory_has_real_checks_and_explicit_gaps():
    tasks=load_suite(ROOT)
    assert len(tasks)==27
    assert len({t.task.id for t in tasks})==27
    assert sum(t.task.expected.kind=='unsupported' for t in tasks)==3
    assert sum(t.task.requires_local_data for t in tasks)==1
    assert sum(t.task.runtime=='postgis' for t in tasks)==2
    for loaded in tasks:
        task=loaded.task
        if task.expected.kind=='deterministic':assert task.expected.checks
        if task.expected.kind=='refusal':assert task.write_mode=='read_only'
        if not task.requires_local_data and task.expected.kind!='unsupported':
            assert (ROOT/'benchmarks/tasks'/task.id/'fixture-plan.json').is_file()


def test_complete_file_fixture_suite_uses_real_operations_and_preserves_inputs(project):
    before={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (project/'benchmarks/tasks').rglob('*') if p.is_file()}
    result,directory=run_suite(project,fixture=True,allow_fixture_writes=True)
    tasks={t.task.id:t.task for t in load_suite(project)}
    assert result['complete']
    for record in result['results']:
        task=tasks[record['task_id']]
        needs_gis=task.requires_gis and not all(shutil.which(p) for p in ('ogr2ogr','ogrinfo','gdalinfo'))
        expected='unsupported' if task.expected.kind=='unsupported' else 'skipped' if task.requires_local_data or task.runtime=='postgis' or needs_gis else 'passed'
        assert record['status']==expected,record
        assert record['evidence_kind']=='fixture'
        if task.expected.kind=='refusal' and not needs_gis:
            assert record['executed_operations']==0 and record['status']=='passed'
    after={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (project/'benchmarks/tasks').rglob('*') if p.is_file()}
    assert before==after
    assert result['counts']['failed']==result['counts']['error']==result['counts']['timeout']==0
    assert not list((directory/'tasks').glob('*/database-fixture.json'))
    for job in (directory/'tasks').glob('*/job.json'):
        value=json.loads(job.read_text())
        assert not {'expected','checks','gold'}&value.keys()
        assert value['database'] is None


def test_fixture_requirement_never_grants_write_authority(project):
    result,directory=run_suite(project,fixture=True,task_id='h-select-001')
    assert result['results'][0]['status']=='skipped'
    assert result['results'][0]['reason_code']=='fixture_writes_not_enabled'
    assert not (directory/'tasks/h-select-001/data/output').exists()


def test_database_requirement_skips_without_explicit_adapter_opt_in(project):
    result,directory=run_suite(project,fixture=True,allow_fixture_writes=True,task_id='e-postgres-001')
    record=result['results'][0]
    assert record['status']=='skipped' and record['reason_code']=='disposable_database_not_enabled'
    assert not (directory/'tasks/e-postgres-001/database-fixture.json').exists()


def test_expected_output_hash_rejects_self_consistent_but_wrong_export(tmp_path):
    path=tmp_path/'data/output/result.csv';path.parent.mkdir(parents=True);path.write_text('id\nwrong\n')
    task=BenchmarkTask(id='hash-fixture',workload='S',title='Verify values',request='Check a synthetic export.',inputs=[],data_class='raw',
        expected={'kind':'deterministic','checks':[{'type':'file_exists','path':'data/output/result.csv','expected_sha256':hashlib.sha256(b'id\nright\n').hexdigest()}]})
    run={'steps':[{'step_id':'step_1','status':'validated_success','outcome':{'output':{'path':'data/output/result.csv','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}}]}
    assert score(task.expected,run,tmp_path)[0].status=='failed'


def test_literal_percentile_and_independent_validation_selectors(tmp_path):
    task=BenchmarkTask(id='selector-fixture',workload='H',title='Known median',request='Inspect a fixture.',inputs=[],data_class='raw',
        expected={'kind':'deterministic','checks':[{'type':'value_close','field':'step_1./percentiles/50.0','expected':1.5,'tolerance':1e-9},
            {'type':'row_count','field':'step_1.$validation.target_feature_count','expected':2}]})
    run={'steps':[{'step_id':'step_1','status':'validated_success','outcome':{'percentiles':{'50.0':1.5}},'validation_outcome':{'passed':True,'target_feature_count':2}}]}
    assert all(c.status=='passed' for c in score(task.expected,run,tmp_path))


def test_no_file_outputs_rejects_an_output_or_link(tmp_path):
    directory=tmp_path/'data/output';directory.mkdir(parents=True)
    task=BenchmarkTask(id='no-write-fixture',workload='S',title='No output',request='Read only.',inputs=[],data_class='raw',expected={'kind':'deterministic','checks':[{'type':'no_file_outputs'}]})
    assert score(task.expected,{},tmp_path)[0].status=='passed'
    (directory/'unexpected').symlink_to(tmp_path/'missing')
    assert score(task.expected,{},tmp_path)[0].status=='failed'


def test_local_data_cannot_be_declared_writable_or_database_backed():
    from pydantic import ValidationError
    for fields in ({'write_mode':'fixture'},{'runtime':'postgis'}):
        with pytest.raises(ValidationError):
            BenchmarkTask(id='local-fixture',workload='H',title='Local data',request='Inspect local data.',inputs=['data/input/private.csv'],requires_local_data=True,
                data_class='raw',expected={'kind':'deterministic','checks':[{'type':'row_count','field':'row_count','expected':1}]},**fields)


def test_file_checks_ignore_null_outputs_from_read_only_database_steps(tmp_path):
    path=tmp_path/'data/output/result.csv';path.parent.mkdir(parents=True);path.write_text('id\n1\n')
    task=BenchmarkTask(id='null-output',workload='E',title='Verified export',request='Export a fixture.',inputs=[],data_class='raw',expected={'kind':'deterministic','checks':[{'type':'file_exists','path':'data/output/result.csv'}]})
    run={'steps':[{'step_id':'step_1','status':'completed','outcome':{'output':None}},
        {'step_id':'step_2','status':'validated_success','outcome':{'output':{'path':'data/output/result.csv','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}}]}
    assert score(task.expected,run,tmp_path)[0].status=='passed'
