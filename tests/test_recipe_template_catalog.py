"""Contracts for the data-only recipe catalog."""

from pathlib import Path

import pytest

from geoagent_harness.recipe_catalog import (
    RecipeTemplateCatalogError,
    load_recipe_template_catalog,
    parse_recipe_template_catalog,
    RecipeTemplateCatalogError,
    load_recipe_template_catalog,
)
from geoagent_harness.recipe_proposals import (
    list_recipe_templates,
)


PROJECT_ROOT = Path(__file__).parents[1]


def test_catalog_matches_existing_templates(
) -> None:
    catalog = load_recipe_template_catalog(
        PROJECT_ROOT
    )

    existing = list_recipe_templates()

    assert [
        template.template_id
        for template in catalog.templates
    ] == [
        template.template_id
        for template in existing
    ]

    assert [
        template.skill_ids
        for template in catalog.templates
    ] == [
        template.skill_ids
        for template in existing
    ]

    assert [
        template.required_parameters
        for template in catalog.templates
    ] == [
        template.required_parameters
        for template in existing
    ]


def test_catalog_lookup_is_deterministic(
) -> None:
    catalog = load_recipe_template_catalog(
        PROJECT_ROOT
    )

    template = catalog.get_template(
        "inspect_and_convert_raster"
    )

    assert template.skill_ids == (
        "inspect_raster",
        "convert_raster",
    )
    assert template.required_parameters == (
        "path",
        "target_path",
        "target_crs",
    )


def test_unknown_template_fails_closed(
) -> None:
    catalog = load_recipe_template_catalog(
        PROJECT_ROOT
    )

    with pytest.raises(KeyError):
        catalog.get_template(
            "model_invented_template"
        )


def test_duplicate_template_ids_are_rejected(
) -> None:
    content = """
schema_version: "1.0"
templates:
  - template_id: duplicate
    skill_ids:
      - inspect_vector
    required_parameters:
      - path
  - template_id: duplicate
    skill_ids:
      - inspect_raster
    required_parameters:
      - path
"""

    with pytest.raises(
        RecipeTemplateCatalogError,
        match="schema validation",
    ):
        parse_recipe_template_catalog(
            content
        )


def test_executable_fields_are_rejected(
) -> None:
    content = """
schema_version: "1.0"
templates:
  - template_id: unsafe
    skill_ids:
      - inspect_vector
    required_parameters:
      - path
    entrypoint: os.system
"""

    with pytest.raises(
        RecipeTemplateCatalogError,
        match="schema validation",
    ):
        parse_recipe_template_catalog(
            content
        )

def test_catalog_file_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    """The fixed catalog file cannot redirect elsewhere."""

    context = tmp_path / "context"
    context.mkdir()

    external = tmp_path / "external.yaml"
    external.write_text(
        (
            'schema_version: "1.0"\n'
            "templates:\n"
            "  - template_id: inspect_vector\n"
            "    skill_ids:\n"
            "      - inspect_vector\n"
            "    required_parameters:\n"
            "      - path\n"
        ),
        encoding="utf-8",
    )

    (
        context / "RECIPE_TEMPLATES.yaml"
    ).symlink_to(external)

    with pytest.raises(
        RecipeTemplateCatalogError,
        match="cannot be a symlink",
    ):
        load_recipe_template_catalog(
            tmp_path
        )


def test_catalog_directory_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    """The catalog directory cannot redirect elsewhere."""

    external = tmp_path / "external"
    external.mkdir()

    (
        external / "RECIPE_TEMPLATES.yaml"
    ).write_text(
        (
            'schema_version: "1.0"\n'
            "templates:\n"
            "  - template_id: inspect_vector\n"
            "    skill_ids:\n"
            "      - inspect_vector\n"
            "    required_parameters:\n"
            "      - path\n"
        ),
        encoding="utf-8",
    )

    (
        tmp_path / "context"
    ).symlink_to(
        external,
        target_is_directory=True,
    )

    with pytest.raises(
        RecipeTemplateCatalogError,
        match="directory cannot be a symlink",
    ):
        load_recipe_template_catalog(
            tmp_path
        )

