"""Typed current-plan review and execution; context never supplies authority."""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.approvals import load_planner_result, plan_sha256
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.planner.policy import normalize_plan_input_filenames, validate_plan_policy
from geoagent_harness.planner.recipe_definition import planner_recipe_definition
from geoagent_harness.recipes import schemas
from geoagent_harness.recipes.policy import validate_recipe_policy
from geoagent_harness.recipes.storage import save_recipe, load_recipe, recipe_path
from geoagent_harness.recipes.digest import recipe_sha256
from geoagent_harness.skill_registry import load_skill_registry

from .snakemake_workflow import ExportArguments, VerifyArguments, has_export

ARGUMENTS = {
    'inspect_vector': schemas.InspectVectorRecipeArguments,
    'inspect_raster': schemas.InspectRasterRecipeArguments,
    'convert_vector': schemas.ConvertVectorRecipeArguments,
    'convert_raster': schemas.ConvertRasterRecipeArguments,
    'load_vector_to_postgis': schemas.LoadVectorToPostGISRecipeArguments,
    'validate_postgis_layer': schemas.ValidatePostGISLayerRecipeArguments,
    'generate_report': schemas.GenerateReportRecipeArguments,
    'export_snakemake_workflow': ExportArguments,
    'verify_snakemake_export': VerifyArguments,
}
_LOCK = Lock()
_ACTIVE: set[str] = set()


class EditRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['validate_plan_edit']
    planner_result: PlannerResult


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: Literal['prepare_workflow', 'authorize_workflow', 'execute_workflow']
    plan_filename: str = Field(pattern=r'^planner-plan\.[a-f0-9]{64}\.json$')
    confirmed_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirmed_review_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    confirm_execution: Literal[True] | None = None
    plan_approval_filename: str | None = Field(default=None, pattern=r'^approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}\.json$')
    recipe_approval_filename: str | None = Field(default=None, pattern=r'^recipe-approval-[a-z0-9-]+\.json$')
    approve_required_steps: bool = False
    approver: str = Field(default='', max_length=200)
    reason: str = Field(default='', max_length=2000)


def _check(result, root):
    from .server import InterfaceApiError
    from geoagent_harness.recipes.dispatcher import _validate_registered_skill, RecipeDispatchError
    from geoagent_harness.intent.input import check_task_input
    from geoagent_harness.intent.service import IntentError
    if has_export(result):
        from .snakemake_workflow import validate_export_plan
        return validate_export_plan(result, root)
    registry = load_skill_registry(root)
    validate_plan_policy(result.plan, available_skills={s.id for s in registry.implemented_skills()})
    for step in result.plan.steps:
        if step.skill not in ARGUMENTS:
            raise InterfaceApiError('This operation is not supported by current workflow execution: ' + step.skill)
        try:
            _validate_registered_skill(skill_id=step.skill, registry=registry)
        except RecipeDispatchError as error:
            raise InterfaceApiError('Registered operation does not match the trusted dispatcher') from error
        ARGUMENTS[step.skill].model_validate(step.arguments)
        if 'path' in step.arguments:
            try:
                check_task_input(project_root=root, input_path=step.arguments['path'])
            except IntentError as error:
                raise InterfaceApiError('Input must be an available regular file under data/input') from error
        if 'target_path' in step.arguments and not step.arguments['target_path'].startswith('data/output/'):
            raise InterfaceApiError('Output paths must remain under data/output')
    recipe = planner_recipe_definition(result, plan_sha256(result.plan))
    policy = validate_recipe_policy(recipe, registry=registry)
    return registry, recipe, policy


def validate_edit(request: EditRequest, *, project_root: Path):
    from .server import _trusted_root
    result = request.planner_result
    normalize_plan_input_filenames(result.plan)
    _check(result, _trusted_root(project_root))
    return dict(schema_version='1.0', status='planned_not_saved',
                **result.model_dump(mode='json'), allowed_skill_ids=list(dict.fromkeys(s.skill for s in result.plan.steps)),
                plan_sha256=plan_sha256(result.plan), plan_saved=False, approval_performed=False, execution_performed=False)


def prepare_workflow(request: WorkflowRequest, *, project_root: Path):
    from .server import (_trusted_root, InterfaceApiError, InterfacePlanApprovalPreparationRequest,
                         prepare_interface_plan_approval, load_settings)
    root = _trusted_root(project_root)
    prepared = prepare_interface_plan_approval(InterfacePlanApprovalPreparationRequest(
        action='prepare_plan_approval', plan_filename=request.plan_filename,
        confirmed_plan_sha256=request.confirmed_plan_sha256), project_root=root)
    result = load_planner_result(path=root / 'plans' / request.plan_filename, plan_root=root / 'plans')
    if has_export(result):
        from .snakemake_workflow import prepare_export_workflow
        return prepare_export_workflow(request, project_root=root)
    registry, recipe, policy = _check(result, root)
    required = list(dict.fromkeys([*prepared['approval_required_step_ids'], *policy.approval_required_step_ids]))
    if not policy.write_step_ids and any(s.skill not in {'inspect_vector', 'inspect_raster'} for s in result.plan.steps):
        raise InterfaceApiError('Direct read-only execution currently supports vector and raster inspection')
    recipes = root / 'workflow-recipes'
    if recipes.is_symlink():
        raise InterfaceApiError('recipe root cannot be a symlink')
    path = recipe_path(recipe, recipe_root=recipes)
    if path.exists():
        if path.is_symlink() or load_recipe(path, recipe_root=recipes) != recipe:
            raise InterfaceApiError('stored recipe does not match current plan')
    else:
        _, path = save_recipe(recipe, recipe_root=recipes)
    recipe_steps = {step.step_id: step for step in recipe.steps}
    plan_steps = {step["step_id"]: step for step in prepared["steps"]}
    steps = [{**step, "depends_on": recipe_steps[step["step_id"]].depends_on, 'requires_approval': step['step_id'] in required,
              'validation_required': step['validation_required'] or registry.get_skill(step['skill']).validation_required}
             for step in (plan_steps[step_id] for step_id in policy.topological_step_ids)]
    basis = dict(schema_version='1.0', plan_filename=request.plan_filename, plan_sha256=request.confirmed_plan_sha256,
                 recipe_filename=path.name, recipe_sha256=recipe_sha256(recipe), steps=steps,
                 approval_required_step_ids=required, write_step_ids=policy.write_step_ids,
                 execution_available=not policy.write_step_ids or load_settings().enable_write_tools,
                 execution_performed=False)
    digest = hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {**basis, 'review_sha256': digest}


def authorize_workflow(request: WorkflowRequest, *, project_root: Path):
    """Record explicit exact-scope decisions without running any operation."""
    from . import server as api
    root = api._trusted_root(project_root)
    review = prepare_workflow(request, project_root=root)
    if review.get('workflow_kind') == 'snakemake_export':
        from .snakemake_workflow import authorize_export_workflow
        return authorize_export_workflow(request, project_root=root)
    if request.confirmed_review_sha256 != review['review_sha256']:
        raise api.InterfaceApiError('Authorization review digest no longer matches')
    if not review['approval_required_step_ids']:
        raise api.InterfaceApiError('This workflow does not require authorization')
    if not request.approve_required_steps or not request.approver.strip() or not request.reason.strip():
        raise api.InterfaceApiError('Explicit approval, approver and reason are required for this exact scope')
    if not review['execution_available']:
        raise api.InterfaceApiError('Write tools are disabled; restart with --enable-write-tools')
    prepared = api.prepare_interface_plan_approval(api.InterfacePlanApprovalPreparationRequest(
        action='prepare_plan_approval', plan_filename=request.plan_filename,
        confirmed_plan_sha256=review['plan_sha256']), project_root=root)
    plan_filename = None
    recipe_filename = None
    if prepared['approval_required_step_ids']:
        decision = api.record_interface_plan_approval(api.InterfacePlanApprovalDecisionRequest(
            action='record_plan_approval', plan_filename=request.plan_filename,
            confirmed_plan_sha256=review['plan_sha256'],
            confirmed_approval_request_sha256=prepared['approval_request_sha256'], decision='approved',
            approver=request.approver.strip(), reason=request.reason.strip(), valid_for_minutes=30), project_root=root)
        plan_filename = decision['approval_filename']
    if review['write_step_ids']:
        prepared_recipe = api.prepare_interface_recipe_approval(recipe_filename=review['recipe_filename'],
            confirmed_recipe_sha256=review['recipe_sha256'], project_root=root)
        approved = api.record_interface_recipe_approval(api.InterfaceApprovalDecision(
            action='record_recipe_approval', recipe_filename=review['recipe_filename'],
            confirmed_recipe_sha256=review['recipe_sha256'],
            confirmed_approval_request_sha256=prepared_recipe['approval_request_sha256'], decision='approved',
            approver=request.approver.strip(), reason=request.reason.strip(), valid_for_minutes=30), project_root=root)
        recipe_filename = approved['approval_filename']
    return dict(schema_version='1.0', review_sha256=review['review_sha256'],
                plan_approval_filename=plan_filename, recipe_approval_filename=recipe_filename,
                approval_recorded=True, execution_performed=False)


def execute_workflow(request: WorkflowRequest, *, project_root: Path):
    from . import server as api
    root = api._trusted_root(project_root)
    review = prepare_workflow(request, project_root=root)
    if review.get('workflow_kind') == 'snakemake_export':
        from .snakemake_workflow import execute_export_workflow
        return execute_export_workflow(request, project_root=root)
    if not request.confirm_execution or request.confirmed_review_sha256 != review['review_sha256']:
        raise api.InterfaceApiError('Confirm the current exact workflow review before execution')
    if not review['execution_available']:
        raise api.InterfaceApiError('Write tools are disabled; restart the launcher with --enable-write-tools')
    plan_approval = request.plan_approval_filename
    recipe_approval = request.recipe_approval_filename
    key = review['plan_sha256']
    with _LOCK:
        if key in _ACTIVE:
            raise api.InterfaceApiError('This exact workflow is already executing')
        _ACTIVE.add(key)
    try:
        # Retain the prior explicit combined contract for existing API clients.
        # The current interface uses the separate Authorize endpoint instead.
        if review['approval_required_step_ids'] and not (plan_approval or recipe_approval):
            if not request.approve_required_steps:
                raise api.InterfaceApiError('Explicit approval is required for this exact scope; use Authorize first')
            authorization = authorize_workflow(request, project_root=root)
            plan_approval = authorization['plan_approval_filename']
            recipe_approval = authorization['recipe_approval_filename']
        prepared = api.prepare_interface_plan_approval(api.InterfacePlanApprovalPreparationRequest(
            action='prepare_plan_approval', plan_filename=request.plan_filename,
            confirmed_plan_sha256=key), project_root=root)
        if prepared['approval_required_step_ids']:
            if not plan_approval:
                raise api.InterfaceApiError('Plan authorization is missing; use Authorize first')
            verified = api.verify_interface_plan_approval(api.InterfacePlanApprovalVerificationRequest(
                action='verify_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=key,
                confirmed_approval_request_sha256=prepared['approval_request_sha256'], approval_filename=plan_approval), project_root=root)
            if not verified['approved']:
                raise api.InterfaceApiError('Plan authorization expired or blocked; make a fresh explicit decision')
        if review['write_step_ids']:
            if not recipe_approval:
                raise api.InterfaceApiError('Recipe authorization is missing; use Authorize first')
            prepared_recipe = api.prepare_interface_recipe_approval(recipe_filename=review['recipe_filename'],
                confirmed_recipe_sha256=review['recipe_sha256'], project_root=root)
            binding = dict(recipe_filename=review['recipe_filename'], confirmed_recipe_sha256=review['recipe_sha256'],
                           confirmed_approval_request_sha256=prepared_recipe['approval_request_sha256'], approval_filename=recipe_approval)
            preview = api.prepare_interface_execution_preview(api.InterfaceExecutionPreviewRequest(action='prepare_execution_preview', **binding), project_root=root)
            return api.execute_interface_recipe(api.InterfaceRecipeExecutionRequest(action='execute_exact_preview', confirmation='execute_exact_preview',
                confirmed_execution_preview_sha256=preview['execution_preview_sha256'], **binding), project_root=root)
        return _execute_inspections(review, root)
    finally:
        with _LOCK:
            _ACTIVE.discard(key)


def _inspection_root(root):
    from .server import InterfaceApiError
    destination = root / 'inspection-runs'
    if destination.is_symlink():
        raise InterfaceApiError('inspection run root cannot be a symlink')
    destination.mkdir(exist_ok=True)
    return destination


def _execute_inspections(review, root):
    from .server import _bounded_outcome, InterfaceApiError
    from geoagent_harness.intent.input import check_task_input
    from geoagent_harness.skills.inspect_vector.service import inspect_vector
    from geoagent_harness.skills.inspect_raster.service import inspect_raster
    from geoagent_harness.skills.inspect_raster.schemas import InspectRasterArguments
    destination = _inspection_root(root)
    record = dict(schema_version='1.0', run_id=uuid.uuid4().hex, plan_sha256=review['plan_sha256'],
                  plan_filename=review['plan_filename'], started_at=datetime.now(timezone.utc).isoformat(),
                  finished_at=None, status='running', step_results=[], approval_recorded=bool(review['approval_required_step_ids']), execution_performed=False)
    path = destination / (record['run_id'] + '.json')
    def persist():
        # Replace only our new UUID-owned record; never follow an existing symlink.
        temporary = destination / (record['run_id'] + '.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(record, stream); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    if path.exists():
        raise InterfaceApiError('inspection attempt already exists')
    persist()
    try:
        for step in review['steps']:
            relative = check_task_input(project_root=root, input_path=step['arguments']['path'])
            record['execution_performed'] = True
            if step['skill'] == 'inspect_vector':
                result = inspect_vector(root / relative, input_root=root / 'data/input')
            else:
                result = inspect_raster(InspectRasterArguments(path=root / relative, input_root=root / 'data/input'))
            record['step_results'].append(dict(step_id=step['step_id'], skill_id=step['skill'],
                status='inspected', validation_performed=False, outcome=_bounded_outcome(result.model_dump(mode='json')), validation_outcome=None))
            persist()
        record['status'] = 'completed'
    except Exception as error:
        record['status'] = 'failed'
        record['finding'] = 'Inspection failed; check the input path and dataset. No data was changed.'
        raise InterfaceApiError(record['finding']) from error
    finally:
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        persist()
    return record


def inspection_inventory(*, project_root):
    from .server import _trusted_root, InterfaceApiError
    destination = _trusted_root(project_root) / 'inspection-runs'
    if destination.is_symlink():
        raise InterfaceApiError('inspection run root cannot be a symlink')
    records = []
    for path in sorted(destination.glob('*.json'), key=lambda p: p.name)[:100]:
        if not path.is_symlink() and path.is_file() and path.stat().st_size <= 500_000:
            value = json.loads(path.read_text())
            if isinstance(value.get('run_id'), str) and value['run_id'] + '.json' == path.name:
                records.append(value)
    return {'records': sorted(records, key=lambda r: r['started_at'], reverse=True), 'execution_performed': False}


def execution_failure_payload(error):
    """Classify trusted failure messages without exposing driver details or values."""
    import re
    chain = []
    seen = set()
    current = error
    while current is not None and id(current) not in seen and len(chain) < 12:
        seen.add(id(current))
        chain.append(current)
        current = current.__cause__
    code = 'execution_failed'
    message = 'Governed execution failed. Inspect the failed attempt in Execution History before retrying.'
    for cause in chain:
        name = type(cause).__name__
        text = str(cause)
        if name == 'LoadVectorError':
            if text.startswith('PostGIS credential file is'):
                code, message = 'postgis_credentials_unavailable', 'PostGIS credential file is missing, unreadable or empty. Check the password-file configuration in the launcher terminal.'
            elif 'not allowed' in text:
                code, message = 'postgis_schema_not_allowed', 'The target schema is outside the configured allowed schemas. Review the schema and launcher configuration.'
            elif text.startswith('approved schema ') and 'does not exist' in text:
                code, message = 'postgis_schema_missing', 'The approved PostGIS schema does not exist. Review the target with your database administrator before a new run.'
            elif text.startswith('target table ') and 'exists' in text:
                code, message = 'postgis_target_exists', 'The target PostGIS table already exists. Choose a fresh reviewed table; destructive replacement remains blocked.'
            elif text.startswith('PostGIS load failed;'):
                code, message = 'postgis_load_failed', 'PostGIS connection or loading failed. Check database reachability, credentials and permissions in the launcher environment; driver details remain private.'
        elif name == 'RecipeEvidencePersistenceError':
            code, message = 'execution_evidence_failed', 'Operations may have completed, but durable evidence storage failed. Inspect the target and execution history before retrying.'
    failed_step = None
    for cause in chain:
        if type(cause).__name__ == 'RecipeRunError':
            match = re.search(r"step '(step_[1-9][0-9]*)'", str(cause))
            if match:
                failed_step = match.group(1)
                break
    return {'error': message, 'failure_code': code, 'failed_step_id': failed_step,
            'recovery_guidance': 'Inspect execution history and actual targets before a retry. Approval does not guarantee that database configuration or operation execution succeeds.'}
