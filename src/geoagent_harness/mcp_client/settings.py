"""Fail-closed settings for the internal MCP client."""

from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict


class MCPClientSettingsError(ValueError):
    """Raised when MCP client settings are unsafe."""


class MCPClientSettings(BaseModel):
    """Trusted connection settings for internal MCP."""

    model_config = ConfigDict(extra="forbid")

    url: str
    timeout_seconds: float


def load_mcp_client_settings(
    environ: Mapping[str, str] | None = None,
) -> MCPClientSettings:
    """Load and validate the internal MCP URL."""

    values = os.environ if environ is None else environ

    url = values.get(
        "GEOAGENT_MCP_URL",
        "http://mcp-gis:8000/mcp",
    ).strip()

    parsed = urlparse(url)

    if parsed.scheme != "http":
        raise MCPClientSettingsError(
            "GEOAGENT_MCP_URL must use internal HTTP"
        )

    if parsed.hostname not in {
        "mcp-gis",
        "127.0.0.1",
        "localhost",
    }:
        raise MCPClientSettingsError(
            "GEOAGENT_MCP_URL host is not allowed"
        )

    if parsed.port != 8000:
        raise MCPClientSettingsError(
            "GEOAGENT_MCP_URL must use port 8000"
        )

    if parsed.path != "/mcp":
        raise MCPClientSettingsError(
            "GEOAGENT_MCP_URL path must be /mcp"
        )

    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise MCPClientSettingsError(
            "GEOAGENT_MCP_URL cannot contain "
            "credentials, query, or fragment"
        )

    try:
        timeout_seconds = float(
            values.get(
                "GEOAGENT_MCP_TIMEOUT_SECONDS",
                "30",
            )
        )
    except ValueError as exc:
        raise MCPClientSettingsError(
            "GEOAGENT_MCP_TIMEOUT_SECONDS "
            "must be numeric"
        ) from exc

    if (
        timeout_seconds <= 0
        or timeout_seconds > 120
    ):
        raise MCPClientSettingsError(
            "GEOAGENT_MCP_TIMEOUT_SECONDS must "
            "be between 0 and 120"
        )

    return MCPClientSettings(
        url=url,
        timeout_seconds=timeout_seconds,
    )