"""Strict schemas for digest-bound PostGIS promotion planning."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from geoagent_harness.postgis_change_assessment import (
    PostGISChangeAssessment,
)
from geoagent_harness.postgis_inspection import (
    PostGISInspectionRequest,
    PostGISInspectionResult,
)


class PostGISPromotionPlanRequest(BaseModel):
    """Exact relations selected for a non-writing promotion plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    plan_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_-]*$",
    )
    reference: PostGISInspectionRequest
    candidate: PostGISInspectionRequest
    archive: PostGISInspectionRequest

    @model_validator(mode="after")
    def relations_are_distinct(self) -> "PostGISPromotionPlanRequest":
        identities = {
            (item.target_schema, item.target_table)
            for item in (self.reference, self.candidate, self.archive)
        }
        if len(identities) != 3:
            raise ValueError(
                "reference, candidate, and archive relations must be distinct"
            )
        return self


class PostGISPromotionOperation(BaseModel):
    """One fixed operation in the future transactional promotion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: Literal[
        "step_1_reverify_assessment",
        "step_2_lock_relations",
        "step_3_verify_archive_absent",
        "step_4_archive_reference",
        "step_5_promote_candidate",
        "step_6_validate_promoted_relation",
    ]
    operation: Literal[
        "reverify_assessment",
        "lock_relations",
        "verify_archive_absent",
        "archive_reference",
        "promote_candidate",
        "validate_promoted_relation",
    ]
    requires_approval: bool
    database_mutation: bool


class PostGISPromotionPlan(BaseModel):
    """Canonical, non-executing plan for one exact promotion."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    plan_id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$", max_length=100)
    assessment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    assessment: PostGISChangeAssessment
    archive: PostGISInspectionResult
    operations: list[PostGISPromotionOperation] = Field(
        min_length=6,
        max_length=6,
    )
    approval_required_step_ids: list[Literal[
        "step_4_archive_reference",
        "step_5_promote_candidate",
    ]] = Field(min_length=2, max_length=2)
    transaction_required: Literal[True] = True
    rollback_required: Literal[True] = True
    post_promotion_validation_required: Literal[True] = True
    ready_for_approval: Literal[True] = True
    planning_performed: Literal[True] = True
    model_called: Literal[False] = False
    arbitrary_sql_accepted: Literal[False] = False
    approval_created: Literal[False] = False
    execution_performed: Literal[False] = False
    database_modified: Literal[False] = False

    @model_validator(mode="after")
    def fixed_choreography_is_intact(self) -> "PostGISPromotionPlan":
        expected = [
            ("step_1_reverify_assessment", "reverify_assessment", False, False),
            ("step_2_lock_relations", "lock_relations", False, False),
            ("step_3_verify_archive_absent", "verify_archive_absent", False, False),
            ("step_4_archive_reference", "archive_reference", True, True),
            ("step_5_promote_candidate", "promote_candidate", True, True),
            ("step_6_validate_promoted_relation", "validate_promoted_relation", False, False),
        ]
        observed = [
            (
                item.step_id,
                item.operation,
                item.requires_approval,
                item.database_mutation,
            )
            for item in self.operations
        ]
        if observed != expected:
            raise ValueError("promotion operation choreography is not exact")
        if self.approval_required_step_ids != [
            "step_4_archive_reference",
            "step_5_promote_candidate",
        ]:
            raise ValueError("approval scope does not match mutation steps")
        if not self.assessment.compatible:
            raise ValueError("promotion plan requires compatible assessment")
        if self.archive.table_exists:
            raise ValueError("archive relation must be absent during planning")
        return self


class PostGISPromotionPlanResult(BaseModel):
    """Digest and canonical plan returned by a planning operation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plan: PostGISPromotionPlan
    planning_performed: Literal[True] = True
    approval_created: Literal[False] = False
    execution_performed: Literal[False] = False
    database_modified: Literal[False] = False
