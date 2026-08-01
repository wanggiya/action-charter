"""Controlled vector loading into an existing PostGIS schema."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import geopandas as gpd
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import URL, create_engine, inspect
from sqlalchemy.engine import Engine

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
    validate_identifier,
)
from geoagent_harness.skills.inspect_vector.service import (
    InspectVectorError,
    inspect_vector,
)


class LoadVectorError(RuntimeError):
    """Raised when a controlled PostGIS load cannot proceed."""


class LoadVectorResult(BaseModel):
    """Secret-free result of a completed database write."""

    model_config = ConfigDict(extra="forbid")

    status: str = "loaded_pending_validation"
    source: str
    source_layer: str
    target_schema: str
    target_table: str
    row_count: int = Field(ge=0)
    geometry_column: str
    srid: int = Field(ge=1)
    validation_required: bool = True
    warnings: list[str]


class PostGISAdapter(Protocol):
    """Narrow database interface used by the loading policy."""

    def schema_exists(self, schema: str) -> bool:
        """Return whether the approved schema already exists."""

    def table_exists(self, schema: str, table: str) -> bool:
        """Return whether the target table already exists."""

    def write(
        self,
        frame: gpd.GeoDataFrame,
        *,
        schema: str,
        table: str,
    ) -> None:
        """Create a new PostGIS table."""

    def close(self) -> None:
        """Release database resources."""


class SQLAlchemyPostGISAdapter:
    """PostGIS adapter with fixed SQLAlchemy operations."""

    def __init__(self, settings: MCPSettings) -> None:
        password = _read_password(
            settings.postgres_password_file
        )

        url = URL.create(
            drivername="postgresql+psycopg",
            username=settings.postgres_user,
            password=password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_database,
        )

        self._engine: Engine = create_engine(
            url,
            pool_pre_ping=True,
        )

    def schema_exists(self, schema: str) -> bool:
        return inspect(self._engine).has_schema(schema)

    def table_exists(self, schema: str, table: str) -> bool:
        return inspect(self._engine).has_table(
            table,
            schema=schema,
        )

    def write(
        self,
        frame: gpd.GeoDataFrame,
        *,
        schema: str,
        table: str,
    ) -> None:
        frame.to_postgis(
            name=table,
            con=self._engine,
            schema=schema,
            if_exists="fail",
            index=False,
        )

    def close(self) -> None:
        self._engine.dispose()


def _read_password(path: Path) -> str:
    """Read a password from a trusted mounted secret file."""
    try:
        password = path.read_text(
            encoding="utf-8"
        ).strip()
    except OSError as exc:
        raise LoadVectorError(
            "PostGIS credential file is unavailable"
        ) from exc

    if not password:
        raise LoadVectorError(
            "PostGIS credential file is empty"
        )

    return password


def _choose_layer(
    layer_names: list[str],
    requested: str | None,
) -> str:
    if requested is not None:
        if requested not in layer_names:
            raise LoadVectorError(
                f"source layer {requested!r} was not found"
            )

        return requested

    if len(layer_names) != 1:
        raise LoadVectorError(
            "source_layer is required when the dataset "
            "contains multiple layers"
        )

    return layer_names[0]


def load_vector_to_postgis(
    *,
    path: Path,
    target_schema: str,
    target_table: str,
    settings: MCPSettings,
    source_layer: str | None = None,
    adapter: PostGISAdapter | None = None,
) -> LoadVectorResult:
    """Load one approved vector layer into a new PostGIS table."""
    if not settings.enable_write_tools:
        raise LoadVectorError(
            "write tools are disabled; set "
            "ENABLE_WRITE_TOOLS=true for an approved run"
        )

    validate_identifier(
        target_schema,
        label="target_schema",
    )
    validate_identifier(
        target_table,
        label="target_table",
    )

    if target_schema not in settings.allowed_schemas:
        allowed = ", ".join(
            sorted(settings.allowed_schemas)
        )

        raise LoadVectorError(
            f"target schema {target_schema!r} is not allowed; "
            f"allowed: {allowed}"
        )

    try:
        inspected = inspect_vector(
            path=path,
            input_root=settings.input_root,
        )
    except InspectVectorError as exc:
        raise LoadVectorError(str(exc)) from exc

    layer_names = [
        layer.name
        for layer in inspected.layers
    ]

    selected_layer = _choose_layer(
        layer_names,
        source_layer,
    )

    selected_info = next(
        layer
        for layer in inspected.layers
        if layer.name == selected_layer
    )

    if selected_info.crs is None:
        raise LoadVectorError(
            "source layer has no CRS; loading is blocked"
        )

    try:
        frame = gpd.read_file(
            inspected.source,
            layer=selected_layer,
        )
    except Exception as exc:
        raise LoadVectorError(
            "approved vector layer could not be read"
        ) from exc

    if frame.crs is None:
        raise LoadVectorError(
            "source layer has no CRS; loading is blocked"
        )

    srid = frame.crs.to_epsg()

    if srid is None or srid <= 0:
        raise LoadVectorError(
            "source CRS has no unambiguous EPSG SRID"
        )

    if frame.geometry.name not in frame.columns:
        raise LoadVectorError(
            "source layer has no active geometry column"
        )

    active_adapter = adapter
    owns_adapter = adapter is None

    try:
        if active_adapter is None:
            active_adapter = SQLAlchemyPostGISAdapter(
                settings
            )

        if not active_adapter.schema_exists(target_schema):
            raise LoadVectorError(
                f"approved schema {target_schema!r} "
                "does not exist"
            )

        if active_adapter.table_exists(
            target_schema,
            target_table,
        ):
            if settings.allow_overwrite:
                raise LoadVectorError(
                    "target table exists; destructive replacement "
                    "is blocked in the MVP even when "
                    "ALLOW_OVERWRITE=true"
                )

            raise LoadVectorError(
                "target table exists and overwrite is disabled"
            )

        active_adapter.write(
            frame,
            schema=target_schema,
            table=target_table,
        )

    except LoadVectorError:
        raise
    except Exception as exc:
        # Do not return driver exceptions, because they can include
        # connection details.
        raise LoadVectorError(
            "PostGIS load failed; database details were redacted"
        ) from None
    finally:
        if owns_adapter and active_adapter is not None:
            active_adapter.close()

    return LoadVectorResult(
        source=inspected.source,
        source_layer=selected_layer,
        target_schema=target_schema,
        target_table=target_table,
        row_count=len(frame),
        geometry_column=frame.geometry.name,
        srid=srid,
        warnings=[
            (
                "The table was created but final success is "
                "withheld until deterministic validation passes."
            )
        ],
    )