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


def planning_sources(root, message, base=None):
    """Resolve positive inspection planning requests, without reading content."""
    import re
    from geoagent_harness.data.discovery.input import input_references
    from geoagent_harness.contracts.paths import relative_path
    from geoagent_harness.agents.roles.planner.request_coverage import metadata_request_text
    if not re.match(r'\s*(?:please\s+)?(?:inspect|profile|analy[sz]e|read|summari[sz]e)\b', metadata_request_text(message), re.I):
        return [], None
    refs = input_references(message, root)
    if refs['unsafe_input_reference']:
        from geoagent_harness.core.policy.plan import PlannerPolicyError
        raise PlannerPolicyError('Read refused: input paths must remain under data/input. Absolute paths and parent traversal are not permitted.')
    if refs['missing_supplied_paths']:
        return [], 'Which existing file under data/input should I use? The requested input is unavailable or unsafe; no source was read.'
    paths = refs['existing_supplied_paths']
    if not paths and re.search(r'\b(?:it|(?:this|that|current|same|the current|the same)\s+(?:dataset|file|table|source))\b', message, re.I):
        for step in base.plan.steps if base else []:
            for key in ('path', 'right_path'):
                value = step.arguments.get(key)
                if not isinstance(value, str):
                    continue
                try:
                    value = relative_path(value, 'input')
                except ValueError:
                    continue
                if value.startswith('data/input/') and value not in paths:
                    paths.append(value)
        if len(paths) != 1:
            return [], 'Which input file should I use? Name one under data/input; the current workflow has no unique source.'
        from geoagent_harness.data.discovery.input import check_task_input
        try:
            check_task_input(project_root=root, input_path=paths[0])
        except ValueError:
            return [], 'Which existing input file should I use? The current workflow source is unavailable or unsafe.'
    if len(paths) > 4:
        return [], 'Which inputs should I use first? Choose at most four explicit sources under data/input.'
    if any(source_skill(path) is None for path in paths):
        return [], 'Which supported input should I use? Select an uncompressed file with a registered table, vector or raster reader.'
    return paths, None


def prepare_planning_cards(root, message, base, conversation_id, paths, available=None):
    """Policy adapter: only an explicit submit option permits new source reads."""
    import re
    from geoagent_harness.data.discovery.context import prepare, reader_contract
    from geoagent_harness.contracts.data_cards import CardUse
    from geoagent_harness.contracts.errors import InterfaceApiError
    from geoagent_harness.contracts.skill_registry import SkillAccess
    from geoagent_harness.platform.skill_registry import load_skill_registry
    from geoagent_harness.agents.roles.planner.request_coverage import requested_source_options
    discovery = planning_discovery.get() or {}
    if discovery.get('metadata') and 'planning_read_permitted' not in discovery:
        return []  # Preserve existing explicitly supplied same-turn reader facts.
    allowed = discovery.get('planning_read_permitted') is True
    options = requested_source_options(message)
    uses = []
    remaining_bytes = 1024**3
    registry = load_skill_registry(root)
    for path in paths:
        arguments = next((step.arguments for step in base.plan.steps
                          if step.skill.startswith('inspect_') and step.arguments.get('path') == path), {}) if base else {}
        analysis = arguments.get('analysis') or {}
        # A new named source starts with its own default selection. Current
        # selection is inherited only for pronoun-based follow-ups.
        from geoagent_harness.data.discovery.input import input_references
        explicit = path in input_references(message, root)['existing_supplied_paths']
        if explicit:
            analysis = {}
        chosen = options or analysis.get('source_options')
        try:
            # Natural-language selection changes are left to typed planning, not
            # used to certify an older/default population as the requested one.
            gate = registry.get_skill(source_skill(path))
            if gate.access != SkillAccess.READ_ONLY or gate.approval_required:
                use = CardUse(source=path, status='review_required', reader_contract=reader_contract(path),
                              finding='The current operation registry requires reviewed handling; no source context was read.').model_dump(mode='json')
            elif available is not None and source_skill(path) not in available:
                use = CardUse(source=path, status='review_required', reader_contract=reader_contract(path),
                              finding='Include the compatible inspector in the selected skills before reading source context.').model_dump(mode='json')
            elif remaining_bytes <= 0:
                use = CardUse(source=path, status='unavailable', reader_contract=reader_contract(path),
                              finding='The request reached its 1 GiB aggregate context budget; choose fewer inputs.').model_dump(mode='json')
            elif re.search(r'\b(?:filter|where|worksheet|cell range)\b', message, re.I) and not options:
                use = CardUse(source=path, status='review_required', reader_contract=reader_contract(path),
                              finding='A selection change needs typed arguments and reviewed Execute; no card certifies the requested population.').model_dump(mode='json')
            else:
                use = prepare(root, path, owner=conversation_id, allow_read=allowed, preliminary=True,
                              delimiter=arguments.get('delimiter') if not explicit else None,
                              source_options=chosen, filters=analysis.get('filters'), missing_values=analysis.get('missing_values'),
                              max_input_bytes=remaining_bytes)
            if use['source_checked']:
                remaining_bytes -= (use['card'] or {}).get('file_bytes') or 0
            uses.append(use)
        except (ValueError, OSError, InterfaceApiError):
            uses.append(CardUse(source=path, status='unavailable', reader_contract=reader_contract(path),
                                finding='Dataset context could not be safely verified. Saved evidence is unchanged; inspect source scope and reader limits.').model_dump(mode='json'))
    return uses

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
