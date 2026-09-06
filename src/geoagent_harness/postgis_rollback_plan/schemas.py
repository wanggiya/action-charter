"""Strict schemas for deterministic PostGIS rollback planning."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from geoagent_harness.postgis_inspection import PostGISInspectionResult


RollbackStepId = Literal[
    "step_1_reverify_evidence",
    "step_2_lock_relations",
    "step_3_verify_candidate_absent",
    "step_4_restore_candidate",
    "step_5_restore_reference",
    "step_6_validate_restored_relations",
]


class PostGISRollbackOperation(BaseModel):
    """One fixed operation in a future transactional rollback."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: RollbackStepId
    operation: Literal[
        "reverify_evidence",
        "lock_relations",
        "verify_candidate_absent",
        "restore_candidate",
        "restore_reference",
        "validate_restored_relations",
    ]
    requires_approval: bool
    database_mutation: bool


class PostGISRollbackPlan(BaseModel):
    """Canonical, non-executing rollback plan for one verified promotion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    rollback_plan_id: str = Field(
        pattern=r"^postgis-rollback-plan-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$"
    )
    promotion_plan_id: str
    promotion_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_id: str
    execution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    verification_id: str
    verification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_reference: PostGISInspectionResult
    promoted_candidate: PostGISInspectionResult
    archive_relation: PostGISInspectionResult
    operations: list[PostGISRollbackOperation] = Field(min_length=6, max_length=6)
    approval_required_step_ids: list[Literal[
        "step_4_restore_candidate",
        "step_5_restore_reference",
    ]] = Field(min_length=2, max_length=2)
    verification_status: Literal["verified"] = "verified"
    transaction_required: Literal[True] = True
    rollback_of_rollback_required: Literal[True] = True
    post_rollback_validation_required: Literal[True] = True
    ready_for_approval: Literal[True] = True
    planning_performed: Literal[True] = True
    approval_created: Literal[False] = False
    execution_performed: Literal[False] = False
    database_modified: Literal[False] = False
    arbitrary_sql_accepted: Literal[False] = False
    model_called: Literal[False] = False

    @model_validator(mode="after")
    def fixed_choreography_is_intact(self) -> "PostGISRollbackPlan":
        expected = [
            ("step_1_reverify_evidence", "reverify_evidence", False, False),
            ("step_2_lock_relations", "lock_relations", False, False),
            ("step_3_verify_candidate_absent", "verify_candidate_absent", False, False),
            ("step_4_restore_candidate", "restore_candidate", True, True),
            ("step_5_restore_reference", "restore_reference", True, True),
            ("step_6_validate_restored_relations", "validate_restored_relations", False, False),
        ]
        observed = [
            (item.step_id, item.operation, item.requires_approval, item.database_mutation)
            for item in self.operations
        ]
        if observed != expected:
            raise ValueError("rollback operation choreography is not exact")
        if self.approval_required_step_ids != [
            "step_4_restore_candidate",
            "step_5_restore_reference",
        ]:
            raise ValueError("approval scope does not match rollback mutation steps")
        identities = {
            (item.target_schema, item.target_table)
            for item in (
                self.original_reference,
                self.promoted_candidate,
                self.archive_relation,
            )
        }
        if len(identities) != 3:
            raise ValueError("rollback relations must be distinct")
        return self


class PostGISRollbackPlanStorageResult(BaseModel):
    """Identity and location of one immutable rollback plan package."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    rollback_plan_id: str
    promotion_plan_id: str
    execution_id: str
    verification_id: str
    rollback_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rollback_plan_directory: str
    rollback_plan_file: str
    planning_performed: Literal[True] = True
    database_modified: Literal[False] = False
