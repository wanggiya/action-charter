"""CLI contracts for controlled raster conversion."""

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.testing.raster import (
    write_test_raster,
)


runner = CliRunner()


def test_plan_convert_raster_does_not_write(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "result.tif"

    result = runner.invoke(
        app,
        [
            "plan-convert-raster",
            str(source),
            str(target),
            "--target-crs",
            "EPSG:3857",
            "--input-root",
            str(input_root),
            "--output-root",
            str(output_root),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)

    assert payload["status"] == (
        "planned_not_executed"
    )
    assert payload["approval_required"] is True
    assert payload["validation_required"] is True
    assert not target.exists()


def test_convert_raster_requires_write_flag(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "result.tif"

    result = runner.invoke(
        app,
        [
            "convert-raster",
            str(source),
            str(target),
            "--target-crs",
            "EPSG:3857",
        ],
        env={
            "GEOAGENT_INPUT_ROOT": (
                str(input_root)
            ),
            "GEOAGENT_OUTPUT_ROOT": (
                str(output_root)
            ),
            "ENABLE_WRITE_TOOLS": "false",
        },
    )

    assert result.exit_code == 2
    assert not target.exists()


def test_convert_and_validate_raster(
    tmp_path: Path,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    output_root.mkdir()

    source = write_test_raster(
        input_root / "sample.tif"
    )
    target = output_root / "result.tif"

    conversion = runner.invoke(
        app,
        [
            "convert-raster",
            str(source),
            str(target),
            "--target-crs",
            "EPSG:3857",
            "--resampling",
            "bilinear",
        ],
        env={
            "GEOAGENT_INPUT_ROOT": (
                str(input_root)
            ),
            "GEOAGENT_OUTPUT_ROOT": (
                str(output_root)
            ),
            "ENABLE_WRITE_TOOLS": "true",
            "ALLOW_OVERWRITE": "false",
        },
    )

    assert conversion.exit_code == 0
    conversion_payload = json.loads(
        conversion.stdout
    )

    assert conversion_payload["status"] == (
        "converted_pending_validation"
    )
    assert (
        conversion_payload[
            "final_success_claimed"
        ]
        is False
    )
    assert target.is_file()

    validation = runner.invoke(
        app,
        [
            "validate-raster-conversion",
            str(source),
            str(target),
            "--target-crs",
            "EPSG:3857",
            "--input-root",
            str(input_root),
            "--output-root",
            str(output_root),
        ],
    )

    assert validation.exit_code == 0
    validation_payload = json.loads(
        validation.stdout
    )

    assert validation_payload["passed"] is True
    assert validation_payload["status"] == (
        "validation_passed"
    )
    assert (
        validation_payload[
            "final_success_claimed"
        ]
        is True
    )

