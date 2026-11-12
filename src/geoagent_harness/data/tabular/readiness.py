"""Pure source-bound readiness/report projection. No reads, model calls or writes."""
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid')


class AssessmentBudgetExceeded(ValueError):
    pass


class ReadinessField(Closed):
    name: str
    observed_type: str
    role: str
    missing: int = Field(ge=0)
    missing_percent: float | None
    distinct: int | None
    numeric_count: int | None
    invalid_numeric: int | None
    mean: float | None
    minimum: float | None
    maximum: float | None
    standard_deviation: float | None


class ReadinessCheck(Closed):
    name: str
    status: Literal['pass', 'attention', 'not_requested']
    finding: str


class MappingCoverage(Closed):
    field: str
    matched_rows: int
    unmatched_rows: int


class ReadinessAssessment(Closed):
    schema_version: Literal['readiness-assessment-v1'] = 'readiness-assessment-v1'
    source: str
    source_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_rows: int = Field(ge=0)
    matching_rows: int = Field(ge=0)
    selection: dict
    filters: list[dict]
    scope: Literal['complete_selected_file_matching_rows'] = 'complete_selected_file_matching_rows'
    population_scope: Literal['unverified'] = 'unverified'
    possible_sample: bool
    missing_policy: dict[str, list[str]]
    codebook: dict[str, str] | None
    mappings: list[MappingCoverage]
    distinct_counts: dict[str, int]
    fields: list[ReadinessField]
    checks: list[ReadinessCheck]
    groups_by: list[str]
    groups: list[dict]
    omissions: dict[str, int]
    limitations: list[str]
    report_markdown: str = ''
    execution_authority: Literal[False] = False
    data_written: Literal[False] = False


def _cell(value):
    text = 'Unavailable' if value is None else str(value)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')


def _table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(map(_cell, row)) + ' |' for row in [headers, ['---'] * len(headers), *rows]])


def render_report(a):
    """Measured findings only. Agent interpretations stay in their own evidence records."""
    parts = ['# Data readiness and findings', '## Source and analysis scope',
        _table(['Source', 'SHA-256', 'Source rows', 'Matching rows'], [[a.source, a.source_sha256, a.source_rows, a.matching_rows]]),
        'Complete selected-file scan; row counts and percentage denominators use matching records, not preview rows. Distinct entities are reported separately. Population/sample provenance is unverified; no extrapolation is made.',
        'Selection: ' + _cell(json.dumps(a.selection, sort_keys=True)),
        'Filters: ' + _cell(json.dumps(a.filters, sort_keys=True)),
        'Missing values: empty analytical cells plus explicitly declared tokens ' + _cell(json.dumps(a.missing_policy, sort_keys=True)) + '. No imputation.',
        '## Readiness checks', _table(['Check', 'Status', 'Recorded finding'], [[c.name, c.status.replace('_', ' ').capitalize(), c.finding] for c in a.checks]),
        '## Field coverage', _table(['Field', 'Observed type', 'Role', 'Missing', '% matching', 'Distinct'],
            [[f.name, f.observed_type, f.role, f.missing, None if f.missing_percent is None else round(f.missing_percent, 4), f.distinct] for f in a.fields])]
    numbers = [f for f in a.fields if f.numeric_count is not None]
    if numbers:
        parts += ['## Numerical findings', 'Valid-value summaries follow the recorded method. Unavailable values were not computed; invalid/missing values are excluded as specified in the original analysis.',
            _table(['Field', 'Valid', 'Invalid', 'Mean', 'Minimum', 'Maximum', 'Standard deviation'],
                [[f.name, f.numeric_count, f.invalid_numeric, f.mean, f.minimum, f.maximum, f.standard_deviation] for f in numbers])]
    if a.distinct_counts:
        parts += ['## Distinct entities', _table(['Field', 'Distinct non-missing values'], list(a.distinct_counts.items())),
            'A distinct identifier count is not the observation count. Repeated entities may invalidate independence assumptions; domain definitions are not inferred.']
    if a.codebook:
        parts += ['## Supplied definitions and coverage', _cell(a.codebook['path']) + ' · SHA-256 ' + a.codebook['sha256'],
            _table(['Field', 'Matched rows', 'Unmapped rows'], [[m.field, m.matched_rows, m.unmatched_rows] for m in a.mappings])]
    if a.groups:
        columns = list(a.groups[0])
        parts += ['## Grouped findings', 'Grouping: ' + _cell(', '.join(a.groups_by)) + '. percentage_total uses all matching records; percentage_within_primary uses the complete first-field group. Denominators include undisplayed groups; missing-token groups are retained.',
            _table(columns, [[g.get(c) for c in columns] for g in a.groups])]
    parts += ['## Interpretation and limitations',
        'This report contains computed evidence, not a clinical assessment or causal conclusion. Planner interpretation and Critic assessment are separate advisory records.',
        *['- ' + _cell(s) for s in a.limitations],
        '- Omitted report fields/groups: ' + _cell(json.dumps(a.omissions, sort_keys=True)) + '. Consult original saved evidence for complete available results.']
    return '\n\n'.join(parts) + '\n'


def build_assessment(result, *, max_bytes=48000):
    """Normalize existing table-analysis/dataset-profile evidence without recomputation."""
    dataset = result.get('schema_version') == 'dataset-profile-v1'
    analysis = result if dataset else result.get('table_analysis')
    if not analysis or not result.get('source_sha256'):
        raise ValueError('Readiness requires completed source-bound analytical evidence')
    query = analysis.get('query' if dataset else 'request', {})
    matched = analysis['matching_rows' if dataset else 'matched_row_count']
    total = analysis['source_rows' if dataset else 'source_row_count']
    if not 0 <= matched <= total:
        raise ValueError('Readiness counts exceed source coverage')
    fields = []
    source_schema = (result.get('table_source') or {}).get('schema', {})
    statistics = (analysis.get('statistics') or {})
    described = {d['column']: d for d in statistics.get('descriptive', [])}
    roles = {f['name']: 'candidate_' + f['role'] for f in (result.get('field_guidance') or {}).get('fields', [])}
    for p in analysis['profiles']:
        numeric = p.get('numeric') or described.get(p['name']) or {}
        description = described.get(p['name'], {})
        # A statistical complete-case set is contained in the valid single-field
        # set. Equal counts therefore permit its SD without mixing populations.
        sd = numeric.get('standard_deviation')
        if sd is None and numeric.get('count') == description.get('count'):
            sd = description.get('standard_deviation')
        types = source_schema.get('storage_types_overrides', {}).get(p['name'], source_schema.get('storage_types_default', []))
        fields.append(ReadinessField(name=p['name'], observed_type=p.get('observed_type', ' | '.join(types) or 'unavailable'),
            role=p.get('analytical_role', roles.get(p['name'], 'not_classified')), missing=p['missing_count'],
            missing_percent=100 * p['missing_count'] / matched if matched else None,
            distinct=analysis.get('distinct_counts', {}).get(p['name'], p.get('distinct_count')),
            numeric_count=numeric.get('count'), invalid_numeric=numeric.get('invalid_count', statistics.get('invalid_counts', {}).get(p['name'])),
            mean=numeric.get('mean'), minimum=numeric.get('minimum'), maximum=numeric.get('maximum'), standard_deviation=sd))
    checks = []
    def check(name, requested, ok, finding):
        checks.append(ReadinessCheck(name=name, status='not_requested' if not requested else 'pass' if ok else 'attention', finding=finding))
    quality = analysis.get('quality') or {}
    duplicates = quality.get('duplicate_rows')
    check('Whole-row duplicates', duplicates is not None, not duplicates or duplicates['excess_occurrences'] == 0,
          f"{duplicates['excess_occurrences']} excess rows" if duplicates is not None else 'Not computed by this inspection; absence of a check does not establish uniqueness.')
    key = quality.get('duplicate_key')
    check('Candidate observation key', key is not None, bool(key and key['candidate_key']),
          f"Fields {', '.join(key['columns'])}: {key['distinct_count']} distinct keys; {key['missing_key_rows']} missing-key rows; {key['excess_occurrences']} excess occurrences" if key is not None else 'Not requested; the record grain and key are not established.')
    book = analysis.get('codebook')
    coverage = [MappingCoverage(field=n, matched_rows=v['matched_rows'], unmatched_rows=v['unmatched_rows']) for n, v in (book or {}).get('coverage', {}).items()]
    check('Supplied codebook coverage', book is not None, bool(coverage) and all(m.unmatched_rows == 0 for m in coverage) and not book.get('unbound_sections', []) if book else False,
          f"{len(coverage)} bound fields; {sum(m.unmatched_rows for m in coverage)} unmapped field-values; {len(book.get('unbound_sections', []))} unbound sections" if book else 'No codebook supplied; category meaning is not verified.')
    groups = analysis.get('groups', [])
    grouped = bool(analysis.get('group_by'))
    from geoagent_harness.data.tabular.grouping import percentages
    group_percentages = percentages(groups, analysis['group_by'], matched) if grouped else []
    check('Group row reconciliation', grouped, sum(g['row_count'] for g in groups) == matched,
          f"{len(groups)} groups; {sum(g['row_count'] for g in groups)} grouped records / {matched} matching records" if grouped else 'No grouped analysis requested.')
    for name, ok in analysis.get('checks', {}).items():
        check(name, True, ok, 'Recorded deterministic check; not an analytical-validity guarantee.')
    limits = list(analysis.get('limitations', [])) + [
        'Selected-file completeness does not establish full-population coverage or sample representativeness.',
        'Observed types and candidate roles are not confirmed domain meanings or measurement units.',
        'Empty cells and declared tokens are missing; undeclared markers may still affect results.',
        'No automatic sampling, imputation, inference of clinical definitions or execution authorization.',
        'Statistics, design assumptions and exclusions remain in the original statistical report when present.']
    a = ReadinessAssessment(source=result['source'], source_sha256=result['source_sha256'], source_rows=total, matching_rows=matched,
        selection=(result.get('table_source') or {}).get('selection') or query.get('source_options') or {}, filters=query.get('filters', []),
        possible_sample=bool(re.search(r'(^|[_ .-])(sample|subset)([_ .-]|\d|$)', result['source'].rsplit('/', 1)[-1], re.I)),
        missing_policy=query.get('missing_values', {}), codebook={k:book[k] for k in ('path','sha256')} if book else None,
        mappings=coverage, distinct_counts=analysis.get('distinct_counts', {}), fields=fields, checks=checks,
        groups_by=analysis.get('group_by', []), groups=[{**g, **p} for g,p in zip(groups[:30], group_percentages[:30])],
        omissions={'fields':len(analysis.get('columns_omitted', [])), 'groups':max(0, len(groups)-30)}, limitations=limits)
    regression=statistics.get('regression') or {}
    coefficients=regression.get('coefficients') or []
    correlation_p=any(value is not None for item in statistics.get('correlations',[]) for i,row in enumerate(item.get('p_values',[])) for j,value in enumerate(row) if i!=j)
    p_available=correlation_p or any(c.get('p_value') is not None for c in coefficients)
    intervals=any(c.get('standard_error') is not None and c.get('confidence_lower') is not None and c.get('confidence_upper') is not None for c in coefficients)
    coverage='\n## Statistical coverage\n\n'+_table(['Metric family','Recorded status','Interpretation'],[
        ['Inferential P-values','Calculated' if p_available else 'Unavailable; inspect method diagnostics' if regression or statistics.get('correlations') else 'Not calculated','Requires a specified test/model and valid design assumptions; not a generic column score.'],
        ['Regression standard errors / confidence intervals','Calculated' if intervals else 'Unavailable; inspect method diagnostics' if regression else 'Not calculated','Estimate uncertainty, distinct from descriptive standard deviation.'],
        ['Regression residual error / R-squared','Calculated' if regression.get('residual_standard_error') is not None else 'Not calculated','In-sample model diagnostics, not held-out predictive performance.'],
        ['Predictive precision / recall / F1','Not calculated','Requires labelled predictions and leakage-safe evaluation; no classification evaluation operation is registered in this slice.']])+'\nProposed analysis goals are advice, not these calculated results. Unsupported methods and missing assumptions must remain explicit.\n'
    statistical_report = statistics.get('report_markdown', '')
    from geoagent_harness.data.tabular.basic_profile import recorded_report
    basic_report = recorded_report(result) if result.get('basic_profile') else None
    if basic_report:
        a.omissions['basic_quality_report'] = 0
    if statistical_report:
        a.omissions['statistical_report'] = 0
    while True:
        a.report_markdown = render_report(a)+coverage
        if statistical_report:
            a.report_markdown += '\n## Statistical method details\n\n' + statistical_report
        if basic_report:
            a.report_markdown += '\n## Complete source basic quality\n\n' + basic_report
        value = a.model_dump(mode='json')
        if len(json.dumps(value, allow_nan=False).encode()) <= max_bytes:
            return value
        if basic_report:
            basic_report = None
            a.omissions['basic_quality_report'] = 1
            a.limitations.append('Basic quality appendix exceeded the combined report budget; the recorded workflow Analytical report retains it separately.')
        elif statistical_report:
            statistical_report = ''
            a.omissions['statistical_report'] = 1
            a.limitations.append('Statistical method details exceeded the combined report budget; the complete original Statistics report is retained separately.')
        elif a.groups:
            a.groups.pop(); a.omissions['groups'] += 1
        elif a.fields:
            a.fields.pop(); a.omissions['fields'] += 1
        else:
            raise AssessmentBudgetExceeded('Readiness metadata exceeds its response budget')


def attach_assessment(result, *, result_budget=128000):
    """Add evidence when it fits; never remove existing numerical results to fit a report."""
    remaining = min(48000, result_budget - len(json.dumps(result, allow_nan=False).encode()) - 512)
    try:
        if remaining < 6000:
            raise AssessmentBudgetExceeded('Insufficient room for source/check coverage')
        result['readiness_assessment'] = build_assessment(result, max_bytes=remaining)
    except AssessmentBudgetExceeded:
        result['readiness_status'] = 'Report omitted within output budget; original analytical evidence is retained.'
    return result


def compact_assessment(value):
    """Bounded agent evidence; no raw rows, group labels or copied report prose."""
    a = ReadinessAssessment.model_validate(value)
    value = {k:v for k,v in a.model_dump(mode='json').items() if k in {
        'schema_version','source','source_sha256','source_rows','matching_rows','scope','population_scope',
        'possible_sample','filters','selection','missing_policy','codebook','checks','distinct_counts','omissions'}}
    ordered = sorted(a.fields, key=lambda f: not (f.missing or f.numeric_count is not None))
    value['field_findings'] = [f.model_dump(mode='json') for f in ordered[:8]]
    value['field_findings_omitted'] = len(a.fields) - len(value['field_findings']) + a.omissions['fields']
    return value
