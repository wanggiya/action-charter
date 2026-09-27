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
