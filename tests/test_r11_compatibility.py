"""Retirement/public ABI/worker bundle contracts; no live Docker, DB or model."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_compatibility import audit, legacy_imports
from scripts.check_import_layers import compatibility_owners, scan

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tests/architecture/r11_compatibility.json'


def test_every_old_adapter_is_accounted_for_without_rewriting_r6_history():
    result = audit()
    assert result['errors'] == []
    assert result['retired'] == 290
    assert result['retained_public'] == 117
    assert result['modules'] == 614
    assert result['native_modules'] == 497


def test_retired_modules_do_not_resolve_through_leftover_parent_exports():
    code = '''import importlib,json,sys
from pathlib import Path
for name,record in json.loads(Path(sys.argv[1]).read_text())['retired'].items():
    try: importlib.import_module(name)
    except ModuleNotFoundError as error:
        assert name==error.name or name.startswith(error.name+'.'),(name,error.name)
    else:
        # An empty directory/cache can remain a Python namespace. It must not
        # execute code or export the retired package's implementation.
        module=sys.modules[name]
        assert record['package'] and module.__file__ is None,(name,module.__file__)
        assert not getattr(module,'__all__',[]),name
'''
    result = subprocess.run([sys.executable, '-c', code, str(MANIFEST)], capture_output=True,
                            text=True, timeout=40)
    assert result.returncode == 0, result.stderr


def test_public_package_exports_keep_native_object_identity():
    code = '''import ast,importlib,json,sys
from pathlib import Path
for name,record in json.loads(Path(sys.argv[1]).read_text())['retained'].items():
    if record['kind']!='package_exports':continue
    public=importlib.import_module(name)
    # A public facade can re-export several owners; its package owner is not
    # necessarily an omnibus API (Snakemake deliberately has a light root).
    for node in ast.walk(ast.parse(Path(public.__file__).read_text())):
        if not isinstance(node,ast.ImportFrom) or not (node.module or '').startswith('geoagent_harness.'):continue
        for imported in node.names:
            symbol=imported.asname or imported.name
            if symbol in getattr(public,'__all__',[]):
                assert getattr(public,symbol) is getattr(importlib.import_module(node.module),imported.name),(name,symbol)
'''
    result = subprocess.run([sys.executable, '-c', code, str(MANIFEST)], capture_output=True,
                            text=True, timeout=40)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('source', [
    'import geoagent_harness.write_policy as policy',
    'from geoagent_harness import write_policy',
    'from geoagent_harness.write_policy import session',
    "importlib.import_module('geoagent_harness.write_policy')",
])
def test_new_callers_cannot_reintroduce_retired_imports(source):
    assert legacy_imports(source, {'geoagent_harness.write_policy'}) == [('geoagent_harness.write_policy', 1)]


@pytest.mark.parametrize('fault', ['unclassified', 'changed_owner', 'no_reason', 'reintroduced', 'history', 'contract'])
def test_retirement_manifest_fails_closed(tmp_path, fault):
    meta = tmp_path / 'tests/architecture'
    meta.mkdir(parents=True)
    path = tmp_path / 'src/geoagent_harness/legacy.py'
    path.parent.mkdir(parents=True)
    content = b'"""fixture"""\n'
    original = {'geoagent_harness.legacy': {'owner': 'geoagent_harness.native', 'package': False,
                'kind': 'alias', 'sha256': hashlib.sha256(content).hexdigest()}}
    history = meta / 'r6_module_owners.json'
    history.write_text(json.dumps(original))
    record = {**original['geoagent_harness.legacy'], 'reason': 'Reviewed unused fixture'}
    partition = {'schema_version': 1, 'historical_sha256': hashlib.sha256(history.read_bytes()).hexdigest(),
                 'retained': {}, 'retired': {'geoagent_harness.legacy': record}}
    if fault == 'unclassified':partition['retired'] = {}
    if fault == 'changed_owner':record['owner'] = 'geoagent_harness.other'
    if fault == 'no_reason':record['reason'] = ''
    if fault == 'reintroduced':path.write_bytes(content)
    if fault == 'history':partition['historical_sha256'] = '0' * 64
    if fault == 'contract':
        fixture = tmp_path / 'contract.json'; fixture.write_text('changed')
        partition['preserved_contracts'] = {'contract.json': '0' * 64}
    (meta / 'r11_compatibility.json').write_text(json.dumps(partition))
    with pytest.raises(ValueError):compatibility_owners(tmp_path)


def test_native_implementation_cannot_hide_under_a_public_compatibility_package(tmp_path):
    package = tmp_path / 'src/geoagent_harness'
    (package / 'legacy').mkdir(parents=True)
    (package / '__init__.py').write_text('')
    (package / 'native.py').write_text('')
    facade = package / 'legacy/__init__.py'; facade.write_text('"""Public facade."""\n')
    (package / 'legacy/new_service.py').write_text('def write(): pass\n')
    record = {'owner': 'geoagent_harness.native', 'package': True, 'kind': 'package_exports',
              'sha256': hashlib.sha256(facade.read_bytes()).hexdigest()}
    meta = tmp_path / 'tests/architecture'; meta.mkdir(parents=True)
    history = meta / 'r6_module_owners.json'
    history.write_text(json.dumps({'geoagent_harness.legacy': record}))
    (meta / 'r11_compatibility.json').write_text(json.dumps({'schema_version': 1,
        'historical_sha256': hashlib.sha256(history.read_bytes()).hexdigest(),
        'retained': {'geoagent_harness.legacy': {**record, 'reasons': ['Fixture public API']}}, 'retired': {}}))
    policy = {'schema_version': 1, 'modules': {'geoagent_harness.legacy': 6,
              'geoagent_harness.native': 1}, 'exact_modules': {'geoagent_harness': 0}}
    with pytest.raises(ValueError, match='New implementation under retired'):
        scan(tmp_path, policy)


def test_analytical_image_context_runs_native_profile_without_installed_project(tmp_path):
    """Intercept docker build; exercise its actual minimal bundle under -I -S."""
    binaries = tmp_path / 'bin'; binaries.mkdir()
    dataset = tmp_path / 'dataset/data/input'; dataset.mkdir(parents=True)
    (dataset / 'orders.csv').write_text('region,amount\nNorth,10\nSouth,20\nNorth,30\n')
    fake = binaries / 'docker'
    fake.write_text(f'''#!{sys.executable}
import pathlib,subprocess,sys
context=pathlib.Path(sys.argv[-1])
assert sys.argv[1:4]==['build','--pull=false','--network=none']
assert 'geoagent_harness.workspaces.sandbox.worker' in (context/'Dockerfile').read_text()
code="""import pathlib,sys
sys.path.insert(0,sys.argv[1])
from geoagent_harness.workspaces.sandbox import worker
from geoagent_harness.data.tabular.dataset_profile import inspect_dataset
r=inspect_dataset(pathlib.Path(sys.argv[2]),'orders.csv')
assert r['source_rows']==3
assert next(p for p in r['profiles'] if p['name']=='amount')['numeric']['mean']==20
assert not any(n=='pandas' or n.startswith('geoagent_harness.agents') for n in sys.modules)
print('native-worker-bundle-passed')
"""
subprocess.run([sys.executable,'-I','-S','-c',code,str(context),{str(tmp_path / 'dataset')!r}],check=True)
''')
    fake.chmod(0o700)
    result = subprocess.run(['bash', str(ROOT / 'scripts/build_analytical_worker.sh')], cwd=tmp_path,
                            env={**os.environ, 'PATH': str(binaries) + os.pathsep + os.environ['PATH']},
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert 'native-worker-bundle-passed' in result.stdout
