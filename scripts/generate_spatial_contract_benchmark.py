"""Generate deterministic dirty-vector benchmark fixtures."""

from __future__ import annotations

import warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point, Polygon


PROJECT_ROOT = Path(__file__).parents[1]
OUTPUT_ROOT = (
    PROJECT_ROOT
    / "benchmarks"
    / "spatial-contracts"
    / "vector"
    / "data"
)


def _frame(
    feature_ids,
    names,
    geometries,
    *,
    crs: str | None = "EPSG:4326",
) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "feature_id": feature_ids,
            "name": names,
        },
        geometry=geometries,
        crs=crs,
    )


def _write_geojson(
    name: str,
    frame: gpd.GeoDataFrame,
) -> None:
    frame.to_file(
        OUTPUT_ROOT / f"{name}.geojson",
        driver="GeoJSON",
        engine="pyogrio",
    )


def main() -> None:
    """Create the complete checked-in vector benchmark."""

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    clean = _frame(
        [1, 2],
        ["alpha", "beta"],
        [Point(-75.0, 43.0), Point(-74.0, 44.0)],
    )
    _write_geojson("clean", clean)

    wrong_crs = clean.copy()
    wrong_crs = wrong_crs.set_crs(
        "EPSG:3857",
        allow_override=True,
    )
    _write_geojson("wrong_crs", wrong_crs)

    _write_geojson(
        "invalid_geometry",
        _frame(
            [1],
            ["bowtie"],
            [
                Polygon(
                    [
                        (-75.0, 43.0),
                        (-74.0, 44.0),
                        (-74.0, 43.0),
                        (-75.0, 44.0),
                        (-75.0, 43.0),
                    ]
                )
            ],
        ),
    )

    _write_geojson(
        "null_geometry",
        _frame(
            [1, 2],
            ["alpha", "missing geometry"],
            [Point(-75.0, 43.0), None],
        ),
    )

    _write_geojson(
        "duplicate_identifiers",
        _frame(
            [1, 1],
            ["alpha", "beta"],
            [Point(-75.0, 43.0), Point(-74.0, 44.0)],
        ),
    )

    missing_fields = gpd.GeoDataFrame(
        {"feature_id": [1, 2]},
        geometry=[Point(-75.0, 43.0), Point(-74.0, 44.0)],
        crs="EPSG:4326",
    )
    _write_geojson("missing_fields", missing_fields)

    _write_geojson(
        "incorrect_field_types",
        _frame(
            ["one", "two"],
            ["alpha", "beta"],
            [Point(-75.0, 43.0), Point(-74.0, 44.0)],
        ),
    )

    _write_geojson(
        "unexpected_extent",
        _frame(
            [1],
            ["outside"],
            [Point(10.0, 10.0)],
        ),
    )

    empty = gpd.GeoDataFrame(
        {
            "feature_id": pd.Series(dtype="int64"),
            "name": pd.Series(dtype="string"),
        },
        geometry=gpd.GeoSeries([], crs="EPSG:4326"),
        crs="EPSG:4326",
    )
    (OUTPUT_ROOT / "empty_data.geojson").unlink(
        missing_ok=True
    )
    empty.to_file(
        OUTPUT_ROOT / "empty_data.gpkg",
        layer="empty_data",
        driver="GPKG",
        engine="pyogrio",
    )

    _write_geojson(
        "mixed_geometry",
        _frame(
            [1, 2],
            ["point", "line"],
            [
                Point(-75.0, 43.0),
                LineString(
                    [(-75.0, 43.0), (-74.0, 44.0)]
                ),
            ],
        ),
    )

    _write_geojson(
        "duplicate_geometry",
        _frame(
            [1, 2],
            ["alpha", "same place"],
            [Point(-75.0, 43.0), Point(-75.0, 43.0)],
        ),
    )

    _write_geojson(
        "null_attribute",
        _frame(
            [1, 2],
            ["alpha", None],
            [Point(-75.0, 43.0), Point(-74.0, 44.0)],
        ),
    )

    missing_crs_path = OUTPUT_ROOT / "missing_crs.shp"
    for member in OUTPUT_ROOT.glob("missing_crs.*"):
        if member.is_file() and not member.is_symlink():
            member.unlink()

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=(
                "'crs' was not provided.*"
            ),
            category=UserWarning,
        )
        _frame(
            [1, 2],
            ["alpha", "beta"],
            [Point(-75.0, 43.0), Point(-74.0, 44.0)],
            crs=None,
        ).to_file(
            missing_crs_path,
            driver="ESRI Shapefile",
            engine="pyogrio",
        )

    print(f"Generated vector benchmark: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
