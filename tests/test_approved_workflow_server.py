"""Tests for server-side approved workflow verification."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.approvals import (
    ApprovalRecord,
    plan_sha256,
)
from geoagent_harness.executor import (
    build_execution_envelope,
)
from geoagent_harness.mcp_server.approved_workflow import (
    ApprovedWorkflowError,
    run_approved_vector_postgis_workflow,
    validate_approved_workflow_request,
)
from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
    WorkflowPlan,
)
from geoagent_harness.skills.load_vector_to_postgis.service import (
    LoadVectorError,
)

NOW = datetime(
    2026,
    8,
    9,
    20,
    0,
    tzinfo=timezone.utc,
)


def planner_result() -> PlannerResult:
    plan = WorkflowPlan.model_validate(
        {
            "schema_version": "1.0",
            "status": "planned",
            "summary": "Approved workflow test.",
            "steps": [
                {
                    "step_id": "step_1",
                    "skill": "inspect_vector",
                    "purpose": "Inspect.",
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        )
                    },
                    "requires_approval": False,
                    "expected_artifacts": [],
                    "validation_required": False,
                },
                {
                    "step_id": "step_2",
                    "skill": "load_vector_to_postgis",
                    "purpose": "Load.",
                    "arguments": {
                        "path": (
                            "data/input/"
                            "sample_points.geojson"
                        ),
                        "target_schema": "agent_sandbox",
                        "target_table": (
                            "checkpoint5d_points"
                        ),
                    },
                    "requires_approval": True,
                    "expected_artifacts": [],
                    "validation_required": False,
                },
                {
                    "step_id": "step_3",
                    "skill": (
                        "validate_postgis_layer"
                    ),
                    "purpose": "Validate.",
                    "arguments": {
                        "target_schema": "agent_sandbox",
                        "target_table": (
                            "checkpoint5d_points"
                        ),
                    },
                    "requires_approval": False,
                    "expected_artifacts": [],
                    "validation_required": True,
                },
                {
                    "step_id": "step_4",
                    "skill": "generate_report",
                    "purpose": "Report.",
                    "arguments": {
                        "task_id": (
                            "checkpoint5d-points"
                        )
                    },
                    "requires_approval": True,
                    "expected_artifacts": [],
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
        model="qwen-test",
        original_request="Approved workflow test.",
        context_references=[
            "context/PROJECT_SUMMARY.md",
        ],
        plan=plan,
    )


def approval_for(
    result: PlannerResult,
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=(
            "approval-20260809t200000z-1234abcd"
        ),
        plan_sha256=plan_sha256(result.plan),
        decision="approved",
        step_ids=["step_2", "step_4"],
        approver="local-user",
        reason="Approved.",
        created_at=NOW,
        secrets_redacted=True,
    )


@pytest.fixture
def records(
    tmp_path: Path,
) -> tuple[
    PlannerResult,
    ApprovalRecord,
    MCPSettings,
]:
    plan_root = tmp_path / "plans"
    approval_root = tmp_path / "approvals"

    plan_root.mkdir()
    approval_root.mkdir()

    result = planner_result()
    approval = approval_for(result)

    (
        plan_root / "plan.json"
    ).write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    (
        approval_root / "approval.json"
    ).write_text(
        approval.model_dump_json(indent=2),
        encoding="utf-8",
    )

    settings = MCPSettings(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        plan_root=plan_root,
        approval_root=approval_root,
        allowed_schemas=frozenset(
            {"agent_sandbox"}
        ),
        enable_write_tools=False,
        allow_overwrite=False,
    )

    return result, approval, settings


def test_server_rebuilds_exact_envelope(
    records,
) -> None:
    result, approval, settings = records

    envelope = build_execution_envelope(
        planner_result=result,
        approval=approval,
        allowed_schemas={"agent_sandbox"},
    )

    verified = validate_approved_workflow_request(
        execution_envelope=(
            envelope.model_dump(mode="json")
        ),
        plan_filename="plan.json",
        approval_filename="approval.json",
        settings=settings,
    )

    assert verified == envelope


def test_changed_envelope_is_rejected(
    records,
) -> None:
    result, approval, settings = records

    envelope = build_execution_envelope(
        planner_result=result,
        approval=approval,
        allowed_schemas={"agent_sandbox"},
    )

    payload = envelope.model_dump(mode="json")
    payload["tool_arguments"][
        "target_table"
    ] = "changed_table"

    with pytest.raises(
        ApprovedWorkflowError,
        match="does not match",
    ):
        validate_approved_workflow_request(
            execution_envelope=payload,
            plan_filename="plan.json",
            approval_filename="approval.json",
            settings=settings,
        )


def test_record_path_escape_is_rejected(
    records,
) -> None:
    result, approval, settings = records

    envelope = build_execution_envelope(
        planner_result=result,
        approval=approval,
        allowed_schemas={"agent_sandbox"},
    )

    with pytest.raises(
        ApprovedWorkflowError,
        match="plain JSON filename",
    ):
        validate_approved_workflow_request(
            execution_envelope=(
                envelope.model_dump(mode="json")
            ),
            plan_filename="../plan.json",
            approval_filename="approval.json",
            settings=settings,
        )


def test_execution_fails_before_records_when_disabled(
    tmp_path: Path,
) -> None:
    settings = MCPSettings(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        plan_root=tmp_path / "missing-plans",
        approval_root=tmp_path / "missing-approvals",
        enable_write_tools=False,
        allow_overwrite=False,
        allowed_schemas=frozenset(
            {"agent_sandbox"}
        ),
    )

    with pytest.raises(
        LoadVectorError,
        match="write tools are disabled",
    ):
        run_approved_vector_postgis_workflow(
            execution_envelope={},
            plan_filename="missing.json",
            approval_filename="missing.json",
            settings=settings,
        )
