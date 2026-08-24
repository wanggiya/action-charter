"""Contracts for the trusted raster conversion adapter."""

from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_conversion import (
    RasterConversionError,
    RasterResampling,
    convert_raster,
    plan_raster_conversion,
    validate_raster_conversion,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def settings(
    *,
    input_root: Path,
    output_root: Path,
    writes: bool,
) -> MCPSettings:
    return MCPSettings(
        input_root=input_root,
        output_root=output_root,
        enable_write_tools=writes,
    )


def test_plans_without_creating_output(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "converted.tif"

    result = plan_raster_conversion(
        path=source,
        target_path=target,
        target_crs="EPSG:3857",
        input_root=input_root,
        output_root=output_root,
        resampling=RasterResampling.NEAREST,
    )

    assert result.status == (
        "planned_not_executed"
    )
    assert result.target_crs == "EPSG:3857"
    assert result.approval_required is True
    assert result.validation_required is True
    assert result.execution_allowed is False
    assert not target.exists()


def test_conversion_requires_write_tools(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )

    with pytest.raises(
        RasterConversionError,
        match="write tools are disabled",
    ):
        convert_raster(
            path=source,
            target_path=(
                output_root / "converted.tif"
            ),
            target_crs="EPSG:3857",
            settings=settings(
                input_root=input_root,
                output_root=output_root,
                writes=False,
            ),
        )


def test_converts_and_validates_new_geotiff(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "converted.tif"

    result = convert_raster(
        path=source,
        target_path=target,
        target_crs="EPSG:3857",
        settings=settings(
            input_root=input_root,
            output_root=output_root,
            writes=True,
        ),
        resampling=RasterResampling.BILINEAR,
    )

    assert target.is_file()
    assert result.status == (
        "converted_pending_validation"
    )
    assert result.target_crs == "EPSG:3857"
    assert result.validation_performed is False
    assert result.final_success_claimed is False

    validation = validate_raster_conversion(
        path=source,
        target_path=target,
        target_crs="EPSG:3857",
        input_root=input_root,
        output_root=output_root,
    )

    assert validation.passed is True
    assert validation.status == (
        "validation_passed"
    )
    assert validation.final_success_claimed is True


def test_rejects_target_outside_output_root(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )

    with pytest.raises(
        RasterConversionError,
        match="escaped",
    ):
        plan_raster_conversion(
            path=source,
            target_path=(
                tmp_path / "outside.tif"
            ),
            target_crs="EPSG:3857",
            input_root=input_root,
            output_root=output_root,
        )


def test_rejects_existing_target(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = write_test_raster(
        output_root / "existing.tif"
    )

    with pytest.raises(
        RasterConversionError,
        match="already exists",
    ):
        plan_raster_conversion(
            path=source,
            target_path=target,
            target_crs="EPSG:3857",
            input_root=input_root,
            output_root=output_root,
        )


def test_rejects_target_symlink(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    real_output = tmp_path / "real-output"

    output_root.mkdir()
    real_output.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )

    link = output_root / "linked"
    link.symlink_to(
        real_output,
        target_is_directory=True,
    )

    with pytest.raises(
        RasterConversionError,
        match="symlink",
    ):
        plan_raster_conversion(
            path=source,
            target_path=(
                link / "converted.tif"
            ),
            target_crs="EPSG:3857",
            input_root=input_root,
            output_root=output_root,
        )

