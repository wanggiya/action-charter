"""Trusted adapter for controlled raster conversion."""

from __future__ import annotations

import os
import re
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import rasterio
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.warp import (
    calculate_default_transform,
    reproject,
)

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skill_adapters.raster_inspection import (
    RasterInspectionError,
    inspect_raster,
    validate_raster_path,
)


_SAFE_TARGET_NAME = re.compile(
    r"^[a-z0-9][a-z0-9_-]{0,80}\.tif$"
)


class RasterConversionError(RuntimeError):
    """Raised when raster conversion fails safely."""


class RasterResampling(str, Enum):
    """Allowlisted raster resampling methods."""

    NEAREST = "nearest"
    BILINEAR = "bilinear"
    CUBIC = "cubic"


_RESAMPLING = {
    RasterResampling.NEAREST: Resampling.nearest,
    RasterResampling.BILINEAR: Resampling.bilinear,
    RasterResampling.CUBIC: Resampling.cubic,
}


class RasterConversionPlan(BaseModel):
    """Validated conversion that has not executed."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal[
        "planned_not_executed"
    ] = "planned_not_executed"

    source: str
    source_driver: str
    source_crs: str
    source_width: int = Field(gt=0)
    source_height: int = Field(gt=0)
    source_band_count: int = Field(gt=0)
    source_data_types: list[str] = Field(
        min_length=1
    )
    source_nodata_values: list[
        float | None
    ]

    target: str
    target_driver: Literal["GTiff"] = "GTiff"
    target_crs: str
    resampling: RasterResampling

    operation: Literal[
        "create_raster_dataset"
    ] = "create_raster_dataset"

    overwrite: Literal[False] = False
    execution_allowed: Literal[False] = False
    approval_required: Literal[True] = True
    validation_required: Literal[True] = True

    warnings: list[str] = Field(
        default_factory=list
    )


class RasterConversionResult(BaseModel):
    """Raster output awaiting deterministic validation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal[
        "converted_pending_validation"
    ] = "converted_pending_validation"

    source: str
    source_crs: str
    source_width: int = Field(gt=0)
    source_height: int = Field(gt=0)
    source_band_count: int = Field(gt=0)

    target: str
    target_driver: Literal["GTiff"] = "GTiff"
    target_crs: str
    target_width: int = Field(gt=0)
    target_height: int = Field(gt=0)
    target_band_count: int = Field(gt=0)
    target_data_types: list[str] = Field(
        min_length=1
    )
    target_nodata_values: list[
        float | None
    ]
    target_size_bytes: int = Field(gt=0)

    resampling: RasterResampling

    overwrite_performed: Literal[False] = False
    validation_required: Literal[True] = True
    validation_performed: Literal[False] = False
    final_success_claimed: Literal[False] = False


class RasterValidationCheck(BaseModel):
    """One deterministic raster validation check."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        pattern=r"^[a-z][a-z0-9_]*$"
    )
    passed: bool
    expected: Any
    actual: Any


class RasterConversionValidationResult(BaseModel):
    """Independent raster-conversion validation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal[
        "validation_passed",
        "validation_failed",
    ]
    passed: bool

    source: str
    target: str
    checks: list[
        RasterValidationCheck
    ] = Field(min_length=1)

    validation_performed: Literal[True] = True
    final_success_claimed: bool


def _lexical_path(path: Path) -> Path:
    """Make a path absolute without resolving links."""

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
    """Check existing components beneath a root."""

    relative = path.relative_to(root)
    current = root

    for part in relative.parts:
        current = current / part

        if current.is_symlink():
            return True

    return False


def _target_path(
    target_path: Path,
    *,
    output_root: Path,
) -> Path:
    """Validate a new GeoTIFF destination."""

    try:
        root = output_root.resolve(
            strict=True
        )
    except FileNotFoundError as exc:
        raise RasterConversionError(
            "approved output root does not exist"
        ) from exc

    lexical = _lexical_path(target_path)

    if not lexical.is_relative_to(root):
        raise RasterConversionError(
            "raster target escaped the approved "
            "output root"
        )

    if lexical == root:
        raise RasterConversionError(
            "raster target must be a file"
        )

    if _contains_symlink(
        lexical,
        root=root,
    ):
        raise RasterConversionError(
            "raster target path cannot contain "
            "symlinks"
        )

    try:
        parent = lexical.parent.resolve(
            strict=True
        )
    except FileNotFoundError as exc:
        raise RasterConversionError(
            "raster target parent does not exist"
        ) from exc

    if not parent.is_relative_to(root):
        raise RasterConversionError(
            "raster target parent escaped the "
            "approved output root"
        )

    if not parent.is_dir():
        raise RasterConversionError(
            "raster target parent is not a directory"
        )

    if not _SAFE_TARGET_NAME.fullmatch(
        lexical.name
    ):
        raise RasterConversionError(
            "raster target filename must use "
            "lowercase letters, numbers, underscores, "
            "or hyphens and end with .tif"
        )

    if lexical.exists():
        raise RasterConversionError(
            "raster target already exists; "
            "overwrite is blocked"
        )

    return lexical


def _canonical_crs(value: str) -> str:
    """Validate and normalize a requested CRS."""

    try:
        crs = CRS.from_user_input(value)
    except (
        rasterio.errors.CRSError,
        ValueError,
    ) as exc:
        raise RasterConversionError(
            "target CRS is invalid"
        ) from exc

    return crs.to_string()


def _display_path(
    path: Path,
    *,
    root: Path,
) -> str:
    return path.relative_to(
        root.resolve()
    ).as_posix()


def plan_raster_conversion(
    *,
    path: Path,
    target_path: Path,
    target_crs: str,
    input_root: Path,
    output_root: Path,
    resampling: RasterResampling = (
        RasterResampling.NEAREST
    ),
) -> RasterConversionPlan:
    """Validate conversion without creating output."""

    try:
        source = validate_raster_path(
            path,
            input_root=input_root,
        )
        inspected = inspect_raster(
            source,
            input_root=input_root,
        )
    except RasterInspectionError as exc:
        raise RasterConversionError(
            "raster source failed inspection"
        ) from exc

    if inspected.crs is None:
        raise RasterConversionError(
            "source raster has no CRS"
        )

    target = _target_path(
        target_path,
        output_root=output_root,
    )
    canonical_target_crs = _canonical_crs(
        target_crs
    )

    return RasterConversionPlan(
        source=inspected.source,
        source_driver=inspected.driver,
        source_crs=inspected.crs,
        source_width=inspected.width,
        source_height=inspected.height,
        source_band_count=(
            inspected.band_count
        ),
        source_data_types=(
            inspected.data_types
        ),
        source_nodata_values=(
            inspected.nodata_values
        ),
        target=_display_path(
            target,
            root=output_root,
        ),
        target_crs=canonical_target_crs,
        resampling=resampling,
        warnings=[
            (
                "Plan only: no output raster was "
                "created."
            ),
            (
                "Execution requires explicit write "
                "authorization and independent "
                "validation."
            ),
        ],
    )


def _temporary_target(target: Path) -> Path:
    return target.with_name(
        f".{target.stem}."
        f"{uuid.uuid4().hex}.tmp.tif"
    )


def _cleanup_temporary(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def convert_raster(
    *,
    path: Path,
    target_path: Path,
    target_crs: str,
    settings: MCPSettings,
    resampling: RasterResampling = (
        RasterResampling.NEAREST
    ),
) -> RasterConversionResult:
    """Create one new raster pending validation."""

    if not settings.enable_write_tools:
        raise RasterConversionError(
            "write tools are disabled"
        )

    if settings.allow_overwrite:
        raise RasterConversionError(
            "raster conversion does not permit "
            "overwrite mode"
        )

    plan = plan_raster_conversion(
        path=path,
        target_path=target_path,
        target_crs=target_crs,
        input_root=settings.input_root,
        output_root=settings.output_root,
        resampling=resampling,
    )

    source = validate_raster_path(
        path,
        input_root=settings.input_root,
    )
    target = _target_path(
        target_path,
        output_root=settings.output_root,
    )
    temporary = _temporary_target(target)

    try:
        with rasterio.open(
            source,
            mode="r",
        ) as source_dataset:
            if source_dataset.crs is None:
                raise RasterConversionError(
                    "source raster has no CRS"
                )

            transform, width, height = (
                calculate_default_transform(
                    source_dataset.crs,
                    plan.target_crs,
                    source_dataset.width,
                    source_dataset.height,
                    *source_dataset.bounds,
                )
            )

            metadata = (
                source_dataset.meta.copy()
            )
            metadata.update(
                {
                    "driver": "GTiff",
                    "crs": plan.target_crs,
                    "transform": transform,
                    "width": width,
                    "height": height,
                }
            )

            with rasterio.open(
                temporary,
                mode="w",
                **metadata,
            ) as target_dataset:
                for band_index in range(
                    1,
                    source_dataset.count + 1,
                ):
                    reproject(
                        source=rasterio.band(
                            source_dataset,
                            band_index,
                        ),
                        destination=rasterio.band(
                            target_dataset,
                            band_index,
                        ),
                        src_transform=(
                            source_dataset.transform
                        ),
                        src_crs=(
                            source_dataset.crs
                        ),
                        src_nodata=(
                            source_dataset.nodatavals[
                                band_index - 1
                            ]
                        ),
                        dst_transform=transform,
                        dst_crs=plan.target_crs,
                        dst_nodata=(
                            source_dataset.nodatavals[
                                band_index - 1
                            ]
                        ),
                        resampling=(
                            _RESAMPLING[
                                plan.resampling
                            ]
                        ),
                    )

        if (
            not temporary.is_file()
            or temporary.stat().st_size <= 0
        ):
            raise RasterConversionError(
                "raster writer produced no valid "
                "temporary output"
            )

        os.chmod(temporary, 0o644)

        try:
            os.link(
                temporary,
                target,
            )
        except FileExistsError as exc:
            raise RasterConversionError(
                "raster target appeared during "
                "conversion; overwrite is blocked"
            ) from exc

    except RasterConversionError:
        raise
    except (
        OSError,
        rasterio.errors.RasterioError,
        ValueError,
    ) as exc:
        raise RasterConversionError(
            "raster conversion failed"
        ) from exc
    finally:
        _cleanup_temporary(temporary)

    try:
        converted = inspect_raster(
            target,
            input_root=settings.output_root,
        )
    except RasterInspectionError as exc:
        raise RasterConversionError(
            "converted raster could not be "
            "inspected"
        ) from exc

    return RasterConversionResult(
        source=plan.source,
        source_crs=plan.source_crs,
        source_width=plan.source_width,
        source_height=plan.source_height,
        source_band_count=(
            plan.source_band_count
        ),
        target=plan.target,
        target_crs=(
            converted.crs
            or plan.target_crs
        ),
        target_width=converted.width,
        target_height=converted.height,
        target_band_count=(
            converted.band_count
        ),
        target_data_types=(
            converted.data_types
        ),
        target_nodata_values=(
            converted.nodata_values
        ),
        target_size_bytes=(
            target.stat().st_size
        ),
        resampling=plan.resampling,
        overwrite_performed=False,
        validation_required=True,
        validation_performed=False,
        final_success_claimed=False,
    )


def _check(
    *,
    name: str,
    expected: Any,
    actual: Any,
) -> RasterValidationCheck:
    return RasterValidationCheck(
        name=name,
        passed=expected == actual,
        expected=expected,
        actual=actual,
    )


def validate_raster_conversion(
    *,
    path: Path,
    target_path: Path,
    target_crs: str,
    input_root: Path,
    output_root: Path,
) -> RasterConversionValidationResult:
    """Independently validate a converted raster."""

    try:
        source = inspect_raster(
            path,
            input_root=input_root,
        )
        target = inspect_raster(
            target_path,
            input_root=output_root,
        )
    except RasterInspectionError as exc:
        raise RasterConversionError(
            "raster validation inspection failed"
        ) from exc

    expected_crs = _canonical_crs(
        target_crs
    )

    target_file = validate_raster_path(
        target_path,
        input_root=output_root,
    )

    checks = [
        _check(
            name="target_driver",
            expected="GTiff",
            actual=target.driver,
        ),
        _check(
            name="target_crs",
            expected=expected_crs,
            actual=target.crs,
        ),
        _check(
            name="band_count",
            expected=source.band_count,
            actual=target.band_count,
        ),
        _check(
            name="data_types",
            expected=source.data_types,
            actual=target.data_types,
        ),
        _check(
            name="nodata_values",
            expected=source.nodata_values,
            actual=target.nodata_values,
        ),
        RasterValidationCheck(
            name="target_width",
            passed=target.width > 0,
            expected="positive",
            actual=target.width,
        ),
        RasterValidationCheck(
            name="target_height",
            passed=target.height > 0,
            expected="positive",
            actual=target.height,
        ),
        RasterValidationCheck(
            name="target_size_bytes",
            passed=(
                target_file.stat().st_size > 0
            ),
            expected="positive",
            actual=target_file.stat().st_size,
        ),
    ]

    passed = all(
        check.passed
        for check in checks
    )

    return RasterConversionValidationResult(
        status=(
            "validation_passed"
            if passed
            else "validation_failed"
        ),
        passed=passed,
        source=source.source,
        target=target.source,
        checks=checks,
        validation_performed=True,
        final_success_claimed=passed,
    )

