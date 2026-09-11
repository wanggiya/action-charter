"""Strict contracts for approval-gated GeoServer layer activation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from geoagent_harness.geoserver_inspection import (
    GeoServerInspectionRequest,
    GeoServerInspectionResult,
)


class GeoServerPublicationPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    plan_id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$", max_length=100)
    target: GeoServerInspectionRequest


class GeoServerPublicationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    plan_id: str
    target: GeoServerInspectionRequest
    before_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    before: GeoServerInspectionResult
    operation: Literal["enable_and_advertise_existing_layer"]
    rest_method: Literal["PUT"] = "PUT"
    approval_required_step_ids: list[
        Literal["step_1_enable_and_advertise_feature_type"]
    ] = Field(min_length=1, max_length=1)
    planning_performed: Literal[True] = True
    approval_created: Literal[False] = False
    execution_performed: Literal[False] = False
    geoserver_modified: Literal[False] = False
    arbitrary_rest_path_accepted: Literal[False] = False
    arbitrary_request_body_accepted: Literal[False] = False
    model_called: Literal[False] = False

    @model_validator(mode="after")
    def target_is_ready(self) -> "GeoServerPublicationPlan":
        if self.before.status != "inspected":
            raise ValueError("publication target must exist")
        if self.before.feature_type is None or not self.before.feature_type.enabled:
            raise ValueError("feature type must already exist and be enabled")
        if self.before.published_layer is None:
            raise ValueError("published layer must already exist")
        if self.before.published_layer.enabled and self.before.published_layer.advertised:
            raise ValueError("layer is already enabled and advertised")
        if self.before.workspace != self.target.workspace or self.before.datastore != self.target.datastore or self.before.layer != self.target.layer:
            raise ValueError("inspection identity does not match publication target")
        if self.approval_required_step_ids != ["step_1_enable_and_advertise_feature_type"]:
            raise ValueError("publication approval scope is not exact")
        return self


class GeoServerPublicationPlanResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plan: GeoServerPublicationPlan


class GeoServerPublicationApproval(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    approval_id: str = Field(pattern=r"^geoserver-publication-approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$")
    plan_id: str
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    approved_step_ids: list[
        Literal["step_1_enable_and_advertise_feature_type"]
    ] = Field(max_length=1)
    approver: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    created_at: datetime
    expires_at: datetime | None = None
    secrets_redacted: Literal[True] = True
    execution_performed: Literal[False] = False
    geoserver_modified: Literal[False] = False

    @model_validator(mode="after")
    def decision_scope_is_exact(self) -> "GeoServerPublicationApproval":
        expected = ["step_1_enable_and_advertise_feature_type"]
        if self.decision == "approved" and self.approved_step_ids != expected:
            raise ValueError("approved publication requires exact mutation scope")
        if self.decision == "denied" and self.approved_step_ids:
            raise ValueError("denied publication cannot approve steps")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")
        return self


class GeoServerPublicationExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    execution_id: str = Field(pattern=r"^geoserver-publication-execution-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$")
    plan_id: str
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_id: str
    approval_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    before_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    after: GeoServerInspectionResult
    status: Literal["published", "rolled_back", "reconciliation_required"]
    findings: list[str] = Field(max_length=8)
    approved_step_ids: list[str] = Field(min_length=1, max_length=1)
    human_approval_verified: Literal[True] = True
    input_state_reverified: Literal[True] = True
    feature_type_put_performed: bool
    compensation_attempted: bool
    compensation_succeeded: bool
    post_publication_validated: bool
    execution_performed: Literal[True] = True
    geoserver_modified: bool
    arbitrary_rest_path_accepted: Literal[False] = False
    arbitrary_request_body_accepted: Literal[False] = False
    credentials_redacted: Literal[True] = True
    model_called: Literal[False] = False

    @model_validator(mode="after")
    def outcome_is_consistent(self) -> "GeoServerPublicationExecutionResult":
        if self.status == "published":
            if self.findings or not self.feature_type_put_performed or not self.post_publication_validated or self.compensation_attempted or not self.geoserver_modified:
                raise ValueError("published execution outcome is inconsistent")
        elif self.status == "rolled_back":
            if not self.findings or not self.compensation_attempted or not self.compensation_succeeded or self.geoserver_modified:
                raise ValueError("rolled-back execution outcome is inconsistent")
        elif not self.findings or not self.compensation_attempted or self.compensation_succeeded or not self.geoserver_modified:
            raise ValueError("reconciliation-required outcome is inconsistent")
        return self


class GeoServerPublicationVerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    verification_id: str = Field(pattern=r"^geoserver-publication-verification-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$")
    execution_id: str
    execution_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plan_id: str
    plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["verified", "failed"]
    findings: list[str] = Field(max_length=8)
    observed: GeoServerInspectionResult
    independent_inspection_performed: Literal[True] = True
    execution_claim_trusted: Literal[False] = False
    geoserver_modified: Literal[False] = False
    model_called: Literal[False] = False

    @model_validator(mode="after")
    def status_matches_findings(self) -> "GeoServerPublicationVerificationResult":
        if (self.status == "verified") == bool(self.findings):
            raise ValueError("verified exactly when findings are empty")
        return self
