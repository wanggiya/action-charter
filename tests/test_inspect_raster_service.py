"""Generated service contracts for inspect_raster."""

from pathlib import Path

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)
from geoagent_harness.skills.inspect_raster.service import (
    inspect_raster,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_inspects_fixture_without_modification(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    path = write_test_raster(
        root / "sample.tif"
    )
    before = path.stat()

    result = inspect_raster(
        InspectRasterArguments(
            path=path,
            input_root=root,
        )
    )

    after = path.stat()

    assert result.status == "completed"
    assert result.driver == "GTiff"
    assert result.width == 3
    assert result.height == 2
    assert result.band_count == 1
    assert result.filesystem_modified is False
    assert result.database_modified is False

    assert before.st_size == after.st_size
    assert before.st_mtime_ns == after.st_mtime_ns
