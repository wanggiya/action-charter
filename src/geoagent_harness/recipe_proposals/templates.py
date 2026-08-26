"""Catalog-backed trusted recipe templates."""

from __future__ import annotations

from geoagent_harness.recipe_catalog import (
    RecipeTemplateCatalogEntry,
    RecipeTemplateCatalogError,
    load_recipe_template_catalog,
)


# Compatibility alias. Existing callers can keep importing
# RecipeTemplateDefinition while definitions come from YAML.
RecipeTemplateDefinition = (
    RecipeTemplateCatalogEntry
)


class RecipeTemplateError(ValueError):
    """Raised when trusted template loading fails."""


def list_recipe_templates(
) -> tuple[RecipeTemplateDefinition, ...]:
    """Return catalog templates in stable YAML order."""

    try:
        catalog = load_recipe_template_catalog()
    except RecipeTemplateCatalogError as exc:
        raise RecipeTemplateError(
            "trusted recipe template catalog "
            "could not be loaded"
        ) from exc

    return catalog.templates


def get_recipe_template(
    template_id: str,
) -> RecipeTemplateDefinition:
    """Return one trusted catalog template."""

    try:
        catalog = load_recipe_template_catalog()
        return catalog.get_template(
            template_id
        )
    except RecipeTemplateCatalogError as exc:
        raise RecipeTemplateError(
            "trusted recipe template catalog "
            "could not be loaded"
        ) from exc
    except KeyError as exc:
        raise RecipeTemplateError(
            f"unknown recipe template: "
            f"{template_id!r}"
        ) from exc