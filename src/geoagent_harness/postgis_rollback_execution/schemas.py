"""Strict evidence schemas for transactional PostGIS rollback."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.postgis_inspection import PostGISInspectionResult


class PostGISRollbackExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    execution_id: str = Field(pattern=r"^postgis-rollback-execution-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$")
    rollback_plan_id: str
    rollback_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_id: str
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    restored_reference: PostGISInspectionResult
    restored_candidate: PostGISInspectionResult
    approved_step_ids: list[str] = Field(min_length=2,max_length=2)
    human_approval_verified: Literal[True] = True
    inputs_reverified: Literal[True] = True
    candidate_absence_reverified: Literal[True] = True
    transaction_committed: Literal[True] = True
    post_rollback_validated: Literal[True] = True
    rollback_performed: Literal[True] = True
    database_modified: Literal[True] = True
    arbitrary_sql_accepted: Literal[False] = False
    model_called: Literal[False] = False


class PostGISRollbackExecutionStorageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    execution_id: str
    rollback_plan_id: str
    rollback_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_id: str
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_directory: str
    execution_file: str
    transaction_committed: Literal[True] = True
    rollback_performed: Literal[True] = True
    database_modified: Literal[True] = True
