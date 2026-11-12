"""Inspection eligibility/authority scope, with compatibility reader exports."""
from __future__ import annotations
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
# Preserve legacy test/caller access to the same standard-library module objects.
import subprocess
import sys
from geoagent_harness.contracts.table_sources import TABLE_SUFFIXES, RECORD_SUFFIXES
from geoagent_harness.contracts.inspection_formats import INSPECTOR_SUFFIXES, source_inspector

# Internal execution scope; never populated from a model or RunRequest field.
active_inspection = ContextVar('submitted_inspection', default=None)
planning_discovery = ContextVar('submitted_discovery_facts', default=None)

# Reader exports preserve legacy callers; eligibility and execution scope stay here.
from geoagent_harness.workspaces.sandbox.inspection import INSPECTION_CONTRACTS, bounded_read, source_skill, probe_action


def contract_digest(root, skill_id='inspect_csv'):
    from geoagent_harness.platform.skill_registry import load_skill_registry
    from geoagent_harness.capabilities.registry.registry import argument_models
    skill = load_skill_registry(root).get_skill(skill_id)
    value = {'adapter': INSPECTION_CONTRACTS[skill_id], 'skill': skill.model_dump(mode='json'), 'arguments': argument_models(root)[skill_id].model_json_schema()}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def request_source(message):
    from geoagent_harness.agents.roles.planner.request_coverage import inspection_only_skill, metadata_request_text
    from geoagent_harness.contracts.paths import relative_path
    import re
    if inspection_only_skill(message) not in INSPECTION_CONTRACTS:
        return None
    match = re.match(r'\s*inspect\s+([^\s;]+\.(?:csv|tsv|xlsx|jsonl|ndjson|json|geojson|gpkg|shp|tiff|tif))', metadata_request_text(message), re.I)
    return relative_path(match[1], 'input')


def eligible(root, result, message, source, *, expected_plan=None):
    """Return an explicit refusal reason, never trim an ineligible workflow."""
    from geoagent_harness.platform.skill_registry import load_skill_registry
    from geoagent_harness.contracts.skill_registry import SkillAccess
    if any(Path(step.arguments.get('path','')).suffix.lower() in RECORD_SUFFIXES for step in result.plan.steps):
        return 'Record/workbook inspection requires reviewed Execute; inspect-on-send does not choose sheets or record policies.'
    from geoagent_harness.task_actions.inspection_planning import plan_for_request
    exact=expected_plan or plan_for_request(message,INSPECTION_CONTRACTS)
    sources=source.get('sources',[source]) if source else []
    if not exact or [s.arguments['path'] for s in exact.steps]!=[s['path'] for s in sources]:
        return 'Only an explicit supported metadata inspection batch can inspect on send.'
    steps = result.plan.steps
    if any(step.arguments.get('analysis') is not None for step in steps):
        return 'Analytical profiles and codebooks require reviewed Execute; inspect-on-send remains metadata-only.'
    if len(steps) != len(sources):
        return 'The complete proposal must match every submitted inspection; nothing was trimmed.'
    registry = load_skill_registry(root)
    for step,item in zip(steps,sources):
        skill = registry.get_skill(step.skill)
        if step.skill!=source_skill(item['path']) or step.arguments.get('path')!=item['path']:
            return 'The proposed input/operation differs from the submitted source.'
        if skill.access != SkillAccess.READ_ONLY or skill.approval_required is not False or step.requires_approval:
            return 'This operation has an approval requirement; review it and use Authorize/Execute.'
    return None


def check_dispatch(root, review, binding):
    from geoagent_harness.contracts.errors import InterfaceApiError
    from geoagent_harness.task_actions.planning_tasks import conversation_record
    from geoagent_harness.core.policy.approvals import plan_sha256
    from geoagent_harness.contracts.planning import PlannerResult
    sources=binding.get('sources',[binding])
    if (review['write_step_ids'] or review['approval_required_step_ids'] or len(review['steps']) != len(sources)
            or review['plan_sha256'] != binding['plan_sha256']):
        raise InterfaceApiError('Submitted inspection scope or operation contract changed; nothing dispatched')
    for step,item in zip(review['steps'],sources):
        if (step['skill']!=source_skill(item['path']) or step['arguments'].get('path')!=item['path']
                or contract_digest(root,source_skill(item['path']))!=item['contract_sha256']):
            raise InterfaceApiError('Submitted inspection scope or operation contract changed; nothing dispatched')
    chat = conversation_record(root, binding['conversation_id'])
    if (not chat or chat['revision'] != binding['revision'] or not chat.get('planner_result')
            or plan_sha256(PlannerResult.model_validate(chat['planner_result']).plan) != binding['plan_sha256']):
        raise InterfaceApiError('Conversation changed before inspection dispatch; send a fresh request')
