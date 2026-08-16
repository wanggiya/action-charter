"""Create and verify append-only plan approvals."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# import yaml
from pydantic import ValidationError

from geoagent_harness.approvals.schemas import (
    ApprovalRecord,
    ApprovalVerification,
)
from geoagent_harness.planner.policy import (
    validate_plan_policy,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
    WorkflowPlan,
)
from geoagent_harness.trace import redact_text

from geoagent_harness.schema_registry import (
    ArtifactType,
    SchemaVersionError,
    require_supported_schema,
)

from geoagent_harness.skill_registry import (
    SkillRegistryError,
    load_skill_registry,
)

MAX_PLAN_FILE_BYTES = 1_000_000


class ApprovalError(RuntimeError):
    """Raised when an approval cannot be created or verified."""


def canonical_plan_json(
    plan: WorkflowPlan,
) -> str:
    """Return the canonical representation used for hashing."""

    return json.dumps(
        plan.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def plan_sha256(
    plan: WorkflowPlan,
) -> str:
    """Create a stable digest for an exact validated plan."""

    return hashlib.sha256(
        canonical_plan_json(plan).encode("utf-8")
    ).hexdigest()


def _safe_file_under_root(
    *,
    path: Path,
    root: Path,
) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve()

    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ApprovalError(
            "file is outside the approved root"
        ) from exc

    return resolved_path


def load_planner_result(
    *,
    path: Path,
    plan_root: Path,
) -> PlannerResult:
    """Load one Planner result from the approved plan root."""

    safe_path = _safe_file_under_root(
        path=path,
        root=plan_root,
    )

    if not safe_path.is_file():
        raise ApprovalError(
            "planner result file is unavailable"
        )

    if safe_path.stat().st_size > MAX_PLAN_FILE_BYTES:
        raise ApprovalError(
            "planner result file exceeds the size limit"
        )

    try:
        payload: dict[str, Any] = json.loads(
            safe_path.read_text(encoding="utf-8")
        )

        require_supported_schema(
            payload,
            artifact_type=ArtifactType.WORKFLOW_PLAN,
            version_path=(
                "plan",
                "schema_version",
            ),
        )

        return PlannerResult.model_validate(payload)
    except (
        json.JSONDecodeError,
        OSError,
        SchemaVersionError,
        ValidationError,
    ) as exc:
        raise ApprovalError(
            "planner result file is invalid"
        ) from exc


def _implemented_skills(
    project_root: Path,
) -> set[str]:
    try:
        registry = load_skill_registry(
            project_root
        )
    except SkillRegistryError as exc:
        raise ApprovalError(
            "trusted skill registry is unavailable"
        ) from exc

    return {
        skill.id
        for skill in registry.implemented_skills()
    }

def _approval_id(
    now: datetime,
) -> str:
    timestamp = now.astimezone(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    return (
        f"approval-{timestamp}-"
        f"{uuid.uuid4().hex[:8]}"
    ).lower()


def create_approval(
    *,
    planner_result: PlannerResult,
    step_ids: list[str],
    decision: str,
    approver: str,
    reason: str,
    approval_root: Path,
    project_root: Path,
    human_corrections: list[str] | None = None,
    expires_at: datetime | None = None,
    now: datetime | None = None,
    approval_id: str | None = None,
) -> tuple[ApprovalRecord, Path]:
    """Create one non-overwriting approval record."""

    active_now = now or datetime.now(timezone.utc)

    validate_plan_policy(
        planner_result.plan,
        available_skills=_implemented_skills(
            project_root
        ),
    )

    plan_steps = {
        step.step_id: step
        for step in planner_result.plan.steps
    }

    if not step_ids:
        raise ApprovalError(
            "at least one step ID is required"
        )

    unknown_steps = sorted(
        set(step_ids) - set(plan_steps)
    )

    if unknown_steps:
        raise ApprovalError(
            "approval references unknown steps: "
            + ", ".join(unknown_steps)
        )

    if decision == "approved":
        non_approval_steps = [
            step_id
            for step_id in step_ids
            if not plan_steps[
                step_id
            ].requires_approval
        ]

        if non_approval_steps:
            raise ApprovalError(
                "approval requested for steps that do not "
                "require approval: "
                + ", ".join(non_approval_steps)
            )

    record = ApprovalRecord(
        approval_id=(
            approval_id
            or _approval_id(active_now)
        ),
        plan_sha256=plan_sha256(
            planner_result.plan
        ),
        decision=decision,
        step_ids=step_ids,
        approver=redact_text(approver),
        reason=redact_text(reason),
        human_corrections=[
            redact_text(correction)
            for correction in (
                human_corrections or []
            )
        ],
        created_at=active_now,
        expires_at=expires_at,
        secrets_redacted=True,
    )

    root = approval_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    path = _safe_file_under_root(
        path=root / f"{record.approval_id}.json",
        root=root,
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as stream:
            json.dump(
                record.model_dump(mode="json"),
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
    except FileExistsError as exc:
        raise ApprovalError(
            "approval record already exists; "
            "overwriting is blocked"
        ) from exc
    except OSError as exc:
        raise ApprovalError(
            "approval record could not be written"
        ) from exc

    return record, path


def load_approval(
    *,
    path: Path,
    approval_root: Path,
) -> ApprovalRecord:
    """Load an approval only from the approved root."""

    safe_path = _safe_file_under_root(
        path=path,
        root=approval_root,
    )

    try:
        payload: dict[str, Any] = json.loads(
            safe_path.read_text(encoding="utf-8")
        )

        require_supported_schema(
            payload,
            artifact_type=ArtifactType.APPROVAL_RECORD,
        )

        return ApprovalRecord.model_validate(payload)
    except (
        json.JSONDecodeError,
        OSError,
        SchemaVersionError,
        ValidationError,
    ) as exc:
        raise ApprovalError(
            "approval record is invalid or unavailable"
        ) from exc


def verify_approval(
    *,
    approval: ApprovalRecord,
    plan: WorkflowPlan,
    required_step_ids: list[str],
    now: datetime | None = None,
) -> ApprovalVerification:
    """Verify an approval against an exact plan and steps."""

    active_now = now or datetime.now(timezone.utc)
    digest = plan_sha256(plan)

    if approval.plan_sha256 != digest:
        return ApprovalVerification(
            approved=False,
            plan_sha256=digest,
            reason="approval does not match the exact plan",
        )

    if approval.decision != "approved":
        return ApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            plan_sha256=digest,
            reason="approval decision is denied",
        )

    if (
        approval.expires_at is not None
        and active_now >= approval.expires_at
    ):
        return ApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            plan_sha256=digest,
            reason="approval has expired",
        )

    missing_steps = sorted(
        set(required_step_ids)
        - set(approval.step_ids)
    )

    if missing_steps:
        return ApprovalVerification(
            approved=False,
            approval_id=approval.approval_id,
            plan_sha256=digest,
            reason=(
                "approval does not cover required steps: "
                + ", ".join(missing_steps)
            ),
        )

    return ApprovalVerification(
        approved=True,
        approval_id=approval.approval_id,
        plan_sha256=digest,
        approved_step_ids=sorted(
            set(required_step_ids)
        ),
        reason="exact plan and required steps are approved",
    )