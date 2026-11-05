"""Explicit submit-and-inspect orchestration. Reads/reconciliation never dispatch.

Receipt claim precedes inference. A crash at an uncertain stage requires review;
no planning or execution is replayed automatically, even for a read-only request.
"""
from __future__ import annotations
from .planning_tasks import as_transaction
import hashlib
import json
import uuid
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .storage_paths import runtime_store_path
from .conversation import TurnRequest, conversation_turn
from .planning_tasks import transaction as database
from .inspection_policy import bounded_read, request_source, eligible, contract_digest, source_skill
from geoagent_harness.tabular.source_contracts import RECORD_SUFFIXES


class SubmissionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['submit', 'read']
    submission_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    conversation_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    inspect_on_send: StrictBool = False
    turn: TurnRequest | None = None


def _table(connection):
    connection = as_transaction(connection)
    connection.records('inspection_submissions_v1').ensure()


def _get(connection, identity):
    connection = as_transaction(connection)
    if connection is None:
        return None
    raw = connection.records('inspection_submissions_v1').get(identity)
    if raw is None:
        return None
    from .common import InterfaceApiError
    if len(raw.encode()) > 2_000_000:
        raise InterfaceApiError('Submission receipt exceeds its storage budget')
    record = json.loads(raw)
    if record['submission_id'] != identity:
        raise InterfaceApiError('Submission receipt identity changed')
    return record


def _put(connection, record):
    connection = as_transaction(connection)
    from .common import InterfaceApiError
    encoded = json.dumps(record, separators=(',', ':'))
    if len(encoded.encode()) > 2_000_000:
        raise InterfaceApiError('Submission receipt exceeds its storage budget')
    connection.records('inspection_submissions_v1').put(record['submission_id'], encoded)


def _present(root, record):
    from .workflow_runs import run_action, RunRequest
    from .inspection_planning import clarification_usage
    conversation = record.get('conversation')
    if conversation is not None:
        conversation = {**conversation, 'context_usage': clarification_usage(
            conversation.get('context_usage'),message_count=len(conversation.get('messages',[])),
            available_count=len(conversation.get('allowed_skill_ids',[])))}
    run = None
    if record.get('run_id'):
        path = runtime_store_path(root, 'workflow-state', 'interface-runs') / (record['run_id'] + '.json')
        if path.exists():
            run = run_action(RunRequest(action='read', run_id=record['run_id']), project_root=root)
            if run.get('submission_id') != record['submission_id'] or run.get('conversation_id') != record['conversation_id']:
                from .common import InterfaceApiError
                raise InterfaceApiError('Submission run provenance does not match')
    return {'submission': {key: record.get(key) for key in (
                'submission_id', 'conversation_id', 'status', 'finding', 'run_id', 'discovery')},
            'conversation': conversation, 'run': run,
            'discovery_performed':bool(record.get('discovery')),
            'approval_performed': False, 'execution_performed': bool(run and run['execution_performed'])}


def _submission_action(request: SubmissionRequest, *, project_root: Path, model_client=None, background=True):
    from .common import InterfaceApiError, _trusted_root
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
            if connection.records('inspection_submissions_v1').count() >= 200:
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
        metadata_message=turn.message
        metadata_expectation=None
        from .inspection_planning import resolve_followup,plan_for_followup
        from geoagent_harness.planner.schemas import PlannerResult
        active=turn.current_plan
        if active is None:
            saved=conversation_turn(TurnRequest(action='read',conversation_id=turn.conversation_id),project_root=root).get('planner_result')
            if saved:active=PlannerResult.model_validate({key:value for key,value in saved.items() if key in PlannerResult.model_fields})
        followup=resolve_followup(turn.message,active.plan if active else None)
        if followup and followup.get('message'):
            metadata_message=followup['message']
            metadata_expectation=plan_for_followup(followup,['inspect_csv','inspect_vector','inspect_raster'])
        if request.inspect_on_send:
            try:
                from .inspection_planning import plan_for_request
                exact=metadata_expectation or plan_for_request(metadata_message, ['inspect_csv','inspect_vector','inspect_raster'])
                paths=[step.arguments['path'] for step in exact.steps] if exact else []
                if any(Path(path).suffix.lower() in RECORD_SUFFIXES for path in paths):
                    paths=[]
                    refusal='Record/workbook inspection requires reviewed Execute; nothing was read on send.'
                if paths:
                    from .inspection_policy import probe_action
                    sources=[]
                    for path in paths:
                        sources.append(bounded_read(root,action=probe_action(path),path=path,delimiter='\t' if path.lower().endswith('.tsv') else ','))
                        record['discovery']={'sources':[item['path'] for item in sources],'source':paths[0],
                            'scope':'preliminary_batch_metadata' if len(paths)>1 else 'preliminary_sample' if sources[0].get('discovery_kind')=='streaming_csv_v1' else 'preliminary_driver_metadata',
                            'column_count':sources[0].get('metadata',{}).get('column_count'),
                            'file_bytes':sum(item['bytes'] for item in sources),'sha256_complete':all('source_sha256' in item for item in sources),
                            'completed_sources':len(sources),'requested_sources':len(paths),'status':'ready' if len(sources)==len(paths) else 'probing'}
                        with database(root,write=True) as connection:
                            _put(connection,record)
                        if record['discovery']['file_bytes']>1024**3:
                            raise InterfaceApiError('Inspection batch exceeds 1 GiB aggregate input budget')
                    source=sources[0] if len(sources)==1 else {'sources':sources}

                else:
                    refusal = refusal or 'Only 1–4 explicit supported local metadata inspections can run on send. Use Execute for other proposals.'
            except (ValueError, OSError, InterfaceApiError):
                if record.get('discovery'):record['discovery']['status']='incomplete'
                refusal = 'The source could not be safely bounded or snapshotted. Review the proposal; ordinary reader limits also apply to Execute.'
        from .inspection_policy import planning_discovery
        discovery_token=planning_discovery.set(source or {'routing':'explicit_submit'})
        try:
            response = conversation_turn(turn, project_root=root, model_client=model_client)
        finally:
            planning_discovery.reset(discovery_token)
        record['conversation'] = response
        record['status'] = 'proposal_only'
        record['finding'] = refusal or ('Proposal saved after preliminary metadata discovery. No workflow run executed; use Execute when ready.' if record.get('discovery') else 'Proposal saved. Nothing executed; use Execute when ready.')
        if (response.get('context_usage') or {}).get('model_request',{}).get('stage')=='inspection_clarification':
            record['finding']='Input clarification required. The current workflow is unchanged; nothing was dispatched.'
        if (response.get('context_usage') or {}).get('result_view'):
            record['finding'] = 'Recorded-result view prepared. The workflow is unchanged; no workflow operation was executed.'
        if (response.get('context_usage') or {}).get('model_request',{}).get('stage')=='field_guidance':
            record['finding']='Field suggestions explained from recorded evidence. The current workflow is unchanged; no workflow operation was executed.'
        if (response.get('context_usage') or {}).get('model_request',{}).get('stage')=='analytical_exploration':
            state=(response.get('analytical_session') or {}).get('status','partial')
            record['status']='explored' if state=='completed' else 'exploration_'+state
            record['finding']='Read-only exploration '+state.replace('_',' ')+'. Evidence is saved; the workflow is unchanged. No data files were written or workflow run dispatched.'
            with database(root,write=True) as connection:_put(connection,record)
            return _present(root,record)
        exact_reply=(response.get('context_usage') or {}).get('model_request',{}).get('stage')=='deterministic_inspection'
        if request.inspect_on_send and (response['proposal_changed'] or exact_reply) and response['planner_result']:
            from geoagent_harness.planner.schemas import PlannerResult
            result = PlannerResult.model_validate({key: response['planner_result'][key] for key in (
                'agent_id', 'model', 'original_request', 'context_references', 'plan', 'warnings')})
            refusal = refusal or eligible(root, result, metadata_message, source, expected_plan=metadata_expectation)
            if not refusal:
                from .artifacts import InterfaceGeneratedPlanSaveRequest, save_interface_reviewed_plan
                from .workflow import WorkflowRequest, prepare_workflow
                from .workflow_runs import RunRequest, run_action
                sha = response['planner_result']['plan_sha256']
                stored = save_interface_reviewed_plan(InterfaceGeneratedPlanSaveRequest(
                    action='save_generated_plan', confirmed_plan_sha256=sha,
                    allowed_skill_ids=response['allowed_skill_ids'], planner_result=result), project_root=root)
                review = prepare_workflow(WorkflowRequest(action='prepare_workflow', plan_filename=stored['plan_filename'],
                                          confirmed_plan_sha256=sha), project_root=root)
                sources=source.get('sources',[source])
                binding = {'sources':[{**item,'contract_sha256':contract_digest(root,source_skill(item['path']))} for item in sources], 'plan_sha256': sha, 'revision': response['revision'],
                           'conversation_id': request.conversation_id, 'submission_id': request.submission_id,
                           }
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


def submission_action(request: SubmissionRequest, *, project_root: Path, model_client=None, background=True):
    if request.action=='read':return _submission_action(request,project_root=project_root,model_client=model_client,background=background)
    from geoagent_harness.model.telemetry import scope
    with scope(project_root,request.conversation_id,request.submission_id) as state:
        response=_submission_action(request,project_root=project_root,model_client=model_client,background=background)
        state['record']['workflow_run_id']=(response.get('submission') or {}).get('run_id')
        state['record']['submission_status']=(response.get('submission') or {}).get('status')
        return response
