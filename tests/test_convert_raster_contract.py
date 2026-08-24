"""Generated security contracts for convert_raster."""

from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)
from geoagent_harness.skills.convert_raster.service import (
    ConvertRasterError,
    convert_raster,
)
from geoagent_harness.skills.convert_raster.validation import (
    validate_raster_conversion,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_conversion_withholds_success_until_validation(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "result.tif"

    arguments = ConvertRasterArguments(
        path=source,
        target_path=target,
        target_crs="EPSG:3857",
    )
    settings = MCPSettings(
        input_root=input_root,
        output_root=output_root,
        enable_write_tools=True,
    )

    result = convert_raster(
        arguments,
        settings=settings,
    )

    assert result.validation_performed is False
    assert result.final_success_claimed is False

    validation = validate_raster_conversion(
        arguments,
        settings=settings,
    )

    assert validation.passed is True
    assert validation.validation_performed is True
    assert validation.final_success_claimed is True


def test_existing_output_is_not_overwritten(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = write_test_raster(
        output_root / "result.tif"
    )
    before = target.read_bytes()

    with pytest.raises(ConvertRasterError):
        convert_raster(
            ConvertRasterArguments(
                path=source,
                target_path=target,
                target_crs="EPSG:3857",
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
                enable_write_tools=True,
            ),
        )

    assert target.read_bytes() == before
