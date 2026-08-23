"""Non-executable recipe proposal boundary."""

from geoagent_harness.recipe_proposals.assessment import (
    assess_recipe_proposal,
)
from geoagent_harness.recipe_proposals.templates import (
    RecipeTemplateDefinition,
    RecipeTemplateError,
    get_recipe_template,
    list_recipe_templates,
)

from geoagent_harness.recipe_proposals.compiler import (
    RecipeCompilationError,
    compile_recipe_proposal,
)

from geoagent_harness.recipe_proposals.storage import (
    MAX_RECIPE_PROPOSAL_BYTES,
    RecipeProposalStorageError,
    load_recipe_proposal,
)

from geoagent_harness.recipe_proposals.schemas import (
    ConvertVectorProposalParameters,
    ConvertVectorTemplateSelection,
    InspectVectorProposalParameters,
    InspectVectorTemplateSelection,
    RecipeProposal,
    RecipeTemplateSelection,
    VectorPostGISProposalParameters,
    VectorPostGISTemplateSelection,
    RecipeProposalAssessment,
    RecipeCompilationResult,
    InspectRasterProposalParameters,
    InspectRasterTemplateSelection,
)
from geoagent_harness.recipe_proposals.agent import (
    ProposalModelClientProtocol,
    RecipeProposalAgentError,
    generate_recipe_proposal,
)
from geoagent_harness.recipe_proposals.prompt import (
    build_recipe_proposal_request,
)
from geoagent_harness.recipe_proposals.schemas import (
    RecipeProposalGenerationResult,
    RecipeProposalPipelineResult,
    RecipeOperatorReview,
    RecipeOperatorSaveResult,
)
from geoagent_harness.recipe_proposals.runtime import (
    propose_recipe_with_shared_model,
    propose_and_compile_recipe,
    # propose_recipe_with_shared_model,
    review_recipe_request,
)
from geoagent_harness.recipe_proposals.rendering import (
    render_recipe_operator_review,
)
from geoagent_harness.recipe_proposals.operator_save import (
    RecipeOperatorSaveError,
    save_reviewed_recipe,
)
from geoagent_harness.recipe_proposals.review_storage import (
    MAX_RECIPE_REVIEW_BYTES,
    RecipeReviewStorageError,
    load_recipe_operator_review,
)


__all__ = [
    "ConvertVectorProposalParameters",
    "ConvertVectorTemplateSelection",
    "InspectVectorProposalParameters",
    "InspectVectorTemplateSelection",
    "RecipeProposal",
    "RecipeTemplateSelection",
    "VectorPostGISProposalParameters",
    "VectorPostGISTemplateSelection",
    "RecipeProposalAssessment",
    "RecipeTemplateDefinition",
    "RecipeTemplateError",
    "assess_recipe_proposal",
    "get_recipe_template",
    "list_recipe_templates",
    "RecipeCompilationError",
    "RecipeCompilationResult",
    "compile_recipe_proposal",
    "MAX_RECIPE_PROPOSAL_BYTES",
    "RecipeProposalStorageError",
    "load_recipe_proposal",
    "ProposalModelClientProtocol",
    "RecipeProposalAgentError",
    "RecipeProposalGenerationResult",
    "build_recipe_proposal_request",
    "generate_recipe_proposal",
    "propose_recipe_with_shared_model",
    "RecipeProposalPipelineResult",
    "propose_and_compile_recipe",
    "RecipeOperatorReview",
    "review_recipe_request",
    "render_recipe_operator_review",
    "MAX_RECIPE_REVIEW_BYTES",
    "RecipeOperatorSaveError",
    "RecipeOperatorSaveResult",
    "RecipeReviewStorageError",
    "load_recipe_operator_review",
    "save_reviewed_recipe",
    "InspectRasterProposalParameters",
    "InspectRasterTemplateSelection",
]

