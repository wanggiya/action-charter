"""Permitted source checks and scoped Data Card reuse over existing readers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from geoagent_harness.contracts.analysis_options import AnalysisOptions, TableSourceOptions
from geoagent_harness.contracts.data_cards import CardUse
from geoagent_harness.contracts.paths import relative_path
from geoagent_harness.contracts.table_sources import RECORD_SUFFIXES, table_format
from geoagent_harness.data.discovery.cards import from_evidence
from geoagent_harness.platform.storage import data_cards as cache

READER_REVISION = 'card-context-readers-v2'  # Bump when projection/reader semantics change.


def reader_contract(path):
    from importlib.metadata import PackageNotFoundError, version
    import sys
    from geoagent_harness.workspaces.sandbox.inspection import INSPECTION_CONTRACTS, source_skill
    skill = source_skill(path)
    if skill is None:
        raise ValueError('Choose a supported dataset format')
    value = {'revision': READER_REVISION, 'card': 'data-card-v1', 'reader': INSPECTION_CONTRACTS[skill],
             'python': list(sys.version_info[:3])}
    dependencies = []
    if skill == 'inspect_csv':
        value['format'] = table_format(path).describe()
        dependencies = [name for name, _ in table_format(path).requirements]
    else:
        dependencies = ['rasterio'] if skill == 'inspect_raster' else ['geopandas','pyogrio','shapely']
    value['runtime_versions'] = {}
    for name in dependencies:
        try:
            value['runtime_versions'][name] = version(name)
        except PackageNotFoundError:
            value['runtime_versions'][name] = 'unavailable'
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def selection_for(path, *, delimiter=None, source_options=None, filters=None, missing_values=None, preliminary=False):
    delimiter = delimiter or ('\t' if path.lower().endswith('.tsv') else ',')
    if delimiter not in {',', '\t'}:
        raise ValueError('Choose comma or tab')
    options = AnalysisOptions(source_options=TableSourceOptions.model_validate(source_options) if source_options is not None else None,
                              filters=filters or [], missing_values=missing_values or {})
    value = {'delimiter': delimiter, 'source_options': options.source_options.model_dump(mode='json', exclude_none=True) if options.source_options else None,
             'filters': [f.model_dump(mode='json') for f in options.filters], 'missing_values': options.missing_values,
             'read_scope': 'preliminary_metadata' if preliminary else 'complete_metadata'}
    if len(json.dumps(value).encode()) > 2000:
        raise ValueError('Data Card selection exceeds its bounded context contract')
    return value


def prepare(root, path, *, owner='explicit_discovery', allow_read=False, preliminary=False,
            delimiter=None, source_options=None, filters=None, missing_values=None, max_input_bytes=1024**3):
    """Never called by history/read/refresh. allow_read is trusted caller policy.

    Cards are facts, not executable results. Reuse always hashes full current
    content; it never replays a workflow or extends an approval. Owner namespaces
    isolate chats from each other and from explicit CLI/MCP discovery.
    """
    from geoagent_harness.workspaces.sandbox.inspection import bounded_read, probe_action
    path = relative_path(path, 'input')
    contract = reader_contract(path)
    selected = selection_for(path, delimiter=delimiter, source_options=source_options,
                             filters=filters, missing_values=missing_values, preliminary=preliminary)
    old = cache.read(root, owner=owner, path=path, selection=selected, contract=contract)
    def receipt(status, finding, *, card=None, checked=False, reader=False):
        return CardUse(source=path, status=status, card=card, source_checked=checked,
            checked_at=datetime.now(timezone.utc).isoformat() if checked else None,
            reader_performed=reader, reader_contract=contract, requested_selection=selected,
            finding=finding).model_dump(mode='json')
    if not allow_read:
        return receipt('historical' if old else 'read_not_permitted',
                       'No current source read permitted. Any retained facts are historical.', card=old)
    suffix = Path(path).suffix.lower()
    complex_selection = bool(source_options or filters or missing_values)
    if preliminary and (suffix in RECORD_SUFFIXES or complex_selection):
        return receipt('review_required', 'Worksheet/record selection and analytical profiles require reviewed Execute; nothing read.', card=old)
    if filters and suffix not in {'.csv', '.tsv'}:
        return receipt('review_required', 'Filtered context requires the qualified CSV profile; use the reviewed operation for other formats.', card=old)
    if suffix not in {'.csv', '.tsv', *RECORD_SUFFIXES} and complex_selection:
        raise ValueError('Table selection options cannot apply to spatial context')
    current = None
    if old is not None:
        current = bounded_read(root, action='source_fingerprint', path=path, max_input_bytes=max_input_bytes)
        if old['source_sha256'] == current['source_sha256'] and old['identity_basis'] == current['identity_basis']:
            return receipt('verified_reused', 'Full content digest, exact selection and reader contract checked for this request; no new inspection.',
                           card=old, checked=True)
    if preliminary and probe_action(path) != 'snapshot':
        evidence = bounded_read(root, action=probe_action(path), path=path, delimiter=selected['delimiter'], preview_rows=0)
        current = bounded_read(root, action='source_fingerprint', path=path, source_identity=evidence['source_identity'], max_input_bytes=max_input_bytes)
        evidence = {**evidence, 'source_sha256': current['source_sha256']}
    else:
        if preliminary:
            current = bounded_read(root, action='source_fingerprint', path=path, max_input_bytes=max_input_bytes)
        analysis = {key: selected[key] for key in ('source_options', 'filters', 'missing_values') if selected[key]}
        if filters:
            evidence = bounded_read(root, action='dataset_profile', path=path, delimiter=selected['delimiter'], analysis=analysis)
        elif suffix in {'.csv', '.tsv', *RECORD_SUFFIXES}:
            evidence = bounded_read(root, action='csv_discover', path=path, delimiter=selected['delimiter'], preview_rows=0,
                                    analysis=analysis or None)
        elif probe_action(path) == 'spatial_probe':
            evidence = bounded_read(root, action='spatial_discover', path=path)
        else:
            snapshot = bounded_read(root, action='snapshot', path=path)
            evidence = bounded_read(root, action='inspect', path=path, source_sha256=snapshot['source_sha256'])
    card = from_evidence(evidence)
    if card is None or card['source_sha256'] is None:
        raise ValueError('The reader did not produce source-bound Data Card facts')
    if current is not None and card['source_sha256'] != current['source_sha256']:
        raise ValueError('Source changed between verification and metadata preparation')
    cache.store(root, owner=owner, path=path, selection=selected, contract=contract, card=card)
    return receipt('prepared', 'Source-bound metadata prepared for this request; sample scope does not establish complete statistics.',
                   card=card, checked=True, reader=True)
