"""Read and validate a logical agent's static manifest."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class AgentPermissions(BaseModel):
    """Known manifest permissions; additional explicit permissions are retained."""

    model_config = ConfigDict(extra="allow")

    tools: list[str] = Field(default_factory=list)
    arbitrary_shell: bool = False
    unrestricted_sql: bool = False
    filesystem_write: bool = False
    database_write: bool = False


class AgentManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Literal["planner", "executor", "critic"]
    model_ref: str
    purpose: str
    permissions: AgentPermissions
    instructions: list[str] = Field(min_length=1)


def load_agent_manifest(role: str, agents_root: Path = Path("/app/agents")) -> AgentManifest:
    """Load only a known role; callers cannot supply an arbitrary manifest path."""
    if role not in {"planner", "executor", "critic"}:
        raise ValueError(f"unknown agent role: {role}")

    path = agents_root / role / "manifest.yaml"
    payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest = AgentManifest.model_validate(payload)
    if manifest.id != role:
        raise ValueError(f"manifest id {manifest.id!r} does not match role {role!r}")
    return manifest

