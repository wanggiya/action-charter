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
)
from geoagent_harness.recipe_proposals.runtime import (
    propose_recipe_with_shared_model,
    propose_and_compile_recipe,
    # propose_recipe_with_shared_model,
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
]

