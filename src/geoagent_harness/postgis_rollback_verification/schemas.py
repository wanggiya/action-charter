"""Strict schemas for independent post-rollback verification."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from geoagent_harness.postgis_inspection import PostGISInspectionResult

class PostGISRollbackVerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    verification_id: str = Field(pattern=r"^postgis-rollback-verification-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$")
    execution_id: str
    execution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rollback_plan_id: str
    rollback_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_id: str
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["verified", "failed"]
    findings: list[str] = Field(max_length=16)
    restored_reference_relation: PostGISInspectionResult
    restored_candidate_relation: PostGISInspectionResult
    archive_relation: PostGISInspectionResult
    independent_inspection_performed: Literal[True] = True
    execution_claim_trusted: Literal[False] = False
    database_modified: Literal[False] = False
    model_called: Literal[False] = False

    @model_validator(mode="after")
    def status_matches_findings(self):
        if (self.status == "verified") == bool(self.findings):
            raise ValueError("verified exactly when findings are empty")
        return self
