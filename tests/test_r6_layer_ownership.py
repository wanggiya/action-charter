"""R6 native ownership, compatibility and zero-debt gates; no live services."""
import copy
import hashlib
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_import_layers import scan, compatibility_owners

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'tests/architecture/import_layers_policy.json'
OWNERS = ROOT / 'tests/architecture/r11_compatibility.json'


def test_every_legacy_leaf_resolves_to_the_actual_native_module():
    code = '''import faulthandler,json,sys
from importlib import import_module
from pathlib import Path
faulthandler.dump_traceback_later(20)
for legacy,record in json.loads(Path(sys.argv[1]).read_text())['retained'].items():
    # __main__ modules intentionally start the application; test entrypoints as
    # processes, never import a server entrypoint into a schema/identity sweep.
    if record['kind'] != 'alias' or legacy.endswith('.__main__'):continue
    print(legacy,flush=True)
    assert import_module(legacy) is import_module(record['owner']),legacy
faulthandler.cancel_dump_traceback_later()
'''
    result = subprocess.run([sys.executable, '-c', code, str(OWNERS)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr


def test_ninety_four_pre_move_schema_exports_keep_their_exact_contracts():
    fixture = json.loads((ROOT / 'tests/architecture/r6_schema_exports.json').read_text())
    actual = {}
    for key in fixture['exports']:
        module, _, name = key.rpartition('.')
        actual[key] = getattr(import_module('geoagent_harness.' + module), name).model_json_schema()
    digest = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert len(actual) == 94
    assert digest == fixture['sha256']


def test_native_layers_have_zero_upward_or_dynamic_import_debt():
    result = scan(ROOT, json.loads(POLICY.read_text()))
    assert result['violations'] == []
    assert result['dynamic_imports'] == []
    legacy = set(compatibility_owners(ROOT))
    assert not [e for e in result['edges'] if e.source not in legacy
                and result['modules'][e.source] < 6 and e.target in legacy]


@pytest.mark.parametrize('module', [
    'core.policy.plan', 'core.policy.approvals.service',
    'core.policy.recipe', 'core.ledger.recipe_storage',
    'core.ledger.task_history.relationships', 'contracts.recipe_evidence',
])
def test_core_policy_and_records_import_without_roles_or_data_execution(module):
    code = f'''import importlib,sys
importlib.import_module('geoagent_harness.{module}')
blocked=('geoagent_harness.agents','geoagent_harness.evolution',
    'geoagent_harness.apps','geoagent_harness.data','geoagent_harness.capabilities',
    'geoagent_harness.interface_api','pandas','numpy','httpx','geopandas','rasterio')
assert not [n for n in sys.modules if any(n==p or n.startswith(p+'.') for p in blocked)]
'''
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_old_and_native_cancellation_share_context_and_exception():
    from geoagent_harness.recipes import control as legacy
    from geoagent_harness.platform import execution_control as native
    assert legacy is native
    assert legacy.ExecutionCancelled is native.ExecutionCancelled
    before = native.observer.get()
    token = legacy.observer.set(object())
    try:
        assert native.observer.get() is legacy.observer.get()
    finally:
        native.observer.reset(token)
    assert legacy.observer.get() is before


def test_legacy_record_and_policy_functions_share_native_implementations():
    from geoagent_harness import approvals, recipes
    from geoagent_harness.planner import policy
    from geoagent_harness.core.policy import plan, recipe_approval
    from geoagent_harness.core.policy.approvals import service
    from geoagent_harness.core.ledger import recipe_storage, recipe_identity
    assert approvals.create_approval is service.create_approval
    assert approvals.verify_approval is service.verify_approval
    assert policy is plan
    assert recipes.verify_recipe_approval is recipe_approval.verify_recipe_approval
    assert recipes.load_recipe is recipe_storage.load_recipe
    assert recipes.recipe_sha256 is recipe_identity.recipe_sha256


def test_legacy_mcp_client_preserves_fixed_transport_and_result_types():
    from geoagent_harness.mcp_client import MCPExecutorClient, MCPReadOnlyClient, MCPToolCallResult
    from geoagent_harness.platform.internal_mcp import client, executor
    from geoagent_harness.contracts.mcp import MCPToolCallResult as Result
    assert MCPExecutorClient is executor.MCPExecutorClient
    assert MCPReadOnlyClient is client.MCPReadOnlyClient
    assert MCPToolCallResult is Result
    assert executor.APPROVED_EXECUTOR_TOOLS == frozenset({'run_approved_vector_postgis_workflow', 'run_approved_recipe'})


def test_native_business_code_cannot_be_hidden_in_a_compatibility_facade(tmp_path):
    # A minimal topology exercises the extra compatibility guard independently.
    root = tmp_path
    package = root / 'src/geoagent_harness'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    (package / 'legacy.py').write_text('def perform_write():\n    return True\n')
    (package / 'native.py').write_text('')
    meta = root / 'tests/architecture'
    meta.mkdir(parents=True)
    (meta / 'r6_module_owners.json').write_text(json.dumps({
        'geoagent_harness.legacy': {'owner': 'geoagent_harness.native', 'package': False,
            'kind': 'alias', 'sha256': hashlib.sha256((package / 'legacy.py').read_bytes()).hexdigest()}}))
    policy = {'schema_version': 1, 'modules': {'geoagent_harness.legacy': 6,
        'geoagent_harness.native': 1}, 'exact_modules': {'geoagent_harness': 0}}
    with pytest.raises(ValueError, match='Business logic is forbidden'):
        scan(root, policy)


def test_upward_import_of_a_legacy_adapter_still_fails_the_native_gate(tmp_path):
    package = tmp_path / 'src/geoagent_harness'
    package.mkdir(parents=True)
    for name, source in {'__init__.py': '', 'legacy.py': '',
                         'native.py': 'import geoagent_harness.legacy\n'}.items():
        (package / name).write_text(source)
    policy = {'schema_version': 1, 'modules': {'geoagent_harness.legacy': 6,
        'geoagent_harness.native': 1}, 'exact_modules': {'geoagent_harness': 0}}
    result = scan(tmp_path, policy)
    assert len(result['violations']) == 1
    assert result['violations'][0].target == 'geoagent_harness.legacy'
