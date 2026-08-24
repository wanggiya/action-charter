"""Approval-gated deterministic recipe execution."""

from __future__ import annotations
from pathlib import Path

from typing import Any

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes.approval import (
    RecipeApprovalRecord,
)
from geoagent_harness.recipes.dispatcher import (
    RecipeDispatchError,
    dispatch_recipe_step,
)
from geoagent_harness.recipes.execution import (
    RecipeExecutionPolicyError,
    build_recipe_execution_envelope,
)
from geoagent_harness.recipes.schemas import (
    ConvertRasterRecipeArguments,
    ConvertVectorRecipeArguments,
    RecipeRunResult,
    RecipeStepRunResult,
    WorkflowRecipe,
)
from geoagent_harness.redaction import (
    redact_value,
)
from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillRegistry,
)
from geoagent_harness.skills.convert_vector.validation import (
    ConvertVectorValidationError,
    validate_vector_conversion,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)
from geoagent_harness.skills.convert_raster.validation import (
    ConvertRasterValidationError,
    validate_raster_conversion,
)


_EXPECTED_VERIFIERS = {
    "convert_vector": (
        "geoagent_harness.skills.convert_vector."
        "validation:validate_vector_conversion"
    ),
    "convert_raster": (
        "geoagent_harness.skills.convert_raster."
        "validation:validate_raster_conversion"
    ),
}


class RecipeRunError(RuntimeError):
    """Raised when an approved recipe cannot run safely."""


def _structured_validation(
    value: Any,
) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        payload = value.model_dump(
            mode="json"
        )
    elif isinstance(value, dict):
        payload = value
    else:
        raise RecipeRunError(
            "verifier returned an unsupported result"
        )

    redacted = redact_value(payload)

    if not isinstance(redacted, dict):
        raise RecipeRunError(
            "validation result must be an object"
        )

    return redacted


def _validate_conversion_step(
    *,
    arguments: dict[str, Any],
    settings: MCPSettings,
):
    try:
        typed = (
            ConvertVectorRecipeArguments.model_validate(
                arguments
            )
        )
    except Exception as exc:
        raise RecipeRunError(
            "conversion arguments failed "
            "validation before verification"
        ) from exc

    return validate_vector_conversion(
        path=Path(typed.path),
        target_path=Path(
            typed.target_path
        ),
        input_root=settings.input_root,
        output_root=settings.output_root,
        source_layer=typed.source_layer,
        target_layer=typed.target_layer,
    )

def _validate_raster_conversion_step(
    *,
    arguments: dict[str, Any],
    settings: MCPSettings,
):
    """Validate one exact converted raster step."""

    try:
        typed = (
            ConvertRasterRecipeArguments
            .model_validate(arguments)
        )

        wrapped = ConvertRasterArguments(
            path=Path(typed.path),
            target_path=Path(
                typed.target_path
            ),
            target_crs=typed.target_crs,
            resampling=typed.resampling,
        )
    except Exception as exc:
        raise RecipeRunError(
            "raster conversion arguments failed "
            "validation before verification"
        ) from exc

    return validate_raster_conversion(
        wrapped,
        settings=settings,
    )

def run_approved_recipe(
    *,
    recipe: WorkflowRecipe,
    approval: RecipeApprovalRecord,
    registry: SkillRegistry,
    settings: MCPSettings,
) -> RecipeRunResult:
    """Execute and validate one exact approved recipe."""

    try:
        envelope = (
            build_recipe_execution_envelope(
                recipe=recipe,
                approval=approval,
                registry=registry,
            )
        )
    except RecipeExecutionPolicyError as exc:
        raise RecipeRunError(
            "approved recipe execution envelope "
            "could not be built"
        ) from exc

    skills_by_step = {
        step.step_id: registry.get_skill(
            step.skill_id
        )
        for step in envelope.steps
    }

    write_steps = [
        step_id
        for step_id, skill in skills_by_step.items()
        if skill.access != SkillAccess.READ_ONLY
    ]

    if (
        write_steps
        and not settings.enable_write_tools
    ):
        raise RecipeRunError(
            "recipe contains write steps but "
            "write tools are disabled"
        )

    step_results: list[
        RecipeStepRunResult
    ] = []
    completed: set[str] = set()
    validated: set[str] = set()
    warnings: list[str] = []

    steps_by_id = {
        step.step_id: step
        for step in envelope.steps
    }

    for step_id in (
        envelope.topological_step_ids
    ):
        step = steps_by_id[step_id]
        skill = skills_by_step[step_id]

        missing_dependencies = [
            dependency
            for dependency in step.depends_on
            if dependency not in completed
        ]

        if missing_dependencies:
            raise RecipeRunError(
                f"step {step_id!r} has incomplete "
                "dependencies: "
                + ", ".join(
                    missing_dependencies
                )
            )

        try:
            execution = dispatch_recipe_step(
                envelope=envelope,
                step_id=step_id,
                registry=registry,
                settings=settings,
            )
        except RecipeDispatchError as exc:
            raise RecipeRunError(
                f"recipe step {step_id!r} "
                "failed dispatch"
            ) from exc

        if not skill.validation_required:
            step_results.append(
                RecipeStepRunResult(
                    step_id=step_id,
                    skill_id=step.skill_id,
                    status="completed",
                    execution=execution,
                    validation_result=None,
                    execution_performed=True,
                    validation_performed=False,
                )
            )
            completed.add(step_id)
            continue

        expected_verifier = (
            _EXPECTED_VERIFIERS.get(
                step.skill_id
            )
        )

        if expected_verifier is None:
            raise RecipeRunError(
                f"skill {step.skill_id!r} has no "
                "hard-coded verifier"
            )

        if skill.verifier != expected_verifier:
            raise RecipeRunError(
                f"skill {step.skill_id!r} verifier "
                "does not match the hard-coded policy"
            )

        try:
            if step.skill_id == "convert_vector":
                validation = (
                    _validate_conversion_step(
                        arguments=step.arguments,
                        settings=settings,
                    )
                )
            elif step.skill_id == (
                "convert_raster"
            ):
                validation = (
                    _validate_raster_conversion_step(
                        arguments=step.arguments,
                        settings=settings,
                    )
                )
            else:
                raise RecipeRunError(
                    f"skill {step.skill_id!r} has no "
                    "implemented recipe verifier"
                )
        except (
            ConvertRasterValidationError,
            ConvertVectorValidationError,
        ) as exc:
            raise RecipeRunError(
                f"verification for step "
                f"{step_id!r} could not run"
            ) from exc

        validation_payload = (
            _structured_validation(
                validation
            )
        )

        validation_passed = (
            validation_payload.get("passed")
            is True
        )

        validation_warnings = (
            validation_payload.get(
                "warnings",
                [],
            )
        )

        if isinstance(
            validation_warnings,
            list,
        ):
            warnings.extend(
                str(warning)
                for warning in validation_warnings
            )

        if not validation_passed:
            step_results.append(
                RecipeStepRunResult(
                    step_id=step_id,
                    skill_id=step.skill_id,
                    status="validation_failed",
                    execution=execution,
                    validation_result=(
                        validation_payload
                    ),
                    execution_performed=True,
                    validation_performed=True,
                )
            )

            return RecipeRunResult(
                recipe_id=recipe.recipe_id,
                recipe_sha256=(
                    envelope.recipe_sha256
                ),
                approval_id=(
                    envelope.approval_id
                ),
                final_status=(
                    "validation_failed"
                ),
                step_results=step_results,
                failed_step_id=step_id,
                warnings=warnings,
                execution_performed=True,
                validation_performed=True,
            )

        validated.add(step_id)
        completed.add(step_id)

        step_results.append(
            RecipeStepRunResult(
                step_id=step_id,
                skill_id=step.skill_id,
                status="validated_success",
                execution=execution,
                validation_result=(
                    validation_payload
                ),
                execution_performed=True,
                validation_performed=True,
            )
        )

    expected_validations = {
        step_id
        for step_id, skill in skills_by_step.items()
        if skill.validation_required
    }

    if validated != expected_validations:
        raise RecipeRunError(
            "recipe validation scope was not "
            "completed"
        )

    return RecipeRunResult(
        recipe_id=recipe.recipe_id,
        recipe_sha256=envelope.recipe_sha256,
        approval_id=envelope.approval_id,
        final_status="validated_success",
        step_results=step_results,
        failed_step_id=None,
        warnings=warnings,
        execution_performed=True,
        validation_performed=bool(
            expected_validations
        ),
    )
