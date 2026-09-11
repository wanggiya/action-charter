"""Deterministic planning, approval, execution and verification for GeoServer."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import httpx

from geoagent_harness.geoserver_inspection import inspect_geoserver_layer
from geoagent_harness.geoserver_inspection.service import (
    GeoServerInspectionReader,
    HttpGeoServerInspectionReader,
    _read_password,
)
from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.redaction import redact_text

from .schemas import (
    GeoServerPublicationApproval,
    GeoServerPublicationExecutionResult,
    GeoServerPublicationPlan,
    GeoServerPublicationPlanRequest,
    GeoServerPublicationPlanResult,
    GeoServerPublicationVerificationResult,
)

STEP_IDS = [
    "step_1_enable_and_advertise_feature_type",
]
FIXED_FEATURE_TYPE_BODY = {"featureType": {"enabled": True, "advertised": True}}


class GeoServerPublicationError(RuntimeError):
    pass


def canonical_json(value: object) -> str:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def publication_plan_sha256(plan: GeoServerPublicationPlan) -> str:
    return sha256(plan)


def publication_approval_sha256(approval: GeoServerPublicationApproval) -> str:
    return sha256(approval)


def publication_execution_sha256(execution: GeoServerPublicationExecutionResult) -> str:
    return sha256(execution)


def plan_geoserver_publication(*, request: GeoServerPublicationPlanRequest,
    settings: MCPSettings, reader: GeoServerInspectionReader | None = None,
) -> GeoServerPublicationPlanResult:
    before = inspect_geoserver_layer(request=request.target, settings=settings, reader=reader)
    try:
        plan = GeoServerPublicationPlan(
            plan_id=request.plan_id, target=request.target,
            before_sha256=sha256(before), before=before,
            operation="enable_and_advertise_existing_layer",
            approval_required_step_ids=STEP_IDS,
        )
    except ValueError as exc:
        raise GeoServerPublicationError("GeoServer target is not ready for bounded publication") from exc
    return GeoServerPublicationPlanResult(plan_sha256=publication_plan_sha256(plan), plan=plan)


def create_geoserver_publication_approval(*, plan_result: GeoServerPublicationPlanResult,
    decision: str, approver: str, reason: str, expires_at: datetime | None = None,
    now: datetime | None = None,
) -> GeoServerPublicationApproval:
    if plan_result.plan_sha256 != publication_plan_sha256(plan_result.plan):
        raise GeoServerPublicationError("publication plan digest changed")
    if decision not in {"approved", "denied"}:
        raise GeoServerPublicationError("decision must be approved or denied")
    active_now = now or datetime.now(timezone.utc)
    stamp = active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return GeoServerPublicationApproval(
        approval_id=f"geoserver-publication-approval-{stamp}-{uuid.uuid4().hex[:8]}",
        plan_id=plan_result.plan.plan_id, plan_sha256=plan_result.plan_sha256,
        decision=decision, approved_step_ids=STEP_IDS if decision == "approved" else [],
        approver=redact_text(approver), reason=redact_text(reason),
        created_at=active_now, expires_at=expires_at,
    )


class GeoServerPublicationClient(GeoServerInspectionReader, Protocol):
    def set_feature_type(self, *, workspace: str, datastore: str, layer: str,
                         enabled: bool, advertised: bool) -> None: ...


class HttpGeoServerPublicationClient(HttpGeoServerInspectionReader):
    def __init__(self, settings: MCPSettings) -> None:
        self._client = httpx.Client(
            base_url=f"{settings.geoserver_base_url}/rest/",
            auth=(settings.geoserver_user, _read_password(settings.geoserver_password_file)),
            timeout=5.0, follow_redirects=False,
            headers={"Accept": "application/json"},
        )

    def _put(self, path: str, body: dict[str, Any]) -> None:
        try:
            response = self._client.put(path, json=body)
        except httpx.HTTPError:
            raise GeoServerPublicationError(
                "GeoServer publication request failed; endpoint details were redacted"
            ) from None
        if response.status_code not in {200, 201}:
            raise GeoServerPublicationError(
                f"GeoServer publication failed with HTTP status {response.status_code}"
            )

    def set_feature_type(self, *, workspace: str, datastore: str, layer: str,
                         enabled: bool, advertised: bool) -> None:
        self._put(
            f"workspaces/{workspace}/datastores/{datastore}/featuretypes/{layer}.json",
            FIXED_FEATURE_TYPE_BODY if enabled and advertised else
            {"featureType": {"enabled": enabled, "advertised": advertised}},
        )

def execute_geoserver_publication(*, plan_result: GeoServerPublicationPlanResult,
    approval: GeoServerPublicationApproval, settings: MCPSettings,
    confirm_plan_sha256: str, confirm_approval_sha256: str,
    client: GeoServerPublicationClient | None = None,
    now: datetime | None = None,
) -> GeoServerPublicationExecutionResult:
    if not settings.enable_write_tools:
        raise GeoServerPublicationError("GeoServer write tools are disabled")
    plan_digest = publication_plan_sha256(plan_result.plan)
    approval_digest = publication_approval_sha256(approval)
    if plan_result.plan_sha256 != plan_digest or confirm_plan_sha256 != plan_digest:
        raise GeoServerPublicationError("explicit plan digest confirmation does not match")
    if confirm_approval_sha256 != approval_digest:
        raise GeoServerPublicationError("explicit approval digest confirmation does not match")
    if approval.decision != "approved" or approval.approved_step_ids != STEP_IDS:
        raise GeoServerPublicationError("publication is not approved for the exact scope")
    if approval.plan_id != plan_result.plan.plan_id or approval.plan_sha256 != plan_digest:
        raise GeoServerPublicationError("approval does not bind the publication plan")
    active_now = now or datetime.now(timezone.utc)
    if approval.expires_at is not None and active_now >= approval.expires_at:
        raise GeoServerPublicationError("publication approval has expired")
    active = client or HttpGeoServerPublicationClient(settings)
    owns = client is None
    try:
        before = inspect_geoserver_layer(request=plan_result.plan.target, settings=settings, reader=active)
        if sha256(before) != plan_result.plan.before_sha256:
            raise GeoServerPublicationError("GeoServer publication target changed after planning")
        target = plan_result.plan.target
        feature_put = False
        try:
            active.set_feature_type(workspace=target.workspace, datastore=target.datastore,
                                    layer=target.layer, enabled=True, advertised=True)
            feature_put = True
            after = inspect_geoserver_layer(request=target, settings=settings, reader=active)
            valid = (
                after.feature_type is not None and after.feature_type.enabled and after.feature_type.advertised
                and after.published_layer is not None and after.published_layer.enabled and after.published_layer.advertised
            )
            if not valid:
                raise GeoServerPublicationError("GeoServer did not confirm the complete published state")
            status, findings = "published", []
            compensation_attempted = compensation_succeeded = False
        except GeoServerPublicationError as exc:
            if not feature_put:
                raise
            findings = ["publication_failed: " + str(exc)]
            compensation_attempted = True
            try:
                old_feature = before.feature_type
                active.set_feature_type(workspace=target.workspace, datastore=target.datastore,
                                        layer=target.layer, enabled=old_feature.enabled,
                                        advertised=old_feature.advertised)
                after = inspect_geoserver_layer(request=target, settings=settings, reader=active)
                compensation_succeeded = sha256(after) == plan_result.plan.before_sha256
            except GeoServerPublicationError:
                compensation_succeeded = False
                after = inspect_geoserver_layer(request=target, settings=settings, reader=active)
            status = "rolled_back" if compensation_succeeded else "reconciliation_required"
            if not compensation_succeeded:
                findings.append("compensation_not_confirmed")
    finally:
        if owns:
            active.close()
    stamp = active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return GeoServerPublicationExecutionResult(
        execution_id=f"geoserver-publication-execution-{stamp}-{uuid.uuid4().hex[:8]}",
        plan_id=plan_result.plan.plan_id, plan_sha256=plan_digest,
        approval_id=approval.approval_id, approval_sha256=approval_digest,
        before_sha256=plan_result.plan.before_sha256, after=after, status=status,
        findings=findings,
        approved_step_ids=approval.approved_step_ids,
        feature_type_put_performed=feature_put,
        compensation_attempted=compensation_attempted,
        compensation_succeeded=compensation_succeeded,
        post_publication_validated=status == "published",
        geoserver_modified=status != "rolled_back",
    )


def verify_geoserver_publication(*, execution: GeoServerPublicationExecutionResult,
    plan_result: GeoServerPublicationPlanResult, settings: MCPSettings,
    reader: GeoServerInspectionReader | None = None,
    now: datetime | None = None,
) -> GeoServerPublicationVerificationResult:
    if execution.plan_id != plan_result.plan.plan_id or execution.plan_sha256 != plan_result.plan_sha256:
        raise GeoServerPublicationError("execution does not bind the supplied publication plan")
    observed = inspect_geoserver_layer(request=plan_result.plan.target, settings=settings, reader=reader)
    findings: list[str] = []
    if execution.status != "published":
        findings.append("execution_not_published")
    if observed.feature_type is None:
        findings.append("feature_type_missing")
    else:
        if not observed.feature_type.enabled:
            findings.append("feature_type_disabled")
        if not observed.feature_type.advertised:
            findings.append("feature_type_not_advertised")
    if observed.published_layer is None:
        findings.append("published_layer_missing")
    else:
        if not observed.published_layer.enabled:
            findings.append("published_layer_disabled")
        if not observed.published_layer.advertised:
            findings.append("published_layer_not_advertised")
    active_now = now or datetime.now(timezone.utc)
    stamp = active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return GeoServerPublicationVerificationResult(
        verification_id=f"geoserver-publication-verification-{stamp}-{uuid.uuid4().hex[:8]}",
        execution_id=execution.execution_id,
        execution_sha256=publication_execution_sha256(execution),
        plan_id=execution.plan_id, plan_sha256=execution.plan_sha256,
        status="failed" if findings else "verified", findings=findings, observed=observed,
    )


def load_json(path: Path, model: type[Any]) -> Any:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
            raise OSError
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GeoServerPublicationError("publication evidence is unavailable or invalid") from exc
