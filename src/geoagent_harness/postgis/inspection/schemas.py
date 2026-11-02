"""Strict schemas for bounded PostGIS inspection."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.verifier.postgis import LayerExtent


class PostGISInspectionRequest(BaseModel):
    """One exact relation selected without accepting SQL."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    target_schema: str = Field(min_length=1, max_length=63)
    target_table: str = Field(min_length=1, max_length=63)


class PostGISColumn(BaseModel):
    """Bounded, secret-free column metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ordinal_position: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=63)
    data_type: str = Field(min_length=1, max_length=128)
    nullable: bool


class PostGISKey(BaseModel):
    """Primary or unique key metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=63)
    columns: list[str] = Field(min_length=1, max_length=64)


class PostGISGeometryColumn(BaseModel):
    """Declared and observed facts for one geometry column."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=63)
    declared_type: str = Field(min_length=1, max_length=64)
    srid: int = Field(ge=0)
    observed_types: list[str] = Field(max_length=32)
    null_count: int = Field(ge=0)
    invalid_count: int = Field(ge=0)
    extent: LayerExtent | None


class PostGISInspectionResult(BaseModel):
    """Deterministic result containing no connection secrets."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal["inspected", "not_found"]
    target_schema: str
    target_table: str
    table_exists: bool
    row_count: int | None = Field(default=None, ge=0)
    columns: list[PostGISColumn] = Field(max_length=256)
    primary_key: PostGISKey | None
    unique_keys: list[PostGISKey] = Field(max_length=256)
    geometry_columns: list[PostGISGeometryColumn] = Field(max_length=8)
    warnings: list[str] = Field(max_length=32)
    inspection_performed: Literal[True] = True
    database_modified: Literal[False] = False
    arbitrary_sql_accepted: Literal[False] = False
    credentials_redacted: Literal[True] = True

