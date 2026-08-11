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

from geoagent_harness.failures import (
    FailureCategory,
    GeoAgentError,
    RetryDisposition,
)
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


class MCPClientError(GeoAgentError):
    """Structured failure from internal MCP communication."""

    @classmethod
    def policy_denied(
        cls,
        tool_name: str,
    ) -> MCPClientError:
        return cls(
            (
                "MCP tool is not allowed by the "
                f"read-only client: {tool_name}"
            ),
            code="mcp_tool_not_allowed",
            category=FailureCategory.POLICY_DENIED,
            retry=RetryDisposition.NEVER,
        )

    @classmethod
    def invalid_response(
        cls,
        message: str,
    ) -> MCPClientError:
        return cls(
            message,
            code="mcp_invalid_response",
            category=(
                FailureCategory.EXTERNAL_RESPONSE_INVALID
            ),
            retry=RetryDisposition.NEVER,
        )

    @classmethod
    def read_tool_error(cls) -> MCPClientError:
        return cls(
            "MCP tool returned an error",
            code="mcp_read_tool_error",
            category=(
                FailureCategory.EXTERNAL_RESPONSE_INVALID
            ),
            retry=RetryDisposition.MANUAL_REVIEW,
        )

    @classmethod
    def read_timeout(cls) -> MCPClientError:
        return cls(
            "Internal MCP read-only request timed out",
            code="mcp_read_timeout",
            category=FailureCategory.TIMEOUT,
            retry=RetryDisposition.SAFE_READ_ONLY,
        )

    @classmethod
    def read_unavailable(cls) -> MCPClientError:
        return cls(
            "Internal MCP service is unavailable",
            code="mcp_read_unavailable",
            category=(
                FailureCategory.DEPENDENCY_UNAVAILABLE
            ),
            retry=RetryDisposition.SAFE_READ_ONLY,
        )

    @classmethod
    def invalid_filename(
        cls,
        *,
        label: str,
    ) -> MCPClientError:
        return cls(
            f"{label} must be a plain JSON filename",
            code="mcp_invalid_filename",
            category=FailureCategory.INVALID_INPUT,
            retry=RetryDisposition.NEVER,
        )

    @classmethod
    def execution_tool_error(
        cls,
    ) -> MCPClientError:
        return cls(
            (
                "Approved workflow MCP tool "
                "returned an error"
            ),
            code="mcp_execution_tool_error",
            category=FailureCategory.EXECUTION_FAILED,
            retry=RetryDisposition.MANUAL_REVIEW,
        )

    @classmethod
    def execution_timeout(cls) -> MCPClientError:
        return cls(
            "Approved workflow MCP request timed out",
            code="mcp_execution_timeout",
            category=FailureCategory.TIMEOUT,
            retry=RetryDisposition.MANUAL_REVIEW,
        )

    @classmethod
    def execution_unavailable(
        cls,
    ) -> MCPClientError:
        return cls(
            "Internal MCP service is unavailable",
            code="mcp_execution_unavailable",
            category=(
                FailureCategory.DEPENDENCY_UNAVAILABLE
            ),
            retry=RetryDisposition.MANUAL_REVIEW,
        )


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

    raise MCPClientError.invalid_response(
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
        except (
            httpx.TimeoutException,
            TimeoutError,
        ) as exc:
            raise MCPClientError.read_timeout() from exc
        except Exception as exc:
            raise MCPClientError.read_unavailable() from exc

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> MCPToolCallResult:
        """Call one explicitly read-only tool."""

        if tool_name not in READ_ONLY_TOOL_ALLOWLIST:
            raise MCPClientError.policy_denied(
                tool_name
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
                            raise (
                                MCPClientError
                                .read_tool_error()
                            )

                        return MCPToolCallResult(
                            tool_name=tool_name,
                            result=_structured_result(
                                response
                            ),
                        )
        except MCPClientError:
            raise
        except (
            httpx.TimeoutException,
            TimeoutError,
        ) as exc:
            raise MCPClientError.read_timeout() from exc
        except Exception as exc:
            raise MCPClientError.read_unavailable() from exc