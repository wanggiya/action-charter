"""Generated policy contracts for convert_raster."""

from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skills.convert_raster.policy import (
    ConvertRasterPolicyError,
    validate_convert_raster_request,
)
from geoagent_harness.skills.convert_raster.schemas import (
    ConvertRasterArguments,
)
from geoagent_harness.testing.raster import (
    write_test_raster,
)


def test_policy_plans_without_writing(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "result.tif"

    plan = validate_convert_raster_request(
        arguments=ConvertRasterArguments(
            path=source,
            target_path=target,
            target_crs="EPSG:3857",
        ),
        settings=MCPSettings(
            input_root=input_root,
            output_root=output_root,
        ),
    )

    assert plan.execution_allowed is False
    assert plan.approval_required is True
    assert plan.validation_required is True
    assert not target.exists()


def test_policy_rejects_output_escape(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )

    with pytest.raises(
        ConvertRasterPolicyError,
        match="failed policy",
    ):
        validate_convert_raster_request(
            arguments=ConvertRasterArguments(
                path=source,
                target_path=(
                    tmp_path / "outside.tif"
                ),
                target_crs="EPSG:3857",
            ),
            settings=MCPSettings(
                input_root=input_root,
                output_root=output_root,
            ),
        )
