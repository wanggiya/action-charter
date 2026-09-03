"""Typed versioned spatial-data contract schemas."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class VectorFieldType(str, Enum):
    """Portable logical field types used by vector contracts."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"


class VectorGeometryType(str, Enum):
    """Supported canonical vector geometry types."""

    POINT = "Point"
    MULTIPOINT = "MultiPoint"
    LINESTRING = "LineString"
    MULTILINESTRING = "MultiLineString"
    POLYGON = "Polygon"
    MULTIPOLYGON = "MultiPolygon"


class SpatialExtentRule(BaseModel):
    """One deterministic rectangular extent rule."""

    model_config = ConfigDict(extra="forbid")

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    tolerance: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def extent_must_be_ordered(self) -> "SpatialExtentRule":
        if self.min_x > self.max_x:
            raise ValueError("extent min_x cannot exceed max_x")
        if self.min_y > self.max_y:
            raise ValueError("extent min_y cannot exceed max_y")
        return self


class VectorFieldContract(BaseModel):
    """Required vector field and its quality constraints."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    )
    field_type: VectorFieldType
    nullable: bool = True
    max_null_fraction: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def nullability_must_be_consistent(self) -> "VectorFieldContract":
        if not self.nullable and self.max_null_fraction != 0.0:
            raise ValueError(
                "non-nullable fields must have max_null_fraction equal to zero"
            )
        return self


class VectorUniqueKeyRule(BaseModel):
    """One single-field or composite unique-key rule."""

    model_config = ConfigDict(extra="forbid")

    fields: list[str] = Field(min_length=1, max_length=16)
    allow_nulls: bool = False

    @field_validator("fields")
    @classmethod
    def fields_must_be_unique_and_safe(cls, fields: list[str]) -> list[str]:
        if len(fields) != len(set(fields)):
            raise ValueError("unique-key fields must be unique")

        for name in fields:
            if (
                not name
                or len(name) > 128
                or not name.isascii()
                or not name.replace("_", "a").isalnum()
                or not (name[0].isalpha() or name[0] == "_")
            ):
                raise ValueError("unique-key field name is invalid")

        return fields


class VectorFeatureCountRule(BaseModel):
    """Allowed inclusive vector feature-count range."""

    model_config = ConfigDict(extra="forbid")

    minimum: int = Field(default=1, ge=0)
    maximum: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def bounds_must_be_ordered(self) -> "VectorFeatureCountRule":
        if self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("feature-count minimum cannot exceed maximum")
        return self


class VectorGeometryQualityRule(BaseModel):
    """Deterministic geometry-quality thresholds."""

    model_config = ConfigDict(extra="forbid")

    max_invalid_count: int = Field(default=0, ge=0)
    max_empty_count: int = Field(default=0, ge=0)
    max_null_count: int = Field(default=0, ge=0)
    max_duplicate_count: int = Field(default=0, ge=0)


class VectorSpatialDataContract(BaseModel):
    """Versioned deterministic contract for one vector layer."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    contract_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_-]*$",
    )
    contract_version: str = Field(
        pattern=(
            r"^(0|[1-9][0-9]*)\."
            r"(0|[1-9][0-9]*)\."
            r"(0|[1-9][0-9]*)$"
        )
    )
    dataset_kind: Literal["vector"] = "vector"
    description: str = Field(min_length=1, max_length=2000)

    layer: str | None = Field(default=None, min_length=1, max_length=128)
    expected_crs: str = Field(min_length=1, max_length=512)
    allowed_geometry_types: list[VectorGeometryType] = Field(
        min_length=1,
        max_length=6,
    )
    mixed_geometry_allowed: bool = False

    required_fields: list[VectorFieldContract] = Field(
        default_factory=list,
        max_length=128,
    )
    unique_keys: list[VectorUniqueKeyRule] = Field(
        default_factory=list,
        max_length=16,
    )

    feature_count: VectorFeatureCountRule = Field(
        default_factory=VectorFeatureCountRule
    )
    geometry_quality: VectorGeometryQualityRule = Field(
        default_factory=VectorGeometryQualityRule
    )

    expected_extent: SpatialExtentRule | None = None
    permitted_extent: SpatialExtentRule | None = None

    filesystem_modified: Literal[False] = False
    database_modified: Literal[False] = False
    execution_performed: Literal[False] = False

    @field_validator("expected_crs")
    @classmethod
    def expected_crs_must_be_normalized(cls, value: str) -> str:
        normalized = value.strip()
        if normalized != value:
            raise ValueError(
                "expected CRS must not contain surrounding whitespace"
            )

        if normalized.lower().startswith("epsg:"):
            authority, code = normalized.split(":", maxsplit=1)
            if (
                authority.lower() != "epsg"
                or not code.isdigit()
                or int(code) < 1
            ):
                raise ValueError("EPSG CRS identifier is invalid")
            return f"EPSG:{int(code)}"

        return normalized

    @field_validator("allowed_geometry_types")
    @classmethod
    def geometry_types_must_be_unique(
        cls,
        values: list[VectorGeometryType],
    ) -> list[VectorGeometryType]:
        if len(values) != len(set(values)):
            raise ValueError("allowed geometry types must be unique")
        return values

    @field_validator("required_fields")
    @classmethod
    def required_fields_must_be_unique(
        cls,
        fields: list[VectorFieldContract],
    ) -> list[VectorFieldContract]:
        names = [field.name for field in fields]
        if len(names) != len(set(names)):
            raise ValueError("required field names must be unique")
        return fields

    @field_validator("unique_keys")
    @classmethod
    def unique_keys_must_be_unique(
        cls,
        rules: list[VectorUniqueKeyRule],
    ) -> list[VectorUniqueKeyRule]:
        identities = [tuple(rule.fields) for rule in rules]
        if len(identities) != len(set(identities)):
            raise ValueError("unique-key rules must be unique")
        return rules

    @model_validator(mode="after")
    def referenced_fields_must_be_declared(self) -> "VectorSpatialDataContract":
        declared = {field.name for field in self.required_fields}
        referenced = {
            name
            for rule in self.unique_keys
            for name in rule.fields
        }
        missing = sorted(referenced - declared)
        if missing:
            raise ValueError(
                "unique-key fields must be declared as required fields: "
                + ", ".join(missing)
            )
        return self


class SpatialDataContractCheck(BaseModel):
    """One deterministic contract check and its outcome."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(
        min_length=1,
        max_length=200,
        pattern=r"^[a-z][a-z0-9_.:-]*$",
    )
    passed: bool
    message: str = Field(min_length=1, max_length=2000)


class SpatialDataContractAssessment(BaseModel):
    """Read-only deterministic assessment of one vector dataset."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    contract_id: str
    contract_version: str
    contract_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dataset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dataset_sha256_after: str = Field(pattern=r"^[a-f0-9]{64}$")
    dataset_unchanged: Literal[True] = True

    source: str
    layer: str
    feature_count: int = Field(ge=0)
    geometry_types: list[str]
    invalid_geometry_count: int = Field(ge=0)
    empty_geometry_count: int = Field(ge=0)
    null_geometry_count: int = Field(ge=0)
    duplicate_geometry_count: int = Field(ge=0)

    checks: list[SpatialDataContractCheck] = Field(min_length=1)
    violations: list[str] = Field(default_factory=list)
    passed: bool

    assessment_performed: Literal[True] = True
    filesystem_modified: Literal[False] = False
    database_modified: Literal[False] = False
    execution_performed: Literal[False] = False

    @model_validator(mode="after")
    def outcome_must_be_consistent(
        self,
    ) -> "SpatialDataContractAssessment":
        checks_passed = all(check.passed for check in self.checks)
        expected_violations = [
            check.message
            for check in self.checks
            if not check.passed
        ]

        if self.passed != checks_passed:
            raise ValueError(
                "contract assessment success conflicts with checks"
            )

        if self.violations != expected_violations:
            raise ValueError(
                "contract assessment violations conflict with checks"
            )

        if self.dataset_sha256 != self.dataset_sha256_after:
            raise ValueError(
                "contract assessment dataset digests changed"
            )

        return self
