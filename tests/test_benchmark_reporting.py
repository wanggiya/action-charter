"""Sanitized baseline rendering is evidence-based, bounded and read-only."""
import copy
import json
from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner

from geoagent_harness.apps.benchmark.runner import run_suite
from geoagent_harness.apps.benchmark.reporting import build_report, markdown_report, source_sha256

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def measured(tmp_path_factory):
    project=tmp_path_factory.mktemp('baseline')
    shutil.copytree(ROOT/'benchmarks/tasks/s-csv-profile-001',project/'benchmarks/tasks/s-csv-profile-001')
    (project/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(project/'state')}))
    summary,directory=run_suite(project,fixture=True)
    assert summary['counts']['passed']==1
    return project,directory


def test_sanitized_report_has_measured_totals_and_reproducibility_context(measured):
    project,directory=measured
    before={p:p.read_bytes() for p in directory.glob('*.json')}
    report=build_report(project,directory.name)
    assert report['counts']['passed']==1 and report['complete']
    assert report['totals']['model_calls']>=1
    assert report['totals']['prompt_tokens'] is None
    assert report['context']['model_configuration'] is None
    assert report['source_unchanged'] is True
    assert report['context']['task_ids']==['s-csv-profile-001']
    assert 'pydantic' in report['context']['package_versions']
    text=json.dumps(report)+markdown_report(report)
    for forbidden in (str(project),'http://','base_url','orders.csv','fixture_plan','password'):
        assert forbidden not in text
    assert 'unknown' in markdown_report(report)
    assert before=={p:p.read_bytes() for p in directory.glob('*.json')}


@pytest.mark.parametrize('change',['counts','extra','task_record','scope','context'])
def test_report_rejects_mismatched_or_injected_evidence(measured,tmp_path,change):
    original,directory=measured
    project=tmp_path/'project';project.mkdir()
    (project/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(project/'state')}))
    target=project/'state/benchmark-runs'/directory.name
    target.mkdir(parents=True)
    for p in directory.glob('*.json'):shutil.copy2(p,target/p.name)
    summary=json.loads((target/'summary.json').read_text())
    if change=='counts':summary['counts']['passed']=99
    elif change=='extra':summary['raw_prompt']='private-canary'
    elif change=='task_record':
        path=target/'s-csv-profile-001.json';value=json.loads(path.read_text());value['metrics']['model_calls']+=1;value['metrics']['roles']=[];path.write_text(json.dumps(value))
    elif change=='scope':summary['context']['task_ids']=['another-task']
    else:summary['context']['base_url']='private-canary'
    (target/'summary.json').write_text(json.dumps(summary))
    with pytest.raises(ValueError):build_report(project,directory.name)


def test_legacy_report_keeps_unrecorded_settings_unknown(measured,tmp_path):
    _,directory=measured
    project=tmp_path/'project';project.mkdir()
    (project/'actioncharter.workspace.json').write_text(json.dumps({'version':1,'state_root':str(project/'state')}))
    target=project/'state/benchmark-runs'/directory.name;target.mkdir(parents=True)
    for p in directory.glob('*.json'):shutil.copy2(p,target/p.name)
    path=target/'summary.json';value=json.loads(path.read_text());value.pop('context');value.pop('source_unchanged');path.write_text(json.dumps(value))
    report=build_report(project,directory.name)
    assert report['context'] is None and report['source_unchanged'] is None
    assert 'Legacy run' in markdown_report(report)


def test_cli_report_shares_validated_renderer_and_rejects_traversal(measured):
    from geoagent_harness.apps.cli.main import app
    project,directory=measured;cli=CliRunner()
    result=cli.invoke(app,['benchmark','report',directory.name,'--project-root',str(project),'--format','json'])
    assert result.exit_code==0,result.output
    assert json.loads(result.stdout)==build_report(project,directory.name)
    invalid=cli.invoke(app,['benchmark','report','../outside','--project-root',str(project)])
    assert invalid.exit_code==2


def test_source_fingerprint_detects_changes_without_reading_env_or_private_data(tmp_path):
    (tmp_path/'src/geoagent_harness').mkdir(parents=True)
    (tmp_path/'src/geoagent_harness/example.py').write_text('x=1\n')
    for p in ('pyproject.toml','context/ARCHITECTURE.md','context/SKILLS_INDEX.yaml','context/DECISIONS.jsonl'):
        target=tmp_path/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('fixture\n')
    digest=source_sha256(tmp_path)
    (tmp_path/'.env').write_text('CANARY=private\n')
    (tmp_path/'data/input').mkdir(parents=True);(tmp_path/'data/input/private.csv').write_text('private\n')
    assert source_sha256(tmp_path)==digest
    (tmp_path/'src/geoagent_harness/example.py').write_text('x=2\n')
    assert source_sha256(tmp_path)!=digest


def test_ci_gate_rejects_missing_skipped_or_real_model_tasks():
    import importlib.util
    spec=importlib.util.spec_from_file_location('benchmark_ci',ROOT/'scripts/benchmark_ci.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    summary={'evidence_kind':'fixture','complete':True,'counts':{s:4 if s=='passed' else 0 for s in
        ('passed','failed','error','timeout','skipped','unsupported')},
        'results':[{'task_id':task,'status':'passed'} for task in module.TASKS]}
    assert module.verify(summary)['counts']['passed']==4
    for change in ('skip','missing','real','counts'):
        value=copy.deepcopy(summary)
        if change=='skip':value['results'][0]['status']='skipped'
        elif change=='missing':value['results'].pop()
        elif change=='real':value['evidence_kind']='real_model'
        else:value['counts']['passed']=99
        with pytest.raises(ValueError):module.verify(value)


def test_operation_selectors_accept_preinspection_but_never_ambiguous_results(tmp_path):
    from geoagent_harness.contracts.benchmark import DeterministicExpected
    from geoagent_harness.apps.benchmark.checks import score
    expected=DeterministicExpected(kind='deterministic',checks=[
        {'type':'row_count','field':'@convert_vector.$validation.target_feature_count','expected':2},
        {'type':'report_contains_columns','skill_id':'convert_vector','columns':['id']}])
    conversion={'step_id':'step_2','skill_id':'convert_vector','status':'validated_success',
        'outcome':{'columns':['id']},'validation_outcome':{'target_feature_count':2}}
    run={'steps':[{'step_id':'step_1','skill_id':'inspect_vector','status':'completed','outcome':{'columns':['wrong']}},conversion]}
    assert all(v.status=='passed' for v in score(expected,run,tmp_path))
    run['steps'].append({**conversion,'step_id':'step_3'})
    assert all(v.status=='error' for v in score(expected,run,tmp_path))
    with pytest.raises(ValueError):
        DeterministicExpected(kind='deterministic',checks=[{'type':'report_contains_columns','step_id':'step_1','skill_id':'inspect_csv','columns':['id']}])


def test_ci_preflight_rejects_missing_asset_outside_fast_subset(tmp_path,monkeypatch):
    import importlib.util
    from geoagent_harness.apps.benchmark.loader import BenchmarkLoadError
    spec=importlib.util.spec_from_file_location('benchmark_ci',ROOT/'scripts/benchmark_ci.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    shutil.copytree(ROOT/'benchmarks/tasks',tmp_path/'benchmarks/tasks')
    (tmp_path/'benchmarks/tasks/e-raster-001/input/grid.tif').unlink()
    def no_dispatch(*args,**kwargs):raise AssertionError('Missing source fixture must fail before dispatch')
    monkeypatch.setattr(module,'run_suite',no_dispatch)
    with pytest.raises(BenchmarkLoadError,match='missing'):module.main(tmp_path)
