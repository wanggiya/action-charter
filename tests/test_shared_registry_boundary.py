"""R6b2 metadata is fresh, bounded and non-executing; temporary default/relocated roots."""
from importlib import import_module
import json
from pathlib import Path
from shutil import copyfile
import subprocess
import sys

import pytest
import yaml

from geoagent_harness.contracts import operation_packages as package_contracts
from geoagent_harness.platform import skill_registry as registry_reader
from geoagent_harness.platform.storage import operation_packages as package_reader
from geoagent_harness.platform.workspace import ensure_state_root, runtime_store_path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((REPO / 'examples/checkpoint25/order_identity.operation.json').read_text())


@pytest.fixture(params=[False, True], ids=['default-root', 'relocated-root'])
def project(tmp_path, request):
    root = tmp_path / 'project'
    (root / 'context').mkdir(parents=True)
    copyfile(REPO / 'context/SKILLS_INDEX.yaml', root / 'context/SKILLS_INDEX.yaml')
    if request.param:
        (root / 'actioncharter.workspace.json').write_text(json.dumps({
            'version': 1, 'state_root': str(tmp_path / 'state')}))
    return root


def seed_metadata(root):
    """Write a synthetic already-installed record, without testing/installing an operation."""
    ensure_state_root(root)
    directory = runtime_store_path(root, 'operation-packages')
    directory.mkdir(exist_ok=True)
    package = package_contracts.parse_package(MANIFEST)
    path = directory / (package.id + '.json')
    path.write_text(json.dumps({'package': package.model_dump(mode='json'),
        'package_sha256': package_contracts.package_sha(package)}, sort_keys=True, separators=(',', ':')))
    return path, package


@pytest.mark.parametrize('legacy,owner', [
    ('skill_registry.schemas', 'contracts.skill_registry'),
    ('skill_registry.service', 'platform.skill_registry'),
])
def test_registry_legacy_modules_alias_actual_owners(legacy, owner):
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


def test_partial_exports_preserve_class_function_and_exception_identity():
    from geoagent_harness.capabilities.registry import legacy_skills as skill_registry
    from geoagent_harness.contracts import skill_registry as contracts, table_arguments, text_transform
    from geoagent_harness.capabilities.registry import packages
    from geoagent_harness.contracts import tabular as schemas
    from geoagent_harness.data.tabular import text
    for name in ('SkillRegistry', 'SkillDefinition', 'SkillAccess', 'SkillKind', 'SkillStatus'):
        assert getattr(skill_registry, name) is getattr(contracts, name)
    assert skill_registry.load_skill_registry is registry_reader.load_skill_registry
    assert skill_registry.SkillRegistryError is registry_reader.SkillRegistryError
    for name in ('Strict', 'Source', '_source_schema'):
        assert getattr(schemas, name) is getattr(table_arguments, name)
    for name in ('TextStep', 'TextTransform'):
        assert getattr(text, name) is getattr(text_transform, name)
    for name in ('OperationPackage', 'ProjectionArguments', 'Fixture', 'PackageError',
                 'canonical', 'package_sha', 'configuration', 'parse_package'):
        assert getattr(packages, name) is getattr(package_contracts, name)
    for name in ('installed_packages', 'package_skills', '_directory'):
        assert getattr(packages, name) is getattr(package_reader, name)


@pytest.mark.parametrize('module', [
    'contracts.operation_packages', 'contracts.skill_registry',
    'platform.skill_registry', 'platform.storage.operation_packages',
])
def test_metadata_imports_do_not_load_operation_execution_or_agents(module):
    code = f'''import importlib, sys
importlib.import_module('geoagent_harness.{module}')
blocked = ('geoagent_harness.capabilities.registry', 'geoagent_harness.capabilities',
    'geoagent_harness.data.tabular', 'geoagent_harness.data.databases.postgres',
    'geoagent_harness.agents.roles.planner', 'geoagent_harness.agents.roles.executor', 'geoagent_harness.agents.roles.critic',
    'geoagent_harness.platform.model_gateway', 'geoagent_harness.interface_api',
    'geoagent_harness.platform.internal_mcp', 'geoagent_harness.apps.mcp',
    'pandas', 'numpy', 'rasterio', 'geopandas', 'httpx')
assert not [n for n in sys.modules if any(n == p or n.startswith(p + '.') for p in blocked)]
'''
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_each_registry_read_reloads_current_metadata_without_mutating_prior_snapshot(project):
    first = registry_reader.load_skill_registry(project)
    index = project / 'context/SKILLS_INDEX.yaml'
    payload = yaml.safe_load(index.read_text())
    selected = next(skill for skill in payload['skills'] if skill['id'] == 'convert_vector')
    before = first.get_skill('convert_vector').version
    selected['version'] = '9.8.7'
    index.write_text(yaml.safe_dump(payload))
    second = registry_reader.load_skill_registry(project)
    assert second.get_skill('convert_vector').version == '9.8.7'
    assert first.get_skill('convert_vector').version == before
    assert first is not second


def test_registry_metadata_reads_do_not_test_install_or_execute_packages(project, monkeypatch):
    from geoagent_harness.capabilities.registry import packages
    path, package = seed_metadata(project)
    before = path.read_bytes()
    def forbidden(*args, **kwargs):
        pytest.fail('Metadata read invoked package testing, installation or execution')
    for name in ('test_package', 'install_package', 'execute_projection'):
        monkeypatch.setattr(packages, name, forbidden)
    loaded = registry_reader.load_skill_registry(project).get_skill(package.id)
    assert loaded.version == package.version
    assert loaded.entrypoint == 'geoagent_harness.operations.packages:execute_projection'
    assert loaded.verifier == 'geoagent_harness.tabular.service:validate_output'
    assert loaded.approval_required is loaded.validation_required is True
    assert path.read_bytes() == before
    assert not (project / 'data/output').exists()
    assert not runtime_store_path(project, 'approvals').exists()


@pytest.mark.parametrize('mutation', ['digest', 'unknown-field', 'invalid-json'])
def test_invalid_installed_record_blocks_registry_before_approval_or_execution(project, mutation):
    path, _ = seed_metadata(project)
    value = json.loads(path.read_text())
    if mutation == 'digest':
        value['package_sha256'] = '0' * 64
    elif mutation == 'unknown-field':
        value['package']['entrypoint'] = 'os:system'
    path.write_text('{' if mutation == 'invalid-json' else json.dumps(value))
    before = path.read_bytes()
    with pytest.raises(registry_reader.SkillRegistryError, match='packages failed validation'):
        registry_reader.load_skill_registry(project)
    assert path.read_bytes() == before
    assert not runtime_store_path(project, 'approvals').exists()
    assert not (project / 'data/output').exists()


@pytest.mark.parametrize('mutation', ['symlink-file', 'symlink-directory', 'oversized'])
def test_metadata_reader_retains_no_follow_and_byte_bounds(project, mutation):
    path, _ = seed_metadata(project)
    before = path.read_bytes()
    outside = project / 'outside.json'
    outside.write_bytes(before)
    if mutation == 'symlink-file':
        path.unlink()
        path.symlink_to(outside)
    elif mutation == 'symlink-directory':
        moved = path.parent.with_name('moved-packages')
        path.parent.rename(moved)
        path.parent.symlink_to(moved, target_is_directory=True)
    else:
        path.write_bytes(b' ' * (package_reader.MAX_BYTES + 1))
    with pytest.raises(package_contracts.PackageError):
        package_reader.installed_packages(project)
    assert outside.read_bytes() == before


def test_legacy_registry_limit_patch_reaches_native_reader(project, monkeypatch):
    legacy = import_module('geoagent_harness.platform.skill_registry')
    monkeypatch.setattr(legacy, 'MAX_SKILL_REGISTRY_BYTES', 1)
    with pytest.raises(registry_reader.SkillRegistryError, match='size limit'):
        registry_reader.load_skill_registry(project)


def test_approval_reloads_registry_and_cannot_use_removed_operation(project):
    from datetime import timedelta
    from geoagent_harness.core.policy.approvals.service import create_approval, verify_approval
    from geoagent_harness.core.policy.plan import PlannerPolicyError
    from tests.test_approval_service import planner_result, NOW
    proposal = planner_result()
    root = runtime_store_path(project, 'approvals')
    args = dict(planner_result=proposal, step_ids=['step_2'], decision='approved',
        approver='fixture', reason='Only temporary authority records; no data execution',
        approval_root=root, project_root=project, now=NOW, expires_at=NOW + timedelta(minutes=30))
    first, path = create_approval(**args, approval_id='approval-20260809t120000z-1234abcd')
    before = path.read_bytes()
    assert verify_approval(approval=first, plan=proposal.plan, required_step_ids=['step_2'], now=NOW).approved
    assert not verify_approval(approval=first, plan=proposal.plan, required_step_ids=['step_2'], now=NOW + timedelta(minutes=31)).approved
    changed = proposal.plan.model_copy(deep=True)
    changed.steps[1].arguments['target_table'] = 'another_table'
    assert not verify_approval(approval=first, plan=changed, required_step_ids=['step_2'], now=NOW).approved
    index = project / 'context/SKILLS_INDEX.yaml'
    payload = yaml.safe_load(index.read_text())
    payload['skills'] = [s for s in payload['skills'] if s['id'] != 'load_vector_to_postgis']
    index.write_text(yaml.safe_dump(payload))
    with pytest.raises(PlannerPolicyError, match='not implemented and approved'):
        create_approval(**args, approval_id='approval-20260809t120000z-1234abce')
    assert path.read_bytes() == before
    assert list(root.iterdir()) == [path]
    assert not (project / 'data/output').exists()


def test_new_process_reopens_same_verified_package_without_installation(project):
    path, package = seed_metadata(project)
    code = "import sys\nfrom pathlib import Path\nfrom geoagent_harness.platform.skill_registry import load_skill_registry\nfrom geoagent_harness.platform.storage.operation_packages import installed_packages\nfrom geoagent_harness.contracts.operation_packages import package_sha\nroot = Path(sys.argv[1])\nassert load_skill_registry(root).get_skill(sys.argv[2]).version == sys.argv[3]\nassert package_sha(installed_packages(root)[sys.argv[2]]) == sys.argv[4]\nassert 'geoagent_harness.operations.packages' not in sys.modules\n"
    result = subprocess.run([sys.executable, '-c', code, str(project), package.id,
        package.version, package_contracts.package_sha(package)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert path.is_file()
    assert not (project / 'data/output').exists()
