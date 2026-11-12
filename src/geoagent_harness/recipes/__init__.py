"""Compatibility exports; native code imports the explicit layer owners."""
"""Reusable, deterministic workflow recipes."""

from geoagent_harness.core.ledger.recipe_identity import canonical_recipe_json, recipe_sha256
from geoagent_harness.core.policy.recipe import RecipePolicyError, validate_recipe_policy
from geoagent_harness.contracts.recipes import RecipeStep, RecipeValidation, WorkflowRecipe, RecipeApprovalRecord, RecipeApprovalVerification, RecipeExecutionEnvelope, RecipeExecutionStep, ConvertVectorRecipeArguments, ConvertRasterRecipeArguments, GenerateReportRecipeArguments, InspectVectorRecipeArguments, LoadVectorToPostGISRecipeArguments, RecipeStepExecutionResult, RecipeRunResult, RecipeStepRunResult, RecipeApprovalInventory, RecipeApprovalMatch, InspectRasterRecipeArguments, ValidatePostGISLayerRecipeArguments

from geoagent_harness.core.ledger.recipe_storage import MAX_RECIPE_BYTES, RecipeStorageError, load_recipe, load_recipe_draft, recipe_path, save_recipe

from geoagent_harness.core.policy.recipe_approval import MAX_RECIPE_APPROVAL_BYTES, RecipeApprovalError, create_recipe_approval, load_recipe_approval, verify_recipe_approval

from geoagent_harness.core.policy.recipe_execution import RecipeExecutionPolicyError, build_recipe_execution_envelope

from geoagent_harness.contracts.recipe_evidence import ArtifactReference, ArtifactRole, LineageEdge, RecipeRunEvidence, RecipeExecutionRecord, PersistedRecipeExecutionResult, RecipeExecutionRecord

from geoagent_harness.core.ledger.recipe_evidence import MAX_RECIPE_EVIDENCE_BYTES, RecipeEvidenceStorageError, canonical_recipe_evidence_json, load_recipe_evidence, recipe_evidence_path, recipe_evidence_sha256, write_recipe_evidence, MAX_RECIPE_RUN_RESULT_BYTES, load_recipe_run_result, canonical_recipe_run_result_json, recipe_run_result_path, recipe_run_result_sha256, write_recipe_run_result

from geoagent_harness.capabilities.recipes.execution.inventory import MAX_INVENTORY_APPROVALS, MAX_INVENTORY_RECIPES, RecipeInventoryError, build_recipe_approval_inventory


__all__ = [
    "RecipePolicyError",
    "RecipeStep",
    "RecipeValidation",
    "WorkflowRecipe",
    "canonical_recipe_json",
    "recipe_sha256",
    "validate_recipe_policy",
    "MAX_RECIPE_BYTES",
    "RecipeStorageError",
    "load_recipe",
    "recipe_path",
    "save_recipe",
    "MAX_RECIPE_APPROVAL_BYTES",
    "RecipeApprovalError",
    "RecipeApprovalRecord",
    "RecipeApprovalVerification",
    "create_recipe_approval",
    "load_recipe_approval",
    "verify_recipe_approval",
    "load_recipe_draft",
    "RecipeExecutionEnvelope",
    "RecipeExecutionPolicyError",
    "RecipeExecutionStep",
    "build_recipe_execution_envelope",
    "ConvertVectorRecipeArguments",
    "InspectVectorRecipeArguments",
    "RecipeDispatchError",
    "RecipeStepExecutionResult",
    "dispatch_recipe_step",
    "RecipeRunError",
    "RecipeRunResult",
    "RecipeStepRunResult",
    "run_approved_recipe",
    "ArtifactReference",
    "ArtifactRole",
    "LineageEdge",
    "RecipeRunEvidence",
    "MAX_EVIDENCE_ARTIFACT_BYTES",
    "RecipeEvidenceError",
    "build_recipe_run_evidence",
    "MAX_RECIPE_EVIDENCE_BYTES",
    "RecipeEvidenceStorageError",
    "canonical_recipe_evidence_json",
    "load_recipe_evidence",
    "recipe_evidence_path",
    "recipe_evidence_sha256",
    "write_recipe_evidence",
    "RecipeExecutionRecord",
    "RecipeEvidencePersistenceError",
    "persist_recipe_run",
    "PersistedRecipeExecutionResult",
    "MAX_INVENTORY_APPROVALS",
    "MAX_INVENTORY_RECIPES",
    "RecipeApprovalInventory",
    "RecipeApprovalMatch",
    "RecipeInventoryError",
    "build_recipe_approval_inventory",
    "InspectRasterRecipeArguments",
    "ConvertRasterRecipeArguments",
    "GenerateReportRecipeArguments",
    "LoadVectorToPostGISRecipeArguments",
    "ValidatePostGISLayerRecipeArguments",
]

def __getattr__(name: str):
    """Load GIS execution code only when explicitly requested."""

    if name == "RecipeDispatchError":
        from geoagent_harness.capabilities.recipes.execution.dispatcher import RecipeDispatchError

        return RecipeDispatchError

    if name == "dispatch_recipe_step":
        from geoagent_harness.capabilities.recipes.execution.dispatcher import dispatch_recipe_step

        return dispatch_recipe_step

    if name == "RecipeRunError":
        from geoagent_harness.capabilities.recipes.execution.runner import RecipeRunError

        return RecipeRunError

    if name == "run_approved_recipe":
        from geoagent_harness.capabilities.recipes.execution.runner import run_approved_recipe

        return run_approved_recipe
    
    if name in {
        "MAX_EVIDENCE_ARTIFACT_BYTES",
        "RecipeEvidenceError",
        "build_recipe_run_evidence",
    }:
        from geoagent_harness.capabilities.recipes.execution.evidence import MAX_EVIDENCE_ARTIFACT_BYTES, RecipeEvidenceError, build_recipe_run_evidence

        evidence_exports = {
            "MAX_EVIDENCE_ARTIFACT_BYTES": (
                MAX_EVIDENCE_ARTIFACT_BYTES
            ),
            "RecipeEvidenceError": (
                RecipeEvidenceError
            ),
            "build_recipe_run_evidence": (
                build_recipe_run_evidence
            ),
        }

        return evidence_exports[name]
    
    if name in {
        "RecipeEvidencePersistenceError",
        "persist_recipe_run",
    }:
        from geoagent_harness.capabilities.recipes.execution import evidence_persistence

        return getattr(
            evidence_persistence,
            name,
        )

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
