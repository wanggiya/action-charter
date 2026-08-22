"""Deterministic human-readable recipe review rendering."""

from __future__ import annotations

from geoagent_harness.recipe_proposals.schemas import (
    RecipeOperatorReview,
)


def render_recipe_operator_review(
    review: RecipeOperatorReview,
) -> str:
    """Render a review without changing or saving it."""

    proposal = review.generation.proposal

    lines = [
        "Recipe request review",
        f"Status: {review.status}",
        f"Model: {review.generation.model}",
        (
            "Template: "
            f"{proposal.selection.template_id}"
        ),
        f"Request: {proposal.original_request}",
        f"Summary: {proposal.summary}",
        "",
    ]

    if review.status == "clarification_required":
        lines.extend(
            [
                "Clarification required:",
            ]
        )

        for index, question in enumerate(
            review.clarification_questions,
            start=1,
        ):
            lines.append(
                f"{index}. {question}"
            )

        lines.extend(
            [
                "",
                "Compilation performed: no",
                "Recipe saved: no",
                "Approval performed: no",
                "Execution performed: no",
            ]
        )

        return "\n".join(lines)

    if review.compilation is None:
        raise ValueError(
            "ready review is missing compilation"
        )

    recipe = review.compilation.recipe
    validation = (
        review.compilation.recipe_validation
    )

    lines.extend(
        [
            f"Recipe ID: {recipe.recipe_id}",
            "",
            "Compiled steps:",
        ]
    )

    for step in recipe.steps:
        dependencies = (
            ", ".join(step.depends_on)
            if step.depends_on
            else "none"
        )

        lines.append(
            (
                f"- {step.step_id}: "
                f"{step.skill_id} "
                f"(depends on: {dependencies})"
            )
        )

    approval_steps = (
        ", ".join(
            validation.approval_required_step_ids
        )
        or "none"
    )
    validation_steps = (
        ", ".join(
            validation.validation_required_step_ids
        )
        or "none"
    )

    lines.extend(
        [
            "",
            (
                "Approval-required steps: "
                f"{approval_steps}"
            ),
            (
                "Validation-required steps: "
                f"{validation_steps}"
            ),
            "",
            "Compilation performed: yes",
            "Recipe saved: no",
            "Approval performed: no",
            "Execution performed: no",
            "",
            (
                "Next boundary: inspect the complete "
                "JSON recipe before explicitly saving it."
            ),
        ]
    )

    return "\n".join(lines)

