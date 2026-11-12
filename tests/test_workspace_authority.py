"""Authority/evidence relocation acceptance with temporary files, no database service."""
import hashlib
import shutil
from datetime import timedelta

import pytest

from tests.test_task_agents import project
from tests.test_workspace_layout import configure
from tests.test_reusable_recipes_and_runs import execution
from geoagent_harness.apps.http import server as api
from geoagent_harness.task_actions.workflow import execute_workflow, prepare_workflow
from geoagent_harness.contracts.planning import PlannerResult
from geoagent_harness.platform.workspace import runtime_store_path, runtime_reference, WorkspaceError


def export_plan(target='exported.csv'):
    return PlannerResult(model='fixture',original_request='Export a fresh CSV',context_references=[],plan={
        'summary':'Export the reviewed source','steps':[{'step_id':'step_1','skill':'export_csv',
        'purpose':'Export original rows','arguments':{'path':'data/input/sample_orders.csv',
        'target_path':'data/output/'+target},'requires_approval':True,'validation_required':True}]})


def test_external_authority_execution_evidence_history_and_trace(project,tmp_path_factory,monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    state=tmp_path_factory.mktemp('authority-state');configure(project,state)
    from geoagent_harness.core.policy.write_policy import session
    with session(project,enabled=True):
        request=execution(project,export_plan())
        result=execute_workflow(request,project_root=project)
    assert result['status']=='validated_success'
    assert (project/'data/output/exported.csv').read_bytes()==(project/'data/input/sample_orders.csv').read_bytes()
    for field,store in [('run_result_path','recipe-runs'),('evidence_path','recipe-evidence')]:
        assert result[field].startswith(store+'/') and (state/result[field]).is_file()
    for store in ('approvals','workflow-recipes','recipe-runs','recipe-evidence'):
        assert (state/store).is_dir() and not (project/store).exists()
    attempt=api.interface_execution_inventory(project)['attempts'][0]
    assert attempt['authority_link']==attempt['result_link']=='verified'
    assert (state/'workflow-state/interface-executions'/(result['execution_preview_sha256']+'.json')).is_file()
    candidates=api._interface_recipe_trace_candidates(project)
    assert len(candidates)==1 and candidates[0]['adaptable']
    assert all(not r.startswith(str(state)) for r in candidates[0]['trace']['context_references'])
    assert any(r.startswith('recipe-evidence/') for r in candidates[0]['trace']['context_references'])
    from geoagent_harness.core.ledger.task_history.service import append_task_event, inspect_task_artifacts
    path=state/result['evidence_path'];raw=path.read_bytes()
    append_task_event(root=project/'task-history',task_id='task-storage',event_type='request',
        summary='Record exact evidence',artifact_path=result['evidence_path'],artifact_sha256=hashlib.sha256(raw).hexdigest())
    links=inspect_task_artifacts(root=project/'task-history',task_id='task-storage',project_root=project)
    assert links['links'][0]['status']=='matched' and not links['execution_performed']
    from geoagent_harness.core.policy.recipe_approval import load_recipe_approval, verify_recipe_approval
    from geoagent_harness.core.ledger.recipe_storage import load_recipe
    from geoagent_harness.platform.skill_registry import load_skill_registry
    approval=load_recipe_approval(state/'approvals'/request.recipe_approval_filename,approval_root=state/'approvals')
    review=prepare_workflow(request,project_root=project)
    recipe=load_recipe(state/'workflow-recipes'/review['recipe_filename'],recipe_root=state/'workflow-recipes')
    expired=verify_recipe_approval(approval=approval,recipe=recipe,registry=load_skill_registry(project),now=approval.expires_at+timedelta(seconds=1))
    assert not expired.approved
    from geoagent_harness.core.policy.write_policy import check, WritePolicyError
    with session(project,enabled=True):
        with pytest.raises(WritePolicyError,match='stale'):
            check(project,approval)


def test_offline_authority_copy_preserves_reviews_and_database_attempt_replay_guard(project,tmp_path_factory,monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS','true')
    request=execution(project,export_plan('after-copy.csv'))
    from geoagent_harness.data.databases.postgres.service import claim_authority, PostgresError
    from geoagent_harness.platform.settings import MCPSettings
    settings=MCPSettings(project_root=project,input_root=project/'data/input',output_root=project/'data/output')
    claim_authority(settings,'database-approval-fixture','step_1')
    stores=('plans','approvals','workflow-recipes','recipe-runs')
    before={p.relative_to(project):p.read_bytes() for store in stores for p in (project/store).rglob('*.json')}
    state=tmp_path_factory.mktemp('copied-authority')
    for store in stores:shutil.copytree(project/store,state/store)
    # R12 dispatch claims must move with authority; never start a fresh audit.
    shutil.copytree(project/'workflow-state',state/'workflow-state')
    configure(project,state)
    assert prepare_workflow(request,project_root=project)['review_sha256']==request.confirmed_review_sha256
    with pytest.raises(PostgresError,match='already has an attempt'):
        claim_authority(settings,'database-approval-fixture','step_1')
    assert all((project/name).read_bytes()==raw and (state/name).read_bytes()==raw for name,raw in before.items())
    result=execute_workflow(request,project_root=project)
    assert result['status']=='validated_success' and (state/result['evidence_path']).exists()
    assert all((project/name).read_bytes()==raw and (state/name).read_bytes()==raw for name,raw in before.items())


@pytest.mark.parametrize('store,parts',[
    ('approvals',()),('workflow-recipes',()),('recipe-runs',()),('recipe-evidence',()),
    ('inspection-runs',()),('workflow-state',('interface-executions',))])
def test_missing_authority_store_never_hides_legacy_records(tmp_path,store,parts):
    legacy=tmp_path.joinpath(store,*parts);legacy.mkdir(parents=True)
    path=legacy/'record.json';path.write_text('{}');configure(tmp_path,'state')
    with pytest.raises(WorkspaceError,match='migration required'):runtime_store_path(tmp_path,store,*parts)
    assert path.read_text()=='{}' and not (tmp_path/'state').exists()


def test_runtime_references_and_explicit_mcp_settings(project,tmp_path_factory):
    from geoagent_harness.platform.settings import MCPSettings, authority_workspace_settings
    state=tmp_path_factory.mktemp('reference-state');configure(project,state)
    assert runtime_reference(project,state/'recipe-runs/record.json')=='recipe-runs/record.json'
    assert runtime_reference(project,project/'reports/record.md')=='reports/record.md'
    with pytest.raises(WorkspaceError):runtime_reference(project,state/'unknown/file.json')
    with pytest.raises(WorkspaceError):runtime_reference(project,state.parent/'unrelated/file.json')
    settings=MCPSettings(project_root=project,input_root=project/'data/input',output_root=project/'data/output',approval_root=project/'custom-approvals')
    resolved=authority_workspace_settings(settings)
    assert resolved.recipe_root==state/'workflow-recipes'
    assert resolved.recipe_run_root==state/'recipe-runs'
    assert resolved.approval_root==settings.approval_root and resolved.input_root==settings.input_root
    assert not (state/'recipe-runs').exists()


def test_absent_execution_progress_read_creates_no_state(tmp_path):
    configure(tmp_path,'private-state')
    assert api._load_execution_progress(tmp_path,'a'*64) is None
    assert api.interface_execution_inventory(tmp_path)['attempts']==[]
    assert not (tmp_path/'private-state').exists()


def test_release_components_resolve_logical_state_paths_and_reject_escape(project,tmp_path_factory):
    from geoagent_harness.core.ledger.releases.assessment import _component
    from geoagent_harness.core.ledger.releases.storage import _source_file, AuthoritativeReleaseStorageError
    from geoagent_harness.core.ledger.releases.schemas import ReleaseComponentKind
    state=tmp_path_factory.mktemp('release-source-state');configure(project,state)
    folder=state/'recipe-runs';folder.mkdir();record=folder/'result.json';record.write_text('{}')
    component=_component(component_id='run_result',kind=ReleaseComponentKind.RUN_RESULT,
        path=record,root=folder,project_root=project)
    assert component.path=='recipe-runs/result.json'
    assert _source_file(component.path,project_root=project)==record
    assert component.sha256==hashlib.sha256(record.read_bytes()).hexdigest()
    for path in ('../escape.json','/tmp/escape.json','recipe-runs/../escape.json'):
        with pytest.raises(AuthoritativeReleaseStorageError):_source_file(path,project_root=project)
    (folder/'linked.json').symlink_to(record)
    with pytest.raises(AuthoritativeReleaseStorageError):_source_file('recipe-runs/linked.json',project_root=project)
