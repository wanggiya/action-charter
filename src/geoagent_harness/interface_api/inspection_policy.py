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

# Closed execution adapters: registry read-only status alone is insufficient.
INSPECTION_CONTRACTS = {
    'inspect_csv': {'suffixes': ('.csv', '.tsv'), 'version': 'csv-v1'},
    'inspect_vector': {'suffixes': ('.geojson', '.gpkg', '.shp'), 'version': 'vector-v1',
                       'max_file_bytes': 8 * 1024**2, 'max_package_bytes': 32 * 1024**2,
                       'max_features': 10000, 'max_layers': 8, 'max_fields': 100},
    'inspect_raster': {'suffixes': ('.tif', '.tiff'), 'version': 'raster-v1',
                       'max_file_bytes': 8 * 1024**2, 'max_bands': 16, 'max_cells': 100_000_000},
}


def source_skill(path):
    suffix = Path(path).suffix.lower()
    return next((skill for skill, contract in INSPECTION_CONTRACTS.items()
                 if suffix in contract['suffixes']), None)



def bounded_read(root, *, action, path, source_sha256=None, delimiter=',', preview_rows=5, checkpoint=None, timeout=30, view_options=None):
    from .server import InterfaceApiError
    if sys.platform != 'linux':
        raise InterfaceApiError('Inspection on send currently requires the Linux bounded reader; use reviewed Execute')
    source = str(Path(__file__).resolve().parents[2])
    command = [sys.executable, '-I', '-B', '-c',
               'import sys;sys.path.insert(0,sys.argv[1]);from geoagent_harness.interface_api.inspection_worker import main;main()', source]
    payload = json.dumps(dict(root=str(root), action=action, path=path, source_sha256=source_sha256,
                              delimiter=delimiter, preview_rows=preview_rows, view_options=view_options)).encode()
    if len(payload) > 4096:
        raise InterfaceApiError('Inspection request exceeds its worker budget')
    env = {'PATH': str(Path(sys.executable).parent), 'LANG': 'C.UTF-8',
           'PROJ_NETWORK': 'OFF', 'GDAL_PAM_ENABLED': 'NO', 'OGR_SQLITE_VIRTUAL_OGR': 'NO',
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    import time
    deadline = time.monotonic() + timeout
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, cwd='/tmp', close_fds=True) as process:
        try:
            first = True
            while True:
                if checkpoint:
                    checkpoint()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise InterfaceApiError('Inspection exceeded its 30-second deadline; nothing was retried')
                try:
                    output, _ = process.communicate(payload if first else None, timeout=min(.2, remaining))
                    break
                except subprocess.TimeoutExpired:
                    first = False
            if process.returncode or len(output) > (500000 if action == 'spatial_view' else 16000):
                raise InterfaceApiError('Bounded inspection failed. Check source changes, validity and the 8 MiB per-file and documented feature/layer/band limits. No dataset was changed.')
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
    if not source or request_source(message) != source['path']:
        return 'Only an explicit supported single-dataset metadata request can inspect on send.'
    steps = result.plan.steps
    if len(steps) != 1 or steps[0].skill != source_skill(source['path']):
        return 'The complete proposal must contain exactly one matching supported inspection.'
    step = steps[0]
    registry = load_skill_registry(root)
    skill = registry.get_skill(step.skill)
    if skill.access != SkillAccess.READ_ONLY or skill.approval_required is not False or step.requires_approval:
        return 'This operation has an approval requirement; review it and use Authorize/Execute.'
    if step.arguments.get('path') != source['path']:
        return 'The proposed input differs from the submitted source.'
    return None


def check_dispatch(root, review, binding):
    from .server import InterfaceApiError
    from .planning_tasks import conversation_record
    from geoagent_harness.approvals import plan_sha256
    from geoagent_harness.planner.schemas import PlannerResult
    if (review['write_step_ids'] or review['approval_required_step_ids'] or len(review['steps']) != 1
            or review['steps'][0]['skill'] != source_skill(binding['path'])
            or review['steps'][0]['arguments'].get('path') != binding['path']
            or review['plan_sha256'] != binding['plan_sha256']
            or contract_digest(root, source_skill(binding['path'])) != binding['contract_sha256']):
        raise InterfaceApiError('Submitted inspection scope or operation contract changed; nothing dispatched')
    chat = conversation_record(root, binding['conversation_id'])
    if (not chat or chat['revision'] != binding['revision'] or not chat.get('planner_result')
            or plan_sha256(PlannerResult.model_validate(chat['planner_result']).plan) != binding['plan_sha256']):
        raise InterfaceApiError('Conversation changed before inspection dispatch; send a fresh request')
