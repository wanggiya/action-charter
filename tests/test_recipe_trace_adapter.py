"""Tests for truthful, non-writing recipe-run trace adaptation."""

from datetime import datetime, timezone

import pytest

from geoagent_harness.critic.recipe_trace import (
    RecipeTraceAdapterError,
    build_recipe_trace_candidate,
    render_recipe_trace_report,
)
from geoagent_harness.recipes import RecipeApprovalRecord, RecipeRunEvidence, WorkflowRecipe


NOW = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)


def sources():
    recipe = WorkflowRecipe.model_validate({
        "recipe_id": "adapter_test", "original_request": "Inspect the governed vector.",
        "summary": "Inspect", "status": "planned", "execution_performed": False,
        "validation_performed": False, "steps": [{"step_id": "step_1", "skill_id": "inspect_vector", "arguments": {"path": "data/input/sample_points.geojson"}, "depends_on": [], "output_ids": ["metadata"]}],
    })
    approval = RecipeApprovalRecord.model_validate({
        "approval_id": "recipe-approval-20260922t120000z-1234abcd", "recipe_sha256": "a" * 64,
        "decision": "approved", "step_ids": ["step_1"], "approver": "operator",
        "reason": "Reviewed exact scope.", "human_corrections": [], "created_at": NOW,
        "expires_at": None, "secrets_redacted": True,
    })
    evidence = RecipeRunEvidence.model_validate({
        "recipe_id": "adapter_test", "recipe_sha256": "a" * 64,
        "approval_id": "recipe-approval-20260922t120000z-1234abcd", "final_status": "validated_success",
        "run_result": {"recipe_id": "adapter_test", "recipe_sha256": "a" * 64,
            "approval_id": "recipe-approval-20260922t120000z-1234abcd", "final_status": "validated_success",
            "step_results": [{"step_id": "step_1", "skill_id": "inspect_vector", "status": "completed",
                "execution": {"step_id": "step_1", "skill_id": "inspect_vector", "status": "completed", "output_ids": ["metadata"], "result": {"driver": "GeoJSON"}, "execution_performed": True, "validation_performed": False},
                "validation_result": None, "execution_performed": True, "validation_performed": False}],
            "failed_step_id": None, "warnings": [], "execution_performed": True, "validation_performed": False},
        "artifacts": [{"artifact_id": "input", "role": "input", "path": "data/input/sample_points.geojson", "sha256": "b" * 64, "size_bytes": 10, "media_type": "application/geo+json", "producer_step_id": None}],
        "lineage": [], "skill_versions": {"inspect_vector": "0.1.0"}, "warnings": [],
        "recorded_at": NOW, "secrets_redacted": True,
    })
    progress = {"recipe_id": "adapter_test", "recipe_sha256": "a" * 64,
        "status": "validated_success", "started_at": "2026-09-22T11:59:59+00:00",
        "finished_at": "2026-09-22T12:00:00+00:00"}
    return recipe, approval, evidence, progress


def test_recipe_trace_candidate_preserves_recipe_authority_without_fake_plan() -> None:
    recipe, approval, evidence, progress = sources()
    trace = build_recipe_trace_candidate(recipe=recipe, approval=approval, evidence=evidence,
        evidence_sha256="c" * 64, progress=progress, context_references=["recipe-evidence/test.json"])
    assert trace.plan_sha256 is None
    assert trace.recipe_sha256 == "a" * 64
    assert trace.validation_results["validation_kind"] == "recipe"
    assert trace.timestamps.started_at < trace.timestamps.finished_at
    report = render_recipe_trace_report(trace)
    assert trace.task_id in report
    assert trace.approval_id in report
    assert "No model was called" in report


def test_recipe_trace_candidate_rejects_missing_durable_identity() -> None:
    recipe, approval, evidence, progress = sources()
    progress.pop("recipe_id")
    with pytest.raises(RecipeTraceAdapterError, match="recipe identity"):
        build_recipe_trace_candidate(recipe=recipe, approval=approval, evidence=evidence,
            evidence_sha256="c" * 64, progress=progress, context_references=[])
