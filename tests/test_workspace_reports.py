"""Relocated report/review/package lifecycle with disposable data and fixture assessments."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner

from tests.test_task_agents import project
from tests.test_workspace_layout import configure
from tests.test_workspace_authority import export_plan
from tests.test_reusable_recipes_and_runs import execution
from geoagent_harness.apps.http import server as api
from geoagent_harness.task_actions.workflow import execute_workflow
from geoagent_harness.contracts.critic import CriticResult
from geoagent_harness.platform.storage.critic_records import critic_result_sha256
from geoagent_harness.platform.workspace import runtime_store_path, WorkspaceError

STORES=('plans','approvals','workflow-recipes','recipe-runs','recipe-evidence',
        'workflow-state','traces','reports','critic-results','operational-history','releases')


@pytest.fixture(autouse=True)
def ordered_fixture_clock(monkeypatch):
    """Storage fixtures need valid ordering even if the host adjusts wall time.

    Keep the production trace validator strict. Clock anomalies are not evidence
    of broken relocation and are outside these fixture lifecycle assertions.
    """
    class Clock(datetime):
        latest = None

        @classmethod
        def now(cls, tz=None):
            observed = datetime.now(tz)
            if cls.latest is None or observed > cls.latest:
                cls.latest = observed
            return cls.latest

    monkeypatch.setattr(api, 'datetime', Clock)
    from geoagent_harness.task_actions import critic_review, release_review, legacy_export
    for owner in (critic_review, release_review, legacy_export):
        monkeypatch.setattr(owner, 'datetime', Clock)
    from geoagent_harness.task_actions import artifacts, execution
    monkeypatch.setattr(artifacts, 'datetime', Clock)
    monkeypatch.setattr(execution, 'datetime', Clock)


def lifecycle(project):
    """Actual temporary export/verification, supplied Critic assessment; no LLM."""
    run=execute_workflow(execution(project,export_plan()),project_root=project)
    candidate=api._interface_recipe_trace_candidates(project)[0]
    saved=api.save_interface_recipe_trace(api.InterfaceRecipeTraceSaveRequest(
        action='save_adapted_recipe_trace',evidence_name=candidate['evidence_name'],
        confirmed_trace_sha256=candidate['trace_sha256']),project_root=project)
    item=api.interface_critic_evidence_inventory(project)['items'][0]
    evidence=item['evidence'];assert evidence['deterministic_status']=='validated_success'
    critic=CriticResult(model='fixture-assessment',task_id=evidence['task_id'],
        deterministic_status=evidence['deterministic_status'],evidence_references=evidence['evidence_references'],
        evidence_gaps=evidence['evidence_gaps'],workflow_warnings=evidence['warnings'],
        human_corrections=evidence['human_corrections'],assessment={
        'deterministic_status':'validated_success','conclusion':'supported','success_claimed':True,
        'summary':'Fixture assessment of recorded deterministic validation.'})
    references={Path(r['path']).name:r['sha256'] for r in evidence['evidence_references']}
    recorded=api.record_interface_critic_result(api.InterfaceCriticRecordRequest(
        action='record_critic_result',trace_name=item['trace_name'],report_name=item['report_name'],
        confirmed_trace_sha256=references[item['trace_name']],confirmed_report_sha256=references[item['report_name']],
        confirmed_critic_result_sha256=critic_result_sha256(critic),result=critic),project_root=project)
    release_request=api.InterfaceRecipeReleaseRequest(action='prepare_recipe_release',release_id='fixture-release',
        trace_name=item['trace_name'],report_name=item['report_name'],critic_record_file=recorded['record_file'],
        confirmed_critic_record_sha256=recorded['critic_record_sha256'])
    prepared=api.prepare_interface_recipe_release(release_request,project_root=project)
    assert prepared['status']=='ready_not_released',prepared['candidate']['violations']
    created=api.create_interface_recipe_release(api.InterfaceRecipeReleaseCreationRequest(
        **{**release_request.model_dump(),'action':'create_recipe_release'},
        confirmed_candidate_sha256=prepared['candidate_sha256'],
        confirmed_assessed_at=prepared['candidate']['assessed_at'],confirmation='create_exact_release'),project_root=project)
    return run,saved,recorded,prepared,created


def test_external_report_critic_history_package_lifecycle_and_read_only_cli(project,tmp_path_factory,monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    state=tmp_path_factory.mktemp('report-state');configure(project,state)
    run,saved,recorded,prepared,created=lifecycle(project)
    assert run['report_path'].startswith('reports/') and (state/run['report_path']).is_file()
    for store in ('traces','reports','critic-results','operational-history','releases'):
        assert (state/store).is_dir() and not (project/store).exists()
    for path in (saved['trace_path'],saved['report_path'],recorded['record_file'],prepared['history_file'],created['release_manifest']):
        assert not Path(path).is_absolute() and (state/path).is_file()
    inventory=api.interface_critic_evidence_inventory(project)
    assert inventory['items'][0]['critic_record_link']=='verified'
    assert inventory['items'][0]['release_link']=='verified'
    from geoagent_harness.apps.cli.main import app
    result=CliRunner().invoke(app,['inspect-authoritative-release',str(state/created['release_manifest']),
        '--release-root',str(state/'releases'),'--pretty'])
    assert result.exit_code==0,result.output
    assert json.loads(result.output)['component_count']==8
    assert not inventory['execution_performed'] and not inventory['critic_model_called']
    from geoagent_harness.core.ledger.task_history.service import append_task_event, inspect_task_artifacts
    for index,path in enumerate((saved['trace_path'],saved['report_path'],recorded['record_file'])):
        append_task_event(root=state/'task-history',task_id='task-report',event_type='request' if not index else 'artifact_reference',
            summary='Fixture recorded artifact',artifact_path=path,artifact_sha256=hashlib.sha256((state/path).read_bytes()).hexdigest())
    links=inspect_task_artifacts(root=state/'task-history',task_id='task-report',project_root=project)
    assert all(link['status']=='matched' for link in links['links'])


def test_offline_report_lifecycle_copy_preserves_bytes_digests_and_links(project,tmp_path_factory,monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    run,saved,recorded,prepared,created=lifecycle(project)
    before={p.relative_to(project):p.read_bytes() for store in STORES for p in (project/store).rglob('*') if p.is_file()}
    state=tmp_path_factory.mktemp('copied-reports')
    for store in STORES:
        if (project/store).exists():shutil.copytree(project/store,state/store)
    configure(project,state)
    from geoagent_harness.core.ledger.releases.storage import inspect_authoritative_release
    verified=inspect_authoritative_release(state/created['release_manifest'],release_root=state/'releases')
    assert verified.release_sha256==created['release_sha256']
    item=api.interface_critic_evidence_inventory(project)['items'][0]
    assert item['critic_record_files']==[recorded['record_file']]
    assert item['release_manifests']==[created['release_manifest']]
    assert all((project/path).read_bytes()==raw and (state/path).read_bytes()==raw for path,raw in before.items())
    # Source modification must remove current-source links; the immutable package
    # remains independently valid because it contains the original verified bytes.
    report=state/saved['report_path'];report.write_bytes(report.read_bytes()+b'\nChanged after recording\n')
    changed=api.interface_critic_evidence_inventory(project)['items'][0]
    assert changed['critic_record_link']==changed['release_link']=='unavailable'
    assert inspect_authoritative_release(state/created['release_manifest'],release_root=state/'releases').release_sha256==verified.release_sha256


@pytest.mark.parametrize('store',['traces','reports','critic-results','operational-history','releases'])
def test_missing_relocated_review_store_preserves_legacy_and_fails_closed(tmp_path,store):
    legacy=tmp_path/store;legacy.mkdir();record=legacy/'record.json';record.write_text('{}')
    configure(tmp_path,'state')
    with pytest.raises(WorkspaceError,match='migration required'):runtime_store_path(tmp_path,store)
    assert record.read_bytes()==b'{}' and not (tmp_path/'state').exists()


def test_empty_review_inventory_does_not_create_state(tmp_path):
    configure(tmp_path,'state')
    assert api.interface_critic_evidence_inventory(tmp_path)['items']==[]
    assert not (tmp_path/'state').exists()


def test_default_mcp_report_roots_follow_workspace_and_custom_roots_remain_explicit(project,tmp_path_factory):
    from geoagent_harness.platform.settings import MCPSettings, authority_workspace_settings
    state=tmp_path_factory.mktemp('transport-report-state');configure(project,state)
    settings=MCPSettings(project_root=project,input_root=project/'data/input',output_root=project/'data/output')
    resolved=authority_workspace_settings(settings)
    assert resolved.report_root==state/'reports' and resolved.trace_root==state/'traces'
    explicit=settings.model_copy(update={'report_root':project/'custom-reports','trace_root':project/'custom-traces'})
    resolved=authority_workspace_settings(explicit)
    assert resolved.report_root==explicit.report_root and resolved.trace_root==explicit.trace_root
    assert not (state/'reports').exists()
