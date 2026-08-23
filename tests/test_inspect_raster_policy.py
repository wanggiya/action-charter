"""Generated policy contracts for inspect_raster."""

from pathlib import Path

import pytest

from geoagent_harness.skills.inspect_raster.policy import (
    InspectRasterPolicyError,
    validate_inspect_raster_request,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_policy_accepts_file_under_input_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    path = write_test_raster(
        root / "sample.tif"
    )

    result = validate_inspect_raster_request(
        path=path,
        input_root=root,
    )

    assert result == path.resolve()


def test_policy_rejects_path_escape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "input"
    root.mkdir()

    outside = write_test_raster(
        tmp_path / "outside.tif"
    )

    with pytest.raises(
        InspectRasterPolicyError,
        match="failed policy",
    ):
        validate_inspect_raster_request(
            path=outside,
            input_root=root,
        )
