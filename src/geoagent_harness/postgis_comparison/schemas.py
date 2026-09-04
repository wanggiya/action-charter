"""Strict schemas for deterministic PostGIS table comparison."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from geoagent_harness.postgis_inspection import (
    PostGISInspectionRequest,
    PostGISInspectionResult,
)


class PostGISComparisonRequest(BaseModel):
    """Two exact relations selected without accepting SQL."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    reference: PostGISInspectionRequest
    candidate: PostGISInspectionRequest

    @model_validator(mode="after")
    def relations_are_distinct(self) -> "PostGISComparisonRequest":
        if (
            self.reference.target_schema
            == self.candidate.target_schema
            and self.reference.target_table
            == self.candidate.target_table
        ):
            raise ValueError(
                "reference and candidate relations must be distinct"
            )
        return self


class PostGISDifference(BaseModel):
    """One exact difference between normalized relation facts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: Literal[
        "columns",
        "primary_key",
        "unique_keys",
        "row_count",
        "geometry_columns",
    ]
    reference: JsonValue
    candidate: JsonValue


class PostGISComparisonResult(BaseModel):
    """Bounded comparison result derived only from trusted inspection."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal["matched", "different"]
    matches: bool
    reference: PostGISInspectionResult
    candidate: PostGISInspectionResult
    differences: list[PostGISDifference] = Field(max_length=16)
    warnings: list[str] = Field(max_length=32)
    comparison_performed: Literal[True] = True
    database_modified: Literal[False] = False
    arbitrary_sql_accepted: Literal[False] = False
    credentials_redacted: Literal[True] = True

    @model_validator(mode="after")
    def status_matches_differences(self) -> "PostGISComparisonResult":
        has_differences = bool(self.differences)
        if self.matches == has_differences:
            raise ValueError(
                "matches must be true exactly when differences are empty"
            )
        expected = "matched" if self.matches else "different"
        if self.status != expected:
            raise ValueError(
                "status does not match comparison result"
            )
        return self
