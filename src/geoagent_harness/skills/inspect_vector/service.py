"""Deterministic vector metadata inspection with a strict path boundary."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pyogrio

from geoagent_harness.schemas import (
    Extent,
    FieldInfo,
    InspectVectorResult,
    VectorLayerInfo,
)

ALLOWED_EXTENSIONS = {".geojson", ".gpkg", ".shp"}


class InspectVectorError(ValueError):
    """A safe, user-facing inspection failure."""


def _resolve_approved_path(path: Path, input_root: Path) -> tuple[Path, Path]:
    root = input_root.resolve(strict=True)
    candidate = path if path.is_absolute() else Path.cwd() / path

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise InspectVectorError(f"input does not exist: {path}") from exc

    if not resolved.is_file():
        raise InspectVectorError(f"input is not a file: {path}")

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise InspectVectorError(
            f"input must be inside the approved root: {input_root}"
        ) from exc

    if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise InspectVectorError(f"unsupported extension; allowed: {allowed}")

    return resolved, root


def _crs_text(frame: gpd.GeoDataFrame) -> str | None:
    if frame.crs is None:
        return None
    authority = frame.crs.to_authority()
    return f"{authority[0]}:{authority[1]}" if authority else frame.crs.to_string()


def _geometry_type(frame: gpd.GeoDataFrame) -> str:
    types = sorted(str(value) for value in frame.geom_type.dropna().unique())
    if not types:
        return "Unknown"
    return types[0] if len(types) == 1 else f"Mixed({','.join(types)})"


def _extent(frame: gpd.GeoDataFrame) -> Extent | None:
    if frame.empty or frame.geometry.dropna().empty:
        return None
    min_x, min_y, max_x, max_y = (float(value) for value in frame.total_bounds)
    return Extent(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)


def inspect_vector(path: Path, input_root: Path = Path("data/input")) -> InspectVectorResult:
    """Inspect GeoJSON, GeoPackage, or Shapefile metadata.

    The function accepts paths only within ``input_root``. It calls Python
    geospatial libraries directly and never evaluates a command or shell text.
    """
    try:
        resolved, root = _resolve_approved_path(path, input_root)
        layer_rows = pyogrio.list_layers(resolved)
    except InspectVectorError:
        raise
    except Exception as exc:
        raise InspectVectorError(f"could not inspect dataset: {exc}") from exc

    layers: list[VectorLayerInfo] = []
    for layer_name, _declared_geometry in layer_rows:
        try:
            frame = gpd.read_file(resolved, layer=str(layer_name), engine="pyogrio")
        except Exception as exc:
            raise InspectVectorError(
                f"could not read layer {layer_name!r}: {exc}"
            ) from exc

        fields = [
            FieldInfo(name=name, type=str(dtype))
            for name, dtype in frame.drop(columns=frame.geometry.name).dtypes.items()
        ]
        layers.append(
            VectorLayerInfo(
                name=str(layer_name),
                crs=_crs_text(frame),
                geometry_type=_geometry_type(frame),
                feature_count=len(frame),
                fields=fields,
                extent=_extent(frame),
            )
        )

    if not layers:
        raise InspectVectorError("dataset contains no vector layers")

    try:
        dataset_info = pyogrio.read_info(resolved, layer=str(layer_rows[0][0]))
    except Exception as exc:
        raise InspectVectorError(f"could not read dataset metadata: {exc}") from exc

    try:
        source = resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        source = resolved.relative_to(root).as_posix()

    return InspectVectorResult(
        source=source,
        driver=str(dataset_info.get("driver") or "Unknown"),
        layers=layers,
    )
