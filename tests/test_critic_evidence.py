"""Tests for deterministic Critic Agent evidence packs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.critic.evidence import (
    CriticEvidenceError,
    build_critic_evidence,
)
from geoagent_harness.reporting import render_report
from geoagent_harness.trace import (
    TraceTimestamps,
    WorkflowTrace,
)


def make_trace(
    *,
    final_status: str = "validated_success",
    validation_passed: bool = True,
    approval: bool = True,
) -> WorkflowTrace:
    now = datetime.now(timezone.utc)

    return WorkflowTrace(
        task_id="critic-evidence-test",
        original_request=(
            "Load and validate the approved sample dataset."
        ),
        context_references=[
            "context/PROJECT_SUMMARY.md",
        ],
        selected_skills=[
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
            "generate_report",
        ],
        tool_arguments={},
        tool_results={},
        validation_results={
            "passed": validation_passed,
            "table_exists": True,
            "geometry_column_exists": True,
            "row_count": 2,
            "srid": 4326,
            "geometry_type": "POINT",
            "invalid_geometry_count": 0,
            "null_geometry_count": 0,
            "extent": {
                "min_x": -77.1,
                "min_y": 38.8,
                "max_x": -77.0,
                "max_y": 38.9,
            },
            "checks": [
                {
                    "name": "row_count",
                    "passed": validation_passed,
                    "expected": 2,
                    "actual": 2,
                }
            ],
            "warnings": [],
        },
        artifacts=[
            "reports/critic-evidence-test.md",
            "traces/critic-evidence-test.json",
        ],
        warnings=[],
        final_status=final_status,
        human_corrections=[],
        timestamps=TraceTimestamps(
            started_at=now,
            finished_at=now,
        ),
        versions={
            "python": "3.12",
        },
        secrets_redacted=True,
        plan_sha256=(
            "a" * 64
            if approval
            else None
        ),
        approval_id=(
            "approval-test"
            if approval
            else None
        ),
        approved_step_ids=(
            ["step_2", "step_4"]
            if approval
            else []
        ),
    )


def write_evidence(
    tmp_path: Path,
    trace: WorkflowTrace,
) -> tuple[Path, Path, Path, Path]:
    trace_root = tmp_path / "traces"
    report_root = tmp_path / "reports"

    trace_root.mkdir()
    report_root.mkdir()

    trace_path = trace_root / f"{trace.task_id}.json"
    report_path = report_root / f"{trace.task_id}.md"

    trace_path.write_text(
        trace.model_dump_json(indent=2),
        encoding="utf-8",
    )
    report_path.write_text(
        render_report(trace),
        encoding="utf-8",
    )

    return (
        trace_path,
        report_path,
        trace_root,
        report_root,
    )


def test_builds_validated_success_evidence(
    tmp_path: Path,
) -> None:
    trace = make_trace()

    (
        trace_path,
        report_path,
        trace_root,
        report_root,
    ) = write_evidence(tmp_path, trace)

    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )

    assert evidence.task_id == trace.task_id
    assert (
        evidence.deterministic_status
        == "validated_success"
    )
    assert evidence.validation.passed is True
    assert evidence.validation.row_count == 2
    assert evidence.validation.srid == 4326
    assert evidence.approval.complete is True
    assert evidence.evidence_gaps == []
    assert len(evidence.evidence_references) == 2


def test_missing_approval_makes_evidence_incomplete(
    tmp_path: Path,
) -> None:
    trace = make_trace(approval=False)

    (
        trace_path,
        report_path,
        trace_root,
        report_root,
    ) = write_evidence(tmp_path, trace)

    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )

    assert (
        evidence.deterministic_status
        == "incomplete_evidence"
    )
    assert evidence.approval.complete is False
    assert any(
        "approval" in gap
        for gap in evidence.evidence_gaps
    )


def test_rejects_success_with_failed_validation(
    tmp_path: Path,
) -> None:
    trace = make_trace(
        final_status="validated_success",
        validation_passed=False,
    )

    (
        trace_path,
        report_path,
        trace_root,
        report_root,
    ) = write_evidence(tmp_path, trace)

    with pytest.raises(
        CriticEvidenceError,
        match="without passing validation",
    ):
        build_critic_evidence(
            trace_path=trace_path,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
        )


def test_rejects_trace_outside_approved_root(
    tmp_path: Path,
) -> None:
    trace = make_trace()

    (
        _,
        report_path,
        trace_root,
        report_root,
    ) = write_evidence(tmp_path, trace)

    outside = tmp_path / "outside.json"
    outside.write_text(
        trace.model_dump_json(),
        encoding="utf-8",
    )

    with pytest.raises(
        CriticEvidenceError,
        match="outside approved traces root",
    ):
        build_critic_evidence(
            trace_path=outside,
            report_path=report_path,
            trace_root=trace_root,
            report_root=report_root,
        )


def test_report_mismatch_becomes_evidence_gap(
    tmp_path: Path,
) -> None:
    trace = make_trace()

    (
        trace_path,
        report_path,
        trace_root,
        report_root,
    ) = write_evidence(tmp_path, trace)

    report_path.write_text(
        "# Unrelated report\n",
        encoding="utf-8",
    )

    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )

    assert (
        evidence.deterministic_status
        == "incomplete_evidence"
    )
    assert evidence.evidence_gaps


def test_report_excerpt_is_secret_redacted(
    tmp_path: Path,
) -> None:
    trace = make_trace()

    (
        trace_path,
        report_path,
        trace_root,
        report_root,
    ) = write_evidence(tmp_path, trace)

    with report_path.open("a", encoding="utf-8") as stream:
        stream.write(
            "\nPOSTGRES_PASSWORD=do-not-expose\n"
        )

    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )

    assert "do-not-expose" not in evidence.report_excerpt
    assert "[REDACTED]" in evidence.report_excerpt