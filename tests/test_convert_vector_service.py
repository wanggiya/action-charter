"""Tests for controlled vector conversion execution."""

from pathlib import Path

import geopandas as gpd
import pytest

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skills.convert_vector import (
    ConvertVectorError,
    convert_vector,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data" / "input"
SAMPLE = INPUT_ROOT / "sample_points.geojson"


def settings(
    output_root: Path,
    *,
    enabled: bool,
) -> MCPSettings:
    return MCPSettings(
        input_root=INPUT_ROOT,
        output_root=output_root,
        enable_write_tools=enabled,
        allow_overwrite=False,
    )


def test_writes_geojson_pending_validation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "converted.geojson"

    result = convert_vector(
        path=SAMPLE,
        target_path=target,
        settings=settings(
            tmp_path,
            enabled=True,
        ),
    )

    assert target.is_file()
    assert result.status == (
        "converted_pending_validation"
    )
    assert result.target_driver == "GeoJSON"
    assert result.target_size_bytes > 0
    assert result.validation_required is True
    assert result.validation_performed is False
    assert result.final_success_claimed is False
    assert result.overwrite_performed is False

    frame = gpd.read_file(
        target,
        engine="pyogrio",
    )

    assert len(frame) == 2


def test_writes_geopackage_pending_validation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "converted.gpkg"

    result = convert_vector(
        path=SAMPLE,
        target_path=target,
        target_layer="converted_points",
        settings=settings(
            tmp_path,
            enabled=True,
        ),
    )

    assert target.is_file()
    assert result.target_driver == "GPKG"
    assert result.target_layer == "converted_points"
    assert result.final_success_claimed is False

    frame = gpd.read_file(
        target,
        layer="converted_points",
        engine="pyogrio",
    )

    assert len(frame) == 2


def test_rejects_when_writes_are_disabled(
    tmp_path: Path,
) -> None:
    target = tmp_path / "disabled.geojson"

    with pytest.raises(
        ConvertVectorError,
        match="write tools are disabled",
    ):
        convert_vector(
            path=SAMPLE,
            target_path=target,
            settings=settings(
                tmp_path,
                enabled=False,
            ),
        )

    assert target.exists() is False


def test_existing_target_is_not_overwritten(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing.geojson"
    original = b"existing-content"
    target.write_bytes(original)

    with pytest.raises(
        ConvertVectorError,
        match="already exists",
    ):
        convert_vector(
            path=SAMPLE,
            target_path=target,
            settings=settings(
                tmp_path,
                enabled=True,
            ),
        )

    assert target.read_bytes() == original


def test_allow_overwrite_does_not_enable_replacement(
    tmp_path: Path,
) -> None:
    target = tmp_path / "protected.geojson"
    original = b"protected-content"
    target.write_bytes(original)

    active = MCPSettings(
        input_root=INPUT_ROOT,
        output_root=tmp_path,
        enable_write_tools=True,
        allow_overwrite=True,
    )

    with pytest.raises(
        ConvertVectorError,
        match="already exists",
    ):
        convert_vector(
            path=SAMPLE,
            target_path=target,
            settings=active,
        )

    assert target.read_bytes() == original


def test_failed_writer_leaves_no_output(
    tmp_path: Path,
) -> None:
    target = tmp_path / "failed.geojson"

    def fail_writer(
        frame,
        *,
        path,
        driver,
        layer,
    ):
        path.write_text(
            "partial",
            encoding="utf-8",
        )
        raise RuntimeError(
            "password=do-not-expose"
        )

    with pytest.raises(
        ConvertVectorError,
        match="driver details were redacted",
    ):
        convert_vector(
            path=SAMPLE,
            target_path=target,
            settings=settings(
                tmp_path,
                enabled=True,
            ),
            writer=fail_writer,
        )

    assert target.exists() is False

    temporary_files = list(
        tmp_path.glob(".failed.*")
    )

    assert temporary_files == []


def test_rejects_missing_target_parent(
    tmp_path: Path,
) -> None:
    target = (
        tmp_path
        / "missing"
        / "converted.geojson"
    )

    with pytest.raises(
        ConvertVectorError,
        match="parent directory",
    ):
        convert_vector(
            path=SAMPLE,
            target_path=target,
            settings=settings(
                tmp_path,
                enabled=True,
            ),
        )

    assert target.exists() is False
