"""Deterministic validation for vector conversion."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import geopandas as gpd

from geoagent_harness.skills.convert_vector.schemas import (
    ConvertVectorValidationResult,
    VectorValidationCheck,
)
from geoagent_harness.skills.inspect_vector.service import (
    InspectVectorError,
    inspect_vector,
)


_TARGET_DRIVERS = {
    ".geojson": "GeoJSON",
    ".gpkg": "GPKG",
}


class ConvertVectorValidationError(ValueError):
    """Raised when conversion evidence cannot be validated."""


def _resolve_existing_file(
    *,
    path: Path,
    root: Path,
    label: str,
) -> Path:
    try:
        approved_root = root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ConvertVectorValidationError(
            f"{label} root does not exist"
        ) from exc

    candidates = (
        [path]
        if path.is_absolute()
        else [
            Path.cwd() / path,
            approved_root / path,
        ]
    )

    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            continue

        try:
            resolved.relative_to(approved_root)
        except ValueError:
            continue

        if not resolved.is_file():
            raise ConvertVectorValidationError(
                f"{label} is not a file"
            )

        return resolved

    raise ConvertVectorValidationError(
        f"{label} does not exist inside its approved root"
    )


def _choose_layer(
    *,
    layer_names: list[str],
    requested: str | None,
    default: str | None,
    label: str,
) -> str:
    selected = requested or default

    if selected is not None:
        if selected not in layer_names:
            raise ConvertVectorValidationError(
                f"{label} layer {selected!r} was not found"
            )

        return selected

    if len(layer_names) != 1:
        raise ConvertVectorValidationError(
            f"{label}_layer is required when the "
            "dataset contains multiple layers"
        )

    return layer_names[0]


def _field_names(
    frame: gpd.GeoDataFrame,
) -> list[str]:
    geometry_column = frame.geometry.name

    return [
        str(column)
        for column in frame.columns
        if column != geometry_column
    ]


def _geometry_types(
    frame: gpd.GeoDataFrame,
) -> list[str]:
    return sorted(
        {
            str(value)
            for value in frame.geom_type.dropna()
        }
    )


def _null_geometry_count(
    frame: gpd.GeoDataFrame,
) -> int:
    return int(frame.geometry.isna().sum())


def _invalid_geometry_count(
    frame: gpd.GeoDataFrame,
) -> int:
    populated = frame.geometry.notna()

    return int(
        (
            populated
            & ~frame.geometry.is_valid
        ).sum()
    )


def _extent(
    frame: gpd.GeoDataFrame,
) -> list[float] | None:
    populated = frame.geometry.dropna()

    if frame.empty or populated.empty:
        return None

    return [
        float(value)
        for value in frame.total_bounds
    ]


def _extents_equal(
    expected: list[float] | None,
    actual: list[float] | None,
    *,
    tolerance: float,
) -> bool:
    if expected is None or actual is None:
        return expected == actual

    if len(expected) != len(actual):
        return False

    return all(
        math.isclose(
            expected_value,
            actual_value,
            rel_tol=tolerance,
            abs_tol=tolerance,
        )
        for expected_value, actual_value in zip(
            expected,
            actual,
            strict=True,
        )
    )


def _check(
    *,
    name: str,
    passed: bool,
    expected: Any,
    actual: Any,
) -> VectorValidationCheck:
    return VectorValidationCheck(
        name=name,
        passed=passed,
        expected=expected,
        actual=actual,
    )


def validate_vector_conversion(
    *,
    path: Path,
    target_path: Path,
    input_root: Path = Path("data/input"),
    output_root: Path = Path("data/output"),
    source_layer: str | None = None,
    target_layer: str | None = None,
    extent_tolerance: float = 1e-8,
) -> ConvertVectorValidationResult:
    """Compare source and converted vector datasets."""

    if extent_tolerance <= 0:
        raise ConvertVectorValidationError(
            "extent_tolerance must be positive"
        )

    source_file = _resolve_existing_file(
        path=path,
        root=input_root,
        label="source",
    )
    target_file = _resolve_existing_file(
        path=target_path,
        root=output_root,
        label="target",
    )

    expected_driver = _TARGET_DRIVERS.get(
        target_file.suffix.lower()
    )

    if expected_driver is None:
        raise ConvertVectorValidationError(
            "target must end with .geojson or .gpkg"
        )

    try:
        source_inspection = inspect_vector(
            source_file,
            input_root=input_root,
        )
        target_inspection = inspect_vector(
            target_file,
            input_root=output_root,
        )
    except InspectVectorError as exc:
        raise ConvertVectorValidationError(
            str(exc)
        ) from exc

    selected_source_layer = _choose_layer(
        layer_names=[
            layer.name
            for layer in source_inspection.layers
        ],
        requested=source_layer,
        default=None,
        label="source",
    )

    default_target_layer = (
        target_file.stem.replace(
            "-",
            "_",
        )
        if target_file.suffix.lower() == ".gpkg"
        else None
    )

    selected_target_layer = _choose_layer(
        layer_names=[
            layer.name
            for layer in target_inspection.layers
        ],
        requested=target_layer,
        default=default_target_layer,
        label="target",
    )

    try:
        source_frame = gpd.read_file(
            source_file,
            layer=selected_source_layer,
            engine="pyogrio",
        )
        target_frame = gpd.read_file(
            target_file,
            layer=selected_target_layer,
            engine="pyogrio",
        )
    except Exception as exc:
        raise ConvertVectorValidationError(
            "source or target layer could not be read"
        ) from exc

    source_extent = _extent(source_frame)
    target_extent = _extent(target_frame)

    source_fields = _field_names(source_frame)
    target_fields = _field_names(target_frame)

    source_geometry_types = _geometry_types(
        source_frame
    )
    target_geometry_types = _geometry_types(
        target_frame
    )

    source_null_count = _null_geometry_count(
        source_frame
    )
    target_null_count = _null_geometry_count(
        target_frame
    )

    source_invalid_count = _invalid_geometry_count(
        source_frame
    )
    target_invalid_count = _invalid_geometry_count(
        target_frame
    )

    source_crs = (
        source_frame.crs.to_string()
        if source_frame.crs is not None
        else None
    )
    target_crs = (
        target_frame.crs.to_string()
        if target_frame.crs is not None
        else None
    )

    checks = [
        _check(
            name="target_file_nonempty",
            passed=target_file.stat().st_size > 0,
            expected="greater_than_zero",
            actual=target_file.stat().st_size,
        ),
        _check(
            name="target_driver",
            passed=(
                target_inspection.driver
                == expected_driver
            ),
            expected=expected_driver,
            actual=target_inspection.driver,
        ),
        _check(
            name="crs_preserved",
            passed=(
                source_frame.crs is not None
                and target_frame.crs is not None
                and source_frame.crs
                == target_frame.crs
            ),
            expected=source_crs,
            actual=target_crs,
        ),
        _check(
            name="feature_count_preserved",
            passed=(
                len(source_frame)
                == len(target_frame)
            ),
            expected=len(source_frame),
            actual=len(target_frame),
        ),
        _check(
            name="fields_preserved",
            passed=source_fields == target_fields,
            expected=source_fields,
            actual=target_fields,
        ),
        _check(
            name="geometry_type_preserved",
            passed=(
                source_geometry_types
                == target_geometry_types
            ),
            expected=source_geometry_types,
            actual=target_geometry_types,
        ),
        _check(
            name="null_geometry_count_preserved",
            passed=(
                source_null_count
                == target_null_count
            ),
            expected=source_null_count,
            actual=target_null_count,
        ),
        _check(
            name="invalid_geometry_count_preserved",
            passed=(
                source_invalid_count
                == target_invalid_count
            ),
            expected=source_invalid_count,
            actual=target_invalid_count,
        ),
        _check(
            name="extent_preserved",
            passed=_extents_equal(
                source_extent,
                target_extent,
                tolerance=extent_tolerance,
            ),
            expected=source_extent,
            actual=target_extent,
        ),
    ]

    passed = all(
        check.passed
        for check in checks
    )

    warnings: list[str] = []

    if not passed:
        warnings.append(
            "Final success is withheld because one "
            "or more deterministic conversion checks "
            "failed."
        )

    return ConvertVectorValidationResult(
        status=(
            "validation_passed"
            if passed
            else "validation_failed"
        ),
        passed=passed,
        source=source_inspection.source,
        source_layer=selected_source_layer,
        target=target_inspection.source,
        target_layer=selected_target_layer,
        checks=checks,
        source_feature_count=len(source_frame),
        target_feature_count=len(target_frame),
        source_invalid_geometry_count=(
            source_invalid_count
        ),
        target_invalid_geometry_count=(
            target_invalid_count
        ),
        source_null_geometry_count=source_null_count,
        target_null_geometry_count=target_null_count,
        warnings=warnings,
    )
