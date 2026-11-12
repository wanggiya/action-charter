"""Trusted read-only adapter for raster inspection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import rasterio
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class RasterInspectionError(RuntimeError):
    """Raised when raster inspection cannot be completed."""


class RasterBounds(BaseModel):
    """Raster bounds in source coordinates."""

    model_config = ConfigDict(extra="forbid")

    left: float
    bottom: float
    right: float
    top: float


class RasterInspectionResult(BaseModel):
    """Typed metadata from one raster dataset."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    status: Literal["completed"] = "completed"
    source: str

    driver: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    band_count: int = Field(gt=0)

    data_types: list[str] = Field(
        min_length=1
    )
    crs: str | None
    bounds: RasterBounds
    transform: list[float] = Field(
        min_length=6,
        max_length=6,
    )
    nodata_values: list[float | None]

    filesystem_modified: Literal[False] = False
    database_modified: Literal[False] = False
    execution_performed: Literal[True] = True


def _lexical_path(
    path: Path,
) -> Path:
    """Return an absolute path without resolving symlinks."""

    return Path(
        os.path.abspath(
            os.fspath(path)
        )
    )


def _contains_symlink(
    path: Path,
    *,
    root: Path,
) -> bool:
    """Check every path component beneath the root."""

    relative = path.relative_to(root)
    current = root

    for part in relative.parts:
        current = current / part

        if current.is_symlink():
            return True

    return False


def validate_raster_path(
    path: Path,
    *,
    input_root: Path,
) -> Path:
    """Require one existing non-symlink file under input root."""

    root = input_root.resolve()
    lexical = _lexical_path(path)

    if not lexical.is_relative_to(root):
        raise RasterInspectionError(
            "raster path escaped the approved input root"
        )

    if _contains_symlink(
        lexical,
        root=root,
    ):
        raise RasterInspectionError(
            "raster path cannot contain symlinks"
        )

    resolved = lexical.resolve()

    if not resolved.is_relative_to(root):
        raise RasterInspectionError(
            "raster path escaped the approved input root"
        )

    if not resolved.is_file():
        raise RasterInspectionError(
            "raster input does not exist"
        )

    return resolved


def inspect_raster(
    path: Path,
    *,
    input_root: Path,
) -> RasterInspectionResult:
    """Inspect one raster without modifying it."""

    safe_path = validate_raster_path(
        path,
        input_root=input_root,
    )

    try:
        before = safe_path.stat()

        with rasterio.open(
            safe_path,
            mode="r",
        ) as dataset:
            crs = (
                dataset.crs.to_string()
                if dataset.crs is not None
                else None
            )

            result = RasterInspectionResult(
                source=(
                    safe_path.relative_to(
                        input_root.resolve()
                    ).as_posix()
                ),
                driver=dataset.driver,
                width=dataset.width,
                height=dataset.height,
                band_count=dataset.count,
                data_types=list(
                    dataset.dtypes
                ),
                crs=crs,
                bounds=RasterBounds(
                    left=dataset.bounds.left,
                    bottom=dataset.bounds.bottom,
                    right=dataset.bounds.right,
                    top=dataset.bounds.top,
                ),
                transform=[
                    float(value)
                    for value in tuple(
                        dataset.transform
                    )[:6]
                ],
                nodata_values=[
                    (
                        float(value)
                        if value is not None
                        else None
                    )
                    for value in dataset.nodatavals
                ],
                filesystem_modified=False,
                database_modified=False,
                execution_performed=True,
            )

        after = safe_path.stat()
    except RasterInspectionError:
        raise
    except (
        OSError,
        rasterio.errors.RasterioError,
        ValueError,
    ) as exc:
        raise RasterInspectionError(
            "raster inspection failed"
        ) from exc

    if (
        before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise RasterInspectionError(
            "raster changed during inspection"
        )

    return result

