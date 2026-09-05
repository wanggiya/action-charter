"""Schemas for independent post-promotion verification."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from geoagent_harness.postgis_inspection import PostGISInspectionResult


class PostGISPromotionVerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    verification_id: str = Field(pattern=r"^postgis-promotion-verification-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$")
    execution_id: str
    execution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plan_id: str
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["verified", "failed"]
    findings: list[str] = Field(max_length=16)
    promoted_relation: PostGISInspectionResult
    archived_relation: PostGISInspectionResult
    independent_inspection_performed: Literal[True] = True
    execution_claim_trusted: Literal[False] = False
    database_modified: Literal[False] = False
    model_called: Literal[False] = False

    @model_validator(mode="after")
    def status_matches_findings(self):
        if (self.status == "verified") == bool(self.findings):
            raise ValueError("verified exactly when findings are empty")
        return self
