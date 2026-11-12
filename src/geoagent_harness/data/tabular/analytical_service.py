"""Shared bounded analytical service used by CLI, MCP and recorded table views."""
import hashlib
import json
from pathlib import Path

from geoagent_harness.contracts.analysis_options import AnalysisOptions, SourceTableReference
from geoagent_harness.contracts.paths import relative_path


def profile_table(root, path, options=None, *, delimiter=',', expected_sha256=None, checkpoint=None, max_seconds=None):
    from geoagent_harness.workspaces.sandbox.inspection import bounded_read
    options = AnalysisOptions.model_validate(options or {})
    path = relative_path(path, 'input')
    result = bounded_read(Path(root).resolve(strict=True), action='csv_discover', path=path,
                          delimiter=delimiter, analysis=options.model_dump(mode='json'), checkpoint=checkpoint, max_seconds=max_seconds)
    if expected_sha256 and result['source_sha256'] != expected_sha256:
        raise ValueError('Source changed since the recorded result. Saved evidence remains; inspect again.')
    return result


def source_reference(result):
    analysis = result.get('table_analysis')
    if not analysis:
        return None
    bindings = [{'path': result['source'], 'sha256': result['source_sha256']}]
    if analysis.get('codebook'):
        bindings.append({k: analysis['codebook'][k] for k in ('path','sha256')})
    identity = {'sources': bindings, 'query': analysis['request'], 'delimiter':result.get('delimiter',',')}
    return SourceTableReference(reference_id=hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
            **identity, row_count=analysis['matched_row_count'], columns=analysis['columns'],
            lifecycle='recorded query and evidence; no materialized full-table cache').model_dump(mode='json')


def recommend_fields(root,path,*,delimiter=',',source_options=None):
    """Shared fresh inspection advice; no model, dataframe, stats dispatch or writes."""
    from geoagent_harness.workspaces.sandbox.inspection import bounded_read
    path=relative_path(path,'input')
    result=bounded_read(Path(root).resolve(strict=True),action='csv_discover',path=path,delimiter=delimiter,preview_rows=0,analysis={'source_options':source_options} if source_options is not None else None)
    return result['field_guidance']


def recorded_analysis(root, record, request, *, max_seconds=None):
    """Explicit new read, bound to a completed chat/plan/step and original sources."""
    if (request.confirmed_plan_sha256 != record['plan_sha256'] or not request.conversation_id
            or request.conversation_id != record.get('conversation_id')):
        raise ValueError('Table analysis requires the matching chat and plan')
    step = next((s for s in record['steps'] if s['step_id'] == request.step_id), None)
    if not step or step['skill_id'] != 'inspect_csv' or step['status'] not in {'completed','validated_success','reused_completed'}:
        raise ValueError('Choose a completed CSV inspection')
    outcome = step.get('outcome') or {}
    if not outcome.get('source_sha256'):
        raise ValueError('No verified source identity in the recorded result')
    options = request.table_options or AnalysisOptions()
    original_selection=((step.get('arguments') or {}).get('analysis') or {}).get('source_options')
    from geoagent_harness.contracts.analysis_options import TableSourceOptions
    original_selection=TableSourceOptions.model_validate(original_selection).model_dump(mode='json') if original_selection is not None else None
    selected=options.source_options.model_dump(mode='json') if options.source_options is not None else None
    if selected is not None and selected!=original_selection:
        raise ValueError('Changing worksheet/record selection requires a new reviewed inspection')
    if original_selection is not None:
        options=options.model_copy(update={'source_options':TableSourceOptions.model_validate(original_selection)})
    original = (outcome.get('table_analysis') or {}).get('codebook')
    requested_codebook = relative_path(options.codebook_path, 'input') if options.codebook_path else None
    if requested_codebook != (original['path'] if original else None):
        raise ValueError('A new codebook requires a new reviewed inspection, not a view change')
    result = profile_table(root, outcome['source'], options, delimiter=(step.get('arguments') or {}).get('delimiter',','),
                           expected_sha256=outcome['source_sha256'], max_seconds=max_seconds)
    if original and result['table_analysis']['codebook']['sha256'] != original['sha256']:
        raise ValueError('Codebook changed since execution; inspect again')
    return {'run_id': record['run_id'], 'plan_sha256': record['plan_sha256'], 'step_id': step['step_id'],
            'table_analysis': result['table_analysis'], 'table_reference': result['table_reference'],
            'source_sha256': result['source_sha256'], 'verified_at_read': True,
            'resource_usage': result['resource_usage'], 'data_written': False, 'approval_performed': False}
