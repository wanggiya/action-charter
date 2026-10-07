"""Terminal graph operations export a verified completed recipe, never replay it."""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.approvals import load_planner_result, plan_sha256
from geoagent_harness.planner.policy import validate_plan_policy
from geoagent_harness.planner.topology import plan_dependencies, plan_topological_order, ancestors
from geoagent_harness.recipes.approval import load_recipe_approval
from geoagent_harness.recipes.evidence_storage import load_recipe_run_result
from geoagent_harness.snakemake_export import generate_snakemake_recipe_export, validate_snakemake_export_contract
from geoagent_harness.snakemake_export.schemas import SnakemakeRecipeExportPlan

EXPORT = 'export_snakemake_workflow'
VERIFY = 'verify_snakemake_export'
TERMINAL = {EXPORT, VERIFY}
_LOCK = Lock()
_ACTIVE = set()


class ExportArguments(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_plan_filename: str = Field(pattern=r'^planner-plan\.[a-f0-9]{64}\.json$')
    source_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class VerifyArguments(BaseModel):
    model_config = ConfigDict(extra='forbid')


def has_export(result):
    return any(step.skill in TERMINAL for step in result.plan.steps)


def validate_export_plan(result, root):
    from .server import InterfaceApiError
    from .workflow import _check
    from geoagent_harness.skill_registry import load_skill_registry
    registry = load_skill_registry(root)
    validate_plan_policy(result.plan, available_skills={s.id for s in registry.implemented_skills()})
    export = [s for s in result.plan.steps if s.skill == EXPORT]
    verify = [s for s in result.plan.steps if s.skill == VERIFY]
    if len(export) != 1 or len(verify) != 1:
        raise InterfaceApiError('Use exactly one Snakemake export and one verification block')
    args = ExportArguments.model_validate(export[0].arguments)
    VerifyArguments.model_validate(verify[0].arguments)
    if not export[0].requires_approval or not export[0].validation_required or not verify[0].validation_required:
        raise InterfaceApiError('Snakemake export requires approval and package verification')
    path = root / 'plans' / args.source_plan_filename
    if path.is_symlink() or (root / 'plans').is_symlink():
        raise InterfaceApiError('Source plan artifact is unsafe')
    source = load_planner_result(path=path, plan_root=root / 'plans')
    if plan_sha256(source.plan) != args.source_plan_sha256:
        raise InterfaceApiError('Snakemake source plan digest no longer matches')
    if has_export(source):
        raise InterfaceApiError('Snakemake export must reference an original operation plan, not another export plan')
    source_registry, recipe, policy = _check(source, root)
    prefix = [s for s in result.plan.steps if s.skill not in TERMINAL]
    deps = plan_dependencies(result.plan)
    source_deps = plan_dependencies(source.plan)
    def scope(steps):
        values = []
        for step in steps:
            value = step.model_dump(mode='json')
            value.pop('depends_on', None)
            values.append(value)
        return values
    if prefix and (scope(prefix) != scope(source.plan.steps) or any(deps.get(step.step_id) != source_deps[step.step_id] for step in prefix)):
        raise InterfaceApiError('Retained operations must exactly match the saved Snakemake source plan')
    ordered = plan_topological_order(result.plan)
    if not set(s.step_id for s in prefix).issubset(ancestors(export[0].step_id, deps)):
        raise InterfaceApiError('Snakemake export must follow every retained source operation')
    if export[0].step_id not in ancestors(verify[0].step_id, deps) or ordered[-2:] != [export[0].step_id, verify[0].step_id]:
        raise InterfaceApiError('Snakemake verification must follow export at the end of the workflow')
    return source_registry, recipe, policy


def _load_result(request, root):
    from .server import InterfaceApiError
    path = root / 'plans' / request.plan_filename
    if path.is_symlink() or (root / 'plans').is_symlink():
        raise InterfaceApiError('Stored export plan is unsafe')
    result = load_planner_result(path=path, plan_root=root / 'plans')
    if plan_sha256(result.plan) != request.confirmed_plan_sha256:
        raise InterfaceApiError('Stored export plan digest no longer matches')
    return result


def prepare_export_workflow(request, *, project_root):
    from . import server as api
    from geoagent_harness.recipes.digest import recipe_sha256
    root = api._trusted_root(project_root)
    result = _load_result(request, root)
    registry, recipe, policy = validate_export_plan(result, root)
    digest = recipe_sha256(recipe)
    attempts = api.interface_execution_inventory(root)['attempts']
    candidates = [a for a in attempts if a['recipe_sha256'] == digest and a['status'] == 'validated_success' and a['authority_link'] == 'verified' and a['result_link'] == 'verified']
    if not candidates:
        raise api.InterfaceApiError('Run the original source workflow successfully first. Snakemake export reuses verified completed evidence and never reruns the source operations.')
    attempt = candidates[0]
    state = api._load_execution_progress(root, attempt['execution_preview_sha256'])
    approval = load_recipe_approval(root / 'approvals' / state['approval_filename'], approval_root=root / 'approvals')
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
        execution_available=api.load_settings().enable_write_tools, execution_performed=False,
        source_attempt_sha256=attempt['execution_preview_sha256'], source_run_result_sha256=state['run_result_sha256'],
        source_evidence_sha256=state['evidence_sha256'], export_plan=export_plan.model_dump(mode='json'),
        export_path=f'snakemake-exports/{recipe.recipe_id}.{digest}.snakemake',
        source_approval_sha256=hashlib.sha256((root / 'approvals' / state['approval_filename']).read_bytes()).hexdigest())
    canonical = json.dumps(basis, sort_keys=True, separators=(',', ':'))
    return {**basis, 'review_sha256': hashlib.sha256(canonical.encode()).hexdigest()}


def authorize_export_workflow(request, *, project_root):
    from . import server as api
    review = prepare_export_workflow(request, project_root=project_root)
    if review['review_sha256'] != request.confirmed_review_sha256:
        raise api.InterfaceApiError('Snakemake authorization review digest no longer matches')
    if not review['execution_available']:
        raise api.InterfaceApiError('Write tools are disabled; restart with --enable-write-tools')
    if not request.approve_required_steps or not request.approver.strip() or not request.reason.strip():
        raise api.InterfaceApiError('Explicit approval, approver and reason are required')
    prepared = api.prepare_interface_plan_approval(api.InterfacePlanApprovalPreparationRequest(action='prepare_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256), project_root=project_root)
    approval = api.record_interface_plan_approval(api.InterfacePlanApprovalDecisionRequest(action='record_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256, confirmed_approval_request_sha256=prepared['approval_request_sha256'], decision='approved', approver=request.approver, reason=request.reason, valid_for_minutes=30), project_root=project_root)
    root = api._trusted_root(project_root)
    binding = root / 'approvals' / ('snakemake-review.' + approval['approval_filename'])
    content = {'schema_version': '1.0', 'plan_approval_filename': approval['approval_filename'], 'plan_sha256': review['plan_sha256'], 'review_sha256': review['review_sha256']}
    with binding.open('x') as handle:
        json.dump(content, handle)
    return dict(schema_version='1.0', review_sha256=review['review_sha256'], plan_approval_filename=approval['approval_filename'], recipe_approval_filename=None, approval_recorded=True, execution_performed=False)


def _safe_package(root, relative):
    from .server import InterfaceApiError
    path = root
    for part in Path(relative).parts:
        path = path / part
        if path.is_symlink():
            raise InterfaceApiError('Snakemake package path cannot contain symlinks')
    if path.exists():
        if not path.is_dir():
            raise InterfaceApiError('Snakemake export destination is not a directory')
        if {p.name for p in path.iterdir()} != {'Snakefile', 'geoagent-replay.json', 'snakemake-export-manifest.json'}:
            raise InterfaceApiError('Existing Snakemake package has unexpected files; it will not be overwritten')
        if any(p.is_symlink() for p in path.iterdir()):
            raise InterfaceApiError('Snakemake package files cannot be symlinks')
    return path


def execute_export_workflow(request, *, project_root):
    from . import server as api
    from .workflow import _inspection_root
    root = api._trusted_root(project_root)
    review = prepare_export_workflow(request, project_root=root)
    if not request.confirm_execution or request.confirmed_review_sha256 != review['review_sha256']:
        raise api.InterfaceApiError('Snakemake execution review digest no longer matches')
    if not review['execution_available'] or not request.plan_approval_filename:
        raise api.InterfaceApiError('Write mode and exact Snakemake plan authorization are required')
    prepared = api.prepare_interface_plan_approval(api.InterfacePlanApprovalPreparationRequest(action='prepare_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256), project_root=root)
    verified = api.verify_interface_plan_approval(api.InterfacePlanApprovalVerificationRequest(action='verify_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=request.confirmed_plan_sha256, confirmed_approval_request_sha256=prepared['approval_request_sha256'], approval_filename=request.plan_approval_filename), project_root=root)
    if not verified['approved']:
        raise api.InterfaceApiError('Snakemake authorization expired or blocked; record a new explicit decision')
    binding = root / 'approvals' / ('snakemake-review.' + request.plan_approval_filename)
    if binding.is_symlink() or not binding.is_file() or binding.stat().st_size > 4000:
        raise api.InterfaceApiError('Snakemake approval review binding is missing or unsafe')
    expected_binding = {'schema_version': '1.0', 'plan_approval_filename': request.plan_approval_filename, 'plan_sha256': review['plan_sha256'], 'review_sha256': review['review_sha256']}
    if json.loads(binding.read_text()) != expected_binding:
        raise api.InterfaceApiError('Snakemake approval review digest no longer matches')

    destination = _inspection_root(root)
    key = review['export_path']
    with _LOCK:
        if key in _ACTIVE:
            raise api.InterfaceApiError('This Snakemake package is already being exported')
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
        run = load_recipe_run_result(root / 'recipe-runs' / f"{review['export_plan']['recipe_id']}.{review['source_run_result_sha256']}.json", result_root=root / 'recipe-runs')
        prior = {step.step_id: step for step in run.step_results}
        for step in review['steps']:
            if step['execution_mode'] == 'reuse_completed':
                old = prior[step['step_id']]
                record['step_results'].append(dict(step_id=step['step_id'], skill_id=step['skill'], status='reused_completed', validation_performed=old.validation_performed, outcome={'source_attempt': review['source_attempt_sha256'], 'reused': True, 'result': api._bounded_outcome(old.execution.result)}, validation_outcome=api._bounded_outcome(old.validation_result) if old.validation_result is not None else None))
                continue
            path = _safe_package(root, review['export_path'])
            plan = SnakemakeRecipeExportPlan.model_validate(review['export_plan'])
            if step['skill'] == EXPORT:
                existing = path.exists()
                if not existing:
                    generate_snakemake_recipe_export(plan, export_root=root / 'snakemake-exports')
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
    from .server import InterfaceApiError
    contract = validate_snakemake_export_contract(path)
    config = json.loads((path / 'geoagent-replay.json').read_text())
    expected = {key: getattr(plan, key) for key in ['recipe_id', 'recipe_sha256', 'approval_id', 'recipe_filename', 'approval_filename', 'approved_step_ids', 'topological_step_ids', 'replay_entrypoint']}
    if not contract.passed or any(config.get(key) != value for key, value in expected.items()):
        raise InterfaceApiError('Snakemake package failed verification or does not match the reviewed source scope')
    return contract
