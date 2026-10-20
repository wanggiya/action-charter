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
