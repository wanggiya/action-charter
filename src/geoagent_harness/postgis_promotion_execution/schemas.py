"""Strict result schema for transactional PostGIS promotion."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoagent_harness.postgis_inspection import PostGISInspectionResult


class PostGISPromotionExecutionResult(BaseModel):
    """Committed promotion evidence returned only after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    execution_id: str = Field(
        pattern=r"^postgis-promotion-execution-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$"
    )
    plan_id: str
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_id: str
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_before_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_before_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    promoted_relation: PostGISInspectionResult
    approved_step_ids: list[str] = Field(min_length=2, max_length=2)
    human_approval_verified: Literal[True] = True
    inputs_reverified: Literal[True] = True
    archive_absence_reverified: Literal[True] = True
    transaction_committed: Literal[True] = True
    rollback_required: Literal[True] = True
    post_promotion_validated: Literal[True] = True
    promotion_performed: Literal[True] = True
    execution_performed: Literal[True] = True
    database_modified: Literal[True] = True
    arbitrary_sql_accepted: Literal[False] = False
    model_called: Literal[False] = False


class PostGISPromotionExecutionStorageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    execution_id: str
    plan_id: str
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_id: str
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_directory: str
    execution_file: str
    transaction_committed: Literal[True] = True
    post_promotion_validated: Literal[True] = True
    promotion_performed: Literal[True] = True
    execution_performed: Literal[True] = True
    database_modified: Literal[True] = True
