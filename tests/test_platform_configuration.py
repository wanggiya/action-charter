"""Configuration parity with temporary roots and explicit synthetic environments."""
import ast
from dataclasses import FrozenInstanceError, replace
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys

import pytest

from geoagent_harness.platform.layout import LayoutConfiguration
from geoagent_harness.platform.configuration import load_configuration
from geoagent_harness.platform.configuration import SETTING_NAMES, selected_model, selected_reasoning
from geoagent_harness.platform.layout import ROOT_ENVIRONMENT
from geoagent_harness.platform.model_settings import ModelSettingsError
from geoagent_harness.platform.settings import authority_workspace_settings, load_settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('old,new', [
    ('mcp_server.settings', 'platform.settings'),
    ('model.settings', 'platform.model_settings'),
    ('mcp_client.settings', 'platform.client_settings'),
    ('snakemake_export.settings', 'platform.replay_settings'),
    ('mcp_server.schemas', 'contracts.tool_results'),
])
def test_legacy_settings_and_contracts_are_the_same_module(old, new):
    assert import_module('geoagent_harness.' + old) is import_module('geoagent_harness.' + new)


@pytest.mark.parametrize('field,environment', [(field, pair[0]) for field, pair in ROOT_ENVIRONMENT.items()])
def test_all_legacy_root_aliases_feed_one_layout(field, environment):
    config = load_configuration({environment: '/fixture/custom-root'})
    assert getattr(config.layout, field) == Path('/fixture/custom-root')
    if hasattr(config.tools, field):
        assert getattr(config.tools, field) == getattr(config.layout, field)
    if hasattr(config.replay, field):
        assert getattr(config.replay, field) == getattr(config.layout, field)


def test_explicit_layout_and_project_arguments_have_precedence():
    layout = replace(LayoutConfiguration(), plan_root=Path('/fixture/plans'),
                     project_root=Path('/fixture/layout-project'))
    config = load_configuration({'GEOAGENT_PLAN_ROOT': '/fixture/environment-plans',
                                 'GEOAGENT_PROJECT_ROOT': '/fixture/environment-project'},
                                layout=layout, project_root=Path('/fixture/explicit-project'))
    assert config.tools.plan_root == Path('/fixture/plans')
    assert config.tools.project_root == config.replay.project_root == Path('/fixture/explicit-project')


def test_snapshots_are_immutable_and_do_not_capture_password_values():
    values = {'MODEL_NAME': 'before', 'POSTGRES_PASSWORD': 'NEVER_CAPTURE',
              'GEOSERVER_PASSWORD': 'NEVER_CAPTURE', 'MODEL_API_KEY': 'NEVER_CAPTURE'}
    config = load_configuration(values)
    values['MODEL_NAME'] = 'after'
    assert config.model.model == 'before'
    assert not {'POSTGRES_PASSWORD', 'GEOSERVER_PASSWORD', 'MODEL_API_KEY'} & config._values.keys()
    assert 'NEVER_CAPTURE' not in repr(config)
    client_view = config.mcp_client
    client_view.url = 'http://localhost:8000/mcp'
    assert config.mcp_client.url == 'http://mcp-gis:8000/mcp'
    with pytest.raises(TypeError):
        config._values['MODEL_NAME'] = 'mutation'
    with pytest.raises(FrozenInstanceError):
        config.layout = LayoutConfiguration()
    with pytest.raises(FrozenInstanceError):
        config.layout.project_root = Path('/mutation')


def test_model_configuration_is_lazy_and_other_groups_validate_independently():
    config = load_configuration({})
    assert not config.tools.enable_write_tools and not config.tools.allow_overwrite
    assert config.replay.recipe_root == config.tools.recipe_root == Path('workflow-recipes')
    assert config.mcp_client.url == 'http://mcp-gis:8000/mcp'
    with pytest.raises(ModelSettingsError, match='MODEL_NAME is required'):
        _ = config.model
    config = load_configuration({'MODEL_NAME': 'fixture', 'POSTGRES_PORT': 'invalid'})
    assert config.model.model == 'fixture'
    with pytest.raises(ValueError):
        _ = config.tools


def test_request_overrides_are_captured_once_and_explicit_mappings_ignore_them(monkeypatch):
    for name in SETTING_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('MODEL_NAME', 'environment-model')
    monkeypatch.setenv('MODEL_REASONING_EFFORT', 'high')
    model_token = selected_model.set('request-model')
    reasoning_token = selected_reasoning.set('none')
    try:
        snapshot = load_configuration()
        assert load_configuration({'MODEL_NAME': 'explicit-model'}).model.model == 'explicit-model'
        assert load_configuration({'MODEL_NAME': 'explicit-model'}).model.reasoning_effort is None
    finally:
        selected_model.reset(model_token)
        selected_reasoning.reset(reasoning_token)
    assert snapshot.model.model == 'request-model'
    assert snapshot.model.reasoning_effort == 'none'
    assert load_configuration().model.model == 'environment-model'
    assert load_configuration().model.reasoning_effort == 'high'
    monkeypatch.setenv('MODEL_NAME', 'new-environment-model')
    assert snapshot.model.model == 'request-model'
    assert load_configuration().model.model == 'new-environment-model'


def test_loading_groups_does_not_read_credentials_or_connect(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Settings loading must not read credential/configuration files')
    monkeypatch.setattr(Path, 'read_text', forbidden)
    config = load_configuration({'MODEL_NAME': 'fixture', 'POSTGRES_PASSWORD_FILE': '/not/a/real/file'})
    assert config.tools.postgres_password_file == Path('/not/a/real/file')
    assert config.model.model == 'fixture'
    assert config.replay.agents_root == Path('agents')
    assert config.mcp_client.timeout_seconds == 30


def test_workspace_resolution_preserves_explicit_roots_and_never_migrates(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    state = tmp_path / 'state'
    (project / 'actioncharter.workspace.json').write_text(json.dumps({'version': 1, 'state_root': str(state)}))
    config = load_configuration({'GEOAGENT_PROJECT_ROOT': str(project),
                                 'GEOAGENT_RECIPE_ROOT': str(tmp_path / 'explicit-recipes')})
    assert config.layout.workspace().state_root == state
    resolved = authority_workspace_settings(config.tools)
    assert resolved.plan_root == state / 'plans'
    assert resolved.recipe_root == tmp_path / 'explicit-recipes'
    assert resolved.input_root == Path('data/input')
    assert not state.exists(), 'Resolving configuration must not copy/create runtime stores'


def test_configuration_imports_do_not_load_transports_or_heavy_clients():
    code = '''import sys
from geoagent_harness.platform import load_configuration
c = load_configuration({'MODEL_NAME':'fixture'})
assert c.model.model == 'fixture'
assert not c.tools.enable_write_tools
assert c.replay.recipe_root == c.tools.recipe_root
assert not {'httpx','mcp','geopandas','rasterio','geoagent_harness.model',
            'geoagent_harness.interface_api.server','geoagent_harness.mcp_server'} & sys.modules.keys()
'''
    result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_live_imports_use_neutral_owners_and_root_parsing_is_centralized():
    forbidden = {'geoagent_harness.mcp_server.settings', 'geoagent_harness.mcp_server.schemas',
                 'geoagent_harness.model.settings', 'geoagent_harness.mcp_client.settings',
                 'geoagent_harness.snakemake_export.settings'}
    for path in (ROOT / 'src/geoagent_harness').rglob('*.py'):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module not in forbidden, (path, node.lineno)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Exact environment-key constants, not historical generated Python strings.
                if node.value.startswith('GEOAGENT_') and node.value.endswith('_ROOT'):
                    assert path.name == 'layout.py' and path.parent.name == 'platform', (path, node.lineno)


def test_tool_default_serialization_and_fixed_result_authority_are_unchanged():
    settings = load_settings({}).model_dump(mode='json')
    assert settings['input_root'] == 'data/input'
    assert settings['state_root'] == 'workflow-state'
    assert settings['project_root'] == '.'
    assert settings['postgres_port'] == 5432
    assert settings['postgres_password_file'] == '/run/secrets/postgis_password'
    assert settings['enable_write_tools'] is False and settings['allow_overwrite'] is False
    from geoagent_harness.contracts.tool_results import LoadVectorPlan
    result = LoadVectorPlan(source='fixture.geojson', source_driver='GeoJSON', source_layers=['fixture'],
                            target_schema='agent_sandbox', target_table='fixture', warnings=[])
    assert result.execution_allowed is False and result.approval_required is True
    with pytest.raises(ValueError):
        LoadVectorPlan(**{**result.model_dump(), 'execution_allowed': True})
