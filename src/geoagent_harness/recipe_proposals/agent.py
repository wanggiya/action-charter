"""Model boundary for non-executable recipe proposals."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from geoagent_harness.agent_manifest import (
    AgentManifest,
)
from geoagent_harness.model import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.recipe_proposals.prompt import (
    build_recipe_proposal_request,
)
from geoagent_harness.recipe_proposals.schemas import (
    RecipeProposal,
    RecipeProposalGenerationResult,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)


class ProposalModelClientProtocol(Protocol):
    """Narrow proposal-only model capability."""

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        ...


class RecipeProposalAgentError(RuntimeError):
    """Raised when model output cannot be accepted."""


def _validate_manifest(
    manifest: AgentManifest,
) -> None:
    """Require the existing non-executing Planner role."""

    permissions = manifest.permissions

    if manifest.id != "planner":
        raise RecipeProposalAgentError(
            "recipe proposal generation requires "
            "the planner manifest"
        )

    if permissions.tools:
        raise RecipeProposalAgentError(
            "recipe proposal model cannot have tools"
        )

    if permissions.arbitrary_shell:
        raise RecipeProposalAgentError(
            "recipe proposal model cannot use shell"
        )

    if permissions.unrestricted_sql:
        raise RecipeProposalAgentError(
            "recipe proposal model cannot use SQL"
        )

    if permissions.filesystem_write:
        raise RecipeProposalAgentError(
            "recipe proposal model cannot write files"
        )

    if permissions.database_write:
        raise RecipeProposalAgentError(
            "recipe proposal model cannot write "
            "to databases"
        )


def generate_recipe_proposal(
    *,
    original_request: str,
    manifest: AgentManifest,
    model_client: ProposalModelClientProtocol,
) -> RecipeProposalGenerationResult:
    """Generate one schema-valid non-executable proposal."""

    _validate_manifest(manifest)

    request = build_recipe_proposal_request(
        original_request
    )

    model_result = model_client.complete(
        request
    )

    try:
        payload = json.loads(
            model_result.content
        )
    except json.JSONDecodeError as exc:
        raise RecipeProposalAgentError(
            "recipe proposal model returned "
            "invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise RecipeProposalAgentError(
            "recipe proposal model must return "
            "one JSON object"
        )

    try:
        require_supported_schema(
            payload,
            artifact_type=(
                ArtifactType.RECIPE_PROPOSAL
            ),
        )

        proposal = RecipeProposal.model_validate(
            payload
        )
    except (
        ValidationError,
        ValueError,
    ) as exc:
        raise RecipeProposalAgentError(
            "recipe proposal model returned an "
            "invalid proposal schema"
        ) from exc

    if (
        proposal.original_request.strip()
        != original_request.strip()
    ):
        raise RecipeProposalAgentError(
            "recipe proposal changed the original "
            "user request"
        )

    return RecipeProposalGenerationResult(
        model=model_result.model,
        proposal=proposal,
        proposal_schema_validated=True,
        assessment_performed=False,
        compilation_performed=False,
        recipe_saved=False,
        approval_performed=False,
        execution_performed=False,
    )

