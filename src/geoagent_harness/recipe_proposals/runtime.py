"""Runtime wiring for proposal-only model generation."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.agent_manifest import (
    load_agent_manifest,
)
from geoagent_harness.model import (
    SharedModelClient,
    load_model_settings,
)
from geoagent_harness.recipe_proposals.agent import (
    ProposalModelClientProtocol,
    generate_recipe_proposal,
)
from geoagent_harness.recipe_proposals.schemas import (
    RecipeCompilationResult,
    RecipeOperatorReview,
    RecipeProposalGenerationResult,
    RecipeProposalPipelineResult,
)

from geoagent_harness.recipe_proposals.compiler import (
    compile_recipe_proposal,
)
from geoagent_harness.recipe_proposals.schemas import (
    RecipeCompilationResult,
    RecipeProposalGenerationResult,
    RecipeProposalPipelineResult,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)
from geoagent_harness.recipe_proposals.assessment import (
    assess_recipe_proposal,
)


def propose_recipe_with_shared_model(
    *,
    original_request: str,
    agents_root: Path = Path("agents"),
    model_client: (
        ProposalModelClientProtocol | None
    ) = None,
) -> RecipeProposalGenerationResult:
    """Generate a proposal through the Planner boundary."""

    manifest = load_agent_manifest(
        "planner",
        agents_root,
    )

    active_client = model_client

    if active_client is None:
        active_client = SharedModelClient(
            load_model_settings()
        )

    return generate_recipe_proposal(
        original_request=original_request,
        manifest=manifest,
        model_client=active_client,
    )

def propose_and_compile_recipe(
    *,
    original_request: str,
    project_root: Path = Path("."),
    agents_root: Path = Path("agents"),
    model_client: (
        ProposalModelClientProtocol | None
    ) = None,
) -> RecipeProposalPipelineResult:
    """Generate, assess, and compile without saving."""

    generation = (
        propose_recipe_with_shared_model(
            original_request=original_request,
            agents_root=agents_root,
            model_client=model_client,
        )
    )

    registry = load_skill_registry(
        project_root
    )

    compilation = compile_recipe_proposal(
        generation.proposal,
        registry=registry,
    )

    return RecipeProposalPipelineResult(
        generation=generation,
        compilation=compilation,
        proposal_generated=True,
        proposal_assessed=True,
        compilation_performed=True,
        recipe_saved=False,
        approval_performed=False,
        execution_performed=False,
    )

def review_recipe_request(
    *,
    original_request: str,
    project_root: Path = Path("."),
    agents_root: Path = Path("agents"),
    model_client: (
        ProposalModelClientProtocol | None
    ) = None,
) -> RecipeOperatorReview:
    """Generate a proposal and stop at operator review."""

    generation = (
        propose_recipe_with_shared_model(
            original_request=original_request,
            agents_root=agents_root,
            model_client=model_client,
        )
    )

    registry = load_skill_registry(
        project_root
    )

    assessment = assess_recipe_proposal(
        generation.proposal,
        registry=registry,
    )

    if not assessment.ready_for_compilation:
        return RecipeOperatorReview(
            status="clarification_required",
            generation=generation,
            assessment=assessment,
            compilation=None,
            clarification_questions=(
                assessment.clarification_questions
            ),
            proposal_generated=True,
            assessment_performed=True,
            compilation_performed=False,
            recipe_saved=False,
            approval_performed=False,
            execution_performed=False,
        )

    compilation = compile_recipe_proposal(
        generation.proposal,
        registry=registry,
    )

    return RecipeOperatorReview(
        status="ready_for_operator_review",
        generation=generation,
        assessment=assessment,
        compilation=compilation,
        clarification_questions=[],
        proposal_generated=True,
        assessment_performed=True,
        compilation_performed=True,
        recipe_saved=False,
        approval_performed=False,
        execution_performed=False,
    )
