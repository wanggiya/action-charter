"""Generated schema contracts for inspect_raster."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.skills.inspect_raster.schemas import (
    InspectRasterArguments,
)


def test_arguments_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        InspectRasterArguments(
            path=Path("sample.tif"),
            input_root=Path("input"),
            unexpected=True,
        )
