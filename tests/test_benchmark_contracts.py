"""P1-B1 fixtures only; no agent/model/DB calls or dataset processing."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path

from pydantic import ValidationError
import pytest
import yaml

from geoagent_harness.contracts.benchmark import BenchmarkTask, BenchmarkResult
from geoagent_harness.apps.benchmark import loader

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'benchmarks/tasks/s-csv-profile-001/task.yaml'


def definition():
    return yaml.safe_load(EXAMPLE.read_text())


@pytest.fixture
def project(tmp_path):
    directory = tmp_path / 'benchmarks/tasks/s-csv-profile-001'
    (directory / 'input').mkdir(parents=True)
    (directory / 'task.yaml').write_bytes(EXAMPLE.read_bytes())
    (directory / 'input/orders.csv').write_text('synthetic fixture content')
    return tmp_path, directory


def test_read_only_loader_hash_order_and_no_dataset_open(project, monkeypatch):
    root, directory = project
    original = os.open
    def checked(path, *args, **kwargs):
        assert str(path).endswith('task.yaml'), 'loading must not open input datasets'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(loader.os, 'open', checked)
    result = loader.load_suite(root)
    assert len(result) == 1 and result[0].available
    assert result[0].task_sha256 == hashlib.sha256((directory/'task.yaml').read_bytes()).hexdigest()
    assert result[0].task.model_dump(mode='json')['expected']['checks'][1]['expected'] == 3
    assert not list(root.glob('**/approvals')) and not list(root.glob('**/benchmark-runs'))


@pytest.mark.parametrize('changes', [
    {'id': '../outside'}, {'inputs': ['/etc/passwd']}, {'inputs': ['input/../secret']},
    {'inputs': ['input//a']}, {'inputs': ['input\\a']}, {'inputs': ['input/a', 'input/a']},
    {'inputs': ['data/input/private.csv']}, {'write_authority': True},
    {'limits': {'wall_clock_s': float('inf')}}, {'limits': {'model_calls': True}},
    {'expected': {'kind': 'deterministic', 'checks': []}},
    {'expected': {'kind': 'refusal', 'nothing_executed': False}},
    {'expected': {'kind': 'unsupported', 'reason_code': 'missing', 'checks': []}},
    {'expected': {'kind': 'deterministic', 'checks': [{'type': 'python', 'code': 'print(1)'}]}},
    {'expected': {'kind': 'deterministic', 'checks': [{'type': 'value_close', 'field': 'mean', 'expected': 1, 'tolerance': -1}]}},
    {'expected': {'kind': 'deterministic', 'checks': [{'type': 'file_exists', 'path': '../report'}]}},
])
def test_invalid_contracts_fail_closed(changes):
    value = definition(); value.update(changes)
    with pytest.raises(ValidationError):
        BenchmarkTask.model_validate(value)


def test_missing_local_inputs_are_unavailable_without_creating_them(project):
    root, directory = project
    value = definition(); value.update(requires_local_data=True, inputs=['data/input/private.csv'])
    (directory/'task.yaml').write_text(yaml.safe_dump(value))
    item = loader.load_task(root, value['id'])
    assert not item.available and item.missing_local_inputs == ('data/input/private.csv',)
    assert not (root/'data').exists()


@pytest.mark.parametrize('fault', ['bad_yaml','duplicate','alias','depth','nodes','huge','identity','missing_fixture','tag','invalid_schema','link','hardlink','directory','parent_link'])
def test_bad_files_are_rejected_without_payload_disclosure(project, fault, monkeypatch):
    root, directory = project; path = directory/'task.yaml'
    if fault == 'bad_yaml':path.write_text('request: [private-fixture-value')
    elif fault == 'duplicate':path.write_text(path.read_text()+'\nid: private-fixture-value\n')
    elif fault == 'alias':path.write_text('a: &a [1]\nb: *a\n')
    elif fault == 'depth':path.write_text('['*40+'0'+']'*40)
    elif fault == 'nodes':
        monkeypatch.setattr(loader, 'MAX_YAML_NODES', 2)
    elif fault == 'huge':path.write_bytes(b' '* (loader.MAX_TASK_BYTES+1))
    elif fault == 'identity':path.write_text(path.read_text().replace('id: s-csv-profile-001','id: different'))
    elif fault == 'missing_fixture':(directory/'input/orders.csv').unlink()
    elif fault == 'tag':path.write_text('!!python/object/apply:os.system [echo private-fixture-value]')
    elif fault == 'invalid_schema':path.write_text('request: private-fixture-value')
    elif fault == 'link':
        path.rename(directory/'original');path.symlink_to(directory/'original')
    elif fault == 'hardlink':os.link(path,directory/'linked')
    elif fault == 'directory':path.unlink();path.mkdir()
    elif fault == 'parent_link':
        (directory/'input').rename(directory/'original-input');(directory/'input').symlink_to(directory/'original-input')
    with pytest.raises(loader.BenchmarkLoadError) as error:
        loader.load_task(root, 's-csv-profile-001')
    assert 'private-fixture-value' not in str(error.value)


def test_gold_reference_is_required_and_must_stay_inside_fixture(project):
    root,directory=project;value=definition();value['expected']={'kind':'gold_set','path':'expected/gold.json'}
    (directory/'task.yaml').write_text(yaml.safe_dump(value))
    with pytest.raises(loader.BenchmarkLoadError):loader.load_suite(root)
    (directory/'expected').mkdir();(directory/'expected/gold.json').write_text('{}')
    assert loader.load_suite(root)[0].available


def test_suite_limits_and_deterministic_order(project, monkeypatch):
    root,directory=project
    other=directory.parent/'a-second';other.mkdir();(other/'input').mkdir()
    (other/'input/orders.csv').write_text('fixture')
    value=definition();value['id']='a-second';(other/'task.yaml').write_text(yaml.safe_dump(value))
    assert [r.task.id for r in loader.load_suite(root)]==['a-second','s-csv-profile-001']
    monkeypatch.setattr(loader,'MAX_TASKS',1)
    with pytest.raises(loader.BenchmarkLoadError,match='count'):loader.load_suite(root)
    monkeypatch.setattr(loader,'MAX_TASKS',256);monkeypatch.setattr(loader,'MAX_SUITE_BYTES',1)
    with pytest.raises(loader.BenchmarkLoadError,match='bytes'):loader.load_suite(root)


def result():
    return dict(run_id='1'*32,task_id='s-csv-profile-001',task_sha256='a'*64,
        evidence_kind='fixture',provider_profile_id='fixture',code_version='b'*40,
        source_dirty=False,egress_class='raw',expected_kind='deterministic',
        status='passed',observed_outcome='completed',executed_operations=1,reason_code='checks_passed',
        checks=[{'check_index':0,'status':'passed','reason_code':'matches'}],
        metrics={'model_calls':0,'wall_seconds':0.1})


def test_results_preserve_unknown_metrics_and_bind_provenance():
    record=BenchmarkResult.model_validate(result())
    assert record.metrics.prompt_tokens is None and record.metrics.process_sampled_peak_rss_bytes is None
    assert BenchmarkResult.model_validate_json(record.model_dump_json())==record
    schema=BenchmarkTask.model_json_schema()
    assert schema['additionalProperties'] is False


@pytest.mark.parametrize('change', [
    {'evidence_kind':'real_model'}, {'task_sha256':'invalid'}, {'code_version':'main'},
    {'checks':[]}, {'observed_outcome':'unknown'}, {'expected_kind':'unsupported'},
    {'metrics':{'model_calls':True,'wall_seconds':1}},
    {'metrics':{'model_calls':1,'wall_seconds':float('nan')}},
    {'metrics':{'model_calls':2,'wall_seconds':1,'roles':[{'role':'planner','model_calls':1}]}},
    {'checks':[{'check_index':0,'status':'failed','reason_code':'mismatch'}]},
    {'status':'skipped','observed_outcome':'not_dispatched','executed_operations':1},
    {'expected_kind':'refusal','observed_outcome':'refused','executed_operations':None},
])
def test_result_cannot_claim_unproven_success(change):
    value=result();value.update(deepcopy(change))
    with pytest.raises(ValidationError):BenchmarkResult.model_validate(value)


def test_refusal_requires_observed_zero_execution_and_real_model_identity():
    value=result();value.update(expected_kind='refusal',observed_outcome='refused',executed_operations=0,
        evidence_kind='real_model',model='fixture-local-name',checks=[])
    record=BenchmarkResult.model_validate(value)
    assert record.status=='passed' and record.evidence_kind=='real_model'
    # This tests schema acceptance only; no real model was called.
    value.update(status='skipped',observed_outcome='not_dispatched')
    assert BenchmarkResult.model_validate(value).status=='skipped'


def test_validated_task_collections_are_immutable():
    task = BenchmarkTask.model_validate(definition())
    with pytest.raises(ValidationError):
        task.request = 'changed after validation'
    assert isinstance(task.inputs, tuple)
    assert isinstance(task.expected.checks, tuple)
    assert isinstance(task.expected.checks[0].columns, tuple)


def test_empty_suite_and_unsafe_inventory_are_not_success(tmp_path):
    directory=tmp_path/'benchmarks/tasks';directory.mkdir(parents=True)
    with pytest.raises(loader.BenchmarkLoadError,match='empty'):loader.load_suite(tmp_path)
    (directory/'unexpected.txt').write_text('not a task directory')
    with pytest.raises(loader.BenchmarkLoadError,match='only task directories'):loader.load_suite(tmp_path)


def test_passing_refusal_cannot_hide_a_failed_check():
    value=result();value.update(expected_kind='refusal',observed_outcome='refused',executed_operations=0,
        checks=[{'check_index':0,'status':'failed','reason_code':'mismatch'}])
    with pytest.raises(ValidationError):BenchmarkResult.model_validate(value)
