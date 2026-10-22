"""Explicit submit-and-inspect orchestration. Reads/reconciliation never dispatch.

Receipt claim precedes inference. A crash at an uncertain stage requires review;
no planning or execution is replayed automatically, even for a read-only request.
"""
from __future__ import annotations
import hashlib
import json
import uuid
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .conversation import TurnRequest, conversation_turn
from .planning_tasks import database
from .inspection_policy import bounded_read, request_source, eligible, contract_digest, source_skill


class SubmissionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['submit', 'read']
    submission_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    conversation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    inspect_on_send: StrictBool = False
    turn: TurnRequest | None = None


def _table(connection):
    connection.execute('CREATE TABLE IF NOT EXISTS inspection_submissions_v1 (id TEXT PRIMARY KEY, value TEXT NOT NULL)')


def _get(connection, identity):
    if connection is None or not connection.execute("SELECT 1 FROM sqlite_master WHERE name='inspection_submissions_v1'").fetchone():
        return None
    row = connection.execute('SELECT value FROM inspection_submissions_v1 WHERE id=?', (identity,)).fetchone()
    if row is None:
        return None
    from .server import InterfaceApiError
    if len(row[0].encode()) > 2_000_000:
        raise InterfaceApiError('Submission receipt exceeds its storage budget')
    record = json.loads(row[0])
    if record['submission_id'] != identity:
        raise InterfaceApiError('Submission receipt identity changed')
    return record


def _put(connection, record):
    from .server import InterfaceApiError
    encoded = json.dumps(record, separators=(',', ':'))
    if len(encoded.encode()) > 2_000_000:
        raise InterfaceApiError('Submission receipt exceeds its storage budget')
    connection.execute('INSERT INTO inspection_submissions_v1 VALUES (?,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value', (record['submission_id'], encoded))


def _present(root, record):
    from .workflow_runs import run_action, RunRequest
    run = None
    if record.get('run_id'):
        path = root / 'workflow-state/interface-runs' / (record['run_id'] + '.json')
        if path.exists():
            run = run_action(RunRequest(action='read', run_id=record['run_id']), project_root=root)
            if run.get('submission_id') != record['submission_id'] or run.get('conversation_id') != record['conversation_id']:
                from .server import InterfaceApiError
                raise InterfaceApiError('Submission run provenance does not match')
    return {'submission': {key: record.get(key) for key in (
                'submission_id', 'conversation_id', 'status', 'finding', 'run_id')},
            'conversation': record.get('conversation'), 'run': run,
            'approval_performed': False, 'execution_performed': bool(run and run['execution_performed'])}


def submission_action(request: SubmissionRequest, *, project_root: Path, model_client=None, background=True):
    from .server import InterfaceApiError, _trusted_root
    root = _trusted_root(project_root)
    if request.action == 'read':
        with database(root) as connection:
            record = _get(connection, request.submission_id)
        if not record or record['conversation_id'] != request.conversation_id:
            raise InterfaceApiError('This submission is unavailable in this chat')
        return _present(root, record)
    turn = request.turn
    if turn is None or turn.action != 'turn' or turn.conversation_id != request.conversation_id:
        raise InterfaceApiError('Submit requires a matching explicit conversation turn')
    payload_sha = hashlib.sha256(json.dumps(request.model_dump(mode='json'), sort_keys=True).encode()).hexdigest()
    with database(root, write=True) as connection:
        _table(connection)
        existing = _get(connection, request.submission_id)
        if existing:
            if existing['request_sha256'] != payload_sha:
                raise InterfaceApiError('Submission ID was already used for different input; nothing replayed')
        else:
            if connection.execute('SELECT COUNT(*) FROM inspection_submissions_v1').fetchone()[0] >= 200:
                raise InterfaceApiError('Submission receipt limit reached; archive reviewed records before sending more')
            record = dict(submission_id=request.submission_id, conversation_id=request.conversation_id,
                          request_sha256=payload_sha, status='processing', run_id=None, conversation=None,
                          finding='Submission may be in progress or interrupted. Check saved chat/run state; nothing is automatically retried.')
            _put(connection, record)
    if existing:
        return _present(root, existing)
    try:
        source = None
        refusal = None
        if request.inspect_on_send:
            try:
                path = request_source(turn.message)
                if path:
                    source = bounded_read(root, action='snapshot', path=path)
                else:
                    refusal = 'Only a single explicit supported local metadata inspection can run on send. Use Execute for other proposals.'
            except (ValueError, OSError, InterfaceApiError):
                refusal = 'The source could not be safely bounded or snapshotted. Review the proposal; ordinary reader limits also apply to Execute.'
        response = conversation_turn(turn, project_root=root, model_client=model_client)
        record['conversation'] = response
        record['status'] = 'proposal_only'
        record['finding'] = refusal or 'Proposal saved. Nothing executed; use Execute when ready.'
        if (response.get('context_usage') or {}).get('result_view'):
            record['finding'] = 'Recorded-result view prepared. The workflow is unchanged; no workflow operation was executed.'
        if request.inspect_on_send and response['proposal_changed'] and response['planner_result']:
            from geoagent_harness.planner.schemas import PlannerResult
            result = PlannerResult.model_validate({key: response['planner_result'][key] for key in (
                'agent_id', 'model', 'original_request', 'context_references', 'plan', 'warnings')})
            refusal = refusal or eligible(root, result, turn.message, source)
            if not refusal:
                from .server import InterfaceGeneratedPlanSaveRequest, save_interface_reviewed_plan
                from .workflow import WorkflowRequest, prepare_workflow
                from .workflow_runs import RunRequest, run_action
                sha = response['planner_result']['plan_sha256']
                stored = save_interface_reviewed_plan(InterfaceGeneratedPlanSaveRequest(
                    action='save_generated_plan', confirmed_plan_sha256=sha,
                    allowed_skill_ids=response['allowed_skill_ids'], planner_result=result), project_root=root)
                review = prepare_workflow(WorkflowRequest(action='prepare_workflow', plan_filename=stored['plan_filename'],
                                          confirmed_plan_sha256=sha), project_root=root)
                binding = {**source, 'plan_sha256': sha, 'revision': response['revision'],
                           'conversation_id': request.conversation_id, 'submission_id': request.submission_id,
                           'contract_sha256': contract_digest(root, source_skill(source['path']))}
                record['run_id'] = uuid.uuid4().hex
                record['status'] = 'starting'
                record['finding'] = 'Inspection dispatch may be in progress. Check the recorded run; never resend automatically.'
                with database(root, write=True) as connection:
                    _put(connection, record)
                # Hold the chat write lease through final revision checking and
                # dispatch. A concurrent turn cannot replace the reviewed chat.
                with database(root, write=True):
                    run_action(RunRequest(action='start', conversation_id=request.conversation_id,
                        workflow=WorkflowRequest(action='execute_workflow', plan_filename=stored['plan_filename'],
                            confirmed_plan_sha256=sha, confirmed_review_sha256=review['review_sha256'], confirm_execution=True)),
                        project_root=root, background=background, inspection_binding=binding,
                        submission_run_id=record['run_id'])
                record['status'] = 'started'
                record['finding'] = 'Bounded inspection submitted. Inspect its recorded outcome; no data writes were authorized.'
            else:
                record['finding'] = refusal
        with database(root, write=True) as connection:
            _put(connection, record)
        return _present(root, record)
    except Exception:
        # Do not hide the existing safe Planner error contract. Record only a
        # fixed finding; raw exceptions may contain prompts, paths or settings.
        record['status'] = 'failed'
        record['finding'] = 'Submission stopped. Saved chat and any recorded run are preserved. Check them before a deliberate new submission; nothing is automatically retried.'
        with database(root, write=True) as connection:
            _put(connection, record)
        raise
