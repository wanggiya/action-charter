"""Generated service contracts for convert_raster."""

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
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_service_requires_write_authority(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )

    with pytest.raises(
        ConvertRasterError,
        match="controlled raster conversion failed",
    ):
        convert_raster(
            ConvertRasterArguments(
                path=source,
                target_path=(
                    output_root / "result.tif"
                ),
                target_crs="EPSG:3857",
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
                enable_write_tools=False,
            ),
        )
