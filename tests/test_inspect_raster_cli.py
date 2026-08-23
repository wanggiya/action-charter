"""CLI tests for promoted raster inspection."""

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.testing.raster import (
    write_test_raster,
)


runner = CliRunner()


def test_inspect_raster_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "inspect-raster",
            "--help",
        ],
    )

    assert result.exit_code == 0


def test_inspects_raster_from_cli(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    path = write_test_raster(
        input_root / "sample.tif"
    )

    before = path.stat()

    result = runner.invoke(
        app,
        [
            "inspect-raster",
            str(path),
            "--input-root",
            str(input_root),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(
        result.stdout
    )

    assert payload["status"] == "completed"
    assert payload["source"] == "sample.tif"
    assert payload["driver"] == "GTiff"
    assert payload["width"] == 3
    assert payload["height"] == 2
    assert payload["band_count"] == 1
    assert payload["data_types"] == [
        "uint16"
    ]
    assert payload["crs"] == "EPSG:4326"

    assert payload[
        "filesystem_modified"
    ] is False
    assert payload[
        "database_modified"
    ] is False

    after = path.stat()

    assert before.st_size == after.st_size
    assert before.st_mtime_ns == after.st_mtime_ns


def test_cli_rejects_path_escape(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()

    outside = write_test_raster(
        tmp_path / "outside.tif"
    )

    result = runner.invoke(
        app,
        [
            "inspect-raster",
            str(outside),
            "--input-root",
            str(input_root),
        ],
    )

    assert result.exit_code == 2
    assert "failed policy" in result.output

