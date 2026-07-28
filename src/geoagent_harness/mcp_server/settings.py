"""Fail-closed configuration for the read-only MCP boundary."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off", ""})


def parse_flag(value: str | None, *, default: bool = False) -> bool:
    """Parse a Boolean without enabling access for an unknown value."""
    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in _TRUE_VALUES:
        return True

    if normalized in _FALSE_VALUES:
        return False

    # Misspelled or unexpected values fail closed.
    return False


def validate_identifier(value: str, *, label: str) -> str:
    """Validate a conservative PostgreSQL identifier."""
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(
            f"{label} must match {_IDENTIFIER.pattern!r}; "
            f"received {value!r}"
        )

    return value


class MCPSettings(BaseModel):
    """Non-secret settings available to MCP tools."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_root: Path
    output_root: Path
    enable_write_tools: bool = False
    allow_overwrite: bool = False
    allowed_schemas: frozenset[str] = Field(
        default_factory=lambda: frozenset({"agent_sandbox"})
    )

    @field_validator("allowed_schemas")
    @classmethod
    def schemas_are_safe(
        cls,
        value: frozenset[str],
    ) -> frozenset[str]:
        if not value:
            raise ValueError("at least one allowed schema is required")

        for schema in value:
            validate_identifier(schema, label="schema")

        return value


def load_settings(
    environ: Mapping[str, str] | None = None,
) -> MCPSettings:
    """Load settings from a mapping or the process environment."""
    source = os.environ if environ is None else environ

    raw_schemas = source.get(
        "ALLOWED_SCHEMAS",
        "agent_sandbox",
    )

    schemas = frozenset(
        item.strip()
        for item in raw_schemas.split(",")
        if item.strip()
    )

    return MCPSettings(
        input_root=Path(
            source.get(
                "GEOAGENT_INPUT_ROOT",
                "data/input",
            )
        ),
        output_root=Path(
            source.get(
                "GEOAGENT_OUTPUT_ROOT",
                "data/output",
            )
        ),
        enable_write_tools=parse_flag(
            source.get("ENABLE_WRITE_TOOLS"),
            default=False,
        ),
        allow_overwrite=parse_flag(
            source.get("ALLOW_OVERWRITE"),
            default=False,
        ),
        allowed_schemas=schemas,
    )