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
    assess_recipe_release_candidate,
    authoritative_release_candidate_sha256,
)
from geoagent_harness.critic.recipe_trace import (
    build_recipe_trace_candidate,
    persist_recipe_trace_candidate,
    recipe_trace_sha256,
)
from geoagent_harness.recipes import (
    RecipeRunEvidence,
    WorkflowRecipe,
    create_recipe_approval,
    recipe_evidence_sha256,
    recipe_sha256,
    save_recipe,
    write_recipe_evidence,
    write_recipe_run_result,
)
from geoagent_harness.skill_registry import load_skill_registry
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


def test_recipe_release_assessment_binds_complete_exact_run(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).parents[1]
    registry = load_skill_registry(project_root)
    recipe = WorkflowRecipe.model_validate({
        "recipe_id": "release_recipe",
        "original_request": "Convert the reviewed vector.",
        "summary": "Convert vector", "status": "planned",
        "execution_performed": False, "validation_performed": False,
        "steps": [{"step_id": "step_1", "skill_id": "convert_vector",
                   "arguments": {"path": "data/input/sample_points.geojson",
                                 "target_path": "data/output/release.gpkg",
                                 "target_format": "geopackage"},
                   "depends_on": [], "output_ids": ["converted_vector"]}],
    })
    recipe_root = tmp_path / "workflow-recipes"
    recipe, recipe_file = save_recipe(recipe, recipe_root=recipe_root)
    approval_root = tmp_path / "approvals"
    approval, approval_file = create_recipe_approval(
        recipe=recipe, registry=registry, step_ids=["step_1"],
        decision="approved", approver="operator", reason="Exact scope reviewed.",
        approval_root=approval_root, now=NOW,
    )
    digest = recipe_sha256(recipe)
    run_result = {
        "recipe_id": recipe.recipe_id, "recipe_sha256": digest,
        "approval_id": approval.approval_id, "final_status": "validated_success",
        "step_results": [{"step_id": "step_1", "skill_id": "convert_vector",
            "status": "validated_success", "execution": {"step_id": "step_1",
                "skill_id": "convert_vector", "status": "completed",
                "output_ids": ["converted_vector"], "result": {"path": "data/output/release.gpkg"},
                "execution_performed": True, "validation_performed": False},
            "validation_result": {"passed": True, "checks": []},
            "execution_performed": True, "validation_performed": True}],
        "failed_step_id": None, "warnings": [], "execution_performed": True,
        "validation_performed": True,
    }
    evidence = RecipeRunEvidence.model_validate({
        "recipe_id": recipe.recipe_id, "recipe_sha256": digest,
        "approval_id": approval.approval_id, "final_status": "validated_success",
        "run_result": run_result,
        "artifacts": [{"artifact_id": "converted_vector", "role": "output",
            "path": "data/output/release.gpkg", "sha256": "b" * 64,
            "size_bytes": 10, "media_type": "application/geopackage+sqlite3",
            "producer_step_id": "step_1"}],
        "lineage": [], "skill_versions": {"convert_vector": "1.0"},
        "warnings": [], "recorded_at": NOW, "secrets_redacted": True,
    })
    evidence_root, result_root = tmp_path / "recipe-evidence", tmp_path / "recipe-runs"
    evidence_file = write_recipe_evidence(evidence, evidence_root=evidence_root)
    result_file = write_recipe_run_result(evidence.run_result, result_root=result_root)
    trace = build_recipe_trace_candidate(
        recipe=recipe, approval=approval, evidence=evidence,
        evidence_sha256=recipe_evidence_sha256(evidence),
        progress={"recipe_id": recipe.recipe_id, "recipe_sha256": digest,
                  "status": "validated_success", "started_at": NOW.isoformat(),
                  "finished_at": NOW.isoformat()},
        context_references=[],
    )
    trace_root, report_root = tmp_path / "traces", tmp_path / "reports"
    trace_file, report_file, _, _ = persist_recipe_trace_candidate(
        trace=trace, confirmed_trace_sha256=recipe_trace_sha256(trace),
        trace_root=trace_root, report_root=report_root,
    )
    critic_evidence = build_critic_evidence(
        trace_path=trace_file, report_path=report_file,
        trace_root=trace_root, report_root=report_root,
    )
    result = CriticResult(
        model="qwen-test", task_id=trace.task_id,
        deterministic_status=critic_evidence.deterministic_status,
        evidence_references=critic_evidence.evidence_references,
        evidence_gaps=critic_evidence.evidence_gaps,
        workflow_warnings=critic_evidence.warnings,
        human_corrections=critic_evidence.human_corrections,
        assessment=CriticAssessment(
            deterministic_status="validated_success", conclusion="supported",
            success_claimed=True, summary="Exact evidence supports release.",
        ),
    )
    critic_root = tmp_path / "critic-results"
    stored = persist_critic_result_record(
        build_critic_result_record(result=result, recorded_at=NOW),
        record_root=critic_root,
    )
    history_root = tmp_path / "operational-history"
    identity = OperationalIdentity(
        agent_id=AgentRole.GIS, agent_instance_id="gis-release-recipe",
        agent_run_id="gis-release-recipe-run", task_id=trace.task_id,
        correlation_id="recipe-release-test",
    )
    record_gis_workflow_history(
        trace_path=trace_file, report_path=report_file,
        trace_root=trace_root, report_root=report_root,
        event_root=history_root, identity=identity,
    )
    candidate = assess_recipe_release_candidate(
        release_id="recipe-release-1", recipe_file=recipe_file,
        approval_file=approval_file, run_result_file=result_file,
        recipe_evidence_file=evidence_file, trace_file=trace_file,
        report_file=report_file, critic_record_file=Path(stored.record_file),
        history_file=history_root / "recipe-release-test.events.jsonl",
        recipe_root=recipe_root, approval_root=approval_root,
        run_result_root=result_root, recipe_evidence_root=evidence_root,
        trace_root=trace_root, report_root=report_root, critic_root=critic_root,
        history_root=history_root, project_root=tmp_path, registry=registry,
        assessed_at=NOW,
    )
    assert candidate.ready_for_release is True
    assert candidate.subject_type.value == "recipe"
    assert candidate.violations == []
    assert {component.kind.value for component in candidate.components} >= {
        "recipe", "approval", "run_result", "recipe_evidence", "trace",
        "report", "critic_result", "operational_history",
    }
