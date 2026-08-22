"""Explicit promotion of reviewed recipes to storage."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.recipe_proposals.compiler import (
    RecipeCompilationError,
    compile_recipe_proposal,
)
from geoagent_harness.recipe_proposals.schemas import (
    RecipeOperatorReview,
    RecipeOperatorSaveResult,
)
from geoagent_harness.recipes import (
    RecipeStorageError,
    recipe_sha256,
    save_recipe,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)


class RecipeOperatorSaveError(RuntimeError):
    """Raised when a reviewed recipe cannot be saved."""


def save_reviewed_recipe(
    *,
    review: RecipeOperatorReview,
    registry: SkillRegistry,
    recipe_root: Path,
) -> RecipeOperatorSaveResult:
    """Recompile, compare, and immutably save a recipe."""

    if review.status != (
        "ready_for_operator_review"
    ):
        raise RecipeOperatorSaveError(
            "only a ready operator review can "
            "be saved"
        )

    if review.compilation is None:
        raise RecipeOperatorSaveError(
            "ready operator review has no "
            "compiled recipe"
        )

    try:
        rebuilt = compile_recipe_proposal(
            review.generation.proposal,
            registry=registry,
        )
    except RecipeCompilationError as exc:
        raise RecipeOperatorSaveError(
            "review proposal no longer compiles"
        ) from exc

    if rebuilt != review.compilation:
        raise RecipeOperatorSaveError(
            "operator review compilation does not "
            "match deterministic recompilation"
        )

    try:
        saved_recipe, saved_path = save_recipe(
            rebuilt.recipe,
            recipe_root=recipe_root,
        )
    except RecipeStorageError as exc:
        raise RecipeOperatorSaveError(
            "reviewed recipe could not be saved"
        ) from exc

    digest = recipe_sha256(
        saved_recipe
    )

    return RecipeOperatorSaveResult(
        recipe_id=saved_recipe.recipe_id,
        recipe_sha256=digest,
        recipe_filename=saved_path.name,
        source_review_status=(
            "ready_for_operator_review"
        ),
        recipe_saved=True,
        approval_performed=False,
        execution_performed=False,
    )

