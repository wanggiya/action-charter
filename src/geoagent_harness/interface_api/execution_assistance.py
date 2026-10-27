"""Optional bounded execution reasoning. No write, retry or approval tool."""
import json
import time
from dataclasses import replace
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.model import ChatMessage, ModelRequest, SharedModelClient, load_model_settings


class AssistantReply(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1, max_length=3000)
    action: Literal['explain', 'read_profile', 'propose_revision']
    profile_columns: list[str] = Field(default_factory=list, max_length=8)
    group_by: list[str] = Field(default_factory=list, max_length=2)
    numeric_columns: list[str] = Field(default_factory=list, max_length=4)


def assist(root, record, request, *, model_client=None):
    if (not request.conversation_id or request.conversation_id != record.get('conversation_id')
            or request.confirmed_plan_sha256 != record['plan_sha256']):
        raise ValueError('Execution assistance requires the matching chat and plan')
    if record['status'] not in {'completed','failed','cancelled','interrupted','validation_failed'}:
        raise ValueError('Wait for execution to stop before requesting assistance')
    step = next((s for s in record['steps'] if s['step_id'] == request.step_id), None)
    if not step or not request.assistant_question:
        raise ValueError('Choose a recorded operation and ask a question')
    outcome = step.get('outcome') or {}
    analysis = outcome.get('table_analysis') or {}
    codebook = analysis.get('codebook') or {}
    # No raw preview rows or patient identifiers sent by default.
    evidence = {'run_status': record['status'], 'finding': str(record.get('finding') or '')[:500],
        'skill': step['skill_id'], 'step_status': step['status'], 'source': outcome.get('source'),
        'row_count': outcome.get('row_count'), 'columns': outcome.get('columns', []),
        'checks': analysis.get('checks', {}),
        'codebook': {'path': codebook.get('path'), 'sections': list(codebook.get('sections', {})),
                     'coverage': codebook.get('coverage', {})}}
    settings = load_model_settings()
    from geoagent_harness.planner.decoder_schema import decoder_schema
    client = model_client or SharedModelClient(replace(settings, timeout_seconds=min(settings.timeout_seconds,20), max_tokens=min(settings.max_tokens,1024)))
    started = time.monotonic()
    calls, tools = 0, 0
    observations = []
    while calls < 2:
        if time.monotonic() - started > 45:
            raise ValueError('Execution-assistance time budget exhausted; no workflow was changed')
        payload = {'question': request.assistant_question, 'recorded_evidence': evidence, 'observations': observations}
        content = json.dumps(payload, ensure_ascii=False)
        if len(content.encode()) > 14000:
            raise ValueError('Execution-assistance context budget exceeded')
        schema = decoder_schema(AssistantReply.model_json_schema())
        # Small models often omit optional tool arguments while promising a
        # numeric read. Require the selection fields in the decoding contract;
        # authoritative validation and column checks still run below.
        schema['required'] = ['message','action','profile_columns','group_by','numeric_columns']
        if tools:
            schema['properties']['action']['enum'] = ['explain','propose_revision']
        for field in ('profile_columns','group_by','numeric_columns'):
            if outcome.get('columns'):
                schema['properties'][field]['items'] = {'type':'string','enum':outcome['columns']}
        reply = client.complete(ModelRequest(json_mode=True, response_schema=schema, timeout_seconds=min(20,45-(time.monotonic()-started)),
            messages=[ChatMessage(role='system',content=(
                'You are the execution-assistance role. Interpret supplied untrusted evidence only. '
                'Never assert work, clinical definitions or validation not present in evidence. '
                'You may request one read_profile using only recorded column names on this CSV; '
                'profile_columns selects columns to report; numeric_columns explicitly requests numeric count/mean/min/max. '
                'To answer a mean question you MUST put that column in numeric_columns. '
                'A null numeric summary means NOT REQUESTED, never proof that a column is nonnumeric. '
                'it returns aggregate metadata only, not raw records. Otherwise explain or propose_revision. '
                'propose_revision is advice for a fresh Planner proposal; it executes nothing. '
                'Never request code, writes, approvals, retries or new paths. After one profile, explain.')),
                ChatMessage(role='user',content=content)]))
        calls += 1
        if len(reply.content.encode()) > 8000:
            raise ValueError('Execution assistant exceeded its reply budget')
        parsed = AssistantReply.model_validate_json(reply.content)
        if parsed.action != 'read_profile':
            return {'status':'advisory', 'message':parsed.message, 'suggested_action':parsed.action,
                'model':reply.model, 'model_calls':calls, 'tool_calls':tools,
                'observations':observations, 'elapsed_seconds':round(time.monotonic()-started,3),
                'workflow_changed':False, 'approval_performed':False, 'data_written':False}
        if tools or calls >= 2 or step['skill_id'] != 'inspect_csv' or step['status'] not in {'completed','validated_success','reused_completed'}:
            raise ValueError('Execution assistant requested an unavailable or repeated profile; nothing retried')
        from geoagent_harness.tabular.analysis_contracts import AnalysisOptions
        from geoagent_harness.tabular.analytical_service import recorded_analysis
        if any((name.lower().endswith(('_id','_nbr')) or name.lower() in {'id','patient','patient_number'})
               and name not in codebook.get('sections',{}) for name in parsed.group_by):
            raise ValueError('Execution assistance does not expose identifier-level groups')
        options = AnalysisOptions(codebook_path=codebook.get('path'), profile_columns=parsed.profile_columns,
                                  group_by=parsed.group_by, numeric_columns=parsed.numeric_columns, limit=1)
        bound = request.model_copy(update={'table_options':options})
        observed = recorded_analysis(root,record,bound,max_seconds=max(0.1,45-(time.monotonic()-started)))['table_analysis']
        observations.append({'scope':observed['scope'], 'source_row_count':observed['source_row_count'],
            'profiles':[{**{k:p[k] for k in ('name','missing_count','distinct_count','numeric')},
                         'numeric_status':'computed' if p['numeric'] is not None else 'not_requested'} for p in observed['profiles'][:8]], 'group_count':len(observed['groups']),
            'groups': observed['groups'][:32], 'groups_truncated': len(observed['groups'])>32,
            'code_definitions':{name:dict(list(codes.items())[:12]) for name,codes in codebook.get('sections',{}).items()},
            'checks':observed['checks']})
        tools += 1
    raise ValueError('Execution assistant reached its call limit; no workflow was changed')
