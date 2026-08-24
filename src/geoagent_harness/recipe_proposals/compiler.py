"""Deterministic compilation of trusted recipe proposals."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from geoagent_harness.recipe_proposals.assessment import (
    assess_recipe_proposal,
)
from geoagent_harness.recipe_proposals.schemas import (
    RecipeCompilationResult,
    RecipeProposal,
)
from geoagent_harness.recipes.policy import (
    RecipePolicyError,
    validate_recipe_policy,
)
from geoagent_harness.recipes.schemas import (
    RecipeStep,
    WorkflowRecipe,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)


class RecipeCompilationError(ValueError):
    """Raised when a proposal cannot compile safely."""


def _recipe_id(
    proposal: RecipeProposal,
) -> str:
    """Return a stable safe recipe identifier."""

    if proposal.recipe_id_hint is not None:
        return proposal.recipe_id_hint

    canonical = json.dumps(
        proposal.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return f"recipe-{digest[:16]}"


def _without_none(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Remove unspecified optional arguments."""

    return {
        key: value
        for key, value in arguments.items()
        if value is not None
    }


def _inspect_recipe(
    proposal: RecipeProposal,
) -> list[RecipeStep]:
    parameters = proposal.selection.parameters

    return [
        RecipeStep(
            step_id="step_1",
            skill_id="inspect_vector",
            arguments={
                "path": parameters.path,
            },
            output_ids=[
                "source_metadata",
            ],
        )
    ]

def _inspect_raster_recipe(
    proposal: RecipeProposal,
) -> list[RecipeStep]:
    """Compile the fixed read-only raster inspection template."""

    parameters = proposal.selection.parameters

    return [
        RecipeStep(
            step_id="step_1",
            skill_id="inspect_raster",
            arguments={
                "path": parameters.path,
            },
            output_ids=[
                "raster_metadata",
            ],
        )
    ]

def _raster_conversion_recipe(
    proposal: RecipeProposal,
) -> list[RecipeStep]:
    """Compile fixed inspection and raster conversion."""

    parameters = proposal.selection.parameters

    return [
        RecipeStep(
            step_id="step_1",
            skill_id="inspect_raster",
            arguments={
                "path": parameters.path,
            },
            output_ids=[
                "source_raster_metadata",
            ],
        ),
        RecipeStep(
            step_id="step_2",
            skill_id="convert_raster",
            depends_on=[
                "step_1",
            ],
            arguments={
                "path": parameters.path,
                "target_path": (
                    parameters.target_path
                ),
                "target_crs": (
                    parameters.target_crs
                ),
                "resampling": (
                    parameters.resampling
                ),
            },
            output_ids=[
                "converted_raster",
            ],
        ),
    ]

def _conversion_recipe(
    proposal: RecipeProposal,
) -> list[RecipeStep]:
    parameters = proposal.selection.parameters

    return [
        RecipeStep(
            step_id="step_1",
            skill_id="inspect_vector",
            arguments={
                "path": parameters.path,
            },
            output_ids=[
                "source_metadata",
            ],
        ),
        RecipeStep(
            step_id="step_2",
            skill_id="convert_vector",
            depends_on=[
                "step_1",
            ],
            arguments=_without_none(
                {
                    "path": parameters.path,
                    "target_path": (
                        parameters.target_path
                    ),
                    "source_layer": (
                        parameters.source_layer
                    ),
                    "target_layer": (
                        parameters.target_layer
                    ),
                }
            ),
            output_ids=[
                "converted_vector",
            ],
        ),
    ]


def _postgis_recipe(
    proposal: RecipeProposal,
) -> list[RecipeStep]:
    parameters = proposal.selection.parameters

    load_arguments = _without_none(
        {
            "path": parameters.path,
            "source_layer": (
                parameters.source_layer
            ),
            "target_schema": (
                parameters.target_schema
            ),
            "target_table": (
                parameters.target_table
            ),
        }
    )

    target_arguments = {
        "target_schema": (
            parameters.target_schema
        ),
        "target_table": (
            parameters.target_table
        ),
    }

    return [
        RecipeStep(
            step_id="step_1",
            skill_id="inspect_vector",
            arguments={
                "path": parameters.path,
            },
            output_ids=[
                "source_metadata",
            ],
        ),
        RecipeStep(
            step_id="step_2",
            skill_id="load_vector_to_postgis",
            depends_on=[
                "step_1",
            ],
            arguments=load_arguments,
            output_ids=[
                "postgis_load_result",
            ],
        ),
        RecipeStep(
            step_id="step_3",
            skill_id="validate_postgis_layer",
            depends_on=[
                "step_2",
            ],
            arguments=target_arguments,
            output_ids=[
                "postgis_validation",
            ],
        ),
        RecipeStep(
            step_id="step_4",
            skill_id="generate_report",
            depends_on=[
                "step_3",
            ],
            arguments={
                **target_arguments,
                "validation_output_id": (
                    "postgis_validation"
                ),
            },
            output_ids=[
                "workflow_report",
            ],
        ),
    ]


def _compile_steps(
    proposal: RecipeProposal,
) -> list[RecipeStep]:
    template_id = (
        proposal.selection.template_id
    )

    if template_id == "inspect_vector":
        return _inspect_recipe(proposal)

    if template_id == "inspect_raster":
        return _inspect_raster_recipe(
            proposal
        )

    if (
        template_id
        == "inspect_and_convert_raster"
    ):
        return _raster_conversion_recipe(
            proposal
        )

    if (
        template_id
        == "inspect_and_convert_vector"
    ):
        return _conversion_recipe(proposal)

    if template_id == "vector_to_postgis":
        return _postgis_recipe(proposal)

    # This should already be impossible because the
    # proposal uses a discriminated union.
    raise RecipeCompilationError(
        "proposal selected an unknown template"
    )


def compile_recipe_proposal(
    proposal: RecipeProposal,
    *,
    registry: SkillRegistry,
) -> RecipeCompilationResult:
    """Compile one ready proposal without side effects."""

    assessment = assess_recipe_proposal(
        proposal,
        registry=registry,
    )

    if not assessment.ready_for_compilation:
        raise RecipeCompilationError(
            "recipe proposal is not ready for "
            "compilation: "
            + assessment.reason
        )

    recipe = WorkflowRecipe(
        recipe_id=_recipe_id(proposal),
        summary=proposal.summary,
        original_request=(
            proposal.original_request
        ),
        steps=_compile_steps(proposal),
        execution_performed=False,
        validation_performed=False,
    )

    try:
        validation = validate_recipe_policy(
            recipe,
            registry=registry,
        )
    except RecipePolicyError as exc:
        raise RecipeCompilationError(
            "compiled recipe failed deterministic "
            "recipe policy"
        ) from exc

    return RecipeCompilationResult(
        proposal_assessment=assessment,
        recipe=recipe,
        recipe_validation=validation,
        compilation_performed=True,
        recipe_saved=False,
        approval_performed=False,
        execution_performed=False,
    )

