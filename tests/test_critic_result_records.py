"""Tests for deterministic Critic-result records."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from geoagent_harness.critic import (
    CriticAssessment,
    CriticResult,
    CriticResultRecord,
    CriticResultRecordError,
    EvidenceReference,
    build_critic_result_record,
    critic_result_sha256,
)


NOW = datetime(2026, 9, 3, 4, tzinfo=timezone.utc)


def critic_result(
    *,
    status: str = "validated_success",
) -> CriticResult:
    conclusion = {
        "validated_success": "supported",
        "validation_failed": "not_supported",
        "execution_failed": "not_supported",
        "incomplete_evidence": "incomplete",
    }[status]
    return CriticResult(
        model="qwen-test",
        task_id="critic-record-test",
        deterministic_status=status,
        evidence_references=[
            EvidenceReference(
                path="traces/critic-record-test.json",
                sha256="a" * 64,
            ),
            EvidenceReference(
                path="reports/critic-record-test.md",
                sha256="b" * 64,
            ),
        ],
        evidence_gaps=(
            ["approval evidence is incomplete"]
            if status == "incomplete_evidence"
            else []
        ),
        workflow_warnings=[],
        human_corrections=[],
        assessment=CriticAssessment(
            deterministic_status=status,
            conclusion=conclusion,
            success_claimed=(status == "validated_success"),
            summary="Assessment follows deterministic evidence.",
        ),
    )


def test_builds_digest_bound_separate_critic_record() -> None:
    result = critic_result()
    record = build_critic_result_record(
        result=result,
        recorded_at=NOW,
    )

    assert record.task_id == result.task_id
    assert record.critic_result_sha256 == critic_result_sha256(result)
    assert record.deterministic_status == "validated_success"
    assert record.critic_result_recorded is True
    assert record.authoritative_status_changed is False
    assert record.release_created is False
    assert record.execution_performed is False


def test_rejects_naive_record_timestamp() -> None:
    with pytest.raises(
        CriticResultRecordError,
        match="could not be constructed",
    ):
        build_critic_result_record(
            result=critic_result(),
            recorded_at=datetime(2026, 9, 3, 4),
        )


def test_schema_rejects_changed_authoritative_status() -> None:
    record = build_critic_result_record(
        result=critic_result(),
        recorded_at=NOW,
    )
    payload = record.model_dump(mode="json")
    payload["deterministic_status"] = "validation_failed"

    with pytest.raises(
        ValidationError,
        match="statuses do not match",
    ):
        CriticResultRecord.model_validate(payload)


def test_schema_rejects_false_success_claim() -> None:
    result = critic_result(status="validation_failed")
    payload = {
        "task_id": result.task_id,
        "deterministic_status": result.deterministic_status,
        "critic_result_sha256": critic_result_sha256(result),
        "critic_result": result.model_dump(mode="json"),
        "recorded_at": NOW.isoformat(),
    }
    payload["critic_result"]["assessment"][
        "success_claimed"
    ] = True

    with pytest.raises(
        ValidationError,
        match="conclusion conflicts",
    ):
        CriticResultRecord.model_validate(payload)
