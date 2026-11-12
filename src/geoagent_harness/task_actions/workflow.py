"""Typed current-plan review and execution; context never supplies authority."""
from __future__ import annotations
from geoagent_harness.platform.storage import repositories
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
from geoagent_harness.platform.workspace import WorkspaceLayout

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.core.policy.approvals import load_planner_result, plan_sha256
from geoagent_harness.contracts.planning import PlannerResult
from geoagent_harness.core.policy.plan import normalize_plan_input_filenames, validate_plan_policy
from geoagent_harness.core.policy.recipe_definition import planner_recipe_definition
from geoagent_harness.capabilities.workflow import _check, validate_edit
from geoagent_harness.contracts.actions import EditRequest
from geoagent_harness.contracts import recipes as schemas
from geoagent_harness.core.policy.recipe import validate_recipe_policy
from geoagent_harness.core.ledger.recipe_storage import save_recipe, load_recipe, recipe_path
from geoagent_harness.core.ledger.recipe_identity import recipe_sha256
from geoagent_harness.platform.skill_registry import load_skill_registry

from geoagent_harness.core.policy.write_policy import effective, snapshot

from geoagent_harness.contracts.snakemake import ExportArguments, VerifyArguments
from geoagent_harness.capabilities.workflow import has_export

from geoagent_harness.capabilities.registry.registry import argument_models, builtin_argument_models
ARGUMENTS = builtin_argument_models()
from geoagent_harness.contracts.postgres import ARGUMENTS as PG_ARGUMENTS, READ_IDS as PG_READS

_LOCK = Lock()
_ACTIVE: set[str] = set()




class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: Literal['prepare_workflow', 'authorize_workflow', 'execute_workflow']
    conversation_id: str | None = Field(default=None,pattern=r'^[a-f0-9]{32}$')
    plan_filename: str = Field(pattern=r'^planner-plan\.[a-f0-9]{64}\.json$')
    confirmed_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirmed_review_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    confirm_execution: Literal[True] | None = None
    plan_approval_filename: str | None = Field(default=None, pattern=r'^approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}\.json$')
    recipe_approval_filename: str | None = Field(default=None, pattern=r'^recipe-approval-[a-z0-9-]+\.json$')
    approve_required_steps: bool = False
    approver: str = Field(default='', max_length=200)
    reason: str = Field(default='', max_length=2000)






def prepare_workflow(request: WorkflowRequest, *, project_root: Path):
    from geoagent_harness.platform.project import _trusted_root
    from geoagent_harness.contracts.errors import InterfaceApiError
    from geoagent_harness.contracts.actions import InterfacePlanApprovalPreparationRequest
    from geoagent_harness.task_actions.artifacts import prepare_interface_plan_approval
    from geoagent_harness.platform.settings import load_settings
    root = _trusted_root(project_root)
    prepared = prepare_interface_plan_approval(InterfacePlanApprovalPreparationRequest(
        action='prepare_plan_approval', plan_filename=request.plan_filename,
        confirmed_plan_sha256=request.confirmed_plan_sha256), project_root=root)
    result = repositories(root).documents('plans', directory=runtime_store_path(root, 'plans')).load((runtime_store_path(root, 'plans') / request.plan_filename).name)
    if has_export(result):
        from geoagent_harness.task_actions.snakemake_workflow import prepare_export_workflow
        return prepare_export_workflow(request, project_root=root)
    registry, recipe, policy = _check(result, root)
    required = list(dict.fromkeys([*prepared['approval_required_step_ids'], *policy.approval_required_step_ids]))
    if not policy.write_step_ids and any(s.skill not in {'inspect_vector', 'inspect_raster', 'inspect_csv', *PG_READS} for s in result.plan.steps):
        raise InterfaceApiError('Direct read-only execution supports vector, raster and CSV inspection')
    recipes = runtime_store_path(root, 'workflow-recipes')
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
    from geoagent_harness.platform.storage.operation_packages import installed_packages
    from geoagent_harness.contracts.operation_packages import configuration
    packages = installed_packages(root)
    for step in steps:
        if step['skill'] in PG_ARGUMENTS:
            from geoagent_harness.data.databases.postgres.service import effects
            step['database_effects']=effects(step['skill'],step['arguments'],load_settings())
        package = packages.get(step['skill'])
        if package:
            step['adapter_configuration'] = configuration(package)
    basis = dict(schema_version='1.0', plan_filename=request.plan_filename, plan_sha256=request.confirmed_plan_sha256,
                 recipe_filename=path.name, recipe_sha256=recipe_sha256(recipe), steps=steps,
                 approval_required_step_ids=required, write_step_ids=policy.write_step_ids,
                 execution_available=not policy.write_step_ids or effective(load_settings(), root).enable_write_tools,
                 execution_performed=False)
    if request.conversation_id:
        from geoagent_harness.task_actions.planning_tasks import conversation_record
        chat=conversation_record(root,request.conversation_id) or {}
        coordination=chat.get('agent_coordination') or {}
        if coordination.get('plan_sha256')==request.confirmed_plan_sha256:
            basis['agent_mode']=coordination['mode']
            basis['conversation_id']=request.conversation_id
            basis['coordination_sha256']=hashlib.sha256(json.dumps(coordination,sort_keys=True).encode()).hexdigest()
    if policy.write_step_ids and snapshot(root):
        state = snapshot(root)
        basis['write_policy'] = {key:state[key] for key in ('session_id','revision','enabled')}
    digest = hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {**basis, 'review_sha256': digest}


def _authorize_workflow(request: WorkflowRequest, *, project_root: Path):
    """Record explicit exact-scope decisions without running any operation."""
    from geoagent_harness.task_actions import execution as actions
    root = actions._trusted_root(project_root)
    review = prepare_workflow(request, project_root=root)
    if review.get('workflow_kind') == 'snakemake_export':
        from geoagent_harness.task_actions.snakemake_workflow import authorize_export_workflow
        return authorize_export_workflow(request, project_root=root)
    if request.confirmed_review_sha256 != review['review_sha256']:
        raise actions.InterfaceApiError('Authorization review digest no longer matches')
    if not review['approval_required_step_ids']:
        raise actions.InterfaceApiError('This workflow does not require authorization')
    if not request.approve_required_steps or not request.approver.strip() or not request.reason.strip():
        raise actions.InterfaceApiError('Explicit approval, approver and reason are required for this exact scope')
    if not review['execution_available']:
        raise actions.InterfaceApiError('Write operations are OFF. Enable them in Settings, then review and authorize again.')
    prepared = actions.prepare_interface_plan_approval(actions.InterfacePlanApprovalPreparationRequest(
        action='prepare_plan_approval', plan_filename=request.plan_filename,
        confirmed_plan_sha256=review['plan_sha256']), project_root=root)
    plan_filename = None
    recipe_filename = None
    if prepared['approval_required_step_ids']:
        decision = actions.record_interface_plan_approval(actions.InterfacePlanApprovalDecisionRequest(
            action='record_plan_approval', plan_filename=request.plan_filename,
            confirmed_plan_sha256=review['plan_sha256'],
            confirmed_approval_request_sha256=prepared['approval_request_sha256'], decision='approved',
            approver=request.approver.strip(), reason=request.reason.strip(), valid_for_minutes=30), project_root=root)
        plan_filename = decision['approval_filename']
    if review['write_step_ids']:
        prepared_recipe = actions.prepare_interface_recipe_approval(recipe_filename=review['recipe_filename'],
            confirmed_recipe_sha256=review['recipe_sha256'], project_root=root)
        approved = actions.record_interface_recipe_approval(actions.InterfaceApprovalDecision(
            action='record_recipe_approval', recipe_filename=review['recipe_filename'],
            confirmed_recipe_sha256=review['recipe_sha256'],
            confirmed_approval_request_sha256=prepared_recipe['approval_request_sha256'], decision='approved',
            approver=request.approver.strip(), reason=request.reason.strip(), valid_for_minutes=30), project_root=root)
        recipe_filename = approved['approval_filename']
    return dict(schema_version='1.0', review_sha256=review['review_sha256'],
                plan_approval_filename=plan_filename, recipe_approval_filename=recipe_filename,
                approval_recorded=True, execution_performed=False)


def execute_workflow(request: WorkflowRequest, *, project_root: Path):
    from geoagent_harness.task_actions import execution as actions
    root = actions._trusted_root(project_root)
    review = prepare_workflow(request, project_root=root)
    if review.get('workflow_kind') == 'snakemake_export':
        from geoagent_harness.task_actions.snakemake_workflow import execute_export_workflow
        return execute_export_workflow(request, project_root=root)
    if not request.confirm_execution or request.confirmed_review_sha256 != review['review_sha256']:
        raise actions.InterfaceApiError('Confirm the current exact workflow review before execution')
    if not review['execution_available']:
        raise actions.InterfaceApiError('Write operations are OFF. Enable them in Settings, then review and authorize again.')
    plan_approval = request.plan_approval_filename
    recipe_approval = request.recipe_approval_filename
    key = review['plan_sha256']
    with _LOCK:
        if key in _ACTIVE:
            raise actions.InterfaceApiError('This exact workflow is already executing')
        _ACTIVE.add(key)
    try:
        # Retain the prior explicit combined contract for existing API clients.
        # The current interface uses the separate Authorize endpoint instead.
        if review['approval_required_step_ids'] and not (plan_approval or recipe_approval):
            if not request.approve_required_steps:
                raise actions.InterfaceApiError('Explicit approval is required for this exact scope; use Authorize first')
            authorization = authorize_workflow(request, project_root=root)
            plan_approval = authorization['plan_approval_filename']
            recipe_approval = authorization['recipe_approval_filename']
        prepared = actions.prepare_interface_plan_approval(actions.InterfacePlanApprovalPreparationRequest(
            action='prepare_plan_approval', plan_filename=request.plan_filename,
            confirmed_plan_sha256=key), project_root=root)
        if prepared['approval_required_step_ids']:
            if not plan_approval:
                raise actions.InterfaceApiError('Plan authorization is missing; use Authorize first')
            verified = actions.verify_interface_plan_approval(actions.InterfacePlanApprovalVerificationRequest(
                action='verify_plan_approval', plan_filename=request.plan_filename, confirmed_plan_sha256=key,
                confirmed_approval_request_sha256=prepared['approval_request_sha256'], approval_filename=plan_approval), project_root=root)
            if not verified['approved']:
                raise actions.InterfaceApiError('Plan authorization expired or blocked; make a fresh explicit decision')
            if review['write_step_ids']:
                from geoagent_harness.core.policy.approvals import load_approval
                from geoagent_harness.core.policy.write_policy import check
                check(root, load_approval(path=runtime_store_path(root, 'approvals') / plan_approval, approval_root=runtime_store_path(root, 'approvals')))
        if review['write_step_ids']:
            if not recipe_approval:
                raise actions.InterfaceApiError('Recipe authorization is missing; use Authorize first')
            prepared_recipe = actions.prepare_interface_recipe_approval(recipe_filename=review['recipe_filename'],
                confirmed_recipe_sha256=review['recipe_sha256'], project_root=root)
            binding = dict(recipe_filename=review['recipe_filename'], confirmed_recipe_sha256=review['recipe_sha256'],
                           confirmed_approval_request_sha256=prepared_recipe['approval_request_sha256'], approval_filename=recipe_approval)
            preview = actions.prepare_interface_execution_preview(actions.InterfaceExecutionPreviewRequest(action='prepare_execution_preview', **binding), project_root=root)
            return actions.execute_interface_recipe(actions.InterfaceRecipeExecutionRequest(action='execute_exact_preview', confirmation='execute_exact_preview',
                confirmed_execution_preview_sha256=preview['execution_preview_sha256'], **binding), project_root=root)
        return _execute_inspections(review, root)
    finally:
        with _LOCK:
            _ACTIVE.discard(key)


def _inspection_root(root):
    from geoagent_harness.contracts.errors import InterfaceApiError
    destination = runtime_store_path(root, 'inspection-runs')
    if destination.is_symlink():
        raise InterfaceApiError('inspection run root cannot be a symlink')
    ensure_state_root(root)
    destination.mkdir(mode=0o700,parents=True,exist_ok=True)
    return destination


def _execute_inspections(review, root):
    from geoagent_harness.platform.outcomes import _bounded_outcome
    from geoagent_harness.contracts.errors import InterfaceApiError
    from geoagent_harness.data.discovery.input import check_task_input
    from geoagent_harness.data.spatial.skills.inspect_vector.service import inspect_vector
    from geoagent_harness.data.spatial.skills.inspect_raster.service import inspect_raster
    from geoagent_harness.data.spatial.skills.inspect_raster.schemas import InspectRasterArguments
    destination = _inspection_root(root)
    record = dict(schema_version='1.0', run_id=uuid.uuid4().hex, plan_sha256=review['plan_sha256'],
                  plan_filename=review['plan_filename'], started_at=datetime.now(timezone.utc).isoformat(),
                  finished_at=None, status='running', step_results=[], approval_recorded=bool(review['approval_required_step_ids']), execution_performed=False)
    from geoagent_harness.platform.execution_control import observer
    if observer.get() is not None:
        record['workflow_run_id'] = observer.get().identity
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
            from geoagent_harness.platform.execution_control import checkpoint, progress
            checkpoint()
            progress(step['step_id'], step['skill'], 'running')
            relative = '' if step['skill'] in PG_READS else check_task_input(project_root=root, input_path=step['arguments']['path'])
            record['execution_performed'] = True
            from geoagent_harness.task_actions.inspection_policy import active_inspection
            spatial_binding = None
            if step['skill']=='inspect_vector' and relative.lower().endswith('.geojson') and not active_inspection.get():
                try:
                    from geoagent_harness.workspaces.sandbox.inspection import bounded_read
                    spatial_binding = bounded_read(root, action='snapshot', path=relative, checkpoint=checkpoint)
                except (ValueError, OSError, InterfaceApiError):
                    pass  # Ordinary Execute retains existing inspector support.
            from geoagent_harness.task_actions.inspection_policy import active_inspection, check_dispatch
            from geoagent_harness.workspaces.sandbox.inspection import bounded_read
            bound = active_inspection.get()
            if step['skill'] in PG_READS:
                from geoagent_harness.data.databases.postgres.service import inspect as inspect_postgres
                from geoagent_harness.platform.settings import load_settings
                result=inspect_postgres(step['skill'],step['arguments'],load_settings().model_copy(update={'project_root':root}))
            elif bound:
                check_dispatch(root, review, bound)
                if 'sources' in bound:
                    bound=next(item for item in bound['sources'] if item['path']==relative)
                if bound.get('discovery_kind') in {'streaming_csv_v1','streaming_spatial_v1'}:
                    result=bounded_read(root,action='csv_discover' if bound['discovery_kind']=='streaming_csv_v1' else 'spatial_discover',path=relative,source_identity=bound['source_identity'],
                        delimiter=step['arguments'].get('delimiter',','),preview_rows=step['arguments'].get('preview_rows',5),
                        checkpoint=checkpoint,on_metadata=lambda value: progress(step['step_id'],step['skill'],'running',value))
                else:

                    result = bounded_read(root, action='inspect', path=relative,
                        source_sha256=bound['source_sha256'],
                        delimiter=step['arguments'].get('delimiter', ','),
                        preview_rows=step['arguments'].get('preview_rows', 5), checkpoint=checkpoint)
            elif step['skill'] == 'inspect_csv':
                from geoagent_harness.data.tabular.service import inspect_csv
                result=bounded_read(root,action='csv_discover',path=relative,
                    delimiter=step['arguments'].get('delimiter',','),preview_rows=step['arguments'].get('preview_rows',5),
                    checkpoint=checkpoint,on_metadata=lambda value: progress(step['step_id'],step['skill'],'running',value),
                    analysis=step['arguments'].get('analysis'))
            elif relative.lower().endswith(('.tif','.tiff','.gpkg','.shp')):
                result=bounded_read(root,action='spatial_discover',path=relative,checkpoint=checkpoint,
                    on_metadata=lambda value: progress(step['step_id'],step['skill'],'running',value))
            elif step['skill'] == 'inspect_vector':
                result = inspect_vector(root / relative, input_root=root / 'data/input')
            else:
                result = inspect_raster(InspectRasterArguments(path=root / relative, input_root=root / 'data/input'))
            if spatial_binding:
                from geoagent_harness.workspaces.sandbox.inspection import bounded_read
                after = bounded_read(root, action='snapshot', path=relative, checkpoint=checkpoint)
                if after['source_sha256'] != spatial_binding['source_sha256']:
                    raise InterfaceApiError('Spatial input changed during inspection')
                result = result if isinstance(result, dict) else result.model_dump(mode='json')
                result['spatial_source_sha256'] = after['source_sha256']
            record['step_results'].append(dict(step_id=step['step_id'], skill_id=step['skill'],
                status='inspected', validation_performed=False, outcome=_bounded_outcome(result if isinstance(result, dict) else result.model_dump(mode='json')), validation_outcome=None))
            persist()
            progress(step['step_id'], step['skill'], 'completed', record['step_results'][-1]['outcome'])
        record['status'] = 'completed'
    except Exception as error:
        from geoagent_harness.platform.execution_control import ExecutionCancelled
        if isinstance(error, ExecutionCancelled):
            record['status'] = 'cancelled'
            raise
        record['status'] = 'failed'
        record['finding'] = 'Inspection failed; check the input path and dataset. No data was changed.'
        raise InterfaceApiError(record['finding']) from error
    finally:
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        persist()
    return record


def inspection_inventory(*, project_root):
    from geoagent_harness.platform.project import _trusted_root
    from geoagent_harness.contracts.errors import InterfaceApiError
    destination = runtime_store_path(_trusted_root(project_root), 'inspection-runs')
    if destination.is_symlink():
        raise InterfaceApiError('inspection run root cannot be a symlink')
    records = []
    for path in sorted(destination.glob('*.json'), key=lambda p: p.name)[:100]:
        if not path.is_symlink() and path.is_file() and path.stat().st_size <= 500_000:
            value = json.loads(path.read_text())
            if isinstance(value.get('run_id'), str) and value['run_id'] + '.json' == path.name:
                if value.get('status') == 'running' and value.get('workflow_run_id'):
                    from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action
                    run = run_action(RunRequest(action='read',run_id=value['workflow_run_id']),project_root=project_root)
                    if run['status'] in {'interrupted','cancelled','failed'}:
                        value['status'] = run['status']
                        value['finished_at'] = run['finished_at']
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
        if name == 'PostgresError':
            code, message = 'postgres_operation_rejected', text[:600]
            break
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
        elif name == 'WritePolicyError':
            code, message = 'write_policy_blocked', text[:500]
        elif name == 'TabularError':
            code, message = 'tabular_operation_rejected', 'Table operation rejected: ' + text[:500]
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


def authorize_workflow(request: WorkflowRequest, *, project_root: Path):
    from geoagent_harness.core.policy.write_policy import issuance
    review=prepare_workflow(request,project_root=project_root)
    with issuance(project_root,review.get('write_policy')):
        return _authorize_workflow(request,project_root=project_root)


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
prepare_workflow = _task_entrypoint(prepare_workflow, audit=False)
execute_workflow = _task_entrypoint(execute_workflow)
inspection_inventory = _task_entrypoint(inspection_inventory, audit=False)
authorize_workflow = _task_entrypoint(authorize_workflow)
