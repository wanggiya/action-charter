from pathlib import Path
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT_ROOT / "scripts" / "start_actioncharter.sh"


def test_interface_launcher_has_valid_shell_syntax() -> None:
    completed = subprocess.run(
        ["bash", "-n", str(LAUNCHER)], capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_interface_launcher_help_is_non_mutating() -> None:
    completed = subprocess.run(
        ["bash", str(LAUNCHER), "--help"], capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0
    assert "--enable-write-tools" in completed.stdout
    assert "disabled by default" in completed.stdout


def test_interface_launcher_preserves_safe_authority_boundary() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'write_tools=false' in source
    assert 'export ENABLE_WRITE_TOOLS="$write_tools"' in source
    assert "export ALLOW_OVERWRITE=false" in source
    assert 'api_host="127.0.0.1"' in source
    assert 'frontend_host="127.0.0.1"' in source
    assert "docker compose up" not in source
    assert "pnpm install" not in source
    assert "pip install" not in source
    assert "eval " not in source


def test_geoserver_probe_treats_an_http_response_as_reachable() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "probe_http_reachability" in source
    assert "authentication is checked only by related actions" in source
    assert '[[ "$http_status" =~ ^[1-5][0-9][0-9]$ ]]' in source


def test_interface_launcher_rejects_unknown_options() -> None:
    completed = subprocess.run(
        ["bash", str(LAUNCHER), "--unknown"], capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2
    assert "unknown option" in completed.stderr


def test_vite_proxy_tracks_the_selected_api_port() -> None:
    import json
    import os
    import shutil
    import pytest
    if not shutil.which('node') or not (PROJECT_ROOT / 'interface/node_modules/vite').exists():
        pytest.skip('Installed frontend dependencies required for configuration integration')
    code = "import {loadConfigFromFile} from 'vite'; const result = await loadConfigFromFile({command:'serve',mode:'development'},'vite.config.ts'); console.log(JSON.stringify(result.config.server.proxy['/api']));"
    for port, expected in ((None, '8765'), ('8876', '8876')):
        env = dict(os.environ)
        env.pop('INTERFACE_API_PORT', None)
        if port: env['INTERFACE_API_PORT'] = port
        result = subprocess.run(['node', '--input-type=module', '-e', code], cwd=PROJECT_ROOT / 'interface', env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout.strip()) == 'http://127.0.0.1:' + expected
    env['INTERFACE_API_PORT'] = 'not-a-port'
    result = subprocess.run(['node', '--input-type=module', '-e', code], cwd=PROJECT_ROOT / 'interface', env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'must be a valid port' in result.stderr


def env_loader():
    import importlib.util
    spec = importlib.util.spec_from_file_location('local_interface_env', PROJECT_ROOT / 'scripts/local_interface_env.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_dotenv_loads_host_settings_without_importing_authority_or_secrets(tmp_path):
    (tmp_path / '.env').write_text('POSTGRES_DB=geoagent\nPOSTGRES_HOST=postgis\nMODEL_NAME="local model"\nPOSTGRES_PASSWORD=private\nENABLE_WRITE_TOOLS=true\nALLOW_OVERWRITE=true\nGEOAGENT_PROJECT_ROOT=/workspace\nGEOSERVER_PASSWORD_FILE=/run/secrets/geoserver_password\n')
    env = env_loader().local_environment(tmp_path, {})
    assert env['POSTGRES_DB'] == 'geoagent'
    assert env['MODEL_NAME'] == 'local model'
    assert env['POSTGRES_HOST'] == '127.0.0.1'
    assert env['POSTGRES_PASSWORD_FILE'] == str(tmp_path / '.secrets/postgis_password')
    assert env['GEOSERVER_PASSWORD_FILE'] == str(tmp_path / '.secrets/geoserver_password')
    assert not {'POSTGRES_PASSWORD', 'ENABLE_WRITE_TOOLS', 'ALLOW_OVERWRITE', 'GEOAGENT_PROJECT_ROOT'} & env.keys()


def test_terminal_overrides_dotenv_and_relative_secret_paths_resolve_at_project(tmp_path):
    (tmp_path / '.env').write_text('MODEL_NAME=dotenv-model\nPOSTGRES_HOST=postgis\nPOSTGRES_PASSWORD_FILE=other-secret\n')
    env = env_loader().local_environment(tmp_path, {'MODEL_NAME': 'terminal-model', 'POSTGRES_HOST': 'test-db', 'POSTGRES_PASSWORD_FILE': 'custom/password'})
    assert env['MODEL_NAME'] == 'terminal-model' and env['POSTGRES_HOST'] == 'test-db'
    assert env['POSTGRES_PASSWORD_FILE'] == str(tmp_path / 'custom/password')


def test_dotenv_is_data_and_command_substitution_cannot_execute(tmp_path):
    marker = tmp_path / 'executed'
    (tmp_path / '.env').write_text(f'MODEL_NAME="$(touch {marker})"\nMODEL_BASE_URL="http://host.docker.internal:11434/v1"\nGEOSERVER_BASE_URL=http://geoserver:8080/geoserver\n')
    env = env_loader().local_environment(tmp_path, {})
    assert env['MODEL_NAME'].startswith('$(touch') and not marker.exists()
    assert env['MODEL_BASE_URL'] == 'http://127.0.0.1:11434/v1'
    assert env['GEOSERVER_BASE_URL'] == 'http://127.0.0.1:8080/geoserver'


def test_isolated_acceptance_overrides_stay_disabled_with_dotenv(tmp_path):
    (tmp_path / '.env').write_text('POSTGRES_HOST=live-db\nPOSTGRES_PASSWORD_FILE=live-secret\nMODEL_NAME=dotenv-model\n')
    env = env_loader().local_environment(tmp_path, {'POSTGRES_HOST': '127.0.0.1', 'POSTGRES_PORT': '1', 'POSTGRES_PASSWORD_FILE': str(tmp_path / '.missing-postgis-secret')})
    assert env['POSTGRES_HOST'] == '127.0.0.1' and env['POSTGRES_PORT'] == '1'
    assert env['POSTGRES_PASSWORD_FILE'] == str(tmp_path / '.missing-postgis-secret')


def test_missing_dotenv_uses_host_secret_without_printing_password(tmp_path):
    env = env_loader().local_environment(tmp_path, {})
    assert env['POSTGRES_PASSWORD_FILE'] == str(tmp_path / '.secrets/postgis_password')
