"""Proposal-only Builder Agent model boundary."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from geoagent_harness.agent_manifest import AgentManifest
from geoagent_harness.builder.policy import (
    validate_builder_proposal,
)
from geoagent_harness.builder.prompt import (
    build_builder_request,
)
from geoagent_harness.builder.schemas import (
    BuilderGenerationResult,
    BuilderProposal,
    BuilderRequest,
)
from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)


class BuilderModelClientProtocol(Protocol):
    """Narrow model capability available to the Builder."""

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        ...


class BuilderAgentError(RuntimeError):
    """Raised when Builder output cannot be accepted."""


def _validate_builder_manifest(
    manifest: AgentManifest,
) -> None:
    permissions = manifest.permissions

    if manifest.id != "builder":
        raise BuilderAgentError(
            "Builder Agent requires the builder manifest"
        )

    if permissions.tools:
        raise BuilderAgentError(
            "Builder Agent cannot have executable tools"
        )

    if permissions.arbitrary_shell:
        raise BuilderAgentError(
            "Builder Agent cannot have arbitrary shell access"
        )

    if permissions.unrestricted_sql:
        raise BuilderAgentError(
            "Builder Agent cannot have unrestricted SQL access"
        )

    if permissions.filesystem_write:
        raise BuilderAgentError(
            "Builder Agent cannot have filesystem write access"
        )

    if permissions.database_write:
        raise BuilderAgentError(
            "Builder Agent cannot have database write access"
        )

    if permissions.model_extra:
        raise BuilderAgentError(
            "Builder Agent cannot have additional permissions"
        )


def generate_builder_proposal(
    *,
    request: BuilderRequest,
    manifest: AgentManifest,
    model_client: BuilderModelClientProtocol,
) -> BuilderGenerationResult:
    """Generate one validated, in-memory candidate proposal."""

    _validate_builder_manifest(manifest)

    model_request = build_builder_request(
        request,
        manifest,
    )
    model_result = model_client.complete(model_request)

    try:
        payload = json.loads(model_result.content)
    except json.JSONDecodeError as exc:
        raise BuilderAgentError(
            "Builder model returned invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise BuilderAgentError(
            "Builder model must return one JSON object"
        )

    try:
        proposal = BuilderProposal.model_validate(payload)
    except ValidationError as exc:
        raise BuilderAgentError(
            "Builder model returned an invalid proposal schema"
        ) from exc

    try:
        validate_builder_proposal(request, proposal)
    except ValueError as exc:
        raise BuilderAgentError(
            f"Builder proposal failed deterministic policy: {exc}"
        ) from exc

    return BuilderGenerationResult(
        model=model_result.model,
        request=request,
        proposal=proposal,
    )
