"""Read-only policy for raster inspection."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionError,
    validate_raster_path,
)


class InspectRasterPolicyError(ValueError):
    """Raised when raster inspection policy fails."""


def validate_inspect_raster_request(
    *,
    path: Path,
    input_root: Path,
) -> Path:
    """Validate one raster request without modifying it."""

    try:
        return validate_raster_path(
            path,
            input_root=input_root,
        )
    except RasterInspectionError as exc:
        raise InspectRasterPolicyError(
            "raster inspection request failed policy"
        ) from exc
