"""Main-workflow Snakemake export reuses completed evidence, never recipe replay."""
import json
from pathlib import Path

import pytest

import importlib.util
_helpers_spec = importlib.util.spec_from_file_location('workflow_test_helpers', Path(__file__).with_name('test_current_workflow.py'))
_helpers = importlib.util.module_from_spec(_helpers_spec)
_helpers_spec.loader.exec_module(_helpers)
project = _helpers.project
result = _helpers.result
stored_request = _helpers.stored_request
execute_request = _helpers.execute_request
authorization_request = _helpers.authorization_request
from geoagent_harness.interface_api import server as api
from geoagent_harness.interface_api.workflow import EditRequest, WorkflowRequest, prepare_workflow, authorize_workflow, execute_workflow, validate_edit, inspection_inventory
from geoagent_harness.interface_api.snakemake_workflow import EXPORT, VERIFY
from geoagent_harness.planner.schemas import PlanStep


def complete_source(project, monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS', 'true')
    source = result(write=True)
    request = stored_request(project, source)
    review = prepare_workflow(request, project_root=project)
    auth = authorize_workflow(authorization_request(request, review), project_root=project)
    run = execute_workflow(execute_request(request, review, plan_approval_filename=auth['plan_approval_filename'], recipe_approval_filename=auth['recipe_approval_filename']), project_root=project)
    assert run['status'] == 'validated_success'
    return source, request, run


def extended(source, request):
    proposed = source.model_copy(deep=True)
    proposed.plan.summary = 'Completed source plus Snakemake export and verification'
    proposed.plan.steps += [
        PlanStep(step_id='step_2', skill=EXPORT, purpose='Export completed source', arguments={'source_plan_filename': request.plan_filename, 'source_plan_sha256': request.confirmed_plan_sha256}, requires_approval=True, validation_required=True, depends_on=['step_1']),
        PlanStep(step_id='step_3', skill=VERIFY, purpose='Verify package', arguments={}, validation_required=True, depends_on=['step_2']),
    ]
    return proposed


def export_request(project, source, source_request):
    proposal = extended(source, source_request)
    validate_edit(EditRequest(action='validate_plan_edit', planner_result=proposal), project_root=project)
    return stored_request(project, proposal)


def test_main_graph_export_and_verification_do_not_rerun_source(project, monkeypatch):
    source, source_request, source_run = complete_source(project, monkeypatch)
    request = export_request(project, source, source_request)
    review = prepare_workflow(request, project_root=project)
    assert review['workflow_kind'] == 'snakemake_export'
    assert review['steps'][0]['execution_mode'] == 'reuse_completed'
    assert review['approval_required_step_ids'] == ['step_2']
    before = (project / 'data/output/result.gpkg').read_bytes()
    source_approvals = len(list((project / 'approvals').glob('recipe-approval-*.json')))
    authorization = authorize_workflow(authorization_request(request, review), project_root=project)
    assert not (project / 'snakemake-exports').exists()
    assert authorization['recipe_approval_filename'] is None
    monkeypatch.setattr(api, 'execute_interface_recipe', lambda *args, **kwargs: pytest.fail('Source recipe must not rerun'))
    run = execute_workflow(execute_request(request, review, plan_approval_filename=authorization['plan_approval_filename']), project_root=project)
    assert run['status'] == 'completed'
    assert [s['status'] for s in run['step_results']] == ['reused_completed', 'exported', 'validated_success']
    assert run['step_results'][-1]['validation_outcome']['passed']
    assert not run['workflow_executed'] and not run['recipe_execution_performed']
    assert (project / 'data/output/result.gpkg').read_bytes() == before
    assert len(list((project / 'approvals').glob('recipe-approval-*.json'))) == source_approvals
    assert set(p.name for p in (project / review['export_path']).iterdir()) == {'Snakefile', 'geoagent-replay.json', 'snakemake-export-manifest.json'}
    assert inspection_inventory(project_root=project)['records'][0]['run_id'] == run['run_id']
    # A repeated export validates the same immutable package, without rerunning source.
    again = execute_workflow(execute_request(request, review, plan_approval_filename=authorization['plan_approval_filename']), project_root=project)
    assert again['step_results'][1]['status'] == 'existing_export'


def test_missing_completion_blocks_export_review(project, monkeypatch):
    monkeypatch.setenv('ENABLE_WRITE_TOOLS', 'true')
    source = result(write=True)
    request = stored_request(project, source)
    candidate = export_request(project, source, request)
    with pytest.raises(api.InterfaceApiError, match='Run the original'):
        prepare_workflow(candidate, project_root=project)
    assert not (project / 'snakemake-exports').exists()


@pytest.mark.parametrize('mutation', ['source_digest', 'original_arguments', 'no_verifier', 'bad_dependency', 'extra_arguments'])
def test_edited_export_rejects_unsafe_or_unbound_scope_before_approval(project, monkeypatch, mutation):
    source, source_request, _ = complete_source(project, monkeypatch)
    proposal = extended(source, source_request)
    if mutation == 'source_digest': proposal.plan.steps[1].arguments['source_plan_sha256'] = '0' * 64
    elif mutation == 'original_arguments': proposal.plan.steps[0].arguments['target_path'] = 'data/output/different.gpkg'
    elif mutation == 'no_verifier': proposal.plan.steps.pop()
    elif mutation == 'bad_dependency': proposal.plan.steps[2].depends_on = ['step_1']
    else: proposal.plan.steps[1].arguments['command'] = 'unsafe'
    with pytest.raises((ValueError, api.InterfaceApiError)):
        validate_edit(EditRequest(action='validate_plan_edit', planner_result=proposal), project_root=project)
    assert not (project / 'snakemake-exports').exists()


def test_export_requires_exact_fresh_approval_and_write_mode(project, monkeypatch):
    source, source_request, _ = complete_source(project, monkeypatch)
    request = export_request(project, source, source_request)
    review = prepare_workflow(request, project_root=project)
    with pytest.raises(api.InterfaceApiError, match='authorization'):
        execute_workflow(execute_request(request, review), project_root=project)
    auth = authorize_workflow(authorization_request(request, review), project_root=project)
    monkeypatch.setenv('ENABLE_WRITE_TOOLS', 'false')
    with pytest.raises(api.InterfaceApiError):
        execute_workflow(execute_request(request, review, plan_approval_filename=auth['plan_approval_filename']), project_root=project)
    assert not (project / 'snakemake-exports').exists()


def test_tampered_package_fails_static_verification_without_overwrite(project, monkeypatch):
    source, source_request, _ = complete_source(project, monkeypatch)
    request = export_request(project, source, source_request)
    review = prepare_workflow(request, project_root=project)
    auth = authorize_workflow(authorization_request(request, review), project_root=project)
    execution = execute_request(request, review, plan_approval_filename=auth['plan_approval_filename'])
    execute_workflow(execution, project_root=project)
    snakefile = project / review['export_path'] / 'Snakefile'
    snakefile.write_text('tampered package')
    with pytest.raises(api.InterfaceApiError, match='verification'):
        execute_workflow(execution, project_root=project)
    assert snakefile.read_text() == 'tampered package'
    assert inspection_inventory(project_root=project)['records'][0]['status'] == 'failed'


def test_expired_source_approval_is_historical_only_and_new_export_authority_required(project, monkeypatch):
    from datetime import datetime, timedelta
    source, source_request, source_run = complete_source(project, monkeypatch)
    request = export_request(project, source, source_request)
    # Advance current verification time: historical source authority is checked at its
    # recorded start, and must not be renewed into fresh recipe execution authority.
    review = prepare_workflow(request, project_root=project)
    from geoagent_harness.recipes.approval import verify_recipe_approval, load_recipe_approval
    from geoagent_harness.recipes.storage import load_recipe
    from geoagent_harness.skill_registry import load_skill_registry
    state = api._load_execution_progress(project, review['source_attempt_sha256'])
    old_approval = load_recipe_approval(project / 'approvals' / state['approval_filename'], approval_root=project / 'approvals')
    recipe = load_recipe(project / 'workflow-recipes' / state['recipe_filename'], recipe_root=project / 'workflow-recipes')
    assert not verify_recipe_approval(approval=old_approval, recipe=recipe, registry=load_skill_registry(project), now=old_approval.expires_at + timedelta(minutes=1)).approved
    auth = authorize_workflow(authorization_request(request, review), project_root=project)
    assert auth['recipe_approval_filename'] is None
    verify_plan = api.verify_interface_plan_approval
    monkeypatch.setattr(api, 'verify_interface_plan_approval', lambda request, **kwargs: verify_plan(request, **kwargs, now=datetime.now().astimezone() + timedelta(minutes=31)))
    with pytest.raises(api.InterfaceApiError, match='expired'):
        execute_workflow(execute_request(request, review, plan_approval_filename=auth['plan_approval_filename']), project_root=project)
    assert not (project / 'snakemake-exports').exists()


def test_source_evidence_tampering_blocks_review(project, monkeypatch):
    source, source_request, source_run = complete_source(project, monkeypatch)
    request = export_request(project, source, source_request)
    evidence = Path(source_run['evidence_path'])
    if not evidence.is_absolute(): evidence = project / evidence
    payload = json.loads(evidence.read_text())
    payload['warnings'].append('changed stored evidence')
    evidence.write_text(json.dumps(payload))
    with pytest.raises(api.InterfaceApiError, match='Run the original'):
        prepare_workflow(request, project_root=project)


def test_export_symlink_rejected_without_touching_target(project, monkeypatch):
    source, source_request, _ = complete_source(project, monkeypatch)
    request = export_request(project, source, source_request)
    review = prepare_workflow(request, project_root=project)
    auth = authorize_workflow(authorization_request(request, review), project_root=project)
    unrelated = project / 'untouched'
    unrelated.mkdir()
    (unrelated / 'marker').write_text('keep')
    (project / 'snakemake-exports').symlink_to(unrelated, target_is_directory=True)
    with pytest.raises(api.InterfaceApiError, match='symlink'):
        execute_workflow(execute_request(request, review, plan_approval_filename=auth['plan_approval_filename']), project_root=project)
    assert (unrelated / 'marker').read_text() == 'keep'
    assert list(unrelated.iterdir()) == [unrelated / 'marker']


def test_conversational_planner_appends_snakemake_using_saved_source_reference(project, monkeypatch):
    from geoagent_harness.interface_api.conversation import TurnRequest, conversation_turn
    from geoagent_harness.model.schemas import ModelResult
    from shutil import copytree, copyfile
    repository = Path(__file__).parents[1]
    copytree(repository / "context", project / "context", dirs_exist_ok=True)
    copytree(repository / "agents", project / "agents")
    copyfile(repository / "README.md", project / "README.md")
    source, source_request, _ = complete_source(project, monkeypatch)
    proposal = extended(source, source_request)
    class Client:
        def complete(self, request):
            payload = json.loads(request.messages[1].content)
            assert payload['saved_source_reference'] == {'source_plan_filename': source_request.plan_filename, 'source_plan_sha256': source_request.confirmed_plan_sha256}
            return ModelResult(model='fixture', content=json.dumps({'message': 'Appended Snakemake export and verification; original steps will be reused.', 'plan': proposal.plan.model_dump(mode='json')}))
    reply = conversation_turn(TurnRequest(action='turn', conversation_id='c'*32, message='Add Snakemake export with verification to my existing workflow', current_plan=source, current_plan_filename=source_request.plan_filename), project_root=project, model_client=Client())
    assert reply['proposal_changed']
    assert reply['messages'][-1]['plan_skill_ids'] == ['convert_vector', EXPORT, VERIFY]
    assert not reply['approval_performed'] and not reply['execution_performed']


def test_materialized_legacy_graph_dependencies_keep_source_scope(project, monkeypatch):
    source, source_request, _ = complete_source(project, monkeypatch)
    proposal = extended(source, source_request)
    # Add uses the graph helper to materialize the original implicit chain.
    proposal.plan.steps[0].depends_on = []
    validate_edit(EditRequest(action='validate_plan_edit', planner_result=proposal), project_root=project)
    request = stored_request(project, proposal)
    assert prepare_workflow(request, project_root=project)['steps'][0]['execution_mode'] == 'reuse_completed'


def test_approval_binds_reviewed_source_evidence_not_only_plan_digest(project, monkeypatch):
    import geoagent_harness.interface_api.snakemake_workflow as module
    source, source_request, _ = complete_source(project, monkeypatch)
    request = export_request(project, source, source_request)
    review = prepare_workflow(request, project_root=project)
    auth = authorize_workflow(authorization_request(request, review), project_root=project)
    changed_review = {**review, 'review_sha256': 'a' * 64, 'source_evidence_sha256': 'b' * 64}
    monkeypatch.setattr(module, 'prepare_export_workflow', lambda *args, **kwargs: changed_review)
    with pytest.raises(api.InterfaceApiError, match='approval review digest'):
        execute_workflow(execute_request(request, changed_review, plan_approval_filename=auth['plan_approval_filename']), project_root=project)
    assert not (project / 'snakemake-exports').exists()
