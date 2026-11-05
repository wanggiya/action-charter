"""Read a bounded CSV artifact belonging to an exact recorded completed step."""
import hashlib
import json

from geoagent_harness.tabular.service import TabularError, read_bytes, read_frame


def recorded_frame(root, record, request):
    if request.confirmed_plan_sha256 != record['plan_sha256']:
        raise TabularError('Result preview plan does not match the recorded run')
    if request.conversation_id and request.conversation_id != record.get('conversation_id'):
        raise TabularError('Result preview conversation does not match the recorded run')
    step = next((s for s in record['steps'] if s['step_id'] == request.step_id), None)
    if not step or step['status'] not in {'completed', 'validated_success', 'reused_completed'}:
        raise TabularError('Choose a completed recorded step for preview')
    outcome = step.get('outcome') or {}
    if not isinstance(outcome, dict):
        raise TabularError('No artifact identity recorded for this step')
    output = outcome.get('output') or {}
    if not isinstance(output, dict):
        raise TabularError('No valid artifact identity recorded for this step')
    if step['skill_id'] == 'inspect_csv':
        path, expected, area = outcome.get('source'), outcome.get('source_sha256'), 'input'
    else:
        path, expected, area = output.get('path'), output.get('sha256'), 'output'
    if not isinstance(path, str) or not path.lower().endswith(('.csv', '.tsv')) or not isinstance(expected, str) or len(expected) != 64:
        raise TabularError('No hash-bound CSV artifact recorded for this step')
    content = read_bytes(root, path, area)
    actual = hashlib.sha256(content).hexdigest()
    if actual != expected:
        raise TabularError('Artifact changed since execution. Saved snapshots remain available; this file is not the recorded result.')
    delimiter = (step.get('arguments') or {}).get('delimiter', ',') if step['skill_id'] == 'inspect_csv' else ','
    if delimiter not in {',', '\t'}:
        raise TabularError('Recorded CSV delimiter is unsupported')
    frame = read_frame(content, delimiter)
    return step, path, actual, frame


def preview_result(root, record, request):
    step, path, actual, frame = recorded_frame(root, record, request)
    analysis = analyze_frame(frame, request.analysis) if request.analysis else None
    columns = list(frame.columns)[:32]
    rows = []
    import pandas as pd
    cells_truncated = False
    for item in frame[columns].head(1000).to_dict(orient='records'):
        row = {key: None if pd.isna(value) else str(value)[:160] for key, value in item.items()}
        if len(json.dumps(rows+[row], ensure_ascii=False).encode()) > 128_000:
            break
        cells_truncated = cells_truncated or any(not pd.isna(v) and len(str(v)) > 160 for v in item.values())
        rows.append(row)
    return {'run_id': record['run_id'], 'step_id': step['step_id'], 'plan_sha256': record['plan_sha256'],
            'source': path, 'source_sha256': actual, 'verified_at_read': True,
            'row_count': len(frame), 'column_count': len(frame.columns), 'columns': columns,
            'preview': rows, 'preview_truncated': len(rows) < len(frame),
            'columns_truncated': len(columns) < len(frame.columns), 'cells_truncated': cells_truncated,
            'limits': {'rows': 1000, 'columns': 32, 'cell_characters': 160, 'preview_bytes': 128000},
            **({'chart_analysis': analysis} if analysis else {}),
            'execution_performed': False, 'approval_performed': False}


def analyze_frame(frame, spec):
    """Deterministic bounded aggregate of the entire hash-verified CSV frame."""
    import math
    import pandas as pd
    if spec.group_by not in frame.columns or (spec.aggregation != 'count' and spec.value not in frame.columns):
        raise TabularError('Choose existing grouping and numeric value columns')
    if frame[spec.group_by].nunique(dropna=False) > 100:
        raise TabularError('Chart summary exceeds 100 categories; filter or aggregate the workflow first')
    work = pd.DataFrame({'category': frame[spec.group_by]})
    if spec.aggregation != 'count':
        source = frame[spec.value]
        numeric = pd.to_numeric(source, errors='coerce')
        if ((source.notna() & numeric.isna()) | numeric.map(lambda v: pd.notna(v) and (not math.isfinite(v) or abs(v) > 1e15))).any():
            raise TabularError('Chart value contains non-numeric or unsupported numeric values')
        work['_value'] = numeric
    grouped = work.groupby('category', dropna=False, sort=True)
    if spec.aggregation == 'count':
        result = grouped.size()
    elif spec.aggregation == 'sum':
        result = grouped['_value'].sum(min_count=1)
    else:
        result = getattr(grouped['_value'], spec.aggregation)()
    rows = []
    for category, value in result.items():
        number = None if pd.isna(value) else float(value)
        if number is not None and (not math.isfinite(number) or abs(number) > 1e15):
            raise TabularError('Chart aggregate exceeds the supported numeric display range')
        rows.append({'category': None if pd.isna(category) else str(category), 'value': number})
    return {'columns': ['category', 'value'], 'preview': rows, 'row_count': len(rows),
            'source_row_count': len(frame), 'scope': 'complete_verified_artifact',
            'group_by': spec.group_by, 'value': spec.value, 'aggregation': spec.aggregation,
            'missing_values': 'Missing categories form a separate group; numeric nulls are excluded, all-null groups remain null.'}
