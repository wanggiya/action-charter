"""Static policy tests for internal MCP HTTP transport."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_compose() -> dict[str, Any]:
    return yaml.safe_load(
        (
            PROJECT_ROOT / "compose.yaml"
        ).read_text(encoding="utf-8")
    )


def test_mcp_uses_streamable_http() -> None:
    service = load_compose()["services"]["mcp-gis"]
    environment = service["environment"]

    assert environment[
        "GEOAGENT_MCP_TRANSPORT"
    ] == "streamable-http"
    assert environment[
        "GEOAGENT_MCP_HOST"
    ] == "0.0.0.0"
    assert environment[
        "GEOAGENT_MCP_PORT"
    ] == 8000
    assert environment[
        "GEOAGENT_MCP_PATH"
    ] == "/mcp"


def test_mcp_port_is_not_published_to_host() -> None:
    service = load_compose()["services"]["mcp-gis"]

    assert service["expose"] == ["8000"]
    assert "ports" not in service


def test_mcp_remains_on_control_and_backend() -> None:
    service = load_compose()["services"]["mcp-gis"]

    assert set(service["networks"]) == {
        "control",
        "backend",
    }


def test_control_network_is_internal() -> None:
    compose = load_compose()

    assert compose["networks"]["control"][
        "internal"
    ] is True


def test_write_tools_remain_fail_closed() -> None:
    service = load_compose()["services"]["mcp-gis"]
    environment = service["environment"]

    assert (
        environment["ENABLE_WRITE_TOOLS"]
        == "${ENABLE_WRITE_TOOLS:-false}"
    )
    assert (
        environment["ALLOW_OVERWRITE"]
        == "${ALLOW_OVERWRITE:-false}"
    )
    
def test_executor_has_only_control_network() -> None:
    compose = load_compose()
    executor = compose["services"]["executor"]

    assert set(executor["networks"]) == {
        "control",
    }

    assert "backend" not in executor["networks"]
    assert "model" not in executor["networks"]
    assert "secrets" not in executor

    environment = executor["environment"]

    assert environment["GEOAGENT_MCP_URL"] == (
        "http://mcp-gis:8000/mcp"
    )

    assert all(
        not str(key).startswith("POSTGRES_")
        for key in environment
    )

    assert all(
        not str(key).startswith("MODEL_")
        for key in environment
    )
    
def test_executor_mounts_only_control_records() -> None:
    compose = load_compose()
    executor = compose["services"]["executor"]

    volumes = executor["volumes"]

    assert all(
        str(volume).endswith(":ro")
        for volume in volumes
    )

    serialized = "\n".join(
        str(volume)
        for volume in volumes
    )

    assert "agents/executor" in serialized
    assert "/workspace/plans" in serialized
    assert "/workspace/approvals" in serialized

    assert "data/input" not in serialized
    assert "data/output" not in serialized
    assert "reports" not in serialized
    assert "traces" not in serialized
    assert "postgis_password" not in serialized
    assert "docker.sock" not in serialized