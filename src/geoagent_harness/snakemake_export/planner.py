"""Deterministic planning for approved recipe exports."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.recipes import (
    RecipeApprovalRecord,
    RecipeExecutionPolicyError,
    WorkflowRecipe,
    build_recipe_execution_envelope,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)
from geoagent_harness.snakemake_export.schemas import (
    SnakemakeRecipeExportPlan,
)


class SnakemakeExportPolicyError(ValueError):
    """Raised when an approved recipe cannot be exported."""


def _plain_json_filename(
    path: Path,
    *,
    label: str,
) -> str:
    value = path.name

    if (
        value != path.as_posix()
        and path.parent != Path(".")
    ):
        # Full canonical paths are accepted by the planner,
        # but only their plain basenames enter the export.
        value = path.name

    if (
        not value
        or value in {".json", ".."}
        or Path(value).name != value
        or Path(value).suffix != ".json"
    ):
        raise SnakemakeExportPolicyError(
            f"{label} must resolve to a plain JSON filename"
        )

    return value


def plan_snakemake_recipe_export(
    *,
    recipe: WorkflowRecipe,
    approval: RecipeApprovalRecord,
    registry: SkillRegistry,
    recipe_path: Path,
    approval_path: Path,
) -> SnakemakeRecipeExportPlan:
    """Plan export after rebuilding the approved envelope."""

    try:
        envelope = build_recipe_execution_envelope(
            recipe=recipe,
            approval=approval,
            registry=registry,
        )
    except RecipeExecutionPolicyError as exc:
        raise SnakemakeExportPolicyError(
            "recipe and approval failed export policy"
        ) from exc

    recipe_filename = _plain_json_filename(
        recipe_path,
        label="recipe_path",
    )
    approval_filename = _plain_json_filename(
        approval_path,
        label="approval_path",
    )

    return SnakemakeRecipeExportPlan(
        recipe_id=envelope.recipe_id,
        recipe_sha256=envelope.recipe_sha256,
        approval_id=envelope.approval_id,
        recipe_filename=recipe_filename,
        approval_filename=approval_filename,
        approved_step_ids=(
            envelope.approved_step_ids
        ),
        topological_step_ids=(
            envelope.topological_step_ids
        ),
        warnings=[
            (
                "Export planning does not execute "
                "Snakemake or the recipe."
            ),
            (
                "Replay must use the trusted GeoAgent "
                "approval-gated MCP execution adapter."
            ),
            (
                "The exported workflow must not call "
                "GIS libraries, shell commands, skill "
                "entrypoints, or PostGIS directly."
            ),
        ],
    )

