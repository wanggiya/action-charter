"""Tests for approval creation and verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from geoagent_harness.approvals import (
    ApprovalError,
    create_approval,
    load_approval,
    plan_sha256,
    verify_approval,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
    WorkflowPlan,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NOW = datetime(
    2026,
    8,
    9,
    12,
    0,
    tzinfo=timezone.utc,
)


def planner_result() -> PlannerResult:
    """Return a policy-valid planner result for approval tests."""

    plan = WorkflowPlan.model_validate(
        {
            "schema_version": "1.0",
            "status": "planned",
            "summary": (
                "Inspect, load, validate, and report."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill": "inspect_vector",
                    "purpose": "Inspect the source vector.",
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                    },
                    "requires_approval": False,
                    "expected_artifacts": [],
                    "validation_required": False,
                },
                {
                    "step_id": "step_2",
                    "skill": "load_vector_to_postgis",
                    "purpose": (
                        "Load into an approved schema."
                    ),
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                        "target_schema": (
                            "agent_sandbox"
                        ),
                        "target_table": (
                            "approval_test_points"
                        ),
                    },
                    "requires_approval": True,
                    "expected_artifacts": [
                        (
                            "agent_sandbox."
                            "approval_test_points"
                        )
                    ],
                    "validation_required": False,
                },
                {
                    "step_id": "step_3",
                    "skill": (
                        "validate_postgis_layer"
                    ),
                    "purpose": (
                        "Deterministically validate "
                        "the loaded layer."
                    ),
                    "arguments": {
                        "target_schema": (
                            "agent_sandbox"
                        ),
                        "target_table": (
                            "approval_test_points"
                        ),
                    },
                    "requires_approval": False,
                    "expected_artifacts": [],
                    "validation_required": True,
                },
                {
                    "step_id": "step_4",
                    "skill": "generate_report",
                    "purpose": (
                        "Generate the validated report."
                    ),
                    "arguments": {
                        "task_id": (
                            "approval-test-points"
                        ),
                    },
                    "requires_approval": True,
                    "expected_artifacts": [
                        (
                            "reports/"
                            "approval-test-points.md"
                        )
                    ],
                    "validation_required": False,
                },
            ],
            "assumptions": [],
            "risks": [],
            "execution_performed": False,
            "validation_performed": False,
        }
    )

    return PlannerResult(
        agent_id="planner",
        model="qwen-test",
        original_request=(
            "Inspect, load, validate, and report "
            "sample_points."
        ),
        context_references=[
            "context/PROJECT_SUMMARY.md",
            "context/SKILLS_INDEX.yaml",
        ],
        plan=plan,
        warnings=[],
    )

def test_plan_digest_is_stable() -> None:
    result = planner_result()

    first = plan_sha256(result.plan)
    second = plan_sha256(
        result.plan.model_copy(deep=True)
    )

    assert first == second
    assert len(first) == 64


def test_creates_and_loads_approval(
    tmp_path: Path,
) -> None:
    result = planner_result()

    record, path = create_approval(
        planner_result=result,
        step_ids=["step_2", "step_4"],
        decision="approved",
        approver="local-user",
        reason="Approved controlled writes.",
        approval_root=tmp_path / "approvals",
        project_root=PROJECT_ROOT,
        now=NOW,
        approval_id=(
            "approval-20260809t120000z-1234abcd"
        ),
    )

    loaded = load_approval(
        path=path,
        approval_root=tmp_path / "approvals",
    )

    assert loaded == record
    assert loaded.plan_sha256 == (
        plan_sha256(result.plan)
    )


def test_approval_does_not_store_plan_arguments(
    tmp_path: Path,
) -> None:
    result = planner_result()

    _, path = create_approval(
        planner_result=result,
        step_ids=["step_2"],
        decision="approved",
        approver="local-user",
        reason="password=do-not-store",
        approval_root=tmp_path / "approvals",
        project_root=PROJECT_ROOT,
        now=NOW,
        approval_id=(
            "approval-20260809t120000z-1234abcd"
        ),
    )

    content = path.read_text(encoding="utf-8")

    assert "do-not-store" not in content
    assert "[REDACTED]" in content
    assert "target_table" not in content


def test_overwrite_is_blocked(
    tmp_path: Path,
) -> None:
    result = planner_result()
    approval_root = tmp_path / "approvals"

    arguments = {
        "planner_result": result,
        "step_ids": ["step_2"],
        "decision": "approved",
        "approver": "local-user",
        "reason": "Approved.",
        "approval_root": approval_root,
        "project_root": PROJECT_ROOT,
        "now": NOW,
        "approval_id": (
            "approval-20260809t120000z-1234abcd"
        ),
    }

    create_approval(**arguments)

    with pytest.raises(
        ApprovalError,
        match="overwriting",
    ):
        create_approval(**arguments)


def test_exact_plan_approval_passes(
    tmp_path: Path,
) -> None:
    result = planner_result()

    record, _ = create_approval(
        planner_result=result,
        step_ids=["step_2", "step_4"],
        decision="approved",
        approver="local-user",
        reason="Approved.",
        approval_root=tmp_path / "approvals",
        project_root=PROJECT_ROOT,
        now=NOW,
        approval_id=(
            "approval-20260809t120000z-1234abcd"
        ),
    )

    verification = verify_approval(
        approval=record,
        plan=result.plan,
        required_step_ids=[
            "step_2",
            "step_4",
        ],
        now=NOW,
    )

    assert verification.approved is True


def test_changed_plan_invalidates_approval(
    tmp_path: Path,
) -> None:
    result = planner_result()

    record, _ = create_approval(
        planner_result=result,
        step_ids=["step_2"],
        decision="approved",
        approver="local-user",
        reason="Approved.",
        approval_root=tmp_path / "approvals",
        project_root=PROJECT_ROOT,
        now=NOW,
        approval_id=(
            "approval-20260809t120000z-1234abcd"
        ),
    )

    changed = result.plan.model_copy(deep=True)
    changed.steps[1].arguments[
        "target_table"
    ] = "different_table"

    verification = verify_approval(
        approval=record,
        plan=changed,
        required_step_ids=["step_2"],
        now=NOW,
    )

    assert verification.approved is False
    assert "exact plan" in verification.reason


def test_expired_approval_fails(
    tmp_path: Path,
) -> None:
    result = planner_result()

    record, _ = create_approval(
        planner_result=result,
        step_ids=["step_2"],
        decision="approved",
        approver="local-user",
        reason="Approved temporarily.",
        approval_root=tmp_path / "approvals",
        project_root=PROJECT_ROOT,
        expires_at=NOW + timedelta(minutes=10),
        now=NOW,
        approval_id=(
            "approval-20260809t120000z-1234abcd"
        ),
    )

    verification = verify_approval(
        approval=record,
        plan=result.plan,
        required_step_ids=["step_2"],
        now=NOW + timedelta(minutes=11),
    )

    assert verification.approved is False
    assert "expired" in verification.reason


def test_non_approval_step_cannot_be_approved(
    tmp_path: Path,
) -> None:
    result = planner_result()

    with pytest.raises(
        ApprovalError,
        match="do not require approval",
    ):
        create_approval(
            planner_result=result,
            step_ids=["step_1"],
            decision="approved",
            approver="local-user",
            reason="Incorrect approval.",
            approval_root=tmp_path / "approvals",
            project_root=PROJECT_ROOT,
            now=NOW,
        )