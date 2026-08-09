"""Tests for approval evidence in workflow traces."""

from datetime import datetime, timezone

from geoagent_harness.reporting import render_report
from geoagent_harness.trace import (
    TraceTimestamps,
    WorkflowTrace,
)


def test_trace_and_report_include_approval() -> None:
    now = datetime.now(timezone.utc)

    trace = WorkflowTrace(
        task_id="approval-trace-test",
        original_request="Test approved workflow.",
        context_references=[
            "context/PROJECT_SUMMARY.md",
        ],
        selected_skills=[
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
            "generate_report",
        ],
        plan_sha256="a" * 64,
        approval_id=(
            "approval-20260809t200000z-1234abcd"
        ),
        approved_step_ids=[
            "step_2",
            "step_4",
        ],
        tool_arguments={},
        tool_results={},
        validation_results={
            "status": "validated",
            "passed": True,
        },
        artifacts=[],
        warnings=[],
        final_status="validated_success",
        human_corrections=[],
        timestamps=TraceTimestamps(
            started_at=now,
            finished_at=now,
        ),
        versions={
            "python": "test",
        },
    )

    payload = trace.model_dump(mode="json")

    assert payload["plan_sha256"] == "a" * 64
    assert payload["approved_step_ids"] == [
        "step_2",
        "step_4",
    ]

    report = render_report(trace)

    assert "Approval evidence" in report
    assert "approval-20260809t200000z-1234abcd" in (
        report
    )
    assert "step_2" in report
    assert "step_4" in report