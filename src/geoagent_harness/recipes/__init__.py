"""Reusable, deterministic workflow recipes."""

from geoagent_harness.recipes.digest import (
    canonical_recipe_json,
    recipe_sha256,
)
from geoagent_harness.recipes.policy import (
    RecipePolicyError,
    validate_recipe_policy,
)
from geoagent_harness.recipes.schemas import (
    RecipeStep,
    RecipeValidation,
    WorkflowRecipe,
    RecipeApprovalRecord,
    RecipeApprovalVerification,
    RecipeExecutionEnvelope,
    RecipeExecutionStep,
    ConvertVectorRecipeArguments,
    InspectVectorRecipeArguments,
    RecipeStepExecutionResult,
    RecipeRunResult,
    RecipeStepRunResult,
)

from geoagent_harness.recipes.storage import (
    MAX_RECIPE_BYTES,
    RecipeStorageError,
    load_recipe,
    load_recipe_draft,
    recipe_path,
    save_recipe,
)

from geoagent_harness.recipes.approval import (
    MAX_RECIPE_APPROVAL_BYTES,
    RecipeApprovalError,
    create_recipe_approval,
    load_recipe_approval,
    verify_recipe_approval,
)

from geoagent_harness.recipes.execution import (
    RecipeExecutionPolicyError,
    build_recipe_execution_envelope,
)

from geoagent_harness.recipes.evidence_schemas import (
    ArtifactReference,
    ArtifactRole,
    LineageEdge,
    RecipeRunEvidence,
)

from geoagent_harness.recipes.evidence_storage import (
    MAX_RECIPE_EVIDENCE_BYTES,
    RecipeEvidenceStorageError,
    canonical_recipe_evidence_json,
    load_recipe_evidence,
    recipe_evidence_path,
    recipe_evidence_sha256,
    write_recipe_evidence,
    MAX_RECIPE_RUN_RESULT_BYTES,
    load_recipe_run_result,
    canonical_recipe_run_result_json,
    recipe_run_result_path,
    recipe_run_result_sha256,
    write_recipe_run_result,
)



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
]

def __getattr__(name: str):
    """Load GIS execution code only when explicitly requested."""

    if name == "RecipeDispatchError":
        from geoagent_harness.recipes.dispatcher import (
            RecipeDispatchError,
        )

        return RecipeDispatchError

    if name == "dispatch_recipe_step":
        from geoagent_harness.recipes.dispatcher import (
            dispatch_recipe_step,
        )

        return dispatch_recipe_step

    if name == "RecipeRunError":
        from geoagent_harness.recipes.runner import (
            RecipeRunError,
        )

        return RecipeRunError

    if name == "run_approved_recipe":
        from geoagent_harness.recipes.runner import (
            run_approved_recipe,
        )

        return run_approved_recipe
    
    if name in {
        "MAX_EVIDENCE_ARTIFACT_BYTES",
        "RecipeEvidenceError",
        "build_recipe_run_evidence",
    }:
        from geoagent_harness.recipes.evidence import (
            MAX_EVIDENCE_ARTIFACT_BYTES,
            RecipeEvidenceError,
            build_recipe_run_evidence,
        )

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

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
