"""Structured MCP client results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MCPToolCallResult(BaseModel):
    """One validated MCP tool response."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    result: dict