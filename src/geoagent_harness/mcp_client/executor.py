"""Dedicated MCP client for one approved workflow tool."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import (
    streamable_http_client,
)
from mcp.types import TextContent

from geoagent_harness.executor.schemas import (
    ExecutionEnvelope,
)
from geoagent_harness.mcp_client.client import (
    MCPClientError,
)
from geoagent_harness.mcp_client.schemas import (
    MCPToolCallResult,
)
from geoagent_harness.mcp_client.settings import (
    MCPClientSettings,
)

APPROVED_WORKFLOW_TOOL = (
    "run_approved_vector_postgis_workflow"
)


def _plain_json_filename(
    value: str,
    *,
    label: str,
) -> str:
    path = Path(value)

    if (
        path.name != value
        or path.suffix != ".json"
        or value in {".json", ".."}
    ):
        raise MCPClientError(
            f"{label} must be a plain JSON filename"
        )

    return value


def _structured_result(response) -> dict:
    if isinstance(
        response.structuredContent,
        dict,
    ):
        return response.structuredContent

    for content in response.content:
        if isinstance(content, TextContent):
            try:
                value = json.loads(content.text)
            except json.JSONDecodeError:
                continue

            if isinstance(value, dict):
                return value

    raise MCPClientError(
        "Approved workflow returned no structured result"
    )


class MCPExecutorClient:
    """Call only the server-verified composite workflow."""

    def __init__(
        self,
        settings: MCPClientSettings,
    ) -> None:
        self._settings = settings

    async def execute_approved_workflow(
        self,
        *,
        envelope: ExecutionEnvelope,
        plan_filename: str,
        approval_filename: str,
    ) -> MCPToolCallResult:
        """Call the single approval-gated MCP tool."""

        safe_plan = _plain_json_filename(
            plan_filename,
            label="plan_filename",
        )
        safe_approval = _plain_json_filename(
            approval_filename,
            label="approval_filename",
        )

        arguments = {
            "execution_envelope": (
                envelope.model_dump(mode="json")
            ),
            "plan_filename": safe_plan,
            "approval_filename": safe_approval,
        }

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
                            APPROVED_WORKFLOW_TOOL,
                            arguments=arguments,
                        )

                        if response.isError:
                            raise MCPClientError(
                                "Approved workflow MCP tool "
                                "returned an error"
                            )

                        return MCPToolCallResult(
                            tool_name=(
                                APPROVED_WORKFLOW_TOOL
                            ),
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