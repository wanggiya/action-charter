"""Tests for MCP transport configuration."""

from __future__ import annotations

import asyncio

import pytest

from geoagent_harness.mcp_server import tools

from geoagent_harness.mcp_server.server import (
    create_mcp_server,
)
from geoagent_harness.mcp_server.transport import (
    MCPTransportError,
    load_transport_settings,
)


def test_transport_defaults_to_stdio() -> None:
    settings = load_transport_settings({})

    assert settings.transport == "stdio"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.path == "/mcp"


def test_streamable_http_configuration() -> None:
    settings = load_transport_settings(
        {
            "GEOAGENT_MCP_TRANSPORT": (
                "streamable-http"
            ),
            "GEOAGENT_MCP_HOST": "0.0.0.0",
            "GEOAGENT_MCP_PORT": "8000",
            "GEOAGENT_MCP_PATH": "/mcp",
        }
    )

    assert settings.transport == (
        "streamable-http"
    )
    assert settings.host == "0.0.0.0"


@pytest.mark.parametrize(
    "transport",
    [
        "sse",
        "http",
        "websocket",
        "shell",
    ],
)
def test_unapproved_transport_is_rejected(
    transport: str,
) -> None:
    with pytest.raises(
        MCPTransportError,
        match="stdio or streamable-http",
    ):
        load_transport_settings(
            {
                "GEOAGENT_MCP_TRANSPORT": transport,
            }
        )


def test_unapproved_host_is_rejected() -> None:
    with pytest.raises(
        MCPTransportError,
        match="HOST",
    ):
        load_transport_settings(
            {
                "GEOAGENT_MCP_HOST": "192.168.1.10",
            }
        )


def test_privileged_port_is_rejected() -> None:
    with pytest.raises(
        MCPTransportError,
        match="between",
    ):
        load_transport_settings(
            {
                "GEOAGENT_MCP_PORT": "80",
            }
        )


def test_custom_path_is_rejected() -> None:
    with pytest.raises(
        MCPTransportError,
        match="/mcp",
    ):
        load_transport_settings(
            {
                "GEOAGENT_MCP_PATH": "/unsafe",
            }
        )


def test_created_server_preserves_tool_allowlist() -> None:
    server = create_mcp_server()
    registered = asyncio.run(server.list_tools())

    names = sorted(
        tool.name
        for tool in registered
    )

    assert names == sorted(
        tools.TOOL_ALLOWLIST
    )