"""Generated security contracts for inspect_raster."""

from pathlib import Path

import pytest

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)
from geoagent_harness.skills.inspect_raster.service import (
    inspect_raster,
)
from geoagent_harness.skills.inspect_raster.policy import (
    InspectRasterPolicyError,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    target = write_test_raster(
        root / "target.tif"
    )
    link = root / "link.tif"
    link.symlink_to(target)

    with pytest.raises(
        InspectRasterPolicyError,
        match="failed policy",
    ):
        inspect_raster(
            InspectRasterArguments(
                path=link,
                input_root=root,
            )
        )


def test_result_withholds_write_claims(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    path = write_test_raster(
        root / "sample.tif"
    )

    result = inspect_raster(
        InspectRasterArguments(
            path=path,
            input_root=root,
        )
    )

    assert result.filesystem_modified is False
    assert result.database_modified is False
