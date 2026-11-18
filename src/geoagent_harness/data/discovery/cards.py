"""Pure, bounded projections of trusted reader evidence; no source reads/cache."""
import json
import math
import re
from copy import deepcopy
from geoagent_harness.contracts.data_cards import DataCard, CardField


def _count(value):
    return value if type(value) is int and value >= 0 else None


def _text(value, maximum=200):
    return value if isinstance(value, str) and 0 < len(value) <= maximum and not any(ord(c) < 32 for c in value) else None


def from_evidence(value):
    """Unqualified legacy JSON must not make the original evidence unreadable."""
    try:
        return _from_evidence(value)
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return None


def _from_evidence(value):
    """Ignore supplied cards and raw examples. Unknown/mismatched facts stay absent.

    The caller must supply trusted reader output, never a model-authored dictionary.
    A recorded full digest identifies that read; this function cannot certify that
    the file is still unchanged. No automatic retained-card reuse is implemented.
    """
    if not isinstance(value, dict):
        return None
    probe = isinstance(value.get('metadata'), dict) and 'path' in value
    evidence = value['metadata'] if probe else value
    path = value.get('path') if probe else evidence.get('source')
    if not isinstance(path, str):
        return None
    from geoagent_harness.contracts.inspection_formats import source_inspector
    skill = source_inspector(path)
    if skill is None:
        return None
    kind = {'inspect_csv': 'table', 'inspect_vector': 'vector', 'inspect_raster': 'raster'}[skill]
    digest = value.get('source_sha256')
    digest = digest if isinstance(digest, str) and re.fullmatch('[a-f0-9]{64}', digest) else None
    discovery = evidence.get('discovery') or {}
    descriptor = evidence.get('table_source') or {}
    if descriptor and (descriptor.get('path') != path or descriptor.get('sha256') != digest):
        return None
    dataset = evidence.get('schema_version') == 'dataset-profile-v1'
    if not dataset and evidence.get('operation') != skill:
        return None
    source_rows = _count(evidence.get('source_rows', evidence.get('row_count')))
    profile_rows = _count(evidence.get('matching_rows', evidence.get('row_count')))
    scope = 'sample' if probe else 'driver_metadata' if kind != 'table' else descriptor.get('scope', discovery.get('statistics_scope', 'not_recorded'))
    if dataset:
        scope = 'filtered_rows' if (evidence.get('query') or {}).get('filters') or profile_rows != source_rows else 'complete_parsed_file'
    if scope not in {'complete_parsed_file', 'complete_selected_table', 'filtered_rows', 'sample', 'driver_metadata'}:
        scope = 'not_recorded'
    names = evidence.get('columns') or []
    names = names if isinstance(names, list) else []
    field_count = _count(evidence.get('column_count'))
    if kind == 'table' and field_count is None and isinstance(evidence.get('columns'), list):
        field_count = len(names)
    card = dict(source=path, source_sha256=digest,
        identity_basis=('package_manifest_sha256' if evidence.get('source_manifest') else 'file_sha256') if digest else 'pending' if probe or discovery.get('verification') == 'pending' else 'not_recorded',
        kind=kind, scope=scope, file_bytes=_count(value.get('bytes', discovery.get('file_bytes'))),
        source_rows=source_rows, profile_rows=profile_rows, field_count=field_count,
        fields=[], fields_omitted=field_count or 0)
    # A worksheet/range/filter is part of the population identity, not a label.
    selection = descriptor.get('source_options') or evidence.get('source_options') or evidence.get('query') or {}
    if isinstance(selection, dict):
        allowed = ('sheet', 'header_row', 'cell_range', 'records_key', 'filters', 'missing_values', 'role_overrides')
        card['selection'] = {k: deepcopy(selection[k]) for k in allowed if k in selection and selection[k] not in (None, [], {})}
        resolved = descriptor.get('selection') or evidence.get('source_selection') or {}
        if isinstance(resolved, dict):
            card['selection'].update({k:deepcopy(resolved[k]) for k in allowed if k in resolved and resolved[k] is not None})
    if descriptor.get('delimiter'):
        card.setdefault('selection', {})['delimiter'] = descriptor['delimiter']
    basic = evidence.get('basic_profile') or {}
    basic_valid = bool(digest and basic.get('schema_version') == 'basic-table-profile-v1'
        and basic.get('source') == path and basic.get('source_sha256') == digest and basic.get('rows') == profile_rows
        and basic.get('field_columns') == ['name', 'role', 'distinct', 'once_only', 'repeated_values', 'excess_occurrences'])
    if basic_valid and basic.get('missing_values'):
        card.setdefault('selection', {})['missing_values'] = deepcopy(basic['missing_values'])
    fields = {f[0]: f for f in basic.get('fields', []) if isinstance(f, list) and len(f) == 6} if basic_valid else {}
    profiles = {p['name']: p for p in evidence.get('profiles', []) if isinstance(p, dict) and 'name' in p} if dataset else {}
    # A sample has no complete-row quality counts, even if a malformed payload supplies them.
    quality = bool(digest and scope in {'complete_parsed_file', 'complete_selected_table', 'filtered_rows'})
    for name in names[:32]:
        if not _text(name):
            continue
        entry = dict(name=name, storage_type=_text((evidence.get('column_types') or {}).get(name)))
        if quality:
            p = profiles.get(name, {})
            f = fields.get(name)
            entry.update(candidate_role=_text(p.get('analytical_role') or (f[1] if f else None), 40),
                missing_count=_count(p.get('missing_count', (evidence.get('missing_counts') or {}).get(name))),
                distinct_count=_count(p.get('distinct_count', f[2] if f else None)))
            entry['observed_type'] = _text(p.get('observed_type'), 80)
            numeric = p.get('numeric') or {}
            raw = (basic.get('numeric') or {}).get(name) if basic_valid else None
            if isinstance(raw, list) and len(raw) == 6:
                numeric = dict(zip(('count', 'mean', 'minimum', 'maximum', 'standard_deviation', 'non_numeric'), raw))
            entry['numeric_count'] = _count(numeric.get('count'))
            for key, source in [('mean', 'mean'), ('minimum', 'minimum'), ('maximum', 'maximum'), ('sample_standard_deviation', 'standard_deviation')]:
                number = numeric.get(source)
                entry[key] = number if type(number) in (int, float) and math.isfinite(number) else None
        card['fields'].append(entry)
    if quality:
        card['missingness'] = 'declared_policy' if dataset else 'native_nulls' if evidence.get('data_contract') == 'table/records-v1' else 'empty_cells'
        duplicates = basic.get('duplicate_rows') if basic_valid else None
        card['excess_duplicate_rows'] = _count(duplicates[3]) if isinstance(duplicates, list) and len(duplicates) == 4 else None
    for key in ('width', 'height', 'band_count'):
        card[key] = _count(evidence.get(key))
    card['crs'] = _text(evidence.get('crs'), 240)
    if isinstance(evidence.get('layers'), list):
        card['layer_count'] = len(evidence['layers'])
    # Selection itself must never be silently truncated into another population.
    if len(json.dumps(card.get('selection', {}), ensure_ascii=True).encode()) > 2000:
        return None
    try:
        # Budget the actual wire shape, including explicit unknown fields.
        card['fields'] = [CardField.model_validate(field).model_dump(mode='json') for field in card['fields']]
    except ValueError:
        return None
    while True:
        card['fields_omitted'] = (field_count or 0) - len(card['fields'])
        if len(json.dumps(card, ensure_ascii=True, separators=(',', ':')).encode()) < 6500:
            break
        if not card['fields']:
            return None
        card['fields'].pop()
    try:
        return DataCard.model_validate(card).model_dump(mode='json')
    except ValueError:
        return None  # Unqualified legacy evidence is not a verified card.


def attach(value):
    card = from_evidence(value)
    original = {k:v for k,v in value.items() if k != 'data_card'}
    return {**original, 'data_card': card} if card is not None else original


def matches_source(card, *, path, sha256, selection):
    """Require an independently obtained current digest/selection; never checks disk."""
    parsed = DataCard.model_validate(card)
    return bool(sha256 and parsed.source == path and parsed.source_sha256 == sha256 and parsed.selection == selection)
