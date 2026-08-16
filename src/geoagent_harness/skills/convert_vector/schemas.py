"""Schemas for controlled vector conversion."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from typing import Any, Literal

class VectorOutputFormat(str, Enum):
    """Allowlisted vector output formats."""

    GEOJSON = "geojson"
    GEOPACKAGE = "geopackage"


class ConvertVectorPlan(BaseModel):
    """Validated conversion that has not executed."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    status: Literal[
        "planned_not_executed"
    ] = "planned_not_executed"

    source: str
    source_driver: str
    source_layer: str
    source_crs: str
    source_geometry_type: str
    source_feature_count: int = Field(ge=0)
    source_fields: list[str]

    target: str
    target_format: VectorOutputFormat
    target_driver: Literal[
        "GeoJSON",
        "GPKG",
    ]
    target_layer: str

    operation: Literal[
        "create_vector_dataset"
    ] = "create_vector_dataset"

    overwrite: Literal[False] = False
    execution_allowed: Literal[False] = False
    approval_required: Literal[True] = True
    validation_required: Literal[True] = True

    warnings: list[str] = Field(
        default_factory=list
    )
    
class ConvertVectorResult(BaseModel):
    """Result of a write awaiting deterministic validation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    status: Literal[
        "converted_pending_validation"
    ] = "converted_pending_validation"

    source: str
    source_driver: str
    source_layer: str
    source_crs: str
    source_geometry_type: str
    source_feature_count: int = Field(ge=0)
    source_fields: list[str]

    target: str
    target_format: VectorOutputFormat
    target_driver: Literal[
        "GeoJSON",
        "GPKG",
    ]
    target_layer: str
    target_size_bytes: int = Field(gt=0)

    overwrite_performed: Literal[False] = False
    validation_required: Literal[True] = True
    validation_performed: Literal[False] = False
    final_success_claimed: Literal[False] = False

    warnings: list[str] = Field(
        default_factory=list
    )

class VectorValidationCheck(BaseModel):
    """One deterministic vector-conversion check."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    passed: bool
    expected: Any
    actual: Any


class ConvertVectorValidationResult(BaseModel):
    """Deterministic validation of a converted vector dataset."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    status: Literal[
        "validation_passed",
        "validation_failed",
    ]
    passed: bool

    source: str
    source_layer: str
    target: str
    target_layer: str

    checks: list[VectorValidationCheck] = Field(
        min_length=1
    )

    source_feature_count: int = Field(ge=0)
    target_feature_count: int = Field(ge=0)

    source_invalid_geometry_count: int = Field(ge=0)
    target_invalid_geometry_count: int = Field(ge=0)

    source_null_geometry_count: int = Field(ge=0)
    target_null_geometry_count: int = Field(ge=0)

    warnings: list[str] = Field(
        default_factory=list
    )

