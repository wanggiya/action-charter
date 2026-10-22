"""Hash-verified bounded result queries, shared by UI, Planner views and CLI."""
from __future__ import annotations
import json
import math
import pandas as pd

from geoagent_harness.tabular.service import TabularError
from .exploration_contracts import ExplorationQuery, ResultViewSpec
from .result_preview import recorded_frame, analyze_frame


def _number(series):
    values = pd.to_numeric(series, errors='coerce')
    if ((series.notna() & values.isna()) | values.map(lambda v: pd.notna(v) and (not math.isfinite(v) or abs(v) > 1e15))).any():
        raise TabularError('Numeric exploration requires finite numeric values within the display range; identifiers are not converted automatically')
    return values


def column_profiles(frame):
    profiles = []
    for column in frame.columns:
        series = frame[column]
        kind = 'empty' if series.notna().sum() == 0 else 'text'
        try:
            numeric = _number(series)
            if kind != 'empty':
                kind = 'numeric-compatible text'
        except TabularError:
            numeric = None
        profiles.append({'name': column, 'storage_type': 'string', 'observed_type': kind,
            'missing_count': int(series.isna().sum()), 'distinct_count': int(series.nunique(dropna=True)),
            'minimum': float(numeric.min()) if numeric is not None and numeric.notna().any() else None,
            'maximum': float(numeric.max()) if numeric is not None and numeric.notna().any() else None})
    return profiles


def apply_query(frame, query):
    work = frame
    for predicate in query.filters:
        if predicate.column not in frame.columns:
            raise TabularError('Filter column is not present in this verified result')
        series = work[predicate.column]
        if predicate.operator in {'is_missing', 'not_missing'}:
            mask = series.isna() if predicate.operator == 'is_missing' else series.notna()
        else:
            if predicate.value_type == 'number':
                series = _number(series)
                try:
                    value = float(predicate.value)
                except (ValueError, TypeError):
                    raise TabularError('Numeric filter requires a numeric value') from None
                if not math.isfinite(value) or abs(value) > 1e15:
                    raise TabularError('Numeric filter value exceeds the display range')
            else:
                value = str(predicate.value)
            if predicate.operator == 'contains':
                mask = series.str.contains(value, regex=False, na=False)
            else:
                mask = {'eq': series.eq, 'ne': series.ne, 'gt': series.gt,
                        'ge': series.ge, 'lt': series.lt, 'le': series.le}[predicate.operator](value).fillna(False)
        if predicate.operator not in {'is_missing', 'not_missing'}:
            mask = mask & series.notna()
        work = work.loc[mask]
    if query.sort:
        sort = query.sort
        if sort.column not in frame.columns:
            raise TabularError('Sort column is not present in this verified result')
        values = _number(work[sort.column]) if sort.value_type == 'number' else work[sort.column]
        work = work.loc[values.sort_values(ascending=not sort.descending, kind='stable', na_position='last').index]
    return work


def explore_result(root, record, request):
    if request.conversation_id is None or request.conversation_id != record.get('conversation_id'):
        raise TabularError('Exploration requires the exact recorded conversation scope')
    step, path, digest, frame = recorded_frame(root, record, request)
    query = request.query or ExplorationQuery()
    columns = query.columns or list(frame.columns)[:32]
    if len(columns) != len(set(columns)) or any(column not in frame.columns for column in columns):
        raise TabularError('Displayed columns must be unique existing columns')
    work = apply_query(frame, query)
    rows, identities, used, cells_truncated = [], [], 2, False
    for identity, item in work[columns].iloc[query.offset:query.offset + query.limit].iterrows():
        row = {key: None if pd.isna(value) else str(value)[:160] for key, value in item.items()}
        size = len(json.dumps(row, ensure_ascii=False).encode()) + 2
        if used + size > 128000:
            break
        used += size
        cells_truncated |= any(pd.notna(value) and len(str(value)) > 160 for value in item.values)
        rows.append(row)
        identities.append(int(identity))
    next_offset = query.offset + len(rows)
    analysis = analyze_frame(work, request.analysis) if request.analysis else None
    if analysis:
        analysis.update(scope='complete_filtered_artifact', source_total_row_count=len(frame),
                        excluded_rows=len(frame)-len(work))
    return {'schema_version': '1.0', 'run_id': record['run_id'], 'step_id': step['step_id'],
        'conversation_id': record['conversation_id'], 'plan_sha256': record['plan_sha256'],
        'source': path, 'source_sha256': digest, 'verified_at_read': True,
        'row_count': len(frame), 'matched_row_count': len(work), 'column_count': len(frame.columns),
        'columns': columns, 'preview': rows, 'row_ids': identities, 'offset': query.offset,
        'next_offset': next_offset if next_offset < len(work) else None,
        'query': query.model_dump(mode='json'), 'column_profiles': column_profiles(frame),
        'profile_scope': 'complete_verified_artifact', 'missing_values': 'Only empty fields are missing; comparisons exclude missing cells. Text sorting is lexical; numeric sorting is explicit. Nulls sort last.',
        'preview_truncated': len(rows) < len(work), 'columns_truncated': len(columns) < len(frame.columns),
        'cells_truncated': cells_truncated, 'scope': 'complete_filtered_artifact',
        'limits': {'source_bytes': 8*1024*1024, 'source_rows': 10000, 'source_columns':100,
                   'page_rows': query.limit, 'columns':32, 'cell_characters':160, 'preview_bytes':128000},
        **({'chart_analysis': analysis} if analysis else {}),
        'execution_performed': False, 'approval_performed': False}



def recorded_facts(outcome, validation=None):
    """Fixed metadata projection, not inferred units or dataset content retrieval."""
    keys = ('row_count','column_count','width','height','band_count','crs','bounds','nodata_values')
    facts = {key: outcome[key] for key in keys if key in outcome and outcome[key] is not None}
    layers = outcome.get('layers')
    if isinstance(layers, list):
        facts['layer_count'] = len(layers)
        facts['layer_features'] = [{'layer': str(layer.get('name',''))[:120], 'feature_count': layer.get('feature_count'), 'crs': layer.get('crs')} for layer in layers[:8] if isinstance(layer,dict)]
    if isinstance(validation,dict):
        facts['validation']={key:validation[key] for key in ('status','validated','validation_performed') if key in validation}
        if isinstance(validation.get('checks'),list):
            facts['validation']['checks']=[{key:item[key] for key in ('name','passed','status') if key in item} for item in validation['checks'][:8] if isinstance(item,dict)]
    preview = outcome.get('spatial_preview')
    if isinstance(preview,dict):
        facts['geometry_sample'] = {'shown':len(preview.get('features',preview.get('points',[]))), 'examined':preview.get('examined_features'), 'total':preview.get('total_features'), 'skipped':preview.get('skipped_features')}
    # Bound values without inventing a numeric replacement for non-finite metadata.
    bounded={}
    for key,value in facts.items():
        try:
            encoded=json.dumps(value,allow_nan=False)
            if len(encoded)<=800:bounded[key]=json.loads(encoded)
        except (ValueError,TypeError):
            continue  # Non-finite/unsupported facts are unavailable, never invented.
    return bounded




def recorded_explanation_spec(message, context):
    """Closed factual questions need neither model inference nor a source read."""
    import re
    match=re.fullmatch(r'\s*(?:explain|summari[sz]e|describe) (?:the )?(?:current |recorded )?(?:result|outcome|inspection)(?: (.*?))?\.?\s*',message,re.I)
    if not match or not context:return None
    candidate=context['results'][0]
    facts=candidate.get('recorded_facts',{})
    aliases={'row count':['row_count'],'column count':['column_count'],'dimensions':['width','height'],
             'width':['width'],'height':['height'],'band count':['band_count'],'crs':['crs'],
             'bounds':['bounds'],'nodata encoding':['nodata_values'],'layer count':['layer_count'],
             'feature count':['layer_features'],'validation checks':['validation']}
    requested=(match[1] or '').strip().rstrip('.').casefold()
    if requested:
        keys=[]
        for token in re.split(r'\s*(?:,|\band\b)\s*',requested):
            if token not in aliases:return None
            keys.extend(aliases[token])
    else:keys=list(facts)[:8]
    keys=list(dict.fromkeys(keys))
    if not keys or len(keys)>8 or any(key not in facts for key in keys):return None
    return {'run_id':context['run_id'],'plan_sha256':context['plan_sha256'],
            'step_id':candidate['step_id'],'view':'Map' if candidate.get('spatial_kind') else 'Table',
            'explanation_fields':keys}


def prepared_view_text(spec):
    if spec.spatial:
        if spec.spatial.mode=='vector':
            details='layer '+json.dumps(spec.spatial.layer) if spec.spatial.layer else 'the first source layer'
        else:
            details='bands '+', '.join(map(str,spec.spatial.bands))+' · '+spec.spatial.render+' · '+spec.spatial.stretch
        return f'Prepared Map display: {details}. The viewer verifies the recorded source before loading; this is not workflow execution or write approval.'
    if spec.chart:
        details=f'{spec.chart.aggregation}({spec.chart.value or "rows"}) by {spec.chart.group_by}'
        return f'Prepared {spec.chart_kind} chart: {details}. The backend calculates values when the verified view loads; no totals are inferred here.'
    return f'Prepared recorded {spec.view} view. This preserves the workflow and grants no execution or write authority.'


def requests_result_explanation(message):
    import re
    return bool(re.match(r'^\s*(?:explain|summari[sz]e|describe)\b',message,re.I)
                and re.search(r'\b(?:result|outcome|inspection|counts?|crs|dimensions|bands|bounds|nodata)\b',message,re.I)
                and not re.search(r'\b(?:write|export|convert|calculate|install|delete|join|merge)\b',message,re.I))


def explanation_text(spec, context):
    candidate = next(item for item in context['results'] if item['step_id']==spec.step_id)
    facts = candidate.get('recorded_facts',{})
    labels={'row_count':'Row count','column_count':'Column count','width':'Source width (pixels)','height':'Source height (pixels)',
            'band_count':'Band count','crs':'Declared CRS','bounds':'Source bounds','nodata_values':'NoData encoding by band',
            'layer_count':'Layer count','layer_features':'Recorded layer counts and CRS','geometry_sample':'Saved geometry sample','validation':'Recorded deterministic checks'}
    lines = [f'Recorded inspection evidence · {spec.step_id}.']
    for key in spec.explanation_fields:
        value=facts[key]
        lines.append(labels[key]+': '+json.dumps(value,ensure_ascii=False,allow_nan=False)+'.')
    lines.append('Scope: saved inspection evidence, not a fresh source check. Sample counts are not full-data statistics. Domain meanings, units and suitability are not established. Nothing approved or executed.')
    return '\n'.join(lines)


def view_context(root, conversation_id, base):
    """Recorded metadata only: no file read and no row values in model context."""
    from .run_assessment import latest_conversation_run
    if base is None:
        return None
    run = latest_conversation_run(root, conversation_id, base)
    if not run:
        return None
    candidates = []
    for step in reversed(run['steps']):
        if step['status'] not in {'completed', 'validated_success', 'reused_completed'}:
            continue
        outcome = step.get('outcome') or {}
        if not isinstance(outcome, dict):
            continue
        extra = {'recorded_facts':recorded_facts(outcome,step.get('validation_outcome'))}
        if step.get('skill_id')=='inspect_vector':
            extra.update(spatial_kind='vector',layers=[str(item.get('name',''))[:120] for item in outcome.get('layers',[])[:8] if isinstance(item,dict)])
        elif step.get('skill_id')=='inspect_raster':
            extra.update(spatial_kind='raster',band_count=outcome.get('band_count'))
        columns = outcome.get('columns')
        spatial = outcome.get('spatial_preview')
        if isinstance(columns, list) and isinstance(outcome.get('preview'), list):
            candidates.append({'step_id': step['step_id'], 'views': ['Table', 'Chart'],
                               'columns': columns[:32], 'row_count': outcome.get('row_count'),**extra})
        elif ((isinstance(spatial, dict) and (spatial.get('status') == 'available' or step.get('skill_id') == 'inspect_vector'))
              or (step.get('skill_id') == 'inspect_vector' and isinstance(outcome.get('layers'),list) and outcome['layers'])
              or (step.get('skill_id') == 'inspect_raster' and outcome.get('width') and outcome.get('height'))):
            candidates.append({'step_id': step['step_id'], 'views':['Map'], 'crs': spatial.get('crs') if isinstance(spatial, dict) else outcome.get('crs'),**extra})
        if len(candidates) == 3:
            break
    return {'run_id': run['run_id'], 'plan_sha256': run['plan_sha256'], 'results': candidates,
            'rule': 'Result views preserve the workflow. Choose only the exact supplied run/plan/step and known fields. Query reads a hash-verified artifact; it never executes workflow operations or grants write authority. Map opens recorded spatial evidence; additional verified source reads require an explicit display action.'} if candidates else None


def validate_view(spec: ResultViewSpec, context):
    if not context or spec.run_id != context['run_id'] or spec.plan_sha256 != context['plan_sha256']:
        raise ValueError('Result view must reference the supplied current-chat recorded run and plan')
    candidate = next((item for item in context['results'] if item['step_id'] == spec.step_id), None)
    if candidate is None or spec.view not in candidate['views']:
        raise ValueError('Choose a supported recorded result view from result_view_context')
    if spec.spatial:
        expected=candidate.get('spatial_kind')
        if spec.spatial.mode!=expected:
            raise ValueError('Choose spatial settings matching the supplied inspector')
        if expected=='vector' and spec.spatial.layer and spec.spatial.layer not in candidate.get('layers',[]):
            raise ValueError('Choose a supplied source layer, never invent layer names')
        if expected=='raster' and any(b>(candidate.get('band_count') or 0) for b in spec.spatial.bands):
            raise ValueError('Choose existing recorded raster bands')
    if len(set(spec.explanation_fields))!=len(spec.explanation_fields) or any(key not in candidate.get('recorded_facts',{}) for key in spec.explanation_fields):
        raise ValueError('Explain only supplied recorded_facts keys; unavailable statistics/domain meanings are not established')
    columns = candidate.get('columns', [])
    used = [item.column for item in spec.query.filters] + (spec.query.columns or [])
    if spec.query.sort:
        used.append(spec.query.sort.column)
    if spec.chart:
        used += [spec.chart.group_by] + ([spec.chart.value] if spec.chart.aggregation != 'count' else [])
    if spec.chart and spec.query.columns and any(column not in spec.query.columns for column in [spec.chart.group_by]+([spec.chart.value] if spec.chart.aggregation!='count' else [])):
        raise ValueError('Chart fields must be included in the displayed columns')
    if any(column not in columns for column in used):
        raise ValueError('Result view fields must exist in result_view_context; ask for a missing semantic choice instead of inventing columns')


def requests_result_view(message):
    """Focus explicit display requests only; processing requests keep general planning."""
    import re
    text = message.casefold().strip()
    return bool(re.match(r'^(?:show|plot|display|visuali[sz]e)\b', text)
        and re.search(r'\b(?:chart|plot|map|table|layer|band|raster|image)\b', text)
        and not re.search(r'\b(?:how|why|explain|workflow|plan|recipe|export|write|save|load|convert|calculate|add|remove|delete|join|merge)\b', text))


def bind_view_schema(schema, context):
    """Bind addresses and field enums without generating analytical decisions."""
    from copy import deepcopy
    result = deepcopy(schema)
    definitions = result['$defs']
    properties = definitions['ResultViewSpec']['properties']
    for key in ('run_id', 'plan_sha256'):
        properties[key] = {'type':'string','const':context[key]}
    properties['step_id'] = {'type':'string','enum':[item['step_id'] for item in context['results']]}
    if not any(item.get('spatial_kind') for item in context['results']):
        properties.pop('spatial',None)
        definitions.pop('SpatialViewOptions',None)
    elif 'SpatialViewOptions' in definitions:
        spatial=definitions['SpatialViewOptions']['properties']
        spatial['mode']={'type':'string','enum':list(dict.fromkeys(item['spatial_kind'] for item in context['results'] if item.get('spatial_kind')))}
        kinds={item.get('spatial_kind') for item in context['results'] if item.get('spatial_kind')}
        if kinds=={'raster'}:
            for key in ('layer','row','column'):spatial.pop(key,None)
            definitions['SpatialViewOptions']['required']=['mode','bands','render']
            spatial['bands']['description']='One-based integer band indices; never put a band name in layer.'
        elif kinds=={'vector'}:
            for key in ('bands','render','stretch','row','column'):spatial.pop(key,None)
        layer_names=list(dict.fromkeys(name for item in context['results'] for name in item.get('layers',[])))
        if layer_names:spatial['layer']={'anyOf':[{'type':'string','enum':layer_names},{'type':'null'}]}
    keys=list(dict.fromkeys(key for item in context['results'] for key in item.get('recorded_facts',{})))
    if keys:
        properties['explanation_fields']={'type':'array','items':{'type':'string','enum':keys},'maxItems':8}
    columns = list(dict.fromkeys(column for item in context['results'] for column in item.get('columns', [])))
    if columns:
        for name, key in (('ResultFilter','column'),('ResultSort','column'),('ChartAnalysis','group_by')):
            definitions[name]['properties'][key] = {'type':'string','enum':columns}
        definitions['ChartAnalysis']['properties']['value'] = {'anyOf':[{'type':'string','enum':columns},{'type':'null'}]}
    return result
