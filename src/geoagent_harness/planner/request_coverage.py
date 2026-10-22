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
        match = re.search(r'^\s*inspect\s+.{0,160}?\.(csv|tsv|geojson|gpkg|shp|tif|tiff)\b', clause)
        if match:
            skill = 'inspect_csv' if match[1] in {'csv','tsv'} else 'inspect_raster' if match[1] in {'tif','tiff'} else 'inspect_vector'
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
        r'\s*inspect\s+[^\s;]+\.(csv|tsv|geojson|gpkg|shp|tif|tiff)\.?\s*'
        r'(?:return\s+(?:row count|column names|columns|feature count|fields|crs|a preview|preview|metadata|width|height|dimensions|band count|bands|bounds|resolution|driver|geometry type|layer names|nodata)'
        r'(?:\s*(?:,|and)\s*(?:row count|column names|columns|feature count|fields|crs|a preview|preview|metadata|width|height|dimensions|band count|bands|bounds|resolution|driver|geometry type|layer names|nodata))*\.\s*)?'
        r'(?:no writes\.?\s*)?', message, re.I,
    )
    if not match:
        return None
    extension = match[1].casefold()
    return ('inspect_csv' if extension in {'csv', 'tsv'} else
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
