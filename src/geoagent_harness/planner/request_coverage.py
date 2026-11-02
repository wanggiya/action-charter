"""Narrow operation-coverage checks, never natural-language execution authority.

This catches explicit calculated-column requests reduced to metadata inspection.
It is not a general proof that a proposed workflow satisfies arbitrary prose.
"""
import re


class RequestedOperationOmission(ValueError):
    """A well-typed proposal omitted an explicitly requested supported operation."""


def simple_calculation_sequence(message: str) -> bool:
    """Only the explicit single-column slice gets a fixed decoder skeleton."""
    text = message.casefold()
    return (
        len(re.findall(r'\b(?:add|create|compute|calculate|derive)\b', text)) == 1
        and bool(re.search(r'\b(?:numeric|computed|calculated|derived)\s+column\b|\bcalculate\s+[a-z_]\w*\s*=\s*[^;\n]+[+*/-]|\bcalculation\s+(?:creating|producing)\s+[a-z_]\w*\s*=\s*[^;\n.]+[+*/-]', text))
        and not re.search(r'\b(?:numeric|computed|calculated|derived)\s+columns\b', text)
        and not re.search(r"\b(?:do not|don't|never|skip|without)\s+inspect\b", text)
    )


def requests_calculated_columns(message: str) -> bool:
    for clause in re.split(r'[.!?](?:\s+|$)|[;\n]', message.casefold()):
        # Removal/negative requests must not require re-adding the operation.
        if re.search(
            r"\b(?:remove|delete|omit|skip|without|do not|don't|never)\s+"
            r"(?:(?:the|any|a|new|all)\s+){0,3}"
            r"(?:calculat\w*|derived\b|computed\b|numeric\b|multiply\b|divide\b|"
            r"(?:add|create|compute|derive)\b)", clause,
        ):
            continue
        if re.search(
            r'\bcalculate_csv_columns\b|\bcalculate\s+[a-z_]\w*\s*=\s*[^;\n]+[+*/-]|'
            r'\b(?:add|create)\b.{0,40}\bcalculation\s+(?:creating|producing)\s+[a-z_]\w*\s*=\s*[^;\n.]+[+*/-]|'
            r'\b(?:add|create|compute|calculate|derive)\b.{0,120}?'
            r'\b(?:numeric|computed|calculated|derived)\s+columns?\b|'
            r'\b(?:multiply|multiplied|divide|divided)\b.{0,80}?\bby\s+-?\d',
            clause,
        ):
            return True
    return False


def validate_calculation_coverage(plan, message: str) -> None:
    """Reject omissions before storage; do not invent formulas or modify plans."""
    if plan is None:
        return
    # A narrow positive command check, not arbitrary prose interpretation. It
    # never inserts a step or treats an inspection request as write authority.
    for clause in re.split(r'[.!?](?:\s+|$)|[;\n]', message.casefold()):
        match = re.search(r'^\s*inspect\s+.{0,160}?\.(csv|tsv|xlsx|jsonl|ndjson|json|geojson|gpkg|shp|tif|tiff)\b', clause)
        if match:
            skill = 'inspect_csv' if match[1] in {'csv','tsv','xlsx','json','jsonl','ndjson'} else 'inspect_raster' if match[1] in {'tif','tiff'} else 'inspect_vector'
            if not any(step.skill == skill for step in plan.steps):
                raise RequestedOperationOmission('The explicit inspection request is missing from plan.steps. Include '+skill+' for the supplied source before the requested transforms, with the declared completion dependencies. Do not claim inspection was performed. If unavailable, explain that limitation without a partial workflow.')
    if any(step.skill == 'calculate_csv_columns' for step in plan.steps):
        return
    if requests_calculated_columns(message):
        raise RequestedOperationOmission(
            'The requested calculated-column operation is missing from plan.steps. '
            'inspect_csv returns metadata and previews only; a summary or assistant '
            'message cannot calculate or save derived columns. Include '
            'calculate_csv_columns with the requested source, output column, typed '
            'formula and missing-value policy. If this capability is unavailable or '
            'a concrete semantic input is missing, return plan=null and explain '
            'that limitation or ask for that input. Do not claim the complete '
            'calculation workflow is ready from inspection alone.'
        )


def requested_table_operations(message: str, existing=()) -> set[str]:
    """Recognize narrow explicit CSV commands; never infer execution authority."""
    text=message.casefold()
    requested=set()
    if not re.search(r'\.(?:csv|tsv)\b|\bcsv\b|\btabular\b|\bpandas\b|\bselect_csv_columns\b|\bfilter_csv_rows\b',text) and not any('csv' in skill for skill in existing):
        return requested
    for clause in re.split(r'[.!?](?:\s+|$)|[;\n]',text):
        if not re.search(r"\b(?:remove|delete|omit|skip|without|no|do not|don't|never)\s+(?:(?:the|any|all|use)\s+){0,2}(?:select\w*|column selection)\b",clause):
            if re.search(r'\bselect_csv_columns\b|\bselect\s+(?:only\s+)?(?:columns?\b|[a-z_]\w*\s*(?:,|\band\b))',clause):
                requested.add('select_csv_columns')
        if not re.search(r"\b(?:remove|delete|omit|skip|without|no|do not|don't|never)\s+(?:(?:the|any|all|use)\s+){0,2}(?:filter\w*|keep)\b",clause):
            if re.search(r'\bfilter_csv_rows\b|\bfilter\s+(?:(?:the|csv|table|data)\s+)?rows\b|\bkeep\s+(?:only\s+)?rows\s+(?:where|with)\b',clause):
                requested.add('filter_csv_rows')
    return requested


def validate_table_coverage(plan, message: str, existing=()) -> None:
    if plan is None:return
    missing=requested_table_operations(message,existing)-{step.skill for step in plan.steps}
    if missing:
        raise RequestedOperationOmission('The explicitly requested table operation is missing: '+', '.join(sorted(missing))+'. Repeated inspect_csv steps only return metadata; they cannot select columns or filter rows. Return the complete requested workflow with typed arguments, or ask only for genuinely missing semantic inputs with plan=null. Nothing has executed.')


def inspection_only_skill(message: str) -> str | None:
    """Recognize a complete, narrow metadata-only request, not arbitrary prose.

    Broader/follow-up requests retain the general planner path. This is scope
    validation, never authorization or an instruction to execute anything.
    """
    match = re.fullmatch(
        r'\s*inspect\s+[^\s;]+\.(csv|tsv|xlsx|jsonl|ndjson|json|geojson|gpkg|shp|tif|tiff)\.?\s*'
        r'(?:return\s+(?:row count|column names|columns|feature count|fields|crs|a preview|preview|metadata|width|height|dimensions|band count|bands|bounds|resolution|driver|geometry type|layer names|nodata)'
        r'(?:\s*(?:,|and)\s*(?:row count|column names|columns|feature count|fields|crs|a preview|preview|metadata|width|height|dimensions|band count|bands|bounds|resolution|driver|geometry type|layer names|nodata))*\.\s*)?'
        r'(?:no writes\.?\s*)?', message, re.I,
    )
    if not match:
        return None
    extension = match[1].casefold()
    return ('inspect_csv' if extension in {'csv', 'tsv', 'xlsx', 'json', 'jsonl', 'ndjson'} else
            'inspect_raster' if extension in {'tif', 'tiff'} else 'inspect_vector')


def validate_inspection_scope(plan, message: str) -> None:
    skill = inspection_only_skill(message)
    if skill and plan is not None and (
        len(plan.steps) != 1 or plan.steps[0].skill != skill
    ):
        raise RequestedOperationOmission(
            'This request is only metadata inspection of one supplied file. '
            f'Return exactly one {skill} step. Do not add PostGIS validation, '
            'reports, exports, transforms or other operations. Correct the proposal '
            'now; no permission to repair is needed and nothing has executed.'
        )


def requests_statistics(message):
    return bool(re.search(r'\b(?:linear regression|pearson|spearman|covariance matri(?:x|ces)|correlat\w*|percentiles?|variance|standard.deviation|descriptive statistics|statistical summary|statistical report|p.values?|r.squared|coefficients?)\b',message,re.I))


def statistical_request_requirements(message):
    """Named requested methods only; never infer variables or generate a plan."""
    clauses=[c for c in re.split(r'[;\n]|[.!?](?:\s+|$)',message.casefold()) if not re.search(r"\b(?:no|without|skip|do not|don't)\s+(?:fit\s+|compute\s+|calculate\s+)?(?:linear regression|correlation|pearson|spearman|statistics)",c)]
    text=' '.join(clauses)
    required=set()
    if 'linear regression' in text:required.add('linear_regression')
    for name in ('pearson','spearman'):
        if name in text:required.add(name)
    if re.search(r'\bcovariance matri(?:x|ces)\b',text):required.add('covariance')
    if re.search(r'\b(?:percentiles?|variance|standard.deviation|descriptive statistics|statistical summary|statistical report)\b',text):required.add('describe')
    correlation=bool(re.search(r'correlation',text))
    inference=bool(re.search(r'\b(?:p.values?|r.squared|coefficients?)\b',text))
    return required,correlation,inference


def validate_statistics_coverage(plan,message):
    if plan is None:return
    required,correlation,inference=statistical_request_requirements(message)
    if not required and not correlation and not inference:return
    supplied=set()
    for step in plan.steps:
        statistics=(step.arguments.get('analysis') or {}).get('statistics') if step.skill=='inspect_csv' else None
        if isinstance(statistics,dict):supplied.update(statistics.get('methods',['describe']))
    if correlation and not supplied.intersection({'pearson','spearman'}):required.add('pearson')
    if inference and not supplied.intersection({'pearson','spearman','linear_regression'}):
        raise RequestedOperationOmission('Requested coefficients/P-values require an explicit supported correlation or regression specification, not a text promise. Ask only for genuinely missing variables/design.')
    if required-supplied:raise RequestedOperationOmission('Requested statistical methods are missing: '+', '.join(sorted(required-supplied))+'. Include inspect_csv.analysis.statistics with actual typed arguments; a summary promising statistics is insufficient.')
    selected=requested_statistical_arguments(message)
    if selected and not any(all(((s.arguments.get('analysis') or {}).get('statistics') or {}).get(k,[] if k=='by' else None)==v for k,v in selected.items()) for s in plan.steps if s.skill=='inspect_csv'):
        raise RequestedOperationOmission('The explicit statistical fields/options were omitted or changed. Use exactly the supplied '+', '.join(selected)+'; do not add historical measurements or grouping. Correct the typed arguments, not just the summary.')


def requested_statistical_arguments(message):
    """Closed typed annotations or a complete simple descriptive command only."""
    import json
    match=re.search(r'"statistics"\s*:\s*(\{)',message)
    if match:
        from geoagent_harness.tabular.statistics import StatisticsSpec
        try:value,_=json.JSONDecoder().raw_decode(message[match.start(1):])
        except ValueError:return {}
        spec=StatisticsSpec.model_validate(value).model_dump(mode='json',exclude_unset=True)
        return {k:v for k,v in spec.items() if k in {'columns','by','methods','missing_policy','ddof','percentiles','question'}}
    match=re.search(r'\b(?:compute|calculate) descriptive statistics for ([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)(?: grouped by ([a-zA-Z_]\w*))?\s+(?:in|from)\s+[^\s]+\.(?:csv|tsv|xlsx|json|jsonl|ndjson)\b',message,re.I)
    if not match:return {}
    return {'columns':[c.strip() for c in match[1].split(',')],'by':[match[2]] if match[2] else []}


def requested_source_options(message):
    """Explicit selectors only, never infer a worksheet or read file contents."""
    import json
    from geoagent_harness.tabular.analysis_contracts import TableSourceOptions
    match=re.search(r'"source_options"\s*:\s*(\{)',message)
    if match:
        try:value,_=json.JSONDecoder().raw_decode(message[match.start(1):])
        except ValueError:return {}
        return TableSourceOptions.model_validate(value).model_dump(mode='json',exclude_unset=True)
    result={}
    for key in ('sheet','records_key','cell_range','header_row'):
        match=re.search(r'\b(?:analysis\.)?source_options\.'+key+r'\s*(?:=|:|\bto\b)\s*(?:"([^"]+)"|\'([^\']+)\'|([\w:-]+))',message,re.I)
        if match and not re.search(r'\b(?:no|not|omit|without|do not|don\'t)(?:\s+\w+){0,2}\s*$',message[:match.start()],re.I):
            result[key]=next(v for v in match.groups() if v is not None)
    if not result.get('sheet'):
        match=re.search(r'\bworksheet\s+(?:"([^"]+)"|\'([^\']+)\'|([\w-]+))',message,re.I)
        if match and not re.search(r'\b(?:no|not|omit|without)\s*$',message[:match.start()],re.I):
            value=next(v for v in match.groups() if v is not None)
            if value.lower() not in {'options','selection','name','names','source','format'}:result['sheet']=value
    return TableSourceOptions.model_validate(result).model_dump(mode='json',exclude_unset=True) if result else {}


def validate_source_option_coverage(plan,message):
    if plan is None:return
    requested=requested_source_options(message)
    if not requested:return
    steps=[s for s in plan.steps if s.skill=='inspect_csv']
    if steps and not any(all(((s.arguments.get('analysis') or {}).get('source_options') or {}).get(k)==v for k,v in requested.items()) for s in steps):
        raise RequestedOperationOmission('The explicit table source selection is missing or changed. Include analysis.source_options with the requested '+', '.join(requested)+'. Do not claim a sheet/range was selected only in message text. Return a corrected proposal; never execute.')


def requests_evidence_report(message):
    """Distinguish durable workflow-evidence files from analytical result reports."""
    return bool(re.search(r'\bgenerate_report\b|\b(?:save|write|persist|create|generate|export)\b.{0,80}\b(?:workflow evidence|evidence report|workflow report file|report file)\b',message,re.I))
