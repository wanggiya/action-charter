"""Strict schemas for bounded GeoServer catalog inspection."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GeoServerInspectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    workspace: str = Field(min_length=1, max_length=63)
    datastore: str = Field(min_length=1, max_length=63)
    layer: str = Field(min_length=1, max_length=63)


class GeoServerFeatureTypeFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    native_name: str
    enabled: bool
    advertised: bool
    srs: str | None = None


class GeoServerLayerFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    enabled: bool
    advertised: bool
    default_style: str | None = None


class GeoServerInspectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    status: Literal["inspected", "not_found"]
    workspace: str
    datastore: str
    layer: str
    workspace_exists: bool
    datastore_exists: bool
    feature_type: GeoServerFeatureTypeFacts | None = None
    published_layer: GeoServerLayerFacts | None = None
    warnings: list[str] = Field(max_length=8)
    inspection_performed: Literal[True] = True
    geoserver_modified: Literal[False] = False
    arbitrary_rest_path_accepted: Literal[False] = False
    credentials_redacted: Literal[True] = True
