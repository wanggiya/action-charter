"""Fixed trusted recipe templates."""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


TemplateId = Literal[
    "inspect_vector",
    "inspect_raster",
    "inspect_and_convert_raster",
    "inspect_and_convert_vector",
    "vector_to_postgis",
]


class RecipeTemplateDefinition(BaseModel):
    """One fixed deterministic recipe template."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    template_id: TemplateId
    skill_ids: tuple[str, ...] = Field(
        min_length=1
    )
    required_parameters: tuple[str, ...] = Field(
        min_length=1
    )


_TEMPLATES: dict[
    str,
    RecipeTemplateDefinition,
] = {
    "inspect_vector": RecipeTemplateDefinition(
        template_id="inspect_vector",
        skill_ids=(
            "inspect_vector",
        ),
        required_parameters=(
            "path",
        ),
    ),
    "inspect_raster": RecipeTemplateDefinition(
        template_id="inspect_raster",
        skill_ids=(
            "inspect_raster",
        ),
        required_parameters=(
            "path",
        ),
    ),
    (
        "inspect_and_convert_raster"
    ): RecipeTemplateDefinition(
        template_id=(
            "inspect_and_convert_raster"
        ),
        skill_ids=(
            "inspect_raster",
            "convert_raster",
        ),
        required_parameters=(
            "path",
            "target_path",
            "target_crs",
        ),
    ),
    (
        "inspect_and_convert_vector"
    ): RecipeTemplateDefinition(
        template_id=(
            "inspect_and_convert_vector"
        ),
        skill_ids=(
            "inspect_vector",
            "convert_vector",
        ),
        required_parameters=(
            "path",
            "target_path",
        ),
    ),
    "vector_to_postgis": RecipeTemplateDefinition(
        template_id="vector_to_postgis",
        skill_ids=(
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
            "generate_report",
        ),
        required_parameters=(
            "path",
            "target_schema",
            "target_table",
        ),
    ),
}


class RecipeTemplateError(ValueError):
    """Raised for an unknown trusted template."""


def list_recipe_templates(
) -> tuple[RecipeTemplateDefinition, ...]:
    """Return templates in fixed stable order."""

    return tuple(_TEMPLATES.values())


def get_recipe_template(
    template_id: str,
) -> RecipeTemplateDefinition:
    """Return one fixed trusted template."""

    try:
        return _TEMPLATES[template_id]
    except KeyError as exc:
        raise RecipeTemplateError(
            f"unknown recipe template: "
            f"{template_id!r}"
        ) from exc

