"""Tests for internal MCP client settings."""

import pytest

from geoagent_harness.mcp_client.settings import (
    MCPClientSettingsError,
    load_mcp_client_settings,
)


def test_default_internal_mcp_url() -> None:
    settings = load_mcp_client_settings({})

    assert settings.url == (
        "http://mcp-gis:8000/mcp"
    )
    assert settings.timeout_seconds == 30


@pytest.mark.parametrize(
    "url",
    [
        "https://mcp-gis:8000/mcp",
        "http://example.com:8000/mcp",
        "http://mcp-gis:9000/mcp",
        "http://mcp-gis:8000/unsafe",
        "http://user:password@mcp-gis:8000/mcp",
        "http://mcp-gis:8000/mcp?token=secret",
    ],
)
def test_unsafe_mcp_url_is_rejected(
    url: str,
) -> None:
    with pytest.raises(MCPClientSettingsError):
        load_mcp_client_settings(
            {
                "GEOAGENT_MCP_URL": url,
            }
        )


def test_invalid_timeout_is_rejected() -> None:
    with pytest.raises(
        MCPClientSettingsError,
        match="between",
    ):
        load_mcp_client_settings(
            {
                "GEOAGENT_MCP_TIMEOUT_SECONDS": "500",
            }
        )