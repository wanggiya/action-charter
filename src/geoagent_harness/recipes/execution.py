"""Deterministic handoff for approved recipe execution."""

from __future__ import annotations

from geoagent_harness.recipes.approval import (
    RecipeApprovalError,
    verify_recipe_approval,
)
from geoagent_harness.recipes.digest import (
    recipe_sha256,
)
from geoagent_harness.recipes.policy import (
    RecipePolicyError,
    validate_recipe_policy,
)
from geoagent_harness.recipes.schemas import (
    RecipeApprovalRecord,
    RecipeExecutionEnvelope,
    RecipeExecutionStep,
    WorkflowRecipe,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)


class RecipeExecutionPolicyError(ValueError):
    """Raised when an execution envelope cannot be built."""


def build_recipe_execution_envelope(
    *,
    recipe: WorkflowRecipe,
    approval: RecipeApprovalRecord,
    registry: SkillRegistry,
) -> RecipeExecutionEnvelope:
    """Build a non-executed envelope from exact approval."""

    try:
        policy = validate_recipe_policy(
            recipe,
            registry=registry,
        )
        verification = verify_recipe_approval(
            approval=approval,
            recipe=recipe,
            registry=registry,
        )
    except (
        RecipeApprovalError,
        RecipePolicyError,
    ) as exc:
        raise RecipeExecutionPolicyError(
            "recipe or approval failed policy"
        ) from exc

    if not verification.approved:
        raise RecipeExecutionPolicyError(
            "recipe approval is not valid: "
            f"{verification.reason}"
        )

    steps_by_id = {
        step.step_id: step
        for step in recipe.steps
    }

    ordered_steps = [
        RecipeExecutionStep(
            step_id=step_id,
            skill_id=steps_by_id[
                step_id
            ].skill_id,
            depends_on=steps_by_id[
                step_id
            ].depends_on,
            arguments=steps_by_id[
                step_id
            ].arguments,
            output_ids=steps_by_id[
                step_id
            ].output_ids,
        )
        for step_id in policy.topological_step_ids
    ]

    return RecipeExecutionEnvelope(
        recipe_id=recipe.recipe_id,
        recipe_sha256=recipe_sha256(recipe),
        approval_id=approval.approval_id,
        approved_step_ids=(
            verification.approved_step_ids
        ),
        topological_step_ids=(
            policy.topological_step_ids
        ),
        steps=ordered_steps,
        tool_name="run_approved_recipe",
        execution_performed=False,
    )
