"""Fail-closed MCP transport configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict


class MCPTransportError(ValueError):
    """Raised when MCP transport configuration is invalid."""


class MCPTransportSettings(BaseModel):
    """Trusted MCP server network settings."""

    model_config = ConfigDict(extra="forbid")

    transport: Literal[
        "stdio",
        "streamable-http",
    ] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    path: Literal["/mcp"] = "/mcp"


def load_transport_settings(
    environ: Mapping[str, str] | None = None,
) -> MCPTransportSettings:
    """Load a narrow set of MCP transport settings."""

    values = os.environ if environ is None else environ

    transport = values.get(
        "GEOAGENT_MCP_TRANSPORT",
        "stdio",
    ).strip()

    if transport not in {
        "stdio",
        "streamable-http",
    }:
        raise MCPTransportError(
            "GEOAGENT_MCP_TRANSPORT must be "
            "stdio or streamable-http"
        )

    host = values.get(
        "GEOAGENT_MCP_HOST",
        "127.0.0.1",
    ).strip()

    if host not in {
        "127.0.0.1",
        "0.0.0.0",
    }:
        raise MCPTransportError(
            "GEOAGENT_MCP_HOST is not allowed"
        )

    try:
        port = int(
            values.get(
                "GEOAGENT_MCP_PORT",
                "8000",
            )
        )
    except ValueError as exc:
        raise MCPTransportError(
            "GEOAGENT_MCP_PORT must be an integer"
        ) from exc

    if port < 1024 or port > 65535:
        raise MCPTransportError(
            "GEOAGENT_MCP_PORT must be between "
            "1024 and 65535"
        )

    path = values.get(
        "GEOAGENT_MCP_PATH",
        "/mcp",
    ).strip()

    if path != "/mcp":
        raise MCPTransportError(
            "GEOAGENT_MCP_PATH must be /mcp"
        )

    return MCPTransportSettings(
        transport=transport,
        host=host,
        port=port,
        path=path,
    )