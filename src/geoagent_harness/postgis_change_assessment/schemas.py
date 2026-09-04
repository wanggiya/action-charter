"""Strict schemas for deterministic PostGIS change assessment."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from geoagent_harness.postgis_comparison import PostGISComparisonResult


class PostGISChangeDisposition(str, Enum):
    """Fixed policy outcome for observed relation change."""

    COMPATIBLE = "compatible"
    REVIEW_REQUIRED = "review_required"
    INCOMPATIBLE = "incompatible"


class PostGISChangeFinding(BaseModel):
    """One policy-classified difference."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: Literal[
        "columns_changed",
        "primary_key_changed",
        "unique_keys_changed",
        "geometry_registration_changed",
        "geometry_type_changed",
        "row_count_changed",
        "geometry_quality_changed",
        "extent_changed",
        "unclassified_change",
    ]
    disposition: PostGISChangeDisposition
    reference: JsonValue
    candidate: JsonValue
    reason: str = Field(min_length=1, max_length=500)


class PostGISChangeAssessment(BaseModel):
    """Non-mutating deterministic policy assessment."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    disposition: PostGISChangeDisposition
    compatible: bool
    operator_review_required: bool
    comparison: PostGISComparisonResult
    findings: list[PostGISChangeFinding] = Field(max_length=32)
    reason: str = Field(min_length=1, max_length=2000)
    assessment_performed: Literal[True] = True
    model_called: Literal[False] = False
    policy_overrides_accepted: Literal[False] = False
    approval_created: Literal[False] = False
    promotion_authorized: Literal[False] = False
    database_modified: Literal[False] = False
    arbitrary_sql_accepted: Literal[False] = False

    @model_validator(mode="after")
    def claims_match_disposition(self) -> "PostGISChangeAssessment":
        expected_compatible = (
            self.disposition == PostGISChangeDisposition.COMPATIBLE
        )
        expected_review = (
            self.disposition
            == PostGISChangeDisposition.REVIEW_REQUIRED
        )
        if self.compatible != expected_compatible:
            raise ValueError(
                "compatible claim does not match disposition"
            )
        if self.operator_review_required != expected_review:
            raise ValueError(
                "operator review claim does not match disposition"
            )
        if expected_compatible and (
            not self.comparison.matches or self.findings
        ):
            raise ValueError(
                "compatible assessment requires matched evidence"
            )
        if not expected_compatible and (
            self.comparison.matches or not self.findings
        ):
            raise ValueError(
                "changed assessment requires findings"
            )
        finding_dispositions = {
            finding.disposition
            for finding in self.findings
        }
        if (
            self.disposition == PostGISChangeDisposition.INCOMPATIBLE
            and PostGISChangeDisposition.INCOMPATIBLE
            not in finding_dispositions
        ):
            raise ValueError(
                "incompatible assessment requires an incompatible finding"
            )
        if (
            self.disposition
            == PostGISChangeDisposition.REVIEW_REQUIRED
            and finding_dispositions
            != {PostGISChangeDisposition.REVIEW_REQUIRED}
        ):
            raise ValueError(
                "review assessment may contain only review findings"
            )
        return self
