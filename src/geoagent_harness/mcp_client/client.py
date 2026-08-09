"""Narrow Streamable HTTP MCP client."""

from __future__ import annotations

import json
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import (
    streamable_http_client,
)
from mcp.types import TextContent

from geoagent_harness.mcp_client.schemas import (
    MCPToolCallResult,
)
from geoagent_harness.mcp_client.settings import (
    MCPClientSettings,
)

READ_ONLY_TOOL_ALLOWLIST = frozenset(
    {
        "health_check",
        "inspect_vector_dataset",
        "plan_load_vector_to_postgis",
    }
)


class MCPClientError(RuntimeError):
    """Raised when internal MCP communication fails."""


def _structured_result(
    result: Any,
) -> dict:
    structured = result.structuredContent

    if isinstance(structured, dict):
        return structured

    for content in result.content:
        if isinstance(content, TextContent):
            try:
                parsed = json.loads(content.text)
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, dict):
                return parsed

    raise MCPClientError(
        "MCP tool returned no structured result"
    )


class MCPReadOnlyClient:
    """Call only non-executing MCP tools."""

    def __init__(
        self,
        settings: MCPClientSettings,
    ) -> None:
        self._settings = settings

    async def list_tools(self) -> list[str]:
        """List server tools without invoking them."""

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.timeout_seconds,
            ) as http_client:
                async with streamable_http_client(
                    self._settings.url,
                    http_client=http_client,
                ) as (
                    read_stream,
                    write_stream,
                    _,
                ):
                    async with ClientSession(
                        read_stream,
                        write_stream,
                    ) as session:
                        await session.initialize()
                        response = await session.list_tools()

                        return sorted(
                            tool.name
                            for tool in response.tools
                        )
        except MCPClientError:
            raise
        except Exception as exc:
            raise MCPClientError(
                "Internal MCP service is unavailable"
            ) from exc

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPToolCallResult:
        """Call one explicitly read-only tool."""

        if tool_name not in READ_ONLY_TOOL_ALLOWLIST:
            raise MCPClientError(
                f"MCP tool is not allowed by the "
                f"read-only client: {tool_name}"
            )

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.timeout_seconds,
            ) as http_client:
                async with streamable_http_client(
                    self._settings.url,
                    http_client=http_client,
                ) as (
                    read_stream,
                    write_stream,
                    _,
                ):
                    async with ClientSession(
                        read_stream,
                        write_stream,
                    ) as session:
                        await session.initialize()

                        response = await session.call_tool(
                            tool_name,
                            arguments=arguments or {},
                        )

                        if response.isError:
                            raise MCPClientError(
                                "MCP tool returned an error"
                            )

                        return MCPToolCallResult(
                            tool_name=tool_name,
                            result=_structured_result(
                                response
                            ),
                        )
        except MCPClientError:
            raise
        except Exception as exc:
            raise MCPClientError(
                "Internal MCP service is unavailable"
            ) from exc