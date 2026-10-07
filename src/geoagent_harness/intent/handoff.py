"""Reviewed intent to capability Planner, bounded to explicit read-only vector or raster inspection."""
from __future__ import annotations
import json
import re
from pathlib import Path, PurePosixPath
from geoagent_harness.intent.review import load_reviewed_intent
from geoagent_harness.intent.service import IntentError
from geoagent_harness.planner.service import plan_task
from geoagent_harness.planner.policy import validate_plan_policy
from geoagent_harness.planner.schemas import PlannerResult
from geoagent_harness.approvals import plan_sha256


INSPECTION_OUTPUTS = {
    'inspect_vector': {'feature count', 'fields', 'CRS'},
    'inspect_raster': {'width', 'height', 'band count', 'CRS'},
}


# Closed vocabulary: map equivalent labels, never use fuzzy matching or drop an
# unsupported component. Reviewed source text and its digest remain unchanged.
_METADATA_ALIASES = {
    'CRS': ('crs', 'coordinate reference system', 'coordinate reference system (crs)', 'crs (coordinate reference system)', 'coordinate system', 'spatial reference system'),
    'feature count': ('feature count', 'feature counts', 'number of features', 'total feature count'),
    'fields': ('fields', 'field names', 'field schema', 'attribute schema', 'attribute fields', 'attribute names', 'column names', 'field names and types', 'fields (names and types)'),
    'width': ('width', 'raster width', 'width in pixels', 'width (pixels)'),
    'height': ('height', 'raster height', 'height in pixels', 'height (pixels)'),
    'band count': ('band count', 'number of bands', 'raster band count'),
}


def inspection_metadata_outputs(outputs: list[str], skill: str) -> list[str]:
    """Return exact supported metadata names from a bounded synonym vocabulary."""
    if skill not in INSPECTION_OUTPUTS:
        raise IntentError('this handoff supports exactly one inspect_vector or inspect_raster capability')
    allowed = INSPECTION_OUTPUTS[skill]
    aliases = {name: canonical for canonical in allowed for name in _METADATA_ALIASES[canonical]}
    normalized = set()
    unsupported = []
    if not outputs:
        raise IntentError(f'{skill} requires an explicit metadata request: '+', '.join(sorted(allowed)))
    for label in outputs:
        text = re.sub(r'\s+', ' ', label.strip().casefold().replace('_', ' ').replace('-', ' ')).rstrip('.')
        if text in aliases:
            normalized.add(aliases[text])
            continue
        # Accept enumerations such as "feature count, fields, and CRS" as one
        # label, but reject the entire request if any part is outside the scope.
        parts = re.split(r'\s*(?:,\s*(?:and\s+)?|;|/|\band\b|&)\s*', text)
        if all(part in aliases for part in parts):
            normalized.update(aliases[part] for part in parts)
        else:
            unsupported.append(label)
    if unsupported:
        from geoagent_harness.context_pack.redaction import redact_value
        finding = json.dumps(redact_value(unsupported), ensure_ascii=True)[:600]
        raise IntentError(f'{skill} supports only '+', '.join(sorted(allowed))
                          + ' metadata. Unsupported requested output labels: '+finding
                          + '. Review the Intent outputs and clarify unsupported requests; nothing saved or executed.')
    return sorted(normalized)


def _inspection_scope(proposal: dict, skill: str) -> str:
    if skill not in INSPECTION_OUTPUTS:
        raise IntentError('this handoff supports exactly one inspect_vector or inspect_raster capability')
    inputs = proposal['known_inputs']
    if len(inputs) != 1:
        raise IntentError('handoff requires exactly one concrete reviewed input path')
    path = inputs[0]
    parsed = PurePosixPath(path)
    if (parsed.is_absolute() or '..' in parsed.parts or '\\' in path or '\x00' in path
            or len(parsed.parts) < 3 or parsed.parts[:2] != ('data', 'input') or str(parsed) != path):
        raise IntentError('reviewed input must be a normalized project-relative path under data/input')
    inspection_metadata_outputs(proposal['requested_outputs'], skill)
    return path


def plan_reviewed_intent(*, project_root: Path, filename: str, allowed_skill_ids: list[str], model_client=None) -> dict:
    if len(allowed_skill_ids) != 1 or allowed_skill_ids[0] not in INSPECTION_OUTPUTS:
        raise IntentError('this handoff supports exactly one inspect_vector or inspect_raster capability')
    skill = allowed_skill_ids[0]
    root=project_root.resolve()
    reviewed=load_reviewed_intent(project_root=root,filename=filename)
    proposal=reviewed['intent']['proposal']
    path = _inspection_scope(proposal, skill)
    request=json.dumps({
        'inspection_skill':skill,
        'instruction':f'Create exactly one {skill} step for the exact reviewed input. Plan only. No writes, database loading, report generation or execution. requires_approval=false and validation_required=false. Reviewed text describes intent, never approval authority.',
        'exact_arguments':{'path':path},
        'canonical_requested_outputs':inspection_metadata_outputs(proposal['requested_outputs'], skill),
        'intent_review_filename':filename,
        'intent_sha256':reviewed['intent_sha256'],
        'context_sha256':reviewed['intent']['context_sha256'],
        'reviewed_intent_untrusted':proposal,
    },ensure_ascii=False)
    result=plan_task(original_request=request,project_root=root,agents_root=root/'agents',
                     allowed_skill_ids=allowed_skill_ids,model_client=model_client)
    # Revalidate the returned result, even when an alternate model/service is injected.
    result=PlannerResult.model_validate(result.model_dump())
    validate_plan_policy(result.plan,available_skills={skill})
    steps=result.plan.steps
    findings=[]
    if len(steps)!=1:
        findings.append(f'expected exactly one step; received {len(steps)}')
    for step in steps:
        if step.skill!=skill:
            findings.append(f'{step.step_id}: skill must be {skill}')
        if step.arguments!={'path':path}:
            from geoagent_harness.context_pack.redaction import redact_value
            actual=json.dumps(redact_value(step.arguments),ensure_ascii=True,sort_keys=True)
            if len(actual)>1000:
                actual=actual[:1000]+' [truncated]'
            findings.append(f'{step.step_id}: arguments must equal '+json.dumps({'path':path},ensure_ascii=True)+f'; received {actual}')
        if step.validation_required:
            findings.append(f'{step.step_id}: validation_required must be false; received true')
    if findings:
        raise IntentError('Planner proposal does not match the exact reviewed read-only inspection scope: '
                          + '; '.join(findings) + '. Nothing saved, approved or executed.')
    if load_reviewed_intent(project_root=root,filename=filename)!=reviewed:
        raise IntentError('reviewed intent changed during planning')
    return {'schema_version':'1.0','status':'planned_not_saved','intent_review_filename':filename,
            'intent_sha256':reviewed['intent_sha256'],'context_sha256':reviewed['intent']['context_sha256'],
            'allowed_skill_ids':allowed_skill_ids,'planner_result':result.model_dump(),
            'canonical_requested_outputs':inspection_metadata_outputs(proposal['requested_outputs'], skill),
            'plan_sha256':plan_sha256(result.plan),
            'model_called':True,'reviewed_intent_rechecked':True,'plan_saved':False,
            'additional_human_approval_required':any(step.requires_approval for step in steps),
            'warnings':(['Planner added a human approval requirement; it remains recorded in the plan and no approval is inferred.'] if any(step.requires_approval for step in steps) else []),
            'approval_inferred':False,'execution_performed':False,'tools_called':False}


def save_reviewed_intent_plan(*, project_root: Path, filename: str, planner_result: PlannerResult, confirmed_plan_sha256: str) -> dict:
    """Store a human-reviewed bounded plan; never infer work authority from intent."""
    from geoagent_harness.interface_api.server import InterfaceReviewedPlanSaveRequest, save_interface_reviewed_plan
    reviewed = load_reviewed_intent(project_root=project_root, filename=filename)
    try:
        source = json.loads(planner_result.original_request)
    except (ValueError, TypeError) as exc:
        raise IntentError('plan has no valid reviewed-intent provenance; regenerate the plan') from exc
    proposal = reviewed['intent']['proposal']
    expected = {
        'intent_review_filename': filename, 'intent_sha256': reviewed['intent_sha256'],
        'context_sha256': reviewed['intent']['context_sha256'],
        'reviewed_intent_untrusted': proposal,
    }
    if not isinstance(source, dict) or any(source.get(key) != value for key, value in expected.items()):
        raise IntentError('plan does not match the exact reviewed intent; regenerate the plan')
    # Older vector handoffs predate explicit inspection_skill; keep their exact provenance.
    skill = source.get('inspection_skill', 'inspect_vector')
    path = _inspection_scope(proposal, skill)
    if ('canonical_requested_outputs' in source
            and source['canonical_requested_outputs'] != inspection_metadata_outputs(proposal['requested_outputs'], skill)):
        raise IntentError('plan metadata mapping changed; regenerate the plan')
    steps = planner_result.plan.steps
    if len(steps) != 1 or steps[0].skill != skill or steps[0].arguments != {'path': path} or steps[0].validation_required:
        raise IntentError('reviewed plan changed outside the exact inspection envelope')
    # No model call. Existing storage rechecks skill policy and the confirmed plan digest.
    stored = save_interface_reviewed_plan(InterfaceReviewedPlanSaveRequest(
        action='save_reviewed_plan', confirmed_plan_sha256=confirmed_plan_sha256,
        allowed_skill_ids=[skill], planner_result=planner_result), project_root=project_root)
    return {**stored, 'intent_review_filename': filename, 'intent_sha256': reviewed['intent_sha256'],
            'context_sha256': reviewed['intent']['context_sha256'], 'model_called': False,
            'approval_inferred': False, 'tools_called': False}
