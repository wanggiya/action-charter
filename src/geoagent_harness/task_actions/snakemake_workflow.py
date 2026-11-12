"""Terminal graph operations export a verified completed recipe, never replay it."""
from __future__ import annotations
from geoagent_harness.platform.storage import repositories
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root, runtime_reference_path
from geoagent_harness.platform.workspace import WorkspaceLayout

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.core.policy.approvals import load_planner_result, plan_sha256
from geoagent_harness.core.policy.plan import validate_plan_policy
from geoagent_harness.contracts.graph import plan_dependencies, plan_topological_order, ancestors
from geoagent_harness.core.policy.recipe_approval import load_recipe_approval
from geoagent_harness.core.ledger.recipe_evidence import load_recipe_run_result
from geoagent_harness.data.export.snakemake.generator import generate_snakemake_recipe_export
from geoagent_harness.data.export.snakemake.contracts import validate_snakemake_export_contract
from geoagent_harness.data.export.snakemake.schemas import SnakemakeRecipeExportPlan

from geoagent_harness.contracts.snakemake import EXPORT, VERIFY, TERMINAL, ExportArguments, VerifyArguments
from geoagent_harness.capabilities.workflow import has_export, validate_export_plan
_LOCK = Lock()
_ACTIVE = set()










def _load_result(request, root):
    from geoagent_harness.contracts.errors import InterfaceApiError
    path = runtime_store_path(root, 'plans') / request.plan_filename
    if path.is_symlink() or (runtime_store_path(root, 'plans')).is_symlink():
        raise InterfaceApiError('Stored export plan is unsafe')
    result = repositories(root).documents('plans', directory=runtime_store_path(root, 'plans')).load((path).name)
    if plan_sha256(result.plan) != request.confirmed_plan_sha256:
        raise InterfaceApiError('Stored export plan digest no longer matches')
    return result


def prepare_export_workflow(request, *, project_root):
    from geoagent_harness.task_actions import execution as actions
    from geoagent_harness.core.ledger.recipe_identity import recipe_sha256
    root = actions._trusted_root(project_root)
    result = _load_result(request, root)
    registry, recipe, policy = validate_export_plan(result, root)
    digest = recipe_sha256(recipe)
    attempts = actions.interface_execution_inventory(root)['attempts']
    candidates = [a for a in attempts if a['recipe_sha256'] == digest and a['status'] == 'validated_success' and a['authority_link'] == 'verified' and a['result_link'] == 'verified']
    if not candidates:
        raise actions.InterfaceApiError('Run the original source workflow successfully first. Snakemake export reuses verified completed evidence and never reruns the source operations.')
    attempt = candidates[0]
    state = actions._load_execution_progress(root, attempt['execution_preview_sha256'])
    approval = load_recipe_approval(runtime_store_path(root, 'approvals') / state['approval_filename'], approval_root=runtime_store_path(root, 'approvals'))
    # This artifact references historical execution authority only. New plan approval
    # authorizes export; no renewed recipe-execution approval is created here.
    export_plan = SnakemakeRecipeExportPlan(recipe_id=recipe.recipe_id, recipe_sha256=digest,
        approval_id=approval.approval_id, recipe_filename=state['recipe_filename'],
        approval_filename=state['approval_filename'], approved_step_ids=approval.step_ids,
        topological_step_ids=policy.topological_step_ids,
        warnings=['Export and static verification only. Source operations and Snakemake are not run. Replay requires independently valid execution approval.'])
    deps = plan_dependencies(result.plan)
    by_id = {s.step_id: s for s in result.plan.steps}
    ordered = plan_topological_order(result.plan)
    steps = [{**by_id[id].model_dump(mode='json'), 'depends_on': deps[id],
              'requires_approval': by_id[id].skill == EXPORT,
              'execution_mode': 'execute' if by_id[id].skill in TERMINAL else 'reuse_completed'} for id in ordered]
    basis = dict(schema_version='1.0', workflow_kind='snakemake_export', plan_filename=request.plan_filename,
        plan_sha256=request.confirmed_plan_sha256, recipe_filename=state['recipe_filename'], recipe_sha256=digest,
        steps=steps, approval_required_step_ids=[s.step_id for s in result.plan.steps if s.skill == EXPORT],
        write_step_ids=[s.step_id for s in result.plan.steps if s.skill == EXPORT],
        execution_available=actions.effective_write_settings(actions.load_settings(), root).enable_write_tools, execution_performed=False,
        source_attempt_sha256=attempt['execution_preview_sha256'], source_run_result_sha256=state['run_result_sha256'],
        source_evidence_sha256=state['evidence_sha256'], export_plan=export_plan.model_dump(mode='json'),
        export_path=f'snakemake-exports/{recipe.recipe_id}.{digest}.snakemake',
        source_approval_sha256=hashlib.sha256((runtime_store_path(root, 'approvals') / state['approval_filename']).read_bytes()).hexdigest())
    state = actions.write_policy_snapshot(root)
    if state:
        basis['write_policy'] = {key:state[key] for key in ('session_id','revision','enabled')}
    canonical = json.dumps(basis, sort_keys=True, separators=(',', ':'))
    return {**basis, 'review_sha256': hashlib.sha256(canonical.encode()).hexdigest()}


def authorize_export_workflow(request, *, project_root):
    from geoagent_harness.task_actions import execution as actions
    review = prepare_export_workflow(request, project_root=project_root)
    if review['review_sha256'] != request.confirmed_review_sha256:
        raise actions.InterfaceApiError('Snakemake authorization review digest no longer matches')
    if not review['execution_available']:
        raise actions.InterfaceApiError('Write operations are OFF. Enable them in Settings and authorize again.')
    if not request.approve_required_steps or not request.approver.strip() or not request.reason.strip():
        raise actions.InterfaceApiError('Explicit approval, approver and reason are required')
    prepared = actions.prepare_interface_plan_approval(actions.InterfacePlanApprovalPreparationRequest(action='prepare_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256), project_root=project_root)
    approval = actions.record_interface_plan_approval(actions.InterfacePlanApprovalDecisionRequest(action='record_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256, confirmed_approval_request_sha256=prepared['approval_request_sha256'], decision='approved', approver=request.approver, reason=request.reason, valid_for_minutes=30), project_root=project_root)
    root = actions._trusted_root(project_root)
    binding = runtime_store_path(root, 'approvals') / ('snakemake-review.' + approval['approval_filename'])
    content = {'schema_version': '1.0', 'plan_approval_filename': approval['approval_filename'], 'plan_sha256': review['plan_sha256'], 'review_sha256': review['review_sha256']}
    with binding.open('x') as handle:
        json.dump(content, handle)
    return dict(schema_version='1.0', review_sha256=review['review_sha256'], plan_approval_filename=approval['approval_filename'], recipe_approval_filename=None, approval_recorded=True, execution_performed=False)


def _safe_package(root, relative):
    from geoagent_harness.contracts.errors import InterfaceApiError
    path = runtime_reference_path(root, relative)
    if path.exists():
        if not path.is_dir():
            raise InterfaceApiError('Snakemake export destination is not a directory')
        if {p.name for p in path.iterdir()} != {'Snakefile', 'geoagent-replay.json', 'snakemake-export-manifest.json'}:
            raise InterfaceApiError('Existing Snakemake package has unexpected files; it will not be overwritten')
        if any(p.is_symlink() for p in path.iterdir()):
            raise InterfaceApiError('Snakemake package files cannot be symlinks')
    return path


def execute_export_workflow(request, *, project_root):
    from geoagent_harness.task_actions import execution as actions
    from geoagent_harness.task_actions.workflow import _inspection_root
    root = actions._trusted_root(project_root)
    review = prepare_export_workflow(request, project_root=root)
    if not request.confirm_execution or request.confirmed_review_sha256 != review['review_sha256']:
        raise actions.InterfaceApiError('Snakemake execution review digest no longer matches')
    if not review['execution_available'] or not request.plan_approval_filename:
        raise actions.InterfaceApiError('Write mode and exact Snakemake plan authorization are required')
    prepared = actions.prepare_interface_plan_approval(actions.InterfacePlanApprovalPreparationRequest(action='prepare_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256), project_root=root)
    verified = actions.verify_interface_plan_approval(actions.InterfacePlanApprovalVerificationRequest(action='verify_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256, confirmed_approval_request_sha256=prepared['approval_request_sha256'], approval_filename=request.plan_approval_filename), project_root=root)
    if not verified['approved']:
        raise actions.InterfaceApiError('Snakemake authorization expired or blocked; record a new explicit decision')
    from geoagent_harness.core.policy.approvals import load_approval
    from geoagent_harness.core.policy.write_policy import check
    check(root, load_approval(path=runtime_store_path(root, 'approvals') / request.plan_approval_filename, approval_root=runtime_store_path(root, 'approvals')))
    binding = runtime_store_path(root, 'approvals') / ('snakemake-review.' + request.plan_approval_filename)
    if binding.is_symlink() or not binding.is_file() or binding.stat().st_size > 4000:
        raise actions.InterfaceApiError('Snakemake approval review binding is missing or unsafe')
    expected_binding = {'schema_version': '1.0', 'plan_approval_filename': request.plan_approval_filename, 'plan_sha256': review['plan_sha256'], 'review_sha256': review['review_sha256']}
    if json.loads(binding.read_text()) != expected_binding:
        raise actions.InterfaceApiError('Snakemake approval review digest no longer matches')

    destination = _inspection_root(root)
    key = review['export_path']
    with _LOCK:
        if key in _ACTIVE:
            raise actions.InterfaceApiError('This Snakemake package is already being exported')
        _ACTIVE.add(key)
    record = dict(schema_version='1.0', workflow_kind='snakemake_export', run_id=uuid.uuid4().hex,
        plan_filename=request.plan_filename, plan_sha256=request.confirmed_plan_sha256, started_at=datetime.now(timezone.utc).isoformat(),
        finished_at=None, status='running', step_results=[], approval_recorded=True, execution_performed=False,
        workflow_executed=False, recipe_execution_performed=False, source_attempt_sha256=review['source_attempt_sha256'],
        source_run_result_sha256=review['source_run_result_sha256'], source_evidence_sha256=review['source_evidence_sha256'])
    target = destination / (record['run_id'] + '.json')
    def persist():
        temporary = target.with_suffix('.tmp')
        with temporary.open('x') as handle:
            json.dump(record, handle)
        os.replace(temporary, target)
    try:
        persist()
        run = load_recipe_run_result(runtime_store_path(root, 'recipe-runs') / f"{review['export_plan']['recipe_id']}.{review['source_run_result_sha256']}.json", result_root=runtime_store_path(root, 'recipe-runs'))
        prior = {step.step_id: step for step in run.step_results}
        for step in review['steps']:
            if step['execution_mode'] == 'reuse_completed':
                old = prior[step['step_id']]
                record['step_results'].append(dict(step_id=step['step_id'], skill_id=step['skill'], status='reused_completed', validation_performed=old.validation_performed, outcome={'source_attempt': review['source_attempt_sha256'], 'reused': True, 'result': actions._bounded_outcome(old.execution.result)}, validation_outcome=actions._bounded_outcome(old.validation_result) if old.validation_result is not None else None))
                continue
            path = _safe_package(root, review['export_path'])
            plan = SnakemakeRecipeExportPlan.model_validate(review['export_plan'])
            if step['skill'] == EXPORT:
                existing = path.exists()
                if not existing:
                    from geoagent_harness.core.policy.approvals import load_approval
                    from geoagent_harness.core.policy.write_policy import authority, operation
                    approval = load_approval(path=runtime_store_path(root, 'approvals') / request.plan_approval_filename, approval_root=runtime_store_path(root, 'approvals'))
                    with authority(root, approval), operation(actions.effective_write_settings(actions.load_settings(), root)):
                        generate_snakemake_recipe_export(plan, export_root=runtime_store_path(root, 'snakemake-exports'), project_root=root)
                record['execution_performed'] = True
                outcome = {'export_path': review['export_path'], 'export_created': not existing, 'recipe_sha256': plan.recipe_sha256, 'workflow_executed': False}
                record['step_results'].append(dict(step_id=step['step_id'], skill_id=EXPORT, status='exported' if not existing else 'existing_export', validation_performed=False, outcome=outcome, validation_outcome=None))
            else:
                contract = validate_snakemake_workflow(path, plan)
                record['step_results'].append(dict(step_id=step['step_id'], skill_id=VERIFY, status='validated_success', validation_performed=True, outcome={'passed': True, 'export_path': review['export_path'], 'workflow_executed': False}, validation_outcome=contract.model_dump(mode='json')))
            persist()
        record['status'] = 'completed'
    except Exception:
        record['status'] = 'failed'
        record['finding'] = 'Snakemake export or static verification failed. Inspect this attempt and package before retrying; source workflow was not rerun.'
        raise
    finally:
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        try:
            persist()
        finally:
            with _LOCK:
                _ACTIVE.discard(key)
    return record


def validate_snakemake_workflow(path, plan):
    from geoagent_harness.contracts.errors import InterfaceApiError
    contract = validate_snakemake_export_contract(path)
    config = json.loads((path / 'geoagent-replay.json').read_text())
    expected = {key: getattr(plan, key) for key in ['recipe_id', 'recipe_sha256', 'approval_id', 'recipe_filename', 'approval_filename', 'approved_step_ids', 'topological_step_ids', 'replay_entrypoint']}
    if not contract.passed or any(config.get(key) != value for key, value in expected.items()):
        raise InterfaceApiError('Snakemake package failed verification or does not match the reviewed source scope')
    return contract


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
prepare_export_workflow = _task_entrypoint(prepare_export_workflow, audit=False)
authorize_export_workflow = _task_entrypoint(authorize_export_workflow)
execute_export_workflow = _task_entrypoint(execute_export_workflow)
