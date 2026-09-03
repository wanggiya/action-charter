"""Deterministic read-only assessment of vector spatial-data contracts."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
from pandas.api import types as pandas_types
from pyproj import CRS

from geoagent_harness.spatial_contracts.schemas import (
    SpatialDataContractAssessment,
    SpatialDataContractCheck,
    SpatialExtentRule,
    VectorFieldType,
    VectorSpatialDataContract,
)
from geoagent_harness.spatial_contracts.storage import (
    spatial_data_contract_sha256,
)


ALLOWED_VECTOR_EXTENSIONS = {".geojson", ".gpkg", ".shp"}
SHAPEFILE_MEMBER_SUFFIXES = {
    ".cpg",
    ".dbf",
    ".prj",
    ".qix",
    ".sbn",
    ".sbx",
    ".shp",
    ".shx",
}


class SpatialDataContractAssessmentError(RuntimeError):
    """Raised when a dataset cannot be safely assessed."""


def _resolve_dataset_path(path: Path, input_root: Path) -> tuple[Path, Path]:
    if input_root.is_symlink():
        raise SpatialDataContractAssessmentError(
            "spatial dataset root cannot be a symlink"
        )

    try:
        root = input_root.resolve(strict=True)
    except OSError as exc:
        raise SpatialDataContractAssessmentError(
            "spatial dataset root is unavailable"
        ) from exc

    if not root.is_dir():
        raise SpatialDataContractAssessmentError(
            "spatial dataset root must be a directory"
        )

    candidate = path if path.is_absolute() else root / path
    if candidate.is_symlink():
        raise SpatialDataContractAssessmentError(
            "spatial dataset cannot be a symlink"
        )

    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise SpatialDataContractAssessmentError(
            "spatial dataset is unavailable"
        ) from exc

    if not resolved.is_file():
        raise SpatialDataContractAssessmentError(
            "spatial dataset must be a regular file"
        )
    if not resolved.is_relative_to(root):
        raise SpatialDataContractAssessmentError(
            "spatial dataset escaped the approved input root"
        )
    if resolved.suffix.lower() not in ALLOWED_VECTOR_EXTENSIONS:
        raise SpatialDataContractAssessmentError(
            "spatial dataset has an unsupported extension"
        )

    return resolved, root


def _dataset_members(dataset: Path) -> tuple[Path, ...]:
    if dataset.suffix.lower() != ".shp":
        return (dataset,)

    members = tuple(
        sorted(
            (
                path
                for path in dataset.parent.iterdir()
                if path.is_file()
                and path.stem == dataset.stem
                and path.suffix.lower() in SHAPEFILE_MEMBER_SUFFIXES
            ),
            key=lambda path: path.suffix.lower(),
        )
    )
    required = {".shp", ".shx", ".dbf"}
    present = {path.suffix.lower() for path in members}
    if not required.issubset(present):
        raise SpatialDataContractAssessmentError(
            "shapefile dataset is missing required members"
        )

    for member in members:
        if member.is_symlink():
            raise SpatialDataContractAssessmentError(
                "spatial dataset members cannot be symlinks"
            )

    return members


def _dataset_sha256(dataset: Path) -> str:
    digest = hashlib.sha256()
    try:
        for member in _dataset_members(dataset):
            digest.update(member.suffix.lower().encode("utf-8"))
            digest.update(b"\0")
            digest.update(member.read_bytes())
            digest.update(b"\0")
    except SpatialDataContractAssessmentError:
        raise
    except OSError as exc:
        raise SpatialDataContractAssessmentError(
            "spatial dataset could not be hashed"
        ) from exc
    return digest.hexdigest()


def _select_layer(dataset: Path, requested: str | None) -> str:
    try:
        rows = pyogrio.list_layers(dataset)
    except Exception as exc:
        raise SpatialDataContractAssessmentError(
            "spatial dataset layers could not be inspected"
        ) from exc

    layers = [str(row[0]) for row in rows]
    if not layers:
        raise SpatialDataContractAssessmentError(
            "spatial dataset contains no vector layers"
        )
    if requested is not None:
        if requested not in layers:
            raise SpatialDataContractAssessmentError(
                "contract layer does not exist in the dataset"
            )
        return requested
    if len(layers) != 1:
        raise SpatialDataContractAssessmentError(
            "contract must select a layer for a multilayer dataset"
        )
    return layers[0]


def _logical_field_type(series: pd.Series) -> str:
    dtype = series.dtype
    if pandas_types.is_bool_dtype(dtype):
        return VectorFieldType.BOOLEAN.value
    if pandas_types.is_integer_dtype(dtype):
        return VectorFieldType.INTEGER.value
    if pandas_types.is_float_dtype(dtype):
        return VectorFieldType.FLOAT.value
    if pandas_types.is_datetime64_any_dtype(dtype):
        return VectorFieldType.DATETIME.value

    values = series.dropna()
    if not values.empty and all(
        isinstance(value, dt.date) and not isinstance(value, dt.datetime)
        for value in values
    ):
        return VectorFieldType.DATE.value
    if values.empty or all(isinstance(value, str) for value in values):
        return VectorFieldType.STRING.value
    return str(dtype)


def _extent_values(
    frame: gpd.GeoDataFrame,
) -> tuple[float, float, float, float] | None:
    usable = frame.geometry.dropna()
    usable = usable[~usable.is_empty]
    if usable.empty:
        return None
    values = tuple(float(value) for value in usable.total_bounds)
    return values[0], values[1], values[2], values[3]


def _expected_extent_passes(
    actual: tuple[float, float, float, float] | None,
    rule: SpatialExtentRule,
) -> bool:
    if actual is None:
        return False
    expected = (rule.min_x, rule.min_y, rule.max_x, rule.max_y)
    return all(
        abs(actual_value - expected_value) <= rule.tolerance
        for actual_value, expected_value in zip(actual, expected, strict=True)
    )


def _permitted_extent_passes(
    actual: tuple[float, float, float, float] | None,
    rule: SpatialExtentRule,
) -> bool:
    if actual is None:
        return False
    min_x, min_y, max_x, max_y = actual
    return (
        min_x >= rule.min_x - rule.tolerance
        and min_y >= rule.min_y - rule.tolerance
        and max_x <= rule.max_x + rule.tolerance
        and max_y <= rule.max_y + rule.tolerance
    )


def assess_spatial_data_contract(
    *,
    path: Path,
    contract: VectorSpatialDataContract,
    input_root: Path = Path("data/input"),
) -> SpatialDataContractAssessment:
    """Assess one vector layer without modifying files or databases."""

    dataset, root = _resolve_dataset_path(path, input_root)
    dataset_digest_before = _dataset_sha256(dataset)
    layer = _select_layer(dataset, contract.layer)

    try:
        frame = gpd.read_file(dataset, layer=layer, engine="pyogrio")
    except Exception as exc:
        raise SpatialDataContractAssessmentError(
            "spatial dataset layer could not be read"
        ) from exc

    checks: list[SpatialDataContractCheck] = []

    def add(check_id: str, passed: bool, message: str) -> None:
        checks.append(
            SpatialDataContractCheck(
                check_id=check_id,
                passed=passed,
                message=message,
            )
        )

    if frame.crs is None:
        crs_passed = False
        actual_crs = "missing"
    else:
        try:
            crs_passed = frame.crs.equals(
                CRS.from_user_input(contract.expected_crs)
            )
        except Exception as exc:
            raise SpatialDataContractAssessmentError(
                "contract expected CRS could not be interpreted"
            ) from exc
        authority = frame.crs.to_authority()
        actual_crs = (
            f"{authority[0]}:{authority[1]}"
            if authority
            else frame.crs.to_string()
        )
    add(
        "crs",
        crs_passed,
        (
            f"CRS matches {contract.expected_crs}"
            if crs_passed
            else f"expected CRS {contract.expected_crs}; found {actual_crs}"
        ),
    )

    geometry = frame.geometry
    usable_geometry = geometry.dropna()
    geometry_types = sorted(
        str(value) for value in usable_geometry.geom_type.unique()
    )
    allowed_types = {value.value for value in contract.allowed_geometry_types}
    unexpected_types = sorted(set(geometry_types) - allowed_types)
    add(
        "geometry_types",
        not unexpected_types,
        (
            "geometry types are allowed"
            if not unexpected_types
            else "dataset contains geometry types outside the contract: "
            + ", ".join(unexpected_types)
        ),
    )

    mixed_passed = contract.mixed_geometry_allowed or len(geometry_types) <= 1
    add(
        "mixed_geometry",
        mixed_passed,
        (
            "mixed-geometry policy is satisfied"
            if mixed_passed
            else "dataset contains mixed geometry types"
        ),
    )

    feature_count = len(frame)
    maximum = contract.feature_count.maximum
    feature_count_passed = (
        feature_count >= contract.feature_count.minimum
        and (maximum is None or feature_count <= maximum)
    )
    add(
        "feature_count",
        feature_count_passed,
        (
            "feature count is within contract bounds"
            if feature_count_passed
            else f"feature count {feature_count} is outside contract bounds"
        ),
    )

    for field in contract.required_fields:
        exists = field.name in frame.columns and field.name != frame.geometry.name
        add(
            f"required_field:{field.name}",
            exists,
            (
                f"required field {field.name} exists"
                if exists
                else f"required field {field.name} is missing"
            ),
        )
        if not exists:
            continue

        series = frame[field.name]
        actual_type = _logical_field_type(series)
        type_passed = actual_type == field.field_type.value
        add(
            f"field_type:{field.name}",
            type_passed,
            (
                f"field {field.name} has type {actual_type}"
                if type_passed
                else f"field {field.name} expected type "
                f"{field.field_type.value}; found {actual_type}"
            ),
        )

        null_fraction = float(series.isna().mean()) if feature_count else 0.0
        null_passed = null_fraction <= field.max_null_fraction
        add(
            f"null_fraction:{field.name}",
            null_passed,
            (
                f"field {field.name} null fraction is within threshold"
                if null_passed
                else f"field {field.name} null fraction "
                f"{null_fraction:.6f} exceeds {field.max_null_fraction:.6f}"
            ),
        )

    for rule in contract.unique_keys:
        identity = "+".join(rule.fields)
        if not all(name in frame.columns for name in rule.fields):
            add(
                f"unique_key:{identity}",
                False,
                f"unique key {identity} cannot be checked because fields are missing",
            )
            continue

        values = frame[rule.fields]
        has_null = bool(values.isna().any(axis=1).any())
        duplicate_count = int(values.duplicated(keep="first").sum())
        unique_passed = duplicate_count == 0 and (
            rule.allow_nulls or not has_null
        )
        add(
            f"unique_key:{identity}",
            unique_passed,
            (
                f"unique key {identity} is satisfied"
                if unique_passed
                else f"unique key {identity} has {duplicate_count} "
                "duplicates or disallowed nulls"
            ),
        )

    null_geometry_count = int(geometry.isna().sum())
    non_null_geometry = geometry.dropna()
    empty_geometry_count = int(non_null_geometry.is_empty.sum())
    invalid_geometry_count = int((~non_null_geometry.is_valid).sum())
    comparable_geometry = non_null_geometry[~non_null_geometry.is_empty]
    geometry_bytes = comparable_geometry.apply(lambda value: value.wkb)
    duplicate_geometry_count = int(
        geometry_bytes.duplicated(keep="first").sum()
    )

    quality_values = (
        ("invalid_geometry", invalid_geometry_count, contract.geometry_quality.max_invalid_count),
        ("empty_geometry", empty_geometry_count, contract.geometry_quality.max_empty_count),
        ("null_geometry", null_geometry_count, contract.geometry_quality.max_null_count),
        ("duplicate_geometry", duplicate_geometry_count, contract.geometry_quality.max_duplicate_count),
    )
    for check_id, actual, maximum_allowed in quality_values:
        quality_passed = actual <= maximum_allowed
        add(
            check_id,
            quality_passed,
            (
                f"{check_id} count is within threshold"
                if quality_passed
                else f"{check_id} count {actual} exceeds {maximum_allowed}"
            ),
        )

    actual_extent = _extent_values(frame)
    if contract.expected_extent is not None:
        extent_passed = _expected_extent_passes(
            actual_extent,
            contract.expected_extent,
        )
        add(
            "expected_extent",
            extent_passed,
            (
                "dataset extent matches the expected extent"
                if extent_passed
                else "dataset extent does not match the expected extent"
            ),
        )
    if contract.permitted_extent is not None:
        extent_passed = _permitted_extent_passes(
            actual_extent,
            contract.permitted_extent,
        )
        add(
            "permitted_extent",
            extent_passed,
            (
                "dataset extent is within the permitted extent"
                if extent_passed
                else "dataset extent exceeds the permitted extent"
            ),
        )

    dataset_digest_after = _dataset_sha256(dataset)
    if dataset_digest_after != dataset_digest_before:
        raise SpatialDataContractAssessmentError(
            "spatial dataset changed during contract assessment"
        )

    violations = [check.message for check in checks if not check.passed]
    source = dataset.relative_to(root).as_posix()
    return SpatialDataContractAssessment(
        contract_id=contract.contract_id,
        contract_version=contract.contract_version,
        contract_sha256=spatial_data_contract_sha256(contract),
        dataset_sha256=dataset_digest_before,
        dataset_sha256_after=dataset_digest_after,
        dataset_unchanged=True,
        source=source,
        layer=layer,
        feature_count=feature_count,
        geometry_types=geometry_types,
        invalid_geometry_count=invalid_geometry_count,
        empty_geometry_count=empty_geometry_count,
        null_geometry_count=null_geometry_count,
        duplicate_geometry_count=duplicate_geometry_count,
        checks=checks,
        violations=violations,
        passed=not violations,
    )
