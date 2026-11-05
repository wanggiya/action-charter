"""Durable, cooperative workflow runs using the existing governed executor.

No worker is restarted automatically. Cancellation is observed between complete
operations; an active write and its verification are allowed to finish.
"""
from __future__ import annotations
from .storage_paths import runtime_store_path, ensure_state_root
from geoagent_harness.workspace import WorkspaceLayout

import fcntl
import hashlib
import json
import os
import re
import time
import uuid
from geoagent_harness.storage import repositories, RepositoryError
from geoagent_harness.storage.files import FileJsonRecords
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock, Thread
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.model import ModelClientError, ModelSettingsError

from .workflow import WorkflowRequest

_LOCK = RLock()
TERMINAL = {'completed', 'failed', 'cancelled', 'interrupted', 'validation_failed'}


from .exploration_contracts import ChartAnalysis, ExplorationQuery
from .spatial_views import SpatialViewOptions
from geoagent_harness.tabular.analysis_contracts import AnalysisOptions


class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['start', 'list', 'latest', 'read', 'cancel', 'recover', 'assess', 'retain', 'preview', 'explore', 'spatial_view', 'table_analysis', 'execution_assistance', 'report']
    run_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    workflow: WorkflowRequest | None = None
    conversation_id: str | None = Field(default=None,pattern=r'^[a-f0-9]{32}$')
    analysis: ChartAnalysis | None = None
    query: ExplorationQuery | None = None
    table_options: AnalysisOptions | None = None
    assistant_question: str | None = Field(default=None, min_length=1, max_length=2000)
    spatial: SpatialViewOptions | None = None
    review_outcome: bool = False
    retry_assessment: bool = False
    step_id: str | None = Field(default=None, pattern=r'^step_[1-9][0-9]*$')
    confirmed_plan_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _directory(root):
    from .common import _trusted_root, InterfaceApiError
    root = _trusted_root(root)
    parent = runtime_store_path(root, 'workflow-state', 'interface-runs').parent
    directory = parent / 'interface-runs'
    if parent.is_symlink() or directory.is_symlink():
        raise InterfaceApiError('Workflow run storage is unsafe')
    ensure_state_root(root)
    try:
        return repositories(root).runs().ensure()
    except RepositoryError as error:
        raise InterfaceApiError(str(error)) from error


def _lease(directory):
    from .common import InterfaceApiError
    fd = os.open(directory / 'active.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise InterfaceApiError('A workflow is already active in this project; inspect or cancel that run first')
    return fd


def _store(directory, *, project_root=None):
    # Private callers with explicit directories retain the legacy override.
    return repositories(project_root).runs(directory=directory) if project_root is not None else FileJsonRecords(directory, max_bytes=512_000)


def _write(directory, record, *, project_root=None):
    content = json.dumps(record, ensure_ascii=False)
    if len(content.encode()) > 512_000:
        raise ValueError('Workflow run exceeds its storage budget')
    try:
        _store(directory, project_root=project_root).replace(record['run_id'] + '.json', content)
    except RepositoryError as error:
        from .common import InterfaceApiError
        raise InterfaceApiError(str(error)) from error


def _read(directory, identity, *, project_root=None):
    from .common import InterfaceApiError
    if not identity:
        raise InterfaceApiError('Choose a workflow run')
    # Compatibility for private legacy callers; production always supplies the project.
    root = project_root if project_root is not None else directory.parent.parent
    if project_root is not None and directory != runtime_store_path(root, 'workflow-state', 'interface-runs'):
        raise InterfaceApiError('Run history does not belong to this project workspace')
    path = directory / (identity + '.json')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 512_000:
        raise InterfaceApiError('Workflow run is unavailable or unsafe')
    try:
        record = _store(directory, project_root=project_root).read(identity + '.json')
    except RepositoryError as error:
        raise InterfaceApiError(str(error)) from error
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
            record['partial_outputs'] = _present_outputs(root,record)
            for step in record['steps']:
                if step['status'] == 'running':
                    step['status'] = 'interrupted'
                    record['failed_step_id'] = step['step_id']
                elif step['status'] == 'queued':
                    step['status'] = 'skipped'
            _write(directory, record, project_root=root)
        finally:
            os.close(fd)
    if record.get('critic_review',{}).get('status')=='running':
        from .run_assessment import review_in_progress
        if not review_in_progress(directory):
            record['critic_review']={**record['critic_review'],'status':'unavailable','finding':'Critic review was interrupted. Recorded results are preserved; no model call or operation was retried.'}
            _write(directory,record, project_root=root)
    if record.get('critic_review',{}).get('status')=='queued' and record['status'] in TERMINAL and record.get('finished_at'):
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(record['finished_at'])).total_seconds()
        if age>30:
            record['critic_review']={'status':'unavailable','finding':'Queued Critic assessment was interrupted or could not start. Results are preserved; nothing was retried.'}
            _write(directory,record, project_root=root)
    if record.get('successful_recipe', {}).get('status') == 'pending' and record['status'] in TERMINAL and record.get('finished_at'):
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(record['finished_at'])).total_seconds()
        if age > 30:
            record['successful_recipe'] = {'status': 'unavailable', 'finding': 'Indexing was interrupted. Retry indexing only; no operation was restarted.'}
            _write(directory, record, project_root=root)
    return record


def _source_paths(record):
    """Small local-file labels only; do not expose other operation arguments."""
    from pathlib import PurePosixPath
    paths=[]
    for step in record['steps']:
        for key in ('path','right_path'):
            value=step.get('arguments',{}).get(key)
            if not isinstance(value,str) or len(value)>960 or not value.startswith(('data/input/','data/output/')):
                continue
            parsed=PurePosixPath(value)
            if '..' in parsed.parts or str(parsed)!=value or '\\' in value or any(ord(c)<32 for c in value):
                continue
            if value not in paths:paths.append(value)
            if len(paths)==20:return paths
    return paths


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


def fit_table_preview(value,limit=6000):
    """Trim displayed rows before discarding useful table identities and quality facts."""
    if not isinstance(value,dict) or value.get('data_contract')!='table/csv-v1':return value
    result={**value,'preview':list(value.get('preview') or [])}
    def size():return len(json.dumps(result).encode())
    while result['preview'] and size()>limit:
        result['preview'].pop();result['preview_truncated']=True
    if size()>limit:
        # These definitions are already retained in the step arguments and full evidence.
        for key in ('decode_arguments','calculation_arguments','arguments','text_transform_definition'):
            result.pop(key,None)
            if size()<=limit:break
    return result


def fit_database_receipt(value,limit=48000):
    """Retain bounded actual mapping/schema facts before trimming displayed rows."""
    if not isinstance(value,dict) or not (value.get('column_metadata') or value.get('schema_version')=='postgres-import-preflight-v1'):
        return value
    result={**value}
    if 'preview' in result:
        result['preview']=list(result['preview'])
        while result['preview'] and len(json.dumps(result).encode())>limit:
            result['preview'].pop();result['preview_truncated']=True
    return result


class _Observer:
    def __init__(self, directory, identity, *, project_root=None):
        self.directory, self.identity = directory, identity
        self.project_root = project_root

    def checkpoint(self):
        from geoagent_harness.recipes.control import ExecutionCancelled
        with _LOCK:
            record = _read(self.directory, self.identity, project_root=self.project_root)
            if record['cancel_requested']:
                raise ExecutionCancelled('Cancelled before the next operation; completed outputs are retained')

    def progress(self, step_id, skill_id, status, outcome=None, validation=None):
        from .common import _bounded_outcome
        with _LOCK:
            record = _read(self.directory, self.identity, project_root=self.project_root)
            if status == 'running' and record['cancel_requested']:
                from geoagent_harness.recipes.control import ExecutionCancelled
                raise ExecutionCancelled('Cancelled before operation dispatch')
            for step in record['steps']:
                if step['step_id'] == step_id and step['skill_id'] == skill_id:
                    step['status'] = status
                    if status == 'running':
                        step.setdefault('started_at', _now())
                        record['execution_performed'] = True  # dispatched; completion not implied
                    else:
                        step['finished_at'] = _now()
                    if outcome is not None:
                        bounded = _bounded_outcome(fit_database_receipt(fit_table_preview(outcome)))
                        limit = 48000 if skill_id in {'validate_postgres_import','import_csv_to_postgres','inspect_postgres_table','export_postgres_to_csv'} else 128000 if isinstance(bounded,dict) and isinstance(bounded.get('table_analysis'),dict) else 16000 if isinstance(bounded,dict) and isinstance(bounded.get('discovery'),dict) else 6000
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
            _write(self.directory, record, project_root=self.project_root)


def _worker_impl(root, directory, identity, workflow, fd, review_outcome=False, inspection_binding=None):
    from .inspection_policy import active_inspection
    inspection_token = active_inspection.set(inspection_binding)
    from geoagent_harness.recipes.control import observer, ExecutionCancelled
    from .workflow import execute_workflow, execution_failure_payload
    token = observer.set(_Observer(directory, identity, project_root=root))
    try:
        with _LOCK:
            record = _read(directory, identity, project_root=root)
            record['status'] = 'running'
            _write(directory, record, project_root=root)
        observer.get().checkpoint()
        from geoagent_harness.model.telemetry import phase
        with phase('executor','execution'):
            result = execute_workflow(workflow, project_root=root)
        with _LOCK:
            record = _read(directory, identity, project_root=root)
            record['result'] = result if len(json.dumps(result).encode())<=160_000 else None
            record['status'] = 'validation_failed' if result['status'] == 'validation_failed' else 'completed'
            record['execution_performed'] = result.get('execution_performed', True)
            if record['status'] == 'validation_failed':
                record['failed_step_id'] = result.get('failed_step_id') or next((s['step_id'] for s in record['steps'] if s['status']=='validation_failed'), None)
            record['finished_at'] = _now()
            for step in record['steps']:
                if step['status'] == 'queued':
                    step['status'] = 'skipped'
            _write(directory, record, project_root=root)
    except Exception as error:
        with _LOCK:
            record = _read(directory, identity, project_root=root)
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
            _write(directory, record, project_root=root)
    finally:
        observer.reset(token)
        active_inspection.reset(inspection_token)
        os.close(fd)
    # Retention is metadata-only and fail-soft after the execution is durable.
    # It is independent of the browser and precedes optional model assessment.
    with _LOCK:
        _retain_record(root, directory, _read(directory, identity, project_root=root))
    with _LOCK:captured_record=_read(directory,identity, project_root=root)
    if captured_record.get('agent_coordination'):
        from geoagent_harness.orchestrator.task_agents import finish_run
        try:completed=finish_run(root,captured_record)
        except Exception:completed=None
        with _LOCK:
            current=_read(directory,identity, project_root=root)
            if completed:
                current['agent_coordination']=completed['coordination'];current['agent_report']=completed['report']
                review=completed['report']['assessment']
                assessment=review.get('assessment')
                current['critic_review']={'status':'complete' if assessment else 'unavailable','evidence_kind':completed['report']['review_kind'],'execution_authority_granted':False,
                    'assessment':{'deterministic_status':current['status'],'conclusion':'supported' if assessment and assessment['conclusion']=='supported' else 'needs_attention','summary':assessment['summary'],'findings':assessment['findings'],'limitations':assessment['limitations']} if assessment else None}
                if current['critic_review'].get('assessment') is None:current['critic_review'].pop('assessment',None)
            else:
                current['agent_report_status']='unavailable; execution results preserved'
                current['critic_review']={'status':'unavailable','finding':'Coordinated report unavailable. Execution results are preserved.'}
            _write(directory,current, project_root=root)
        return
    if review_outcome:
        from .run_assessment import assess_run
        # Execution is already final/durable and its lease released. Assessment
        # cannot hold up a later operation, grant authority or restart a worker.
        assess_run(root,identity)


def _worker(root, directory, identity, workflow, fd, review_outcome=False, inspection_binding=None):
    from geoagent_harness.model.telemetry import scope,phase
    try:conversation_id=_read(directory,identity, project_root=root).get('conversation_id')
    except Exception:conversation_id=None
    if not conversation_id:return _worker_impl(root,directory,identity,workflow,fd,review_outcome,inspection_binding)
    from geoagent_harness.model.catalog import request_selection
    with scope(root,conversation_id,independent=True) as telemetry,request_selection(root):
        telemetry['record']['workflow_run_id']=identity
        result=_worker_impl(root,directory,identity,workflow,fd,review_outcome,inspection_binding)
        try:
            final=_read(directory,identity, project_root=root)
            review=final.get('critic_review') or {}
            telemetry['record'].update(workflow_status=final['status'],outcome_review={key:review[key] for key in ('status','error_code','timeout_seconds') if key in review})
        except Exception:pass
        return result


def _retain_record(root, directory, record):
    from geoagent_harness.planner.outcome_recommendations import record_outcome
    try:
        record['recommendation_evidence'] = record_outcome(root, record)
    except Exception:
        record['recommendation_evidence'] = 'unavailable'
    from geoagent_harness.recipe_catalog.successful import retain
    try:
        receipt = retain(root, record)
    except Exception:
        receipt = {'status': 'unavailable', 'finding': 'Successful-workflow indexing was unavailable. Execution results are preserved; retry indexing only, never execution.'}
    record['successful_recipe'] = receipt
    try:
        _write(directory, record, project_root=root)
    except (OSError, ValueError):
        pass  # Even receipt persistence cannot change completed processing.
    return record


def _recovery(root, record):
    """Prepare a new proposal, never replay a write with old authority."""
    from geoagent_harness.approvals import load_planner_result
    from .workflow import EditRequest, validate_edit
    from .common import InterfaceApiError
    result = repositories(root).documents('plans').load(record['plan_filename']).model_copy(deep=True)
    if any(step.skill in {'export_snakemake_workflow', 'verify_snakemake_export', 'generate_report', 'soft_delete_postgres_rows', 'restore_postgres_rows'} for step in result.plan.steps):
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
        if 'target_table' in args and not (step.skill=='export_postgres_to_csv' and not args.get('source_step')):
            args['target_table'] = str(args['target_table'])[:40] + '_retry_' + suffix
    result.plan.summary = (('Resume remaining read operations: ' if read_only else 'Recovery with fresh targets: ') + result.plan.summary)[:2000]
    return validate_edit(EditRequest(action='validate_plan_edit', planner_result=result), project_root=root)


def _latest_scoped_run(directory, request, *, project_root=None):
    """Find exact saved scope before applying an inventory display limit.

    Inspect metadata without reconciling/writing unrelated runs. A bounded lookup
    failure is unavailable evidence, never a claim that no run exists.
    """
    from .common import InterfaceApiError
    if not request.conversation_id or not request.confirmed_plan_sha256:
        raise InterfaceApiError('Latest run lookup requires the exact conversation and plan')
    started = time.monotonic()
    latest = None
    for index, name in enumerate(_store(directory, project_root=project_root).names(order='native',limit=10001)):
        path = directory / name
        if index >= 10000 or time.monotonic() - started > 3:
            raise InterfaceApiError('Scoped run lookup exceeded its budget. Open Execution History; no execution was retried.')
        if not re.fullmatch('[a-f0-9]{32}', path.stem):
            continue
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 512000:
                raise ValueError('Unsafe receipt')
            record = _store(directory, project_root=project_root).read(path.name)
            if not isinstance(record, dict) or record.get('run_id') != path.stem or not isinstance(record.get('started_at'), str):
                raise ValueError('Invalid receipt')
        except (OSError, ValueError, RepositoryError):
            raise InterfaceApiError('Scoped run lookup encountered an unreadable receipt. Inspect Execution History; saved work was not retried.') from None
        if (record.get('conversation_id') == request.conversation_id
                and record.get('plan_sha256') == request.confirmed_plan_sha256
                and (latest is None or (record['started_at'], record['run_id']) > (latest['started_at'], latest['run_id']))):
            latest = record
    # Only the selected scope may undergo existing interrupted-run reconciliation.
    return _read(directory, latest['run_id'], project_root=project_root) if latest else None


def run_action(request: RunRequest, *, project_root: Path, background=True, inspection_binding=None, submission_run_id=None):
    from .common import _trusted_root, InterfaceApiError
    from .workflow import prepare_workflow
    root = _trusted_root(project_root)
    directory = _directory(root)
    if request.action == 'latest':
        with _LOCK:
            record = _latest_scoped_run(directory, request, project_root=root)
        return {'record':record,'execution_performed':False,'approval_performed':False}
    if request.action == 'execution_assistance':
        with _LOCK:
            record = _read(directory, request.run_id, project_root=root)
        if (not request.conversation_id or request.conversation_id != record.get('conversation_id')
                or request.confirmed_plan_sha256 != record['plan_sha256']):
            raise InterfaceApiError('Execution assistance requires the matching chat and plan')
        from geoagent_harness.model import load_model_settings
        try:
            model_name = load_model_settings().model
        except ModelSettingsError as error:
            raise InterfaceApiError('Choose an available model in Settings before requesting execution assistance. Recorded results are preserved.') from error
        identity = hashlib.sha256(json.dumps({'question':request.assistant_question,'step':request.step_id,
            'plan':record['plan_sha256'],'status':record['status'],'steps':record['steps'],
            'model':model_name},sort_keys=True).encode()).hexdigest()
        previous = record.get('execution_assistance') or {}
        if previous.get('request_sha256') == identity and not request.retry_assessment:
            return {**previous, 'cached': True}
        from .execution_assistance import assist
        try:
            response = assist(root,record,request)
        except (ModelClientError, ModelSettingsError) as error:
            from geoagent_harness.model.diagnostics import model_failure
            failure = model_failure(error)
            raise InterfaceApiError(f"{failure['error']}. {failure['retry_guidance']} Recorded workflow is preserved.") from error
        except ValueError as error:
            raise InterfaceApiError(str(error)) from error
        with _LOCK:
            latest = _read(directory,request.run_id, project_root=root)
            latest['execution_assistance'] = {**response,'request_sha256':identity}
            _write(directory,latest, project_root=root)
        return response
    if request.action=='assess':
        with _LOCK:record=_read(directory,request.run_id, project_root=root)
        if record.get('agent_coordination'):return record  # Reopening assessment never changes a frozen agent topology or calls another model.
        from .run_assessment import assess_run
        return assess_run(root,request.run_id,retry=request.retry_assessment)
    if request.action in {'preview', 'explore', 'spatial_view', 'table_analysis'}:
        # Capture scope under the run lock; CSV I/O must not hold up progress,
        # cooperative cancellation or another read of the execution record.
        with _LOCK:
            record = _read(directory, request.run_id, project_root=root)
        if request.action == 'table_analysis':
            from geoagent_harness.tabular.analytical_service import recorded_analysis
            try:
                return recorded_analysis(root, record, request)
            except ValueError as error:
                raise InterfaceApiError(str(error)) from error
        if request.action == 'spatial_view':
            if request.spatial is None:
                raise InterfaceApiError('Choose spatial viewing options')
            from .spatial_views import spatial_result
            return spatial_result(root, record, request)
        from .result_preview import preview_result
        from geoagent_harness.tabular.service import TabularError
        try:
            if request.action == 'explore':
                from .result_exploration import explore_result
                return explore_result(root, record, request)
            return preview_result(root, record, request)
        except TabularError as error:
            raise InterfaceApiError(str(error)) from error
    with _LOCK:
        if request.action == 'list':
            records = [_read(directory, p.stem, project_root=root) for p in (directory / name for name in _store(directory, project_root=root).names(order='recent',limit=50))]
            # Inventory stays small; full bounded results are fetched by run ID.
            records = [{**r,'source_paths':_source_paths(r),'result':None,'steps':[{**s,'arguments':{},'outcome':None,'validation_outcome':None} for s in r['steps']]} for r in records]
            return {'records': sorted(records, key=lambda r:r['started_at'], reverse=True), 'execution_performed':False}
        if request.action != 'start':
            record = _read(directory, request.run_id, project_root=root)
            if request.action=='report':
                from geoagent_harness.recipes.handoff import handoff
                return {**(record.get('agent_report') or {}),'handoff':handoff(record)}
            if request.action == 'cancel' and record['status'] not in TERMINAL:
                record['cancel_requested'] = True
                record['status'] = 'cancelling'
                _write(directory, record, project_root=root)
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
        if inspection_binding is not None:
            from .inspection_policy import check_dispatch
            check_dispatch(root, review, inspection_binding)
        if submission_run_id is not None and (directory / (submission_run_id + '.json')).exists():
            raise InterfaceApiError('Submission already has an execution record; inspect it rather than restarting')
        paths = [directory / name for name in _store(directory, project_root=root).names(order='native',limit=201)]
        if len(paths) >= 200:
            raise InterfaceApiError('Run inventory limit reached; archive reviewed run records before starting more')
        fd = _lease(directory)
        try:
            authority = hashlib.sha256(json.dumps({key:getattr(request.workflow,key) for key in (
                'plan_filename','confirmed_plan_sha256','confirmed_review_sha256','plan_approval_filename','recipe_approval_filename')}, sort_keys=True).encode()).hexdigest()
            if review['write_step_ids'] and any(_read(directory,p.stem, project_root=root)['authority_sha256']==authority for p in paths):
                raise InterfaceApiError('This write authority already has an attempt. Prepare recovery and record fresh authorization.')
            record = {'schema_version':'1.0', 'run_id':submission_run_id or uuid.uuid4().hex, 'plan_filename':review['plan_filename'],
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
            if inspection_binding is not None:
                record['submission_id'] = inspection_binding['submission_id']
                record['inspection_limits'] = {'source_bytes':8*1024*1024,'rows':10000,'columns':100,'wall_seconds':30,'preview_rows':20,'preview_columns':20}
            record['successful_recipe'] = {'status': 'pending'}
            record['conversation_id']=None
            if request.conversation_id:
                from .planning_tasks import conversation_record
                from geoagent_harness.planner.schemas import PlannerResult
                from geoagent_harness.approvals import plan_sha256
                chat=conversation_record(root,request.conversation_id)
                if chat and chat.get('planner_result') and plan_sha256(PlannerResult.model_validate(chat['planner_result']).plan)==review['plan_sha256']:
                    record['conversation_id']=request.conversation_id
                    captured=chat.get('agent_coordination') or {}
                    if captured.get('plan_sha256')==review['plan_sha256']:
                        record['agent_mode']=captured['mode'];record['agent_coordination']=captured;record['critic_review']={'status':'queued'}
            _write(directory, record, project_root=root)
        except BaseException:
            os.close(fd)
            raise
    if background:
        try:
            from contextvars import copy_context
            context = copy_context()
            Thread(target=context.run, args=(_worker,root,directory,record['run_id'],request.workflow,fd,request.review_outcome,inspection_binding), daemon=True).start()
        except BaseException:
            os.close(fd)
            raise
        return record
    _worker(root,directory,record['run_id'],request.workflow,fd,request.review_outcome,inspection_binding)
    return run_action(RunRequest(action='read',run_id=record['run_id']),project_root=root)
