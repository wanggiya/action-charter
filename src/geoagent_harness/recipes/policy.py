"""Deterministic policy for reusable workflow recipes."""

from __future__ import annotations

from geoagent_harness.recipes.digest import (
    recipe_sha256,
)
from geoagent_harness.recipes.schemas import (
    RecipeValidation,
    WorkflowRecipe,
)
from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillRegistry,
    SkillStatus,
)


class RecipePolicyError(ValueError):
    """Raised when a recipe violates deterministic policy."""


def _topological_order(
    recipe: WorkflowRecipe,
) -> list[str]:
    """Return deterministic order or reject an invalid DAG."""

    step_ids = [
        step.step_id
        for step in recipe.steps
    ]
    known_steps = set(step_ids)

    dependencies: dict[str, set[str]] = {}
    dependents: dict[str, list[str]] = {
        step_id: []
        for step_id in step_ids
    }

    for step in recipe.steps:
        dependency_set = set(step.depends_on)

        if step.step_id in dependency_set:
            raise RecipePolicyError(
                f"step {step.step_id!r} depends on itself"
            )

        unknown = sorted(
            dependency_set - known_steps
        )

        if unknown:
            raise RecipePolicyError(
                f"step {step.step_id!r} references "
                "unknown dependencies: "
                + ", ".join(unknown)
            )

        dependencies[step.step_id] = dependency_set

        for dependency in step.depends_on:
            dependents[dependency].append(
                step.step_id
            )

    ready = [
        step_id
        for step_id in step_ids
        if not dependencies[step_id]
    ]

    ordered: list[str] = []

    while ready:
        current = ready.pop(0)
        ordered.append(current)

        for dependent in dependents[current]:
            dependencies[dependent].remove(
                current
            )

            if not dependencies[dependent]:
                ready.append(dependent)

    if len(ordered) != len(step_ids):
        raise RecipePolicyError(
            "recipe dependencies contain a cycle"
        )

    return ordered


def validate_recipe_policy(
    recipe: WorkflowRecipe,
    *,
    registry: SkillRegistry,
) -> RecipeValidation:
    """Validate a recipe without executing any skill."""

    approval_required: list[str] = []
    write_steps: list[str] = []
    validation_required: list[str] = []

    for step in recipe.steps:
        try:
            skill = registry.get_skill(
                step.skill_id
            )
        except KeyError as exc:
            raise RecipePolicyError(
                f"step {step.step_id!r} references "
                f"unknown skill {step.skill_id!r}"
            ) from exc

        if skill.status != SkillStatus.IMPLEMENTED:
            raise RecipePolicyError(
                f"step {step.step_id!r} references "
                f"unimplemented skill {step.skill_id!r}"
            )

        if (
            skill.entrypoint is None
            or skill.access is None
            or skill.approval_required is None
            or skill.validation_required is None
        ):
            raise RecipePolicyError(
                f"skill {step.skill_id!r} has "
                "incomplete trusted metadata"
            )

        if skill.approval_required:
            approval_required.append(
                step.step_id
            )

        if skill.access != SkillAccess.READ_ONLY:
            write_steps.append(
                step.step_id
            )

            if not step.output_ids:
                raise RecipePolicyError(
                    f"write step {step.step_id!r} "
                    "must declare at least one "
                    "logical output"
                )

        if skill.validation_required:
            validation_required.append(
                step.step_id
            )

            if skill.verifier is None:
                raise RecipePolicyError(
                    f"step {step.step_id!r} requires "
                    "validation but its skill has "
                    "no verifier"
                )

    order = _topological_order(recipe)

    return RecipeValidation(
        recipe_id=recipe.recipe_id,
        recipe_sha256=recipe_sha256(recipe),
        topological_step_ids=order,
        approval_required_step_ids=(
            approval_required
        ),
        write_step_ids=write_steps,
        validation_required_step_ids=(
            validation_required
        ),
        execution_performed=False,
    )
