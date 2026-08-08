"""Structured schemas for model requests and responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """One OpenAI-compatible chat message."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ModelRequest(BaseModel):
    """Validated request sent to the shared model runtime."""

    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    json_mode: bool = False


class ModelResult(BaseModel):
    """Redacted result returned by the shared model client."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["ollama-openai-compatible"] = (
        "ollama-openai-compatible"
    )
    model: str
    content: str
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None