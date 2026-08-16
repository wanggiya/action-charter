"""Deterministic policy for vector conversion planning."""

from __future__ import annotations

import re
from pathlib import Path

from geoagent_harness.skills.convert_vector.schemas import (
    ConvertVectorPlan,
    VectorOutputFormat,
)
from geoagent_harness.skills.inspect_vector.service import (
    InspectVectorError,
    inspect_vector,
)


_SAFE_FILENAME = re.compile(
    r"^[a-z0-9][a-z0-9_-]{0,80}"
    r"\.(geojson|gpkg)$"
)

_SAFE_LAYER = re.compile(
    r"^[a-z_][a-z0-9_]{0,62}$"
)

_OUTPUT_FORMATS = {
    ".geojson": (
        VectorOutputFormat.GEOJSON,
        "GeoJSON",
    ),
    ".gpkg": (
        VectorOutputFormat.GEOPACKAGE,
        "GPKG",
    ),
}


class ConvertVectorPolicyError(ValueError):
    """Raised when a conversion plan is unsafe."""


def _choose_source_layer(
    layer_names: list[str],
    requested: str | None,
) -> str:
    if requested is not None:
        if requested not in layer_names:
            raise ConvertVectorPolicyError(
                f"source layer {requested!r} "
                "was not found"
            )

        return requested

    if len(layer_names) != 1:
        raise ConvertVectorPolicyError(
            "source_layer is required when the "
            "dataset contains multiple layers"
        )

    return layer_names[0]


def _resolve_target(
    *,
    target_path: Path,
    output_root: Path,
) -> tuple[Path, Path]:
    root = output_root.resolve()

    candidate = (
        target_path
        if target_path.is_absolute()
        else Path.cwd() / target_path
    ).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ConvertVectorPolicyError(
            "target must be inside the approved "
            "output root"
        ) from exc

    if candidate == root:
        raise ConvertVectorPolicyError(
            "target must be a file, not the "
            "output root"
        )

    if not _SAFE_FILENAME.fullmatch(
        candidate.name
    ):
        raise ConvertVectorPolicyError(
            "target filename must use lowercase "
            "letters, numbers, underscores, or "
            "hyphens and end with .geojson or .gpkg"
        )

    if candidate.exists():
        raise ConvertVectorPolicyError(
            "target already exists; overwrite is "
            "blocked"
        )

    return candidate, root


def _display_path(
    path: Path,
    *,
    trusted_root: Path,
) -> str:
    working_directory = Path.cwd().resolve()

    try:
        return path.relative_to(
            working_directory
        ).as_posix()
    except ValueError:
        return path.relative_to(
            trusted_root
        ).as_posix()


def plan_vector_conversion(
    *,
    path: Path,
    target_path: Path,
    input_root: Path = Path("data/input"),
    output_root: Path = Path("data/output"),
    source_layer: str | None = None,
    target_layer: str | None = None,
) -> ConvertVectorPlan:
    """Validate a conversion without writing output."""
    try:
        inspected = inspect_vector(
            path=path,
            input_root=input_root,
        )
    except InspectVectorError as exc:
        raise ConvertVectorPolicyError(
            str(exc)
        ) from exc

    layer_names = [
        layer.name
        for layer in inspected.layers
    ]

    selected_source_layer = (
        _choose_source_layer(
            layer_names,
            source_layer,
        )
    )

    source_info = next(
        layer
        for layer in inspected.layers
        if layer.name == selected_source_layer
    )

    if source_info.crs is None:
        raise ConvertVectorPolicyError(
            "source layer has no CRS; conversion "
            "is blocked"
        )

    resolved_target, resolved_output_root = (
        _resolve_target(
            target_path=target_path,
            output_root=output_root,
        )
    )

    suffix = resolved_target.suffix.lower()

    try:
        output_format, target_driver = (
            _OUTPUT_FORMATS[suffix]
        )
    except KeyError as exc:
        raise ConvertVectorPolicyError(
            "unsupported output format"
        ) from exc

    active_target_layer = (
        target_layer
        if target_layer is not None
        else resolved_target.stem.replace(
            "-",
            "_",
        )
    )

    if not _SAFE_LAYER.fullmatch(
        active_target_layer
    ):
        raise ConvertVectorPolicyError(
            "target_layer must be a safe lowercase "
            "GIS layer identifier"
        )

    return ConvertVectorPlan(
        source=inspected.source,
        source_driver=inspected.driver,
        source_layer=selected_source_layer,
        source_crs=source_info.crs,
        source_geometry_type=(
            source_info.geometry_type
        ),
        source_feature_count=(
            source_info.feature_count
        ),
        source_fields=[
            field.name
            for field in source_info.fields
        ],
        target=_display_path(
            resolved_target,
            trusted_root=resolved_output_root,
        ),
        target_format=output_format,
        target_driver=target_driver,
        target_layer=active_target_layer,
        overwrite=False,
        execution_allowed=False,
        approval_required=True,
        validation_required=True,
        warnings=[
            (
                "Plan only: no output file was "
                "created."
            ),
            (
                "Execution must preserve CRS, "
                "features, geometry type, fields, "
                "and extent, then pass deterministic "
                "validation."
            ),
        ],
    )