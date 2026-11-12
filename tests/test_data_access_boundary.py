"""R4 compatibility and data-access boundaries on disposable local workspaces."""
import hashlib
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys

import pytest

from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.outcomes import _bounded_outcome
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.workspaces.sandbox.inspection import bounded_read


@pytest.fixture(params=[False, True], ids=['default-root', 'relocated-root'])
def project(tmp_path, request):
    root = tmp_path / 'project'
    folder = root / 'data/input'
    folder.mkdir(parents=True)
    (folder / 'orders.csv').write_text('age,group\n10,A\n20,A\n,B\n')
    if request.param:
        (root / 'actioncharter.workspace.json').write_text(json.dumps({
            'version': 1, 'state_root': str(tmp_path / 'state')}))
    return root


@pytest.mark.parametrize('legacy,owner', [
    ('task_actions.contracts', 'contracts.actions'),
    ('context_pack.redaction', 'contracts.context_redaction'),
    ('tabular.source_contracts', 'contracts.table_sources'),
    ('operations.inspection_contracts', 'contracts.inspection_formats'),
    ('task_actions.inspection_worker', 'sandbox.inspection_worker'),
    ('task_actions.spatial_inspection_snapshot', 'sandbox.spatial_snapshot'),
])
def test_legacy_modules_retain_exact_owner_identity(legacy, owner):
    metadata = Path(__file__).resolve().parents[1] / 'tests/architecture'
    historical = json.loads((metadata / 'r6_module_owners.json').read_text())
    retired = json.loads((metadata / 'r11_compatibility.json').read_text())['retired']
    legacy = 'geoagent_harness.' + legacy
    owner = 'geoagent_harness.' + owner
    native = import_module(historical.get(owner, {}).get('owner', owner))
    if legacy in retired:
        with pytest.raises(ModuleNotFoundError):import_module(legacy)
    else:
        assert import_module(legacy) is native


def test_policy_retains_scopes_but_reexports_the_same_reader_and_rendering():
    from geoagent_harness.task_actions import inspection_policy as legacy
    from geoagent_harness.task_actions import inspection_policy as policy, spatial_views
    from geoagent_harness.workspaces.sandbox import inspection, spatial_rendering
    assert legacy is policy
    for name in ('bounded_read', 'probe_action', 'source_skill', 'INSPECTION_CONTRACTS'):
        assert getattr(policy, name) is getattr(inspection, name)
    assert policy.subprocess is inspection.subprocess
    assert policy.sys is inspection.sys
    for name in ('SpatialViewOptions', 'SpatialDisplayError', 'render_snapshot', 'raster_view', '_png'):
        assert getattr(spatial_views, name) is getattr(spatial_rendering, name)
    token = policy.active_inspection.set({'fixture': True})
    try:
        assert legacy.active_inspection.get() == {'fixture': True}
        assert not hasattr(inspection, 'active_inspection')
        assert not hasattr(inspection, 'check_dispatch')
    finally:
        policy.active_inspection.reset(token)


def test_shared_errors_roots_and_projection_keep_callable_identity():
    from geoagent_harness.task_actions import common
    assert common.InterfaceApiError is common.TaskActionError is InterfaceApiError
    assert common._trusted_root is _trusted_root
    assert common._bounded_outcome is _bounded_outcome


def test_new_reader_keeps_source_digest_and_does_not_write_runtime_state(project):
    source = project / 'data/input/orders.csv'
    before = sorted(str(p.relative_to(project)) for p in project.rglob('*'))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    snapshot = bounded_read(project, action='snapshot', path='data/input/orders.csv')
    assert snapshot == {'path': 'data/input/orders.csv', 'source_sha256': digest,
                        'bytes': source.stat().st_size}
    result = bounded_read(project, action='inspect', path='data/input/orders.csv', source_sha256=digest)
    assert result['row_count'] == 3
    assert result['source_sha256'] == digest
    assert result['effects'] == 'read_only'
    assert sorted(str(p.relative_to(project)) for p in project.rglob('*')) == before
    source.write_text('age,group\n30,C\n')
    with pytest.raises(InterfaceApiError, match='Bounded inspection failed'):
        bounded_read(project, action='inspect', path='data/input/orders.csv', source_sha256=digest)


@pytest.mark.parametrize('path', ['../orders.csv', '/tmp/orders.csv', 'data/output/orders.csv', 'data/input/link.csv'])
def test_new_worker_rejects_unsafe_paths_without_changing_files(project, path):
    source = project / 'data/input/orders.csv'
    (project / 'data/input/link.csv').symlink_to(source)
    before = source.read_bytes()
    with pytest.raises(InterfaceApiError, match='Bounded inspection failed'):
        bounded_read(project, action='snapshot', path=path)
    assert source.read_bytes() == before
    assert not (project / 'data/output').exists()


def test_trusted_root_retains_existing_errors_and_exception_cause(tmp_path):
    with pytest.raises(InterfaceApiError, match='trusted project root is unavailable') as error:
        _trusted_root(tmp_path / 'missing')
    assert isinstance(error.value.__cause__, FileNotFoundError)
    file = tmp_path / 'file'; file.write_text('fixture')
    with pytest.raises(InterfaceApiError, match='trusted project root must be a directory'):
        _trusted_root(file)
    assert _trusted_root(tmp_path) == tmp_path.resolve()


def test_redaction_profiles_remain_distinct_and_compatible():
    from geoagent_harness.contracts.context_redaction import redact_value as context_redact
    from geoagent_harness.contracts.redaction import redact_value as result_redact
    value = {'password_hint': 'fixture', 'passwd': 'fixture', 'connection_string': 'fixture'}
    assert context_redact(value) == {
        'password_hint': '[REDACTED]', 'passwd': '[REDACTED]', 'connection_string': 'fixture'}
    assert result_redact(value) == {
        'password_hint': 'fixture', 'passwd': 'fixture', 'connection_string': '[REDACTED]'}
    assert context_redact('mysql://user:fixture@host/data') == 'mysql://[REDACTED]@host/data'
    assert result_redact('mysql://user:fixture@host/data') == 'mysql://user:fixture@host/data'


@pytest.mark.parametrize('analysis,limit', [(False, 16384), (True, 128000)])
def test_projection_keeps_utf8_byte_limits_and_redacts_before_sizing(analysis, limit):
    value = {'table_analysis': {}} if analysis else {}
    overhead = len(json.dumps({**value, 'text': ''}, sort_keys=True, separators=(',', ':')).encode())
    value['text'] = 'x' * (limit - overhead)
    assert _bounded_outcome(value) == value
    value['text'] += 'é'
    assert _bounded_outcome(value) == {
        'outcome_available': True, 'projection_truncated': True,
        'message': 'Outcome is too large for the interface projection; inspect durable evidence.'}
    assert _bounded_outcome({'password': 'x' * 20000}) == {'password': '[REDACTED]'}


@pytest.mark.parametrize('change', [
    {'allowed_skill_ids': ['inspect_csv', 'inspect_csv']},
    {'confirmed_plan_sha256': 'invalid'},
    {'confirmation': 'authorize everything'},
])
def test_neutral_save_contract_still_rejects_invalid_requests(change):
    from geoagent_harness.contracts.actions import InterfaceReviewedPlanSaveRequest
    payload = dict(action='save_reviewed_plan', confirmed_plan_sha256='a' * 64,
                   allowed_skill_ids=['inspect_csv'], planner_result={
                       'model': 'fixture', 'original_request': 'Inspect', 'context_references': [],
                       'plan': {'summary': 'Inspect', 'steps': [{'step_id': 'step_1', 'skill': 'inspect_csv',
                                 'purpose': 'Inspect', 'arguments': {'path': 'data/input/orders.csv'}}]}})
    assert InterfaceReviewedPlanSaveRequest.model_validate(payload).allowed_skill_ids == ['inspect_csv']
    with pytest.raises(ValueError):
        InterfaceReviewedPlanSaveRequest.model_validate({**payload, **change})


def test_shared_access_imports_do_not_load_task_actions_or_agent_roles():
    code = "import sys\nfrom geoagent_harness.workspaces.sandbox import inspection\nfrom geoagent_harness.workspaces.sandbox import inspection_worker\nfrom geoagent_harness.workspaces.sandbox import spatial_snapshot\nfrom geoagent_harness.workspaces.sandbox import spatial_rendering\nfrom geoagent_harness.platform import project, outcomes\nfrom geoagent_harness.contracts import actions, context_redaction, inspection_formats, table_sources\nassert not any(name.startswith(('geoagent_harness.task_actions', 'geoagent_harness.interface_api',\n    'geoagent_harness.context_pack', 'geoagent_harness.planner', 'geoagent_harness.model',\n    'geoagent_harness.critic', 'geoagent_harness.executor')) for name in sys.modules)\n"
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
