"""Tests for read-only authoritative workflow assessment."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.critic import (
    CriticAssessment,
    CriticResult,
    build_critic_evidence,
    build_critic_result_record,
    persist_critic_result_record,
)
from geoagent_harness.operational_history import (
    AgentRole,
    OperationalIdentity,
    record_gis_workflow_history,
)
from geoagent_harness.releases import (
    ReleaseAssessmentError,
    ReleaseLifecycleState,
    assess_workflow_release_candidate,
    authoritative_release_candidate_sha256,
)
from tests.test_critic_evidence import make_trace, write_evidence


NOW = datetime(2026, 9, 3, 6, tzinfo=timezone.utc)


def prepared_incomplete_candidate(tmp_path: Path):
    trace = make_trace(approval=False)
    trace_path, report_path, trace_root, report_root = (
        write_evidence(tmp_path, trace)
    )
    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )
    critic_result = CriticResult(
        model="qwen-test",
        task_id=evidence.task_id,
        deterministic_status=evidence.deterministic_status,
        evidence_references=evidence.evidence_references,
        evidence_gaps=evidence.evidence_gaps,
        workflow_warnings=evidence.warnings,
        human_corrections=evidence.human_corrections,
        assessment=CriticAssessment(
            deterministic_status="incomplete_evidence",
            conclusion="incomplete",
            success_claimed=False,
            summary="Approval evidence is incomplete.",
        ),
    )
    critic_root = tmp_path / "critic-results"
    critic_record = build_critic_result_record(
        result=critic_result,
        recorded_at=NOW,
    )
    stored = persist_critic_result_record(
        critic_record,
        record_root=critic_root,
    )

    history_root = tmp_path / "operational-history"
    identity = OperationalIdentity(
        agent_id=AgentRole.GIS,
        agent_instance_id="gis-instance-release-test",
        agent_run_id="gis-run-release-test",
        task_id=evidence.task_id,
        correlation_id="release-assessment-test",
    )
    record_gis_workflow_history(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
        event_root=history_root,
        identity=identity,
    )

    return {
        "trace_file": trace_path,
        "report_file": report_path,
        "critic_record_file": Path(stored.record_file),
        "history_file": (
            history_root / "release-assessment-test.events.jsonl"
        ),
        "trace_root": trace_root,
        "report_root": report_root,
        "critic_root": critic_root,
        "history_root": history_root,
        "project_root": tmp_path,
    }


def assess(prepared: dict[str, Path]):
    return assess_workflow_release_candidate(
        release_id="release-assessment-1",
        assessed_at=NOW,
        **prepared,
    )


def test_incomplete_evidence_is_not_release_ready(
    tmp_path: Path,
) -> None:
    candidate = assess(prepared_incomplete_candidate(tmp_path))

    assert candidate.deterministic_status == "incomplete_evidence"
    assert candidate.lifecycle_state == ReleaseLifecycleState.CANDIDATE
    assert candidate.approval_complete is False
    assert candidate.validation_complete is True
    assert candidate.critic_complete is True
    assert candidate.evidence_complete is False
    assert candidate.ready_for_release is False
    assert candidate.release_created is False
    assert any(
        "approval" in violation.lower()
        for violation in candidate.violations
    )
    assert {item.kind.value for item in candidate.components} == {
        "trace",
        "report",
        "critic_result",
        "operational_history",
    }


def test_candidate_digest_is_deterministic(
    tmp_path: Path,
) -> None:
    candidate = assess(prepared_incomplete_candidate(tmp_path))
    assert authoritative_release_candidate_sha256(candidate) == (
        authoritative_release_candidate_sha256(candidate)
    )


def test_rejects_symlinked_release_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_incomplete_candidate(tmp_path)
    linked = tmp_path / "linked-trace.json"
    linked.symlink_to(prepared["trace_file"])
    prepared["trace_file"] = linked

    with pytest.raises(ReleaseAssessmentError):
        assess(prepared)


def test_rejects_critic_record_from_another_task(
    tmp_path: Path,
) -> None:
    prepared = prepared_incomplete_candidate(tmp_path)
    record_path = prepared["critic_record_file"]
    payload = record_path.read_text(encoding="utf-8")
    record_path.write_text(
        payload.replace(
            "critic-evidence-test",
            "different-task",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ReleaseAssessmentError,
        match="could not be verified",
    ):
        assess(prepared)
