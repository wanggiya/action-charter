"""Tests for authoritative release lifecycle schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from geoagent_harness.releases import (
    AuthoritativeReleaseCandidate,
    AuthoritativeReleaseManifest,
    ReleaseLifecycleState,
)


NOW = datetime(2026, 9, 3, 5, tzinfo=timezone.utc)


def components():
    return [
        {
            "component_id": "approval",
            "kind": "approval",
            "path": "approvals/approval.json",
            "sha256": "a" * 64,
            "size_bytes": 100,
        },
        {
            "component_id": "plan",
            "kind": "plan",
            "path": "plans/workflow.json",
            "sha256": "b" * 64,
            "size_bytes": 200,
        },
        {
            "component_id": "critic_result",
            "kind": "critic_result",
            "path": "critic/CRITIC_RESULT.json",
            "sha256": "c" * 64,
            "size_bytes": 300,
        },
        {
            "component_id": "report",
            "kind": "report",
            "path": "reports/workflow.md",
            "sha256": "d" * 64,
            "size_bytes": 600,
        },
        {
            "component_id": "trace",
            "kind": "trace",
            "path": "traces/workflow.json",
            "sha256": "e" * 64,
            "size_bytes": 700,
        },
        {
            "component_id": "operational_history",
            "kind": "operational_history",
            "path": "operational-history/workflow.events.jsonl",
            "sha256": "f" * 64,
            "size_bytes": 800,
        },
    ]


def candidate_payload():
    return {
        "release_id": "release-test-1",
        "subject_type": "workflow",
        "subject_id": "workflow-test-1",
        "deterministic_status": "validated_success",
        "lifecycle_state": "validated",
        "components": components(),
        "approval_complete": True,
        "validation_complete": True,
        "critic_complete": True,
        "evidence_complete": True,
        "ready_for_release": True,
        "violations": [],
        "assessed_at": NOW,
    }


def test_validated_candidate_requires_complete_evidence() -> None:
    candidate = AuthoritativeReleaseCandidate.model_validate(
        candidate_payload()
    )
    assert candidate.lifecycle_state == ReleaseLifecycleState.VALIDATED
    assert candidate.ready_for_release is True
    assert candidate.release_created is False


def test_incomplete_evidence_cannot_be_release_ready() -> None:
    payload = candidate_payload()
    payload.update(
        deterministic_status="incomplete_evidence",
        lifecycle_state="candidate",
        approval_complete=False,
        evidence_complete=False,
        ready_for_release=False,
        violations=["approval evidence is incomplete"],
    )
    candidate = AuthoritativeReleaseCandidate.model_validate(payload)
    assert candidate.lifecycle_state == ReleaseLifecycleState.CANDIDATE
    assert candidate.ready_for_release is False


def test_rejects_false_release_readiness() -> None:
    payload = candidate_payload()
    payload["approval_complete"] = False

    with pytest.raises(
        ValidationError,
        match="evidence-complete claim",
    ):
        AuthoritativeReleaseCandidate.model_validate(payload)


def test_failed_run_uses_rejected_lifecycle() -> None:
    payload = candidate_payload()
    payload.update(
        deterministic_status="validation_failed",
        lifecycle_state="rejected",
        ready_for_release=False,
        violations=["deterministic validation failed"],
    )
    candidate = AuthoritativeReleaseCandidate.model_validate(payload)
    assert candidate.lifecycle_state == ReleaseLifecycleState.REJECTED


def test_rejects_duplicate_component_paths() -> None:
    payload = candidate_payload()
    payload["components"][1]["path"] = (
        payload["components"][0]["path"]
    )

    with pytest.raises(
        ValidationError,
        match="paths must be unique",
    ):
        AuthoritativeReleaseCandidate.model_validate(payload)


def test_missing_required_component_prevents_readiness() -> None:
    payload = candidate_payload()
    payload["components"] = [
        item
        for item in payload["components"]
        if item["kind"] != "operational_history"
    ]

    payload.update(
        lifecycle_state="candidate",
        evidence_complete=False,
        ready_for_release=False,
        violations=["operational history is missing"],
    )
    candidate = AuthoritativeReleaseCandidate.model_validate(payload)
    assert candidate.ready_for_release is False


def test_rejects_unsafe_component_path() -> None:
    payload = candidate_payload()
    payload["components"][0]["path"] = "../approval.json"

    with pytest.raises(
        ValidationError,
        match="normalized and relative",
    ):
        AuthoritativeReleaseCandidate.model_validate(payload)


def test_release_manifest_is_explicitly_released() -> None:
    manifest = AuthoritativeReleaseManifest(
        release_id="release-test-1",
        subject_type="workflow",
        subject_id="workflow-test-1",
        candidate_sha256="3" * 64,
        components=components(),
        released_at=NOW,
    )
    assert manifest.lifecycle_state == ReleaseLifecycleState.RELEASED
    assert manifest.release_created is True
    assert manifest.execution_performed is False
