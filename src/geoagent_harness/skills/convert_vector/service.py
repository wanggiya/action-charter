"""Controlled vector conversion without arbitrary commands."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Protocol

import geopandas as gpd

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.skills.convert_vector.policy import (
    ConvertVectorPolicyError,
    plan_vector_conversion,
)
from geoagent_harness.skills.convert_vector.schemas import (
    ConvertVectorResult,
    VectorOutputFormat,
)


class ConvertVectorError(RuntimeError):
    """Raised when controlled conversion cannot finish safely."""


class VectorWriter(Protocol):
    """Narrow injectable vector writer."""

    def __call__(
        self,
        frame: gpd.GeoDataFrame,
        *,
        path: Path,
        driver: str,
        layer: str,
    ) -> None:
        """Write one new vector dataset."""


def _default_writer(
    frame: gpd.GeoDataFrame,
    *,
    path: Path,
    driver: str,
    layer: str,
) -> None:
    """Write through GeoPandas and pyogrio."""
    arguments: dict[str, object] = {
        "filename": path,
        "driver": driver,
        "engine": "pyogrio",
        "index": False,
    }

    if driver == "GPKG":
        arguments["layer"] = layer

    frame.to_file(**arguments)


def _resolved_target(
    target_path: Path,
) -> Path:
    return (
        target_path
        if target_path.is_absolute()
        else Path.cwd() / target_path
    ).resolve()


def _temporary_target(
    target: Path,
) -> Path:
    return target.with_name(
        f".{target.stem}."
        f"{uuid.uuid4().hex}.tmp"
        f"{target.suffix}"
    )


def _cleanup_temporary(
    temporary: Path,
) -> None:
    candidates = [
        temporary,
        Path(f"{temporary}-wal"),
        Path(f"{temporary}-shm"),
        Path(f"{temporary}-journal"),
    ]

    for candidate in candidates:
        try:
            candidate.unlink(missing_ok=True)
        except OSError:
            pass


def convert_vector(
    *,
    path: Path,
    target_path: Path,
    settings: MCPSettings,
    source_layer: str | None = None,
    target_layer: str | None = None,
    writer: VectorWriter | None = None,
) -> ConvertVectorResult:
    """Create one new output pending deterministic validation."""
    if not settings.enable_write_tools:
        raise ConvertVectorError(
            "write tools are disabled; set "
            "ENABLE_WRITE_TOOLS=true for an "
            "approved run"
        )

    try:
        plan = plan_vector_conversion(
            path=path,
            target_path=target_path,
            input_root=settings.input_root,
            output_root=settings.output_root,
            source_layer=source_layer,
            target_layer=target_layer,
        )
    except ConvertVectorPolicyError as exc:
        raise ConvertVectorError(
            str(exc)
        ) from exc

    target = _resolved_target(target_path)

    if not target.parent.is_dir():
        raise ConvertVectorError(
            "target parent directory does not exist"
        )

    if target.exists():
        raise ConvertVectorError(
            "target already exists; overwrite is "
            "blocked"
        )

    try:
        frame = gpd.read_file(
            path.resolve(),
            layer=plan.source_layer,
            engine="pyogrio",
        )
    except Exception as exc:
        raise ConvertVectorError(
            "approved source layer could not be read"
        ) from exc

    if frame.crs is None:
        raise ConvertVectorError(
            "source layer has no CRS; conversion "
            "is blocked"
        )

    if frame.geometry.name not in frame.columns:
        raise ConvertVectorError(
            "source layer has no active geometry "
            "column"
        )

    temporary = _temporary_target(target)
    active_writer = writer or _default_writer

    try:
        active_writer(
            frame,
            path=temporary,
            driver=plan.target_driver,
            layer=plan.target_layer,
        )

        if not temporary.is_file():
            raise ConvertVectorError(
                "vector writer did not create the "
                "expected output"
            )

        if temporary.stat().st_size <= 0:
            raise ConvertVectorError(
                "vector writer created an empty output"
            )

        os.chmod(
            temporary,
            0o644,
        )

        try:
            os.link(
                temporary,
                target,
            )
        except FileExistsError as exc:
            raise ConvertVectorError(
                "target appeared during conversion; "
                "overwrite is blocked"
            ) from exc

    except ConvertVectorError:
        raise
    except Exception as exc:
        raise ConvertVectorError(
            "vector conversion failed; driver "
            "details were redacted"
        ) from exc
    finally:
        _cleanup_temporary(temporary)

    if not target.is_file():
        raise ConvertVectorError(
            "converted output is unavailable"
        )

    return ConvertVectorResult(
        source=plan.source,
        source_driver=plan.source_driver,
        source_layer=plan.source_layer,
        source_crs=plan.source_crs,
        source_geometry_type=(
            plan.source_geometry_type
        ),
        source_feature_count=(
            plan.source_feature_count
        ),
        source_fields=plan.source_fields,
        target=plan.target,
        target_format=plan.target_format,
        target_driver=plan.target_driver,
        target_layer=plan.target_layer,
        target_size_bytes=target.stat().st_size,
        overwrite_performed=False,
        validation_required=True,
        validation_performed=False,
        final_success_claimed=False,
        warnings=[
            (
                "The output file was created, but "
                "final success is withheld until "
                "deterministic validation passes."
            )
        ],
    )
