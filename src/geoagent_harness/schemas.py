"""Shared typed schemas for the harness."""

from pydantic import BaseModel, ConfigDict, Field


class FieldInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str


class Extent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_x: float
    min_y: float
    max_x: float
    max_y: float


class VectorLayerInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    crs: str | None
    geometry_type: str
    feature_count: int = Field(ge=0)
    fields: list[FieldInfo]
    extent: Extent | None


class InspectVectorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    driver: str
    layers: list[VectorLayerInfo] = Field(min_length=1)

