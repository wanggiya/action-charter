"""Tests for the fixed raster candidate renderer."""

import ast

import pytest

from geoagent_harness.skill_definitions.adapters import (
    RasterInspectionRendererError,
    render_raster_inspection_candidate,
)


def test_renderer_produces_exact_scaffold_file_set(
) -> None:
    files = render_raster_inspection_candidate(
        skill_id="inspect_raster"
    )

    assert set(files) == {
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/__init__.py"
        ),
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/schemas.py"
        ),
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/policy.py"
        ),
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/service.py"
        ),
        "tests/test_inspect_raster_schemas.py",
        "tests/test_inspect_raster_policy.py",
        "tests/test_inspect_raster_service.py",
        "tests/test_inspect_raster_contract.py",
    }

    for path, source in files.items():
        ast.parse(
            source,
            filename=path,
        )

        assert "pytest.skip" not in source
        assert "not implemented" not in (
            source.lower()
        )


def test_renderer_rejects_unapproved_skill_id(
) -> None:
    with pytest.raises(
        RasterInspectionRendererError,
        match="supports only",
    ):
        render_raster_inspection_candidate(
            skill_id="arbitrary_skill"
        )

