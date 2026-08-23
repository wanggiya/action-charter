"""Deterministic raster fixtures for contract tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


def write_test_raster(
    path: Path,
) -> Path:
    """Write one tiny deterministic GeoTIFF fixture."""

    values = np.array(
        [
            [1, 2, 3],
            [4, 5, 6],
        ],
        dtype="uint16",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=3,
        height=2,
        count=1,
        dtype="uint16",
        crs="EPSG:4326",
        transform=from_origin(
            -71.1,
            42.4,
            0.01,
            0.01,
        ),
        nodata=0,
    ) as dataset:
        dataset.write(
            values,
            indexes=1,
        )

    return path

