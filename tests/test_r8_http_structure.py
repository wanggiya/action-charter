"""HTTP extraction parity from pre-R8 schemas, code and response fixtures."""
import ast
from contextlib import contextmanager
from email.message import Message
import hashlib
import inspect
from io import BytesIO
import json
from pathlib import Path
import textwrap

import pytest

from geoagent_harness.interface_api import server
from tests.http_contract_probe import capture_contract

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / 'tests/architecture/r8_http_contract.json').read_text())

# P0-C2 (#84) deliberately changes only these display inventories. Preserve the
# original R8 fixture bytes and keep all other coordinator ASTs locked to history.
INVENTORY_FIX_SHA256 = {'interface_saved_plan_inventory': 'b821cafa7922a122f87ce5f7d98b5096fc7cbc25e2ef95dedd815964f442b728', 'interface_saved_recipe_inventory': '4de60d6b3c1f87d9bd7a3978aac5e2b3231b4fab11d3b71a90ce4bc86d3ea5b9'}



def ast_digest(function):
    return hashlib.sha256(ast.dump(ast.parse(textwrap.dedent(inspect.getsource(function))).body[0],
                                  include_attributes=False).encode()).hexdigest()


def test_all_sixteen_request_schemas_keep_their_exact_contracts():
    actual = {name: getattr(server, name).model_json_schema() for name in BASELINE['schema_names']}
    assert len(actual) == 16
    digest = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert digest == BASELINE['schemas_sha256']


def test_original_coordinator_bodies_and_signatures_are_unchanged_and_shared():
    for name, digest in BASELINE['functions'].items():
        function = getattr(server, name)
        assert ast_digest(function) == INVENTORY_FIX_SHA256.get(name, digest), name
        assert function.__module__.startswith('geoagent_harness.task_actions.'), name
    assert len(BASELINE['functions']) == 24


def test_existing_serializer_origin_guard_and_logging_keep_their_ast():
    handler = server._handler(ROOT)
    for name, digest in BASELINE['transport_methods'].items():
        assert ast_digest(getattr(handler, name)) == digest, name


def test_route_paths_matching_order_and_post_allowlist_are_preserved():
    from geoagent_harness.apps.http.dispatch import GET_ROUTES, POST_ROUTES, POST_PATHS
    assert [(kind, path) for kind, path, _ in GET_ROUTES] == [
        (route['kind'], route['path']) for route in BASELINE['get_routes']]
    assert len(GET_ROUTES) == 21
    assert sorted(POST_ROUTES) == BASELINE['post_paths']
    assert POST_PATHS == frozenset(BASELINE['post_paths'])
    assert len(POST_PATHS) == 50


def test_all_pre_extraction_request_and_error_responses_match():
    assert capture_contract(BASELINE) == BASELINE['responses']
    assert len(BASELINE['responses']) == 104


def test_snapshot_uses_fixture_versions_but_production_catalog_stays_live(tmp_path, monkeypatch):
    import shutil
    from types import SimpleNamespace
    from geoagent_harness.capabilities.registry import registry
    metadata = SimpleNamespace(version=lambda _name: '99.0.0',
                               PackageNotFoundError=registry.metadata.PackageNotFoundError)
    monkeypatch.setattr(registry, 'metadata', metadata)
    (tmp_path/'context').mkdir()
    shutil.copyfile(ROOT/'context/SKILLS_INDEX.yaml', tmp_path/'context/SKILLS_INDEX.yaml')
    actual = registry.operation_catalog(tmp_path)
    requirements = [r for op in actual['operations'] for r in op['runtime_requirements']]
    assert requirements and all(r['installed_version'] == '99.0.0' and r['available'] for r in requirements)
    assert capture_contract(BASELINE) == BASELINE['responses']
    assert registry.metadata is metadata
    assert all(r['installed_version'] == '99.0.0'
               for op in registry.operation_catalog(tmp_path)['operations'] for r in op['runtime_requirements'])


def test_native_http_modules_are_small_and_routers_do_not_import_server_or_other_routers():
    directory = ROOT / 'src/geoagent_harness/apps/http'
    for path in directory.rglob('*.py'):
        assert len(path.read_text().splitlines()) < 500, path
        if path.parent.name != 'routers':
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            modules = [node.module or ''] if isinstance(node, ast.ImportFrom) else (
                [name.name for name in node.names] if isinstance(node, ast.Import) else [])
            assert not any(module.startswith(('geoagent_harness.apps.http.server',
                'geoagent_harness.apps.http.routers', 'geoagent_harness.interface_api'))
                for module in modules), path


def test_public_server_alias_and_execution_state_keep_identity():
    from geoagent_harness.apps.http import server as native
    from geoagent_harness.task_actions import execution
    assert server is native
    assert server._EXECUTION_LOCK is execution._EXECUTION_LOCK
    assert server._EXECUTION_PROGRESS is execution._EXECUTION_PROGRESS
    assert server._ACTIVE_EXECUTIONS is execution._ACTIVE_EXECUTIONS


def test_unmatched_errors_escape_and_selection_context_is_restored(tmp_path, monkeypatch):
    from geoagent_harness.platform.model_gateway import catalog
    events = []

    @contextmanager
    def selection(root):
        events.append(('enter', root))
        try:
            yield
        finally:
            events.append(('leave', root))

    def fail(*args, **kwargs):
        raise TypeError('unhandled fixture failure')

    monkeypatch.setattr(catalog, 'request_selection', selection)
    monkeypatch.setattr(server, 'plan_interface_task', fail)
    handler_class = server._handler(tmp_path)
    handler = handler_class.__new__(handler_class)
    handler.path = '/api/v1/plans/create'
    payload = json.dumps({'action': 'plan_task', 'request': 'Inspect only',
                          'allowed_skill_ids': ['inspect_vector']}).encode()
    handler.headers = Message()
    handler.headers['Content-Type'] = 'application/json'
    handler.headers['Content-Length'] = str(len(payload))
    handler.rfile = BytesIO(payload)
    sent = []
    handler._send = lambda *args: sent.append(args)
    with pytest.raises(TypeError, match='unhandled fixture failure'):
        handler.do_POST()
    assert sent == []
    assert events == [('enter', tmp_path), ('leave', tmp_path)]


@pytest.mark.parametrize('cache_corrupt', [False, True])
def test_progress_load_and_cache_failures_retain_distinct_boundaries(tmp_path, monkeypatch, cache_corrupt):
    from geoagent_harness.task_actions import execution
    digest = 'a' * 64
    cyclic = {}
    cyclic['self'] = cyclic
    monkeypatch.setattr(execution, '_EXECUTION_PROGRESS', {digest: cyclic} if cache_corrupt else {})

    def fail(*args, **kwargs):
        raise ValueError('invalid recorded fixture')

    monkeypatch.setattr(execution, '_load_execution_progress', fail)
    handler_class = server._handler(tmp_path)
    handler = handler_class.__new__(handler_class)
    handler.path = '/api/v1/executions/' + digest
    handler.headers = Message()
    sent = []
    handler._send = lambda status, payload: sent.append([int(status), payload])
    if cache_corrupt:
        with pytest.raises(ValueError, match='Circular reference'):
            handler.do_GET()
        assert sent == []
    else:
        handler.do_GET()
        assert sent == [[503, {'error': 'execution progress is unavailable'}]]
