"""Relocated catalogs preserve contracts; discovery and registration grant no authority."""
import json
from shutil import copytree

import pytest
from typer.testing import CliRunner

from geoagent_harness.apps.cli.main import app
from geoagent_harness.capabilities.registry.discovery import ScanRequest, scan_libraries
from geoagent_harness.platform.storage.operation_packages import installed_packages
from geoagent_harness.contracts.operation_packages import PackageError, package_sha
from geoagent_harness.capabilities.registry.registry import operation_catalog, argument_models
from geoagent_harness.capabilities.registry.storage import save_scan, read_scan, saved_scans
from geoagent_harness.task_actions import recipe_catalog as recipes
from geoagent_harness.platform.workspace import WorkspaceError
from tests.test_operation_discovery import project, Distribution, install, proposal, stored
from tests.test_workspace_layout import configure


STORES = ('library-discovery', 'operation-packages', 'reusable-recipes')


def snapshot(root):
    # Parsing this source must never import it, either before or after relocation.
    (root / 'fixture_library.py').write_text('raise RuntimeError("MUST NOT IMPORT")\ndef describe(): pass\n')
    report = scan_libraries(ScanRequest(), [Distribution(root, files=['fixture_library.py'])])
    return save_scan(root, report)


def register(root):
    definition = recipes.catalog(root)['recipe_clean_csv'].model_copy(deep=True)
    definition.id = 'recipe_workspace_clean'
    digest = recipes.recipe_digest(definition)
    result = recipes.recipe_action(recipes.RecipeRequest(action='register', definition=definition,
        confirmed_recipe_sha256=digest, confirm_register=True), project_root=root)
    assert result['registered'] and not result['execution_performed']
    return definition


def compose(root, definition):
    return recipes.compose([recipes.RecipeUse(recipe_id=definition.id,
        recipe_sha256=recipes.recipe_digest(definition), alias='clean', parameters={
            'source': 'data/input/sample_orders.csv', 'columns': ['region', 'amount'],
            'fill_values': {'region': 'Unknown'}, 'selected_path': 'data/output/selected.csv',
            'target_path': 'data/output/cleaned.csv'})], root)


def test_external_snapshot_is_searchable_in_cli_without_import_or_install(project, tmp_path_factory):
    state = tmp_path_factory.mktemp('catalog-state') / 'private'
    configure(project, state)
    digest = snapshot(project)
    assert (state / 'library-discovery' / (digest + '.json')).is_file()
    assert not (project / 'library-discovery').exists()
    assert saved_scans(project)['scans'][0]['scan_sha256'] == digest
    result = CliRunner().invoke(app, ['search-library-functions', digest,
        '--project-root', str(project), '--query', 'describe'])
    assert result.exit_code == 0, result.output
    value = json.loads(result.output)
    assert value['match_count'] == 1 and not value['execution_performed']
    assert not value['candidates'][0]['executable']
    assert installed_packages(project) == {}
    assert not (state / 'operation-packages').exists()
    assert state.stat().st_mode & 0o777 == 0o700


def test_relocated_installed_adapter_requires_exact_authority_and_executes(project, tmp_path_factory):
    from geoagent_harness.apps.http import server as api
    from geoagent_harness.task_actions.workflow import WorkflowRequest, prepare_workflow, authorize_workflow, execute_workflow
    state = tmp_path_factory.mktemp('installed-state')
    configure(project, state)
    digest = install(project)
    assert (state / 'operation-packages/ext_order_identity.json').is_file()
    assert not (project / 'operation-packages').exists()
    assert 'ext_order_identity' in argument_models(project)
    extension = next(op for op in operation_catalog(project)['operations'] if op['id'] == 'ext_order_identity')
    assert extension['default_arguments']['package_sha256'] == digest
    assert extension['approval_required'] and extension['validation_required']
    request = stored(project, proposal(digest))
    review = prepare_workflow(request, project_root=project)
    common = {**request.model_dump(), 'confirmed_review_sha256': review['review_sha256']}
    with pytest.raises(api.InterfaceApiError):
        execute_workflow(WorkflowRequest(**{**common, 'action': 'execute_workflow',
            'confirm_execution': True}), project_root=project)
    assert not (project / 'data/output').exists()
    authority = authorize_workflow(WorkflowRequest(**{**common, 'action': 'authorize_workflow',
        'approve_required_steps': True, 'approver': 'temporary-fixture',
        'reason': 'Only isolated CSV fixture outputs'}), project_root=project)
    result = execute_workflow(WorkflowRequest(**{**common, 'action': 'execute_workflow',
        'confirm_execution': True, 'plan_approval_filename': authority['plan_approval_filename'],
        'recipe_approval_filename': authority['recipe_approval_filename']}), project_root=project)
    assert result['status'] == 'validated_success'
    assert result['step_results'][1]['outcome']['package_sha256'] == digest
    assert (project / 'data/output/final.csv').read_text().startswith('order_id,region\n001,north\n')
    assert not (state / 'data').exists()


def test_offline_catalog_copy_preserves_bytes_identity_and_composition(project, tmp_path_factory):
    digest = snapshot(project)
    package_digest = install(project)
    definition = register(project)
    before_plan, before_receipts = compose(project, definition)
    before = {str(path.relative_to(project)): path.read_bytes()
        for store in STORES for path in (project / store).glob('*.json')}
    state = tmp_path_factory.mktemp('copied-catalogs')
    for store in STORES:
        copytree(project / store, state / store)
    configure(project, state)
    assert read_scan(project, digest)['scan_sha256'] == digest
    assert package_sha(installed_packages(project)['ext_order_identity']) == package_digest
    assert recipes.recipe_digest(recipes.catalog(project)[definition.id]) == recipes.recipe_digest(definition)
    after_plan, after_receipts = compose(project, definition)
    assert after_plan == before_plan and after_receipts == before_receipts
    inventory = recipes.recipe_action(recipes.RecipeRequest(action='list'), project_root=project)
    assert any(r['origin'] == 'registered' and r['definition']['id'] == definition.id for r in inventory['recipes'])
    assert not inventory['execution_performed']
    assert all((state / name).read_bytes() == data == (project / name).read_bytes()
        for name, data in before.items())
    assert not (project / 'data/output').exists()
    assert not (state / 'approvals').exists()


@pytest.mark.parametrize('store', STORES)
def test_missing_catalog_copy_is_an_error_not_an_empty_inventory(tmp_path, store):
    legacy = tmp_path / store
    legacy.mkdir()
    (legacy / 'record.json').write_text('{}')
    configure(tmp_path, 'state')
    reader = {'library-discovery': saved_scans, 'operation-packages': installed_packages,
              'reusable-recipes': recipes.catalog}[store]
    with pytest.raises((WorkspaceError, PackageError, OSError), match='migration required'):
        reader(tmp_path)
    assert not (tmp_path / 'state').exists()
    assert (legacy / 'record.json').read_text() == '{}'


def test_empty_catalog_reads_create_no_state_and_keep_builtin_recipes(project):
    configure(project, 'absent-state')
    assert saved_scans(project)['scans'] == []
    assert installed_packages(project) == {}
    assert 'recipe_inspect_csv' in recipes.catalog(project)
    assert not (project / 'absent-state').exists()


@pytest.mark.parametrize('store', STORES)
def test_relocated_catalog_symlinks_are_rejected(project, tmp_path_factory, store):
    state = tmp_path_factory.mktemp('linked-state')
    other = tmp_path_factory.mktemp('other-catalog')
    configure(project, state)
    (state / store).symlink_to(other, target_is_directory=True)
    reader = {'library-discovery': saved_scans, 'operation-packages': installed_packages,
              'reusable-recipes': recipes.catalog}[store]
    with pytest.raises((WorkspaceError, PackageError, OSError), match='symbolic'):
        reader(project)
    assert list(other.iterdir()) == []


def test_relocated_catalog_integrity_still_rejects_changed_records(project, tmp_path_factory):
    state = tmp_path_factory.mktemp('integrity-state')
    configure(project, state)
    digest = snapshot(project)
    install(project)
    definition = register(project)
    path = state / 'library-discovery' / (digest + '.json')
    path.write_text(path.read_text().replace('describe', 'altered'))
    with pytest.raises(ValueError, match='identity'):
        read_scan(project, digest)
    path = state / 'operation-packages/ext_order_identity.json'
    original = path.read_bytes()
    record = json.loads(original)
    record['package']['columns'] = ['amount']
    path.write_text(json.dumps(record))
    with pytest.raises(PackageError, match='digest'):
        installed_packages(project)
    path.write_bytes(original)
    path = state / 'reusable-recipes' / (definition.id + '.json')
    record = json.loads(path.read_text())
    record['operation_contracts_sha256'] = '0' * 64
    path.write_text(json.dumps(record))
    diagnostics = []
    assert definition.id not in recipes.catalog(project, diagnostics)
    assert diagnostics[0]['id'] == definition.id
    assert 'contracts changed' in diagnostics[0]['finding']
