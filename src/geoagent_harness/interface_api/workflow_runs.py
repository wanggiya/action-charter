"""Durable, cooperative workflow runs using the existing governed executor.

No worker is restarted automatically. Cancellation is observed between complete
operations; an active write and its verification are allowed to finish.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock, Thread
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .workflow import WorkflowRequest

_LOCK = RLock()
TERMINAL = {'completed', 'failed', 'cancelled', 'interrupted', 'validation_failed'}


class ChartAnalysis(BaseModel):
    model_config = ConfigDict(extra='forbid')
    group_by: str = Field(min_length=1, max_length=120)
    value: str | None = Field(default=None, min_length=1, max_length=120)
    aggregation: Literal['count', 'sum', 'mean', 'min', 'max']


class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['start', 'list', 'read', 'cancel', 'recover', 'assess', 'retain', 'preview']
    run_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    workflow: WorkflowRequest | None = None
    conversation_id: str | None = Field(default=None,pattern=r'^[a-f0-9]{32}$')
    analysis: ChartAnalysis | None = None
    review_outcome: bool = False
    retry_assessment: bool = False
    step_id: str | None = Field(default=None, pattern=r'^step_[1-9][0-9]*$')
    confirmed_plan_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _directory(root):
    from .server import _trusted_root, InterfaceApiError
    root = _trusted_root(root)
    parent = root / 'workflow-state'
    directory = parent / 'interface-runs'
    if parent.is_symlink() or directory.is_symlink():
        raise InterfaceApiError('Workflow run storage is unsafe')
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _lease(directory):
    from .server import InterfaceApiError
    fd = os.open(directory / 'active.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise InterfaceApiError('A workflow is already active in this project; inspect or cancel that run first')
    return fd


def _write(directory, record):
    content = json.dumps(record, ensure_ascii=False)
    if len(content.encode()) > 512_000:
        raise ValueError('Workflow run exceeds its storage budget')
    fd, name = tempfile.mkstemp(dir=directory, prefix='.run-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, directory / (record['run_id'] + '.json'))
        directory_fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(name).unlink(missing_ok=True)


def _read(directory, identity):
    from .server import InterfaceApiError
    if not identity:
        raise InterfaceApiError('Choose a workflow run')
    path = directory / (identity + '.json')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 512_000:
        raise InterfaceApiError('Workflow run is unavailable or unsafe')
    record = json.loads(path.read_text())
    if record.get('run_id') != identity:
        raise InterfaceApiError('Workflow run identity does not match')
    if record['status'] not in TERMINAL:
        # A lease held by any API/CLI process means this may still be active.
        try:
            fd = _lease(directory)
        except InterfaceApiError:
            return record
        try:
            record['status'] = 'interrupted'
            record['finished_at'] = _now()
            record['finding'] = 'Process stopped before a final result. Inspect targets; no workflow was restarted.'
            record['partial_outputs'] = _present_outputs(directory.parent.parent,record)
            for step in record['steps']:
                if step['status'] == 'running':
                    step['status'] = 'interrupted'
                    record['failed_step_id'] = step['step_id']
                elif step['status'] == 'queued':
                    step['status'] = 'skipped'
            _write(directory, record)
        finally:
            os.close(fd)
    if record.get('critic_review',{}).get('status')=='running':
        from .run_assessment import review_in_progress
        if not review_in_progress(directory):
            record['critic_review']={**record['critic_review'],'status':'unavailable','finding':'Critic review was interrupted. Recorded results are preserved; no model call or operation was retried.'}
            _write(directory,record)
    if record.get('critic_review',{}).get('status')=='queued' and record['status'] in TERMINAL and record.get('finished_at'):
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(record['finished_at'])).total_seconds()
        if age>30:
            record['critic_review']={'status':'unavailable','finding':'Queued Critic assessment was interrupted or could not start. Results are preserved; nothing was retried.'}
            _write(directory,record)
    if record.get('successful_recipe', {}).get('status') == 'pending' and record['status'] in TERMINAL and record.get('finished_at'):
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(record['finished_at'])).total_seconds()
        if age > 30:
            record['successful_recipe'] = {'status': 'unavailable', 'finding': 'Indexing was interrupted. Retry indexing only; no operation was restarted.'}
            _write(directory, record)
    return record


def _present_outputs(root, record):
    """Observe bounded local outputs only; never query a live database/service."""
    outputs=[]
    if (root/'data').is_symlink() or (root/'data/output').is_symlink():
        return outputs
    approved_root=(root/'data/output').resolve()
    for step in record['steps']:
        target=step['arguments'].get('target_path')
        if not isinstance(target,str) or not target.startswith('data/output/'):
            continue
        path=root/target
        try:
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(approved_root):
                continue
            size=path.stat().st_size
            digest=None
            if size<=32_000_000:
                with path.open('rb') as stream:
                    digest=hashlib.file_digest(stream,'sha256').hexdigest()
        except OSError:
            continue  # Missing preview must not prevent final run-state persistence.
        outputs.append({'step_id':step['step_id'],'path':target,'sha256':digest,'bytes':size,
                        'status':'present_after_stop_not_proof_of_success'})
    return outputs


class _Observer:
    def __init__(self, directory, identity):
        self.directory, self.identity = directory, identity

    def checkpoint(self):
        from geoagent_harness.recipes.control import ExecutionCancelled
        with _LOCK:
            record = _read(self.directory, self.identity)
            if record['cancel_requested']:
                raise ExecutionCancelled('Cancelled before the next operation; completed outputs are retained')

    def progress(self, step_id, skill_id, status, outcome=None, validation=None):
        from .server import _bounded_outcome
        with _LOCK:
            record = _read(self.directory, self.identity)
            if status == 'running' and record['cancel_requested']:
                from geoagent_harness.recipes.control import ExecutionCancelled
                raise ExecutionCancelled('Cancelled before operation dispatch')
            for step in record['steps']:
                if step['step_id'] == step_id and step['skill_id'] == skill_id:
                    step['status'] = status
                    if status == 'running':
                        step['started_at'] = _now()
                        record['execution_performed'] = True  # dispatched; completion not implied
                    else:
                        step['finished_at'] = _now()
                    if outcome is not None:
                        bounded = _bounded_outcome(outcome)
                        limit = 6000
                        if isinstance(bounded, dict) and isinstance(bounded.get('spatial_preview'), dict) and bounded['spatial_preview'].get('kind') == 'wgs84_geometry':
                            from geoagent_harness.skills.inspect_vector.preview import fit_recorded_geometry
                            bounded = fit_recorded_geometry(bounded)
                            limit = 12000
                        step['outcome'] = bounded if len(json.dumps(bounded).encode())<=limit else {'preview_omitted':True,'reason':'Intermediate result exceeds the recorded preview budget; inspect durable evidence'}
                    if validation is not None:
                        bounded = _bounded_outcome(validation)
                        step['validation_outcome'] = bounded if len(json.dumps(bounded).encode())<=3000 else {
                            'passed':validation.get('passed') if isinstance(validation,dict) else None,
                            'preview_omitted':True,'reason':'Validation preview exceeds 3 KB; inspect durable evidence'}
                    break
            _write(self.directory, record)


def _worker(root, directory, identity, workflow, fd, review_outcome=False):
    from geoagent_harness.recipes.control import observer, ExecutionCancelled
    from .workflow import execute_workflow, execution_failure_payload
    token = observer.set(_Observer(directory, identity))
    try:
        with _LOCK:
            record = _read(directory, identity)
            record['status'] = 'running'
            _write(directory, record)
        observer.get().checkpoint()
        result = execute_workflow(workflow, project_root=root)
        with _LOCK:
            record = _read(directory, identity)
            record['result'] = result if len(json.dumps(result).encode())<=160_000 else None
            record['status'] = 'validation_failed' if result['status'] == 'validation_failed' else 'completed'
            record['execution_performed'] = result.get('execution_performed', True)
            if record['status'] == 'validation_failed':
                record['failed_step_id'] = result.get('failed_step_id') or next((s['step_id'] for s in record['steps'] if s['status']=='validation_failed'), None)
            record['finished_at'] = _now()
            for step in record['steps']:
                if step['status'] == 'queued':
                    step['status'] = 'skipped'
            _write(directory, record)
    except Exception as error:
        with _LOCK:
            record = _read(directory, identity)
            cancelled = isinstance(error, ExecutionCancelled)
            record['status'] = 'cancelled' if cancelled else 'failed'
            record['finished_at'] = _now()
            failure = execution_failure_payload(error)
            record['finding'] = 'Cancelled at an operation boundary. Completed outputs remain.' if cancelled else failure['error']
            record['partial_outputs'] = _present_outputs(root,record)
            record['failed_step_id'] = None if cancelled else failure.get('failed_step_id') or next((s['step_id'] for s in record['steps'] if s['status']=='running'), None)
            for step in record['steps']:
                if step['status'] == 'running':
                    step['status'] = 'failed' if not cancelled else 'interrupted'
                elif step['status'] == 'queued':
                    step['status'] = 'skipped'
            _write(directory, record)
    finally:
        observer.reset(token)
        os.close(fd)
    # Retention is metadata-only and fail-soft after the execution is durable.
    # It is independent of the browser and precedes optional model assessment.
    with _LOCK:
        _retain_record(root, directory, _read(directory, identity))
    if review_outcome:
        from .run_assessment import assess_run
        # Execution is already final/durable and its lease released. Assessment
        # cannot hold up a later operation, grant authority or restart a worker.
        assess_run(root,identity)


def _retain_record(root, directory, record):
    from geoagent_harness.recipe_catalog.successful import retain
    try:
        receipt = retain(root, record)
    except Exception:
        receipt = {'status': 'unavailable', 'finding': 'Successful-workflow indexing was unavailable. Execution results are preserved; retry indexing only, never execution.'}
    record['successful_recipe'] = receipt
    try:
        _write(directory, record)
    except (OSError, ValueError):
        pass  # Even receipt persistence cannot change completed processing.
    return record


def _recovery(root, record):
    """Prepare a new proposal, never replay a write with old authority."""
    from geoagent_harness.approvals import load_planner_result
    from .workflow import EditRequest, validate_edit
    from .server import InterfaceApiError
    result = load_planner_result(path=root / 'plans' / record['plan_filename'], plan_root=root / 'plans').model_copy(deep=True)
    if any(step.skill in {'export_snakemake_workflow', 'verify_snakemake_export', 'generate_report'} for step in result.plan.steps):
        raise InterfaceApiError('This workflow needs target-specific recovery review; use Planner to revise it')
    suffix = uuid.uuid4().hex[:12]
    from geoagent_harness.skill_registry import load_skill_registry, SkillAccess
    registry=load_skill_registry(root)
    read_only=all(registry.get_skill(s.skill).access==SkillAccess.READ_ONLY for s in result.plan.steps)
    if read_only:
        completed={s['step_id'] for s in record['steps'] if s['status'] in {'completed','validated_success'}}
        remaining=[s for s in result.plan.steps if s.step_id not in completed]
        if not remaining:
            raise InterfaceApiError('All read operations completed; inspect recorded results rather than repeating them')
        mapping={s.step_id:f'step_{i}' for i,s in enumerate(remaining,1)}
        for step in remaining:
            step.depends_on=[mapping[s] for s in (step.depends_on or []) if s in mapping]
            step.step_id=mapping[step.step_id]
        result.plan.steps=remaining
    for step in result.plan.steps:
        args = step.arguments
        if 'target_path' in args:
            path = Path(args['target_path'])
            args['target_path'] = str(path.with_name(path.stem + '_retry_' + suffix + path.suffix))
        if 'target_table' in args:
            args['target_table'] = str(args['target_table'])[:40] + '_retry_' + suffix
    result.plan.summary = (('Resume remaining read operations: ' if read_only else 'Recovery with fresh targets: ') + result.plan.summary)[:2000]
    return validate_edit(EditRequest(action='validate_plan_edit', planner_result=result), project_root=root)


def run_action(request: RunRequest, *, project_root: Path, background=True):
    from .server import _trusted_root, InterfaceApiError
    from .workflow import prepare_workflow
    root = _trusted_root(project_root)
    directory = _directory(root)
    if request.action=='assess':
        from .run_assessment import assess_run
        return assess_run(root,request.run_id,retry=request.retry_assessment)
    if request.action == 'preview':
        # Capture scope under the run lock; CSV I/O must not hold up progress,
        # cooperative cancellation or another read of the execution record.
        with _LOCK:
            record = _read(directory, request.run_id)
        from .result_preview import preview_result
        from geoagent_harness.tabular.service import TabularError
        try:
            return preview_result(root, record, request)
        except TabularError as error:
            raise InterfaceApiError(str(error)) from error
    with _LOCK:
        if request.action == 'list':
            records = [_read(directory, p.stem) for p in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]]
            # Inventory stays small; full bounded results are fetched by run ID.
            records = [{**r,'result':None,'steps':[{**s,'arguments':{},'outcome':None,'validation_outcome':None} for s in r['steps']]} for r in records]
            return {'records': sorted(records, key=lambda r:r['started_at'], reverse=True), 'execution_performed':False}
        if request.action != 'start':
            record = _read(directory, request.run_id)
            if request.action == 'cancel' and record['status'] not in TERMINAL:
                record['cancel_requested'] = True
                record['status'] = 'cancelling'
                _write(directory, record)
            if request.action == 'retain':
                return _retain_record(root, directory, record)
            if request.action == 'recover':
                if record['status'] not in TERMINAL - {'completed'}:
                    raise InterfaceApiError('Recovery is available only after a stopped or failed run')
                return _recovery(root, record)
            return record
        if request.workflow is None or request.workflow.action != 'execute_workflow' or not request.workflow.confirm_execution:
            raise InterfaceApiError('Starting a run requires an explicit exact execution request')
        if request.workflow.approve_required_steps:
            raise InterfaceApiError('Record exact authorization separately before starting a durable run')
        review = prepare_workflow(request.workflow, project_root=root)
        if request.workflow.confirmed_review_sha256 != review['review_sha256']:
            raise InterfaceApiError('Workflow review digest no longer matches')
        if review.get('workflow_kind') == 'snakemake_export':
            raise InterfaceApiError('Snakemake export uses its existing synchronous execution path')
        paths = list(directory.glob('*.json'))
        if len(paths) >= 200:
            raise InterfaceApiError('Run inventory limit reached; archive reviewed run records before starting more')
        fd = _lease(directory)
        try:
            authority = hashlib.sha256(json.dumps({key:getattr(request.workflow,key) for key in (
                'plan_filename','confirmed_plan_sha256','confirmed_review_sha256','plan_approval_filename','recipe_approval_filename')}, sort_keys=True).encode()).hexdigest()
            if review['write_step_ids'] and any(_read(directory,p.stem)['authority_sha256']==authority for p in paths):
                raise InterfaceApiError('This write authority already has an attempt. Prepare recovery and record fresh authorization.')
            record = {'schema_version':'1.0', 'run_id':uuid.uuid4().hex, 'plan_filename':review['plan_filename'],
                'plan_sha256':review['plan_sha256'], 'authority_sha256':authority, 'status':'queued',
                'started_at':_now(), 'finished_at':None, 'cancel_requested':False, 'failed_step_id':None,
                'finding':None, 'result':None, 'execution_performed':False,
                'partial_outputs':[],
                'critic_review':{'status':'queued' if request.review_outcome else 'not_requested'},
                'recovery_guidance':'Completed writes are retained. Recovery prepares a full new workflow with fresh targets and requires fresh authorization; no automatic retry or write reuse.',
                'steps':[{'step_id':s['step_id'],'skill_id':s['skill'],'status':'queued','arguments':s['arguments'],
                          'depends_on':s.get('depends_on',[]),'outcome':None,'validation_outcome':None} for s in review['steps']]}
            # Only a matching own-chat snapshot can become automatic planning context.
            from geoagent_harness.recipe_catalog.successful import capture_basis
            try:
                record['retention_basis'] = capture_basis(root, review['steps'])
            except Exception:
                record['retention_basis'] = None
            record['successful_recipe'] = {'status': 'pending'}
            record['conversation_id']=None
            if request.conversation_id:
                from .planning_tasks import conversation_record
                from geoagent_harness.planner.schemas import PlannerResult
                from geoagent_harness.approvals import plan_sha256
                chat=conversation_record(root,request.conversation_id)
                if chat and chat.get('planner_result') and plan_sha256(PlannerResult.model_validate(chat['planner_result']).plan)==review['plan_sha256']:
                    record['conversation_id']=request.conversation_id
            _write(directory, record)
        except BaseException:
            os.close(fd)
            raise
    if background:
        try:
            Thread(target=_worker, args=(root,directory,record['run_id'],request.workflow,fd,request.review_outcome), daemon=True).start()
        except BaseException:
            os.close(fd)
            raise
        return record
    _worker(root,directory,record['run_id'],request.workflow,fd,request.review_outcome)
    return run_action(RunRequest(action='read',run_id=record['run_id']),project_root=root)
