"""Deterministic inspection-on-send eligibility and resource-bounded reading."""
from __future__ import annotations
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import subprocess
import sys

# Internal execution scope; never populated from a model or RunRequest field.
active_inspection = ContextVar('submitted_inspection', default=None)
planning_discovery = ContextVar('submitted_discovery_facts', default=None)

# Closed execution adapters: registry read-only status alone is insufficient.
INSPECTION_CONTRACTS = {
    'inspect_csv': {'suffixes': ('.csv', '.tsv'), 'version': 'csv-stream-v2', 'max_file_bytes': 1024**3, 'seconds': 120},
    'inspect_vector': {'suffixes': ('.geojson', '.gpkg', '.shp'), 'version': 'vector-discovery-v2', 'metadata_package_bytes': 1024**3, 'metadata_suffixes': ('.gpkg','.shp'),
                       'max_file_bytes': 8 * 1024**2, 'max_package_bytes': 32 * 1024**2,
                       'max_features': 10000, 'max_layers': 8, 'max_fields': 100},
    'inspect_raster': {'suffixes': ('.tif', '.tiff'), 'version': 'raster-discovery-v2', 'metadata_package_bytes': 1024**3, 'metadata_bands': 128,
                       'max_file_bytes': 8 * 1024**2, 'max_bands': 16, 'max_cells': 100_000_000},
}


def source_skill(path):
    suffix = Path(path).suffix.lower()
    return next((skill for skill, contract in INSPECTION_CONTRACTS.items()
                 if suffix in contract['suffixes']), None)



def bounded_read(root, *, action, path, source_sha256=None, delimiter=',', preview_rows=5, checkpoint=None, timeout=30, view_options=None, source_identity=None, on_metadata=None):
    from .server import InterfaceApiError
    if sys.platform != 'linux':
        raise InterfaceApiError('Inspection on send currently requires the Linux bounded reader; use reviewed Execute')
    source = str(Path(__file__).resolve().parents[2])
    command = [sys.executable, '-I', '-B', '-c',
               'import sys;sys.path.insert(0,sys.argv[1]);from geoagent_harness.interface_api.inspection_worker import main;main()', source]
    env = {'PATH': str(Path(sys.executable).parent), 'LANG': 'C.UTF-8',
           'PROJ_NETWORK': 'OFF', 'GDAL_PAM_ENABLED': 'NO', 'OGR_SQLITE_VIRTUAL_OGR': 'NO',
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    import time
    import os
    if action in {'csv_discover','spatial_discover'}:
        timeout = 120
    progress_read = progress_write = None
    if on_metadata is not None:
        progress_read, progress_write = os.pipe()
        os.set_blocking(progress_read, False)
    progress_buffer = bytearray()
    def drain():
        if progress_read is None:
            return
        while True:
            try: chunk = os.read(progress_read, 16385)
            except BlockingIOError: break
            if not chunk: break
            progress_buffer.extend(chunk)
            if len(progress_buffer)>16000:
                raise InterfaceApiError('Discovery metadata exceeds its progress budget')
            if b'\n' in progress_buffer:
                line, _, rest = progress_buffer.partition(b'\n')
                progress_buffer[:] = rest
                on_metadata(json.loads(line))
    payload=json.dumps(dict(root=str(root), action=action, path=path, source_sha256=source_sha256,
        source_identity=source_identity, delimiter=delimiter, preview_rows=preview_rows,
        view_options=view_options, progress_fd=progress_write)).encode()
    if len(payload)>4096:
        if progress_read is not None:
            os.close(progress_read);os.close(progress_write)
        raise InterfaceApiError('Inspection request exceeds its worker budget')
    deadline = time.monotonic() + timeout
    from contextlib import ExitStack
    with ExitStack() as resources:
        if progress_read is not None:
            resources.callback(os.close, progress_read)
            resources.callback(os.close, progress_write)
        process=resources.enter_context(subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, cwd='/tmp', close_fds=True, pass_fds=(() if progress_write is None else (progress_write,))))
        try:
            first = True
            while True:
                drain()
                if checkpoint:
                    checkpoint()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise InterfaceApiError(f'Inspection exceeded its {timeout}-second deadline; nothing was retried')
                try:
                    output, _ = process.communicate(payload if first else None, timeout=min(.2, remaining))
                    drain()
                    break
                except subprocess.TimeoutExpired:
                    first = False
            if process.returncode or len(output) > (500000 if action == 'spatial_view' else 16000):
                raise InterfaceApiError('Dataset discovery failed: source changed, unsupported/invalid input or a discovery budget was exceeded. No data was changed.' if action in {'csv_probe','csv_discover','spatial_probe','spatial_discover'} else 'Bounded inspection failed. Check source changes, validity and the 8 MiB per-file and documented feature/layer/band limits. No dataset was changed.')
            result = json.loads(output)
            if action == 'spatial_view' and result.get('error'):
                raise InterfaceApiError(result['error'])
            return result
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()


def contract_digest(root, skill_id='inspect_csv'):
    from geoagent_harness.skill_registry import load_skill_registry
    from geoagent_harness.operations.registry import argument_models
    skill = load_skill_registry(root).get_skill(skill_id)
    value = {'adapter': INSPECTION_CONTRACTS[skill_id], 'skill': skill.model_dump(mode='json'), 'arguments': argument_models(root)[skill_id].model_json_schema()}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def probe_action(path):
    suffix=Path(path).suffix.lower()
    return 'csv_probe' if suffix in {'.csv','.tsv'} else 'spatial_probe' if suffix in {'.tif','.tiff','.gpkg','.shp'} else 'snapshot'


def request_source(message):
    from geoagent_harness.planner.request_coverage import inspection_only_skill
    from geoagent_harness.tabular.service import relative_path
    import re
    if inspection_only_skill(message) not in INSPECTION_CONTRACTS:
        return None
    match = re.match(r'\s*inspect\s+([^\s;]+\.(?:csv|tsv|geojson|gpkg|shp|tiff|tif))', message, re.I)
    return relative_path(match[1], 'input')


def eligible(root, result, message, source):
    """Return an explicit refusal reason, never trim an ineligible workflow."""
    from geoagent_harness.skill_registry import load_skill_registry, SkillAccess
    from .inspection_planning import plan_for_request
    exact=plan_for_request(message,INSPECTION_CONTRACTS)
    sources=source.get('sources',[source]) if source else []
    if not exact or [s.arguments['path'] for s in exact.steps]!=[s['path'] for s in sources]:
        return 'Only an explicit supported metadata inspection batch can inspect on send.'
    steps = result.plan.steps
    if len(steps) != len(sources):
        return 'The complete proposal must match every submitted inspection; nothing was trimmed.'
    registry = load_skill_registry(root)
    for step,item in zip(steps,sources):
        skill = registry.get_skill(step.skill)
        if step.skill!=source_skill(item['path']) or step.arguments.get('path')!=item['path']:
            return 'The proposed input/operation differs from the submitted source.'
        if skill.access != SkillAccess.READ_ONLY or skill.approval_required is not False or step.requires_approval:
            return 'This operation has an approval requirement; review it and use Authorize/Execute.'
    return None


def check_dispatch(root, review, binding):
    from .server import InterfaceApiError
    from .planning_tasks import conversation_record
    from geoagent_harness.approvals import plan_sha256
    from geoagent_harness.planner.schemas import PlannerResult
    sources=binding.get('sources',[binding])
    if (review['write_step_ids'] or review['approval_required_step_ids'] or len(review['steps']) != len(sources)
            or review['plan_sha256'] != binding['plan_sha256']):
        raise InterfaceApiError('Submitted inspection scope or operation contract changed; nothing dispatched')
    for step,item in zip(review['steps'],sources):
        if (step['skill']!=source_skill(item['path']) or step['arguments'].get('path')!=item['path']
                or contract_digest(root,source_skill(item['path']))!=item['contract_sha256']):
            raise InterfaceApiError('Submitted inspection scope or operation contract changed; nothing dispatched')
    chat = conversation_record(root, binding['conversation_id'])
    if (not chat or chat['revision'] != binding['revision'] or not chat.get('planner_result')
            or plan_sha256(PlannerResult.model_validate(chat['planner_result']).plan) != binding['plan_sha256']):
        raise InterfaceApiError('Conversation changed before inspection dispatch; send a fresh request')
