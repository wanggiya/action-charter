import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.skills.inspect_vector.service import (
    InspectVectorError,
    inspect_vector,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data" / "input"
SAMPLE = INPUT_ROOT / "sample_points.geojson"


def test_inspect_sample_geojson() -> None:
    result = inspect_vector(SAMPLE, INPUT_ROOT)

    assert result.driver == "GeoJSON"
    assert len(result.layers) == 1
    layer = result.layers[0]
    assert layer.geometry_type == "Point"
    assert layer.feature_count == 2
    assert layer.crs in {"EPSG:4326", "OGC:CRS84"}
    assert [field.name for field in layer.fields] == ["id", "name"]
    assert layer.extent is not None
    assert layer.extent.min_x == pytest.approx(-71.0589)
    assert layer.extent.max_y == pytest.approx(42.3612)


def test_rejects_path_outside_input_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside.geojson"
    outside.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    with pytest.raises(InspectVectorError, match="approved root"):
        inspect_vector(outside, INPUT_ROOT)


def test_rejects_unsupported_extension(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    text_file = input_root / "notes.txt"
    text_file.write_text("not spatial", encoding="utf-8")

    with pytest.raises(InspectVectorError, match="unsupported extension"):
        inspect_vector(text_file, input_root)


def test_rejects_missing_file() -> None:
    with pytest.raises(InspectVectorError, match="does not exist"):
        inspect_vector(INPUT_ROOT / "missing.geojson", INPUT_ROOT)


@pytest.mark.parametrize(
    ("filename", "driver"),
    [
        ("fixture.geojson", "GeoJSON"),
        ("fixture.gpkg", "GPKG"),
        ("fixture.shp", "ESRI Shapefile"),
    ],
)
def test_supported_formats(tmp_path: Path, filename: str, driver: str) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    dataset = input_root / filename
    frame = gpd.GeoDataFrame(
        {"id": [1], "label": ["fixture"]},
        geometry=[Point(-71.0, 42.0)],
        crs="EPSG:4326",
    )
    frame.to_file(dataset, driver=driver, engine="pyogrio")

    result = inspect_vector(dataset, input_root)

    assert result.driver == driver
    assert result.layers[0].feature_count == 1
    assert result.layers[0].geometry_type == "Point"


def test_lists_all_geopackage_layers(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    dataset = input_root / "layers.gpkg"
    frame = gpd.GeoDataFrame(
        {"id": [1]}, geometry=[Point(-71.0, 42.0)], crs="EPSG:4326"
    )
    frame.to_file(dataset, layer="first", driver="GPKG", engine="pyogrio")
    frame.to_file(dataset, layer="second", driver="GPKG", engine="pyogrio")

    result = inspect_vector(dataset, input_root)

    assert [layer.name for layer in result.layers] == ["first", "second"]


def test_cli_emits_structured_json() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "inspect-vector",
            str(SAMPLE),
            "--input-root",
            str(INPUT_ROOT),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["driver"] == "GeoJSON"
    assert payload["layers"][0]["feature_count"] == 2
