"""Bounded loading of the trusted recipe catalog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from geoagent_harness.recipe_catalog.schemas import (
    RecipeTemplateCatalog,
)


MAX_RECIPE_TEMPLATE_CATALOG_BYTES = 250_000


class RecipeTemplateCatalogError(RuntimeError):
    """Raised when the recipe catalog is invalid."""


def recipe_template_catalog_path(
    project_root: Path,
) -> Path:
    """Return the fixed lexical catalog path."""

    root = project_root.resolve()

    return (
        root
        / "context"
        / "RECIPE_TEMPLATES.yaml"
    )


def parse_recipe_template_catalog(
    content: str,
) -> RecipeTemplateCatalog:
    """Parse strict non-executable catalog YAML."""

    try:
        payload: Any = yaml.safe_load(
            content
        )
    except yaml.YAMLError as exc:
        raise RecipeTemplateCatalogError(
            "recipe template catalog is not "
            "valid YAML"
        ) from exc

    if not isinstance(payload, dict):
        raise RecipeTemplateCatalogError(
            "recipe template catalog must be "
            "an object"
        )

    try:
        return (
            RecipeTemplateCatalog
            .model_validate(payload)
        )
    except ValidationError as exc:
        raise RecipeTemplateCatalogError(
            "recipe template catalog failed "
            "schema validation"
        ) from exc


def load_recipe_template_catalog(
    project_root: Path = Path("."),
) -> RecipeTemplateCatalog:
    """Load the fixed trusted recipe catalog."""

    path = recipe_template_catalog_path(
        project_root
    )
    context_directory = path.parent

    if context_directory.is_symlink():
        raise RecipeTemplateCatalogError(
            "recipe template catalog directory "
            "cannot be a symlink"
        )

    if path.is_symlink():
        raise RecipeTemplateCatalogError(
            "recipe template catalog cannot "
            "be a symlink"
        )

    if not path.is_file():
        raise RecipeTemplateCatalogError(
            "recipe template catalog does not exist"
        )

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise RecipeTemplateCatalogError(
            "recipe template catalog could not "
            "be inspected"
        ) from exc

    if size <= 0:
        raise RecipeTemplateCatalogError(
            "recipe template catalog is empty"
        )

    if size > MAX_RECIPE_TEMPLATE_CATALOG_BYTES:
        raise RecipeTemplateCatalogError(
            "recipe template catalog exceeds "
            "the size limit"
        )

    try:
        content = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise RecipeTemplateCatalogError(
            "recipe template catalog is not UTF-8"
        ) from exc
    except OSError as exc:
        raise RecipeTemplateCatalogError(
            "recipe template catalog could not "
            "be read"
        ) from exc

    return parse_recipe_template_catalog(
        content
    )

