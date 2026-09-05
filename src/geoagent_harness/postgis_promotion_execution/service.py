"""Approval-gated transactional PostGIS relation promotion."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import psycopg
from psycopg import IsolationLevel, sql

from geoagent_harness.mcp_server.settings import MCPSettings, validate_identifier
from geoagent_harness.postgis_inspection import (
    PostGISInspectionRequest,
    PostGISInspectionResult,
    inspect_postgis_table,
)
from geoagent_harness.postgis_inspection.service import PsycopgPostGISInspectionReader
from geoagent_harness.postgis_promotion_approval import (
    APPROVAL_STEP_IDS,
    load_postgis_promotion_approval,
    postgis_promotion_approval_sha256,
)
from geoagent_harness.postgis_promotion_plan import postgis_promotion_plan_sha256
from geoagent_harness.postgis_promotion_approval.service import load_postgis_promotion_plan_result
from geoagent_harness.verifier.postgis import _read_password
from geoagent_harness.postgis_promotion_execution.schemas import PostGISPromotionExecutionResult


class PostGISPromotionExecutionError(RuntimeError):
    """Raised when promotion cannot be committed safely."""


def _digest(value: object) -> str:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _profile(value: PostGISInspectionResult) -> dict[str, object]:
    return {
        "columns": [item.model_dump(mode="json") for item in value.columns],
        "primary_key": value.primary_key.columns if value.primary_key else None,
        "unique_keys": sorted(item.columns for item in value.unique_keys),
        "row_count": value.row_count,
        "geometry_columns": [item.model_dump(mode="json") for item in value.geometry_columns],
    }


class PromotionTransaction(Protocol):
    def lock(self, relations: list[tuple[str, str]]) -> None: ...
    def inspect(self, request: PostGISInspectionRequest) -> PostGISInspectionResult: ...
    def rename(self, source: tuple[str, str], target: tuple[str, str]) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


class PsycopgPromotionTransaction:
    """One fixed, identifier-safe PostGIS transaction."""

    def __init__(self, settings: MCPSettings) -> None:
        self.settings = settings
        try:
            self.connection = psycopg.connect(
                host=settings.postgres_host, port=settings.postgres_port,
                dbname=settings.postgres_database, user=settings.postgres_user,
                password=_read_password(settings.postgres_password_file), connect_timeout=5,
            )
            self.connection.isolation_level = IsolationLevel.SERIALIZABLE
            self.reader = PsycopgPostGISInspectionReader(
                settings, connection=self.connection
            )
        except (psycopg.Error, RuntimeError):
            raise PostGISPromotionExecutionError(
                "PostGIS promotion connection failed; connection details were redacted"
            ) from None

    def lock(self, relations: list[tuple[str, str]]) -> None:
        self.connection.execute(
            "SELECT set_config('statement_timeout', %s, true), "
            "set_config('lock_timeout', %s, true)",
            ("30000", "10000"),
        )
        query = sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(
            sql.SQL(", ").join(sql.Identifier(s, t) for s, t in relations)
        )
        self.connection.execute(query)

    def inspect(self, request: PostGISInspectionRequest) -> PostGISInspectionResult:
        return inspect_postgis_table(request=request, settings=self.settings, reader=self.reader)

    def rename(self, source: tuple[str, str], target: tuple[str, str]) -> None:
        source_schema, source_table = source
        target_schema, target_table = target
        current_schema = source_schema
        if source_schema != target_schema:
            self.connection.execute(
                sql.SQL("ALTER TABLE {} SET SCHEMA {}").format(
                    sql.Identifier(source_schema, source_table), sql.Identifier(target_schema)
                )
            )
            current_schema = target_schema
        if source_table != target_table:
            self.connection.execute(
                sql.SQL("ALTER TABLE {} RENAME TO {}").format(
                    sql.Identifier(current_schema, source_table), sql.Identifier(target_table)
                )
            )

    def commit(self) -> None: self.connection.commit()
    def rollback(self) -> None: self.connection.rollback()
    def close(self) -> None: self.connection.close()


def execute_postgis_promotion(
    *, plan_file: Path, plan_root: Path, approval_file: Path,
    approval_root: Path, settings: MCPSettings,
    confirm_plan_sha256: str, confirm_approval_sha256: str,
    transaction: PromotionTransaction | None = None,
    now: datetime | None = None,
) -> PostGISPromotionExecutionResult:
    """Execute exactly two approved renames and commit only after validation."""
    if not settings.enable_write_tools:
        raise PostGISPromotionExecutionError("PostGIS write tools are disabled")
    try:
        plan_result = load_postgis_promotion_plan_result(plan_file, plan_root=plan_root)
        approval = load_postgis_promotion_approval(approval_file, approval_root=approval_root)
    except Exception as exc:
        raise PostGISPromotionExecutionError("promotion evidence could not be verified") from exc
    plan_digest = postgis_promotion_plan_sha256(plan_result.plan)
    approval_digest = postgis_promotion_approval_sha256(approval)
    active_now = now or datetime.now(timezone.utc)
    if confirm_plan_sha256 != plan_digest or confirm_approval_sha256 != approval_digest:
        raise PostGISPromotionExecutionError("explicit digest confirmation does not match")
    if approval.decision != "approved" or approval.approved_step_ids != APPROVAL_STEP_IDS:
        raise PostGISPromotionExecutionError("promotion is not approved for the exact scope")
    if approval.plan_id != plan_result.plan.plan_id or approval.plan_sha256 != plan_digest:
        raise PostGISPromotionExecutionError("approval does not bind the promotion plan")
    if approval.assessment_sha256 != plan_result.plan.assessment_sha256:
        raise PostGISPromotionExecutionError("approval assessment digest does not match")
    if active_now.tzinfo is None or active_now.utcoffset() is None:
        raise PostGISPromotionExecutionError("execution time must be timezone-aware")
    if approval.expires_at is not None:
        if approval.expires_at.tzinfo is None or approval.expires_at.utcoffset() is None:
            raise PostGISPromotionExecutionError("approval expiry must be timezone-aware")
        if active_now >= approval.expires_at:
            raise PostGISPromotionExecutionError("promotion approval has expired")

    plan = plan_result.plan
    reference = plan.assessment.comparison.reference
    candidate = plan.assessment.comparison.candidate
    archive = plan.archive
    requests = [
        PostGISInspectionRequest(target_schema=x.target_schema, target_table=x.target_table)
        for x in (reference, candidate, archive)
    ]
    for request in requests:
        validate_identifier(request.target_schema, label="target_schema")
        validate_identifier(request.target_table, label="target_table")
        if request.target_schema not in settings.allowed_schemas:
            raise PostGISPromotionExecutionError("promotion schema is not allowlisted")
    active = transaction or PsycopgPromotionTransaction(settings)
    committed = False
    try:
        active.lock([(reference.target_schema, reference.target_table), (candidate.target_schema, candidate.target_table)])
        observed_reference = active.inspect(requests[0])
        observed_candidate = active.inspect(requests[1])
        observed_archive = active.inspect(requests[2])
        if _digest(observed_reference) != plan.reference_snapshot_sha256:
            raise PostGISPromotionExecutionError("reference snapshot changed")
        if _digest(observed_candidate) != plan.candidate_snapshot_sha256:
            raise PostGISPromotionExecutionError("candidate snapshot changed")
        if observed_archive.table_exists:
            raise PostGISPromotionExecutionError("archive relation now exists")
        active.rename(
            (reference.target_schema, reference.target_table),
            (archive.target_schema, archive.target_table),
        )
        active.rename(
            (candidate.target_schema, candidate.target_table),
            (reference.target_schema, reference.target_table),
        )
        promoted = active.inspect(requests[0])
        if not promoted.table_exists or _profile(promoted) != _profile(candidate):
            raise PostGISPromotionExecutionError("promoted relation failed validation")
        active.commit()
        committed = True
    except Exception as exc:
        if not committed:
            active.rollback()
        if isinstance(exc, PostGISPromotionExecutionError):
            raise
        raise PostGISPromotionExecutionError(
            "PostGIS promotion failed and was rolled back; details were redacted"
        ) from None
    finally:
        try:
            active.close()
        except Exception:
            if not committed:
                raise PostGISPromotionExecutionError(
                    "PostGIS promotion connection could not be closed safely"
                ) from None
    stamp = active_now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ").lower()
    return PostGISPromotionExecutionResult(
        execution_id=f"postgis-promotion-execution-{stamp}-{uuid.uuid4().hex[:8]}",
        plan_id=plan.plan_id, plan_sha256=plan_digest,
        approval_id=approval.approval_id, approval_sha256=approval_digest,
        reference_before_sha256=plan.reference_snapshot_sha256,
        candidate_before_sha256=plan.candidate_snapshot_sha256,
        promoted_relation=promoted, approved_step_ids=approval.approved_step_ids,
    )
