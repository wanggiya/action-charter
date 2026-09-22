"""Tests for the loopback-only non-mutating interface API."""

from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import geoagent_harness.interface_api.server as interface_api_module

from geoagent_harness.interface_api import (
    InterfaceApiError,
    record_interface_recipe_approval,
    verify_interface_recipe_approval,
    compile_interface_recipe_proposal,
    interface_recipe_template_catalog,
    interface_data_resource_inventory,
    interface_execution_inventory,
    interface_critic_evidence_inventory,
    run_interface_critic,
    save_interface_recipe_trace,
    interface_planner_skill_catalog,
    interface_saved_plan_inventory,
    plan_interface_task,
    save_interface_reviewed_plan,
    prepare_interface_plan_approval,
    record_interface_plan_approval,
    verify_interface_plan_approval,
    compile_interface_plan_recipe,
    save_interface_plan_recipe,
    interface_saved_recipe_inventory,
    prepare_interface_recipe_approval,
    prepare_interface_execution_preview,
    execute_interface_recipe,
    save_interface_reviewed_recipe,
    serve_interface_api,
)
from geoagent_harness.interface_api.server import _handler
from geoagent_harness.interface_api.server import InterfaceApprovalDecision
from geoagent_harness.interface_api.server import InterfaceApprovalVerificationRequest
from geoagent_harness.interface_api.server import InterfaceExecutionPreviewRequest
from geoagent_harness.interface_api.server import InterfaceRecipeExecutionRequest
from geoagent_harness.interface_api.server import InterfacePlanRequest
from geoagent_harness.interface_api.server import InterfaceReviewedPlanSaveRequest
from geoagent_harness.interface_api.server import InterfacePlanApprovalPreparationRequest
from geoagent_harness.interface_api.server import InterfacePlanApprovalDecisionRequest
from geoagent_harness.interface_api.server import InterfacePlanApprovalVerificationRequest
from geoagent_harness.interface_api.server import InterfacePlanRecipeCompilationRequest
from geoagent_harness.interface_api.server import InterfacePlanRecipeSaveRequest
from geoagent_harness.interface_api.server import InterfaceRecipeTraceSaveRequest
from geoagent_harness.interface_api.server import InterfaceCriticRunRequest
from geoagent_harness.approvals import load_planner_result, plan_sha256
from geoagent_harness.planner import PlannerResult
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.recipe_proposals import RecipeCompilationError
from geoagent_harness.reporting import render_report
from geoagent_harness.trace import TraceTimestamps, WorkflowTrace
from geoagent_harness.critic.recipe_trace import recipe_trace_sha256


PROJECT_ROOT = Path(__file__).parents[1]
PROPOSAL_FILE = (
    PROJECT_ROOT
    / "examples"
    / "interface-parity"
    / "checkpoint17l-vector-conversion-proposal.json"
)


def write_critic_fixture(project_root: Path) -> WorkflowTrace:
    """Create complete Critic evidence without relying on ignored run data."""

    now = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    trace = WorkflowTrace(
        task_id="interface-critic-fixture",
        original_request="Inspect the approved vector and validate the result.",
        context_references=["context/PROJECT_SUMMARY.md"],
        selected_skills=["inspect_vector"],
        plan_sha256="a" * 64,
        approval_id="approval-interface-critic-fixture",
        approved_step_ids=["step_1"],
        tool_arguments={},
        tool_results={},
        validation_results={
            "passed": True,
            "table_exists": True,
            "geometry_column_exists": True,
            "row_count": 2,
            "srid": 4326,
            "geometry_type": "POINT",
            "invalid_geometry_count": 0,
            "null_geometry_count": 0,
            "checks": [],
        },
        artifacts=[
            "traces/interface-critic-fixture.json",
            "reports/interface-critic-fixture.md",
        ],
        warnings=[],
        final_status="validated_success",
        timestamps=TraceTimestamps(started_at=now, finished_at=now),
        versions={"python": "3.12"},
        secrets_redacted=True,
    )
    trace_root = project_root / "traces"
    report_root = project_root / "reports"
    trace_root.mkdir(parents=True)
    report_root.mkdir(parents=True)
    (trace_root / f"{trace.task_id}.json").write_text(
        trace.model_dump_json(indent=2) + "\n", encoding="utf-8",
    )
    (report_root / f"{trace.task_id}.md").write_text(
        render_report(trace), encoding="utf-8",
    )
    return trace


def proposal_payload() -> dict[str, object]:
    return json.loads(PROPOSAL_FILE.read_text(encoding="utf-8"))


def test_critic_evidence_inventory_is_read_only_and_model_free(tmp_path: Path) -> None:
    trace = write_critic_fixture(tmp_path)
    result = interface_critic_evidence_inventory(tmp_path)

    assert result["status"] == "inspected"
    assert result["item_count"] >= 1
    assert result["critic_model_called"] is False
    assert result["critic_result_recorded"] is False
    assert result["release_created"] is False
    assert result["execution_performed"] is False
    assert result["recipe_candidate_count"] == 0
    item = result["items"][0]
    assert item["available"] is True
    assert item["evidence"]["task_id"] == trace.task_id
    assert len(item["evidence"]["evidence_references"]) == 2


def test_critic_evidence_inventory_reports_missing_matching_report(tmp_path: Path) -> None:
    (tmp_path / "traces").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "traces" / "unpaired.json").write_text("{}", encoding="utf-8")

    result = interface_critic_evidence_inventory(tmp_path)

    assert result["item_count"] == 1
    assert result["items"][0] == {
        "trace_name": "unpaired.json",
        "report_name": None,
        "available": False,
        "finding": "matching Markdown report is unavailable",
        "evidence": None,
    }


def test_reviewed_recipe_trace_is_stored_immutably_without_critic_or_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = write_critic_fixture(tmp_path)
    evidence_name = f"fixture.{('b' * 64)}.json"
    preview = {
        "evidence_name": evidence_name,
        "adaptable": True,
        "finding": None,
        "trace": trace.model_dump(mode="json"),
        "trace_sha256": recipe_trace_sha256(trace),
        "critic_status": "validated_success",
        "critic_gaps": [],
        "stored": False,
        "files_modified": False,
    }
    monkeypatch.setattr(
        interface_api_module,
        "_interface_recipe_trace_candidates",
        lambda _root: [preview],
    )
    (tmp_path / "traces" / f"{trace.task_id}.json").unlink()
    (tmp_path / "reports" / f"{trace.task_id}.md").unlink()
    result = save_interface_recipe_trace(
        InterfaceRecipeTraceSaveRequest(action="save_adapted_recipe_trace", evidence_name=evidence_name, confirmed_trace_sha256=preview["trace_sha256"]),
        project_root=tmp_path,
    )
    assert result["status"] == "stored"
    assert (tmp_path / result["trace_path"]).is_file()
    assert (tmp_path / result["report_path"]).is_file()
    assert result["critic_model_called"] is False
    assert result["critic_result_recorded"] is False
    assert result["release_created"] is False
    assert result["execution_performed"] is False
    with pytest.raises(InterfaceApiError, match="already exists"):
        save_interface_recipe_trace(
            InterfaceRecipeTraceSaveRequest(action="save_adapted_recipe_trace", evidence_name=evidence_name, confirmed_trace_sha256=preview["trace_sha256"]),
            project_root=tmp_path,
        )


def test_interface_critic_assesses_exact_evidence_without_recording(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_critic_fixture(tmp_path)
    inventory = interface_critic_evidence_inventory(tmp_path)
    item = next(candidate for candidate in inventory["items"] if candidate["available"])
    references = {
        Path(reference["path"]).name: reference["sha256"]
        for reference in item["evidence"]["evidence_references"]
    }
    captured: dict[str, object] = {}
    result_payload = {
        "agent_id": "critic",
        "model": "critic-test",
        "task_id": item["evidence"]["task_id"],
        "deterministic_status": item["evidence"]["deterministic_status"],
        "evidence_references": item["evidence"]["evidence_references"],
        "evidence_gaps": item["evidence"]["evidence_gaps"],
        "workflow_warnings": [],
        "human_corrections": [],
        "assessment": {
            "schema_version": "1.0",
            "deterministic_status": item["evidence"]["deterministic_status"],
            "conclusion": "supported",
            "success_claimed": True,
            "summary": "The deterministic evidence supports the recorded outcome.",
            "validation_basis": ["Independent validation passed."],
            "additional_risks": [],
            "recommendations": [],
            "edits_performed": False,
            "database_actions_performed": False,
        },
    }

    def fake_critique_task(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(model_dump=lambda **_kwargs: result_payload)

    monkeypatch.setattr(interface_api_module, "critique_task", fake_critique_task)
    monkeypatch.setattr(interface_api_module, "critic_result_sha256", lambda _result: "a" * 64)
    result = run_interface_critic(
        InterfaceCriticRunRequest(
            action="run_critic",
            trace_name=item["trace_name"],
            report_name=item["report_name"],
            confirmed_trace_sha256=references[item["trace_name"]],
            confirmed_report_sha256=references[item["report_name"]],
        ),
        project_root=tmp_path,
    )

    assert captured["trace_path"] == tmp_path / "traces" / item["trace_name"]
    assert result["status"] == "assessed_not_recorded"
    assert result["critic_result_sha256"] == "a" * 64
    assert result["critic_model_called"] is True
    assert result["critic_result_recorded"] is False
    assert result["release_created"] is False
    assert result["execution_performed"] is False


def test_interface_critic_rejects_stale_digest_before_model_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_critic_fixture(tmp_path)
    inventory = interface_critic_evidence_inventory(tmp_path)
    item = next(candidate for candidate in inventory["items"] if candidate["available"])
    references = {
        Path(reference["path"]).name: reference["sha256"]
        for reference in item["evidence"]["evidence_references"]
    }
    called = False

    def fake_critique_task(**_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(interface_api_module, "critique_task", fake_critique_task)
    with pytest.raises(InterfaceApiError, match="trace digest no longer matches"):
        run_interface_critic(
            InterfaceCriticRunRequest(
                action="run_critic",
                trace_name=item["trace_name"],
                report_name=item["report_name"],
                confirmed_trace_sha256="0" * 64,
                confirmed_report_sha256=references[item["report_name"]],
            ),
            project_root=tmp_path,
        )
    assert called is False


def test_interface_planner_uses_existing_service_without_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import geoagent_harness.planner as planner_module

    request_text = "Inspect sample_points and propose a validated workflow."
    plan_payload = {
        "schema_version": "1.0",
        "status": "planned",
        "summary": "Inspect the approved input.",
        "steps": [{
            "step_id": "step_1",
            "skill": "inspect_vector",
            "purpose": "Inspect metadata.",
            "arguments": {"path": "data/input/sample_points.geojson"},
            "requires_approval": False,
            "expected_artifacts": [],
            "validation_required": False,
        }],
        "assumptions": [],
        "risks": [],
        "execution_performed": False,
        "validation_performed": False,
    }
    captured: dict[str, object] = {}

    def fake_plan_task(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            agent_id="planner",
            model="qwen-test",
            original_request=request_text,
            context_references=["context/PROJECT_SUMMARY.md"],
            plan=SimpleNamespace(model_dump=lambda **_kwargs: plan_payload),
            warnings=[],
        )

    monkeypatch.setattr(planner_module, "plan_task", fake_plan_task)
    result = plan_interface_task(
        InterfacePlanRequest(
            action="plan_task",
            request=request_text,
            allowed_skill_ids=["inspect_vector"],
            input_paths=["data/input/sample_points.geojson"],
        ),
        project_root=PROJECT_ROOT,
    )

    assert captured["original_request"] == (
        request_text
        + "\n\nOperator-selected governed input references:\n"
        + "- data/input/sample_points.geojson"
    )
    assert captured["allowed_skill_ids"] == ["inspect_vector"]
    assert captured["project_root"] == PROJECT_ROOT.resolve()
    assert result["status"] == "planned_not_saved"
    assert result["allowed_skill_ids"] == ["inspect_vector"]
    assert result["original_request"] == request_text
    assert "data/input/sample_points.geojson" in result["context_references"]
    assert result["plan"] == plan_payload
    assert len(result["plan_sha256"]) == 64
    assert result["plan_saved"] is False
    assert result["approval_performed"] is False
    assert result["execution_performed"] is False


def reviewed_plan_request() -> InterfaceReviewedPlanSaveRequest:
    result = PlannerResult.model_validate({
        "agent_id": "planner",
        "model": "qwen-test",
        "original_request": "Inspect the approved sample vector. Plan only.",
        "context_references": ["context/DATASET_CATALOG.json"],
        "plan": {
            "schema_version": "1.0",
            "status": "planned",
            "summary": "Inspect the approved input.",
            "steps": [{
                "step_id": "step_1",
                "skill": "inspect_vector",
                "purpose": "Inspect metadata.",
                "arguments": {"path": "data/input/sample_points.geojson"},
                "requires_approval": False,
                "expected_artifacts": ["inspection result"],
                "validation_required": False,
            }],
            "assumptions": [],
            "risks": [],
            "execution_performed": False,
            "validation_performed": False,
        },
        "warnings": [],
    })
    return InterfaceReviewedPlanSaveRequest(
        action="save_reviewed_plan",
        confirmed_plan_sha256=plan_sha256(result.plan),
        allowed_skill_ids=["inspect_vector"],
        planner_result=result,
    )


def reviewed_write_plan_request() -> InterfaceReviewedPlanSaveRequest:
    payload = reviewed_plan_request().planner_result.model_dump(mode="json")
    payload["original_request"] = "Convert the approved sample vector. Plan only."
    payload["plan"]["summary"] = "Convert the approved input."
    payload["plan"]["steps"] = [{
        "step_id": "step_1",
        "skill": "convert_vector",
        "purpose": "Create a GeoPackage output.",
        "arguments": {
            "path": "data/input/sample_points.geojson",
            "target_path": "data/output/planner_test.gpkg",
        },
        "requires_approval": True,
        "expected_artifacts": ["converted vector"],
        "validation_required": True,
    }]
    result = PlannerResult.model_validate(payload)
    return InterfaceReviewedPlanSaveRequest(
        action="save_reviewed_plan",
        confirmed_plan_sha256=plan_sha256(result.plan),
        allowed_skill_ids=["convert_vector"],
        planner_result=result,
    )


def test_reviewed_plan_save_is_immutable_and_cli_compatible(tmp_path: Path) -> None:
    request = reviewed_plan_request()
    plan_root = tmp_path / "plans"

    stored = save_interface_reviewed_plan(
        request,
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
    )

    assert stored["status"] == "stored"
    assert stored["plan_sha256"] == request.confirmed_plan_sha256
    assert stored["plan_saved"] is True
    assert stored["plan_modified"] is True
    assert stored["approval_performed"] is False
    assert stored["execution_performed"] is False
    loaded = load_planner_result(
        path=plan_root / stored["plan_filename"],
        plan_root=plan_root,
    )
    assert loaded == request.planner_result

    prepared = prepare_interface_plan_approval(
        InterfacePlanApprovalPreparationRequest(
            action="prepare_plan_approval",
            plan_filename=stored["plan_filename"],
            confirmed_plan_sha256=stored["plan_sha256"],
        ),
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
    )
    assert prepared["status"] == "approval_not_required"
    assert prepared["approval_required_step_ids"] == []
    assert prepared["approval_recorded"] is False
    assert prepared["execution_performed"] is False
    assert len(prepared["approval_request_sha256"]) == 64

    inventory = interface_saved_plan_inventory(
        PROJECT_ROOT, plan_root=plan_root, approval_root=tmp_path / "approvals",
    )
    assert inventory["plan_count"] == 1
    assert inventory["plans"][0]["plan_sha256"] == stored["plan_sha256"]
    assert inventory["plans"][0]["planner_result"]["plan"]["steps"][0]["skill"] == "inspect_vector"
    assert inventory["plans"][0]["approvals"] == []
    assert inventory["execution_performed"] is False

    original_mtime = (plan_root / stored["plan_filename"]).stat().st_mtime_ns
    repeated = save_interface_reviewed_plan(
        request,
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
    )
    assert repeated["status"] == "already_stored"
    assert repeated["plan_modified"] is False
    assert (plan_root / stored["plan_filename"]).stat().st_mtime_ns == original_mtime


def test_reviewed_plan_save_rejects_digest_drift_and_symlink_root(tmp_path: Path) -> None:
    request = reviewed_plan_request()
    with pytest.raises(InterfaceApiError, match="digest no longer matches"):
        save_interface_reviewed_plan(
            request.model_copy(update={"confirmed_plan_sha256": "0" * 64}),
            project_root=PROJECT_ROOT,
            plan_root=tmp_path / "mismatch",
        )
    assert not (tmp_path / "mismatch").exists()

    real_root = tmp_path / "real-plans"
    real_root.mkdir()
    linked_root = tmp_path / "linked-plans"
    linked_root.symlink_to(real_root, target_is_directory=True)
    with pytest.raises(InterfaceApiError, match="cannot be a symlink"):
        save_interface_reviewed_plan(
            request,
            project_root=PROJECT_ROOT,
            plan_root=linked_root,
        )
    assert not list(real_root.iterdir())


def test_plan_approval_preparation_rejects_digest_drift(tmp_path: Path) -> None:
    request = reviewed_plan_request()
    plan_root = tmp_path / "plans"
    stored = save_interface_reviewed_plan(
        request, project_root=PROJECT_ROOT, plan_root=plan_root,
    )
    with pytest.raises(InterfaceApiError, match="digest no longer matches"):
        prepare_interface_plan_approval(
            InterfacePlanApprovalPreparationRequest(
                action="prepare_plan_approval",
                plan_filename=stored["plan_filename"],
                confirmed_plan_sha256="0" * 64,
            ),
            project_root=PROJECT_ROOT,
            plan_root=plan_root,
        )


def test_plan_decision_is_append_only_and_bound_to_prepared_scope(tmp_path: Path) -> None:
    request = reviewed_write_plan_request()
    plan_root = tmp_path / "plans"
    approval_root = tmp_path / "approvals"
    stored = save_interface_reviewed_plan(
        request, project_root=PROJECT_ROOT, plan_root=plan_root,
    )
    prepared = prepare_interface_plan_approval(
        InterfacePlanApprovalPreparationRequest(
            action="prepare_plan_approval",
            plan_filename=stored["plan_filename"],
            confirmed_plan_sha256=stored["plan_sha256"],
        ),
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
    )
    assert prepared["approval_required_step_ids"] == ["step_1"]
    assert prepared["steps"][0]["arguments"]["target_path"] == "data/output/planner_test.gpkg"
    assert prepared["steps"][0]["requires_approval"] is True
    assert prepared["steps"][0]["validation_required"] is True
    recorded = record_interface_plan_approval(
        InterfacePlanApprovalDecisionRequest(
            action="record_plan_approval",
            plan_filename=stored["plan_filename"],
            confirmed_plan_sha256=stored["plan_sha256"],
            confirmed_approval_request_sha256=prepared["approval_request_sha256"],
            decision="approved",
            approver="test operator",
            reason="Reviewed exact conversion scope.",
            # Compilation re-verifies against the real clock, so this fixture
            # must not expire merely because the test suite runs after 2026-09-19.
            valid_for_minutes=None,
        ),
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
        approval_root=approval_root,
        now=datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc),
    )
    assert recorded["decision"] == "approved"
    assert recorded["approved_step_ids"] == ["step_1"]
    assert recorded["approval_recorded"] is True
    assert recorded["execution_performed"] is False
    assert (approval_root / recorded["approval_filename"]).is_file()

    verified = verify_interface_plan_approval(
        InterfacePlanApprovalVerificationRequest(
            action="verify_plan_approval",
            plan_filename=stored["plan_filename"],
            confirmed_plan_sha256=stored["plan_sha256"],
            confirmed_approval_request_sha256=prepared["approval_request_sha256"],
            approval_filename=recorded["approval_filename"],
        ),
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
        approval_root=approval_root,
        now=datetime(2026, 9, 19, 12, 1, tzinfo=timezone.utc),
    )
    assert verified["approved"] is True
    assert verified["verified_step_ids"] == ["step_1"]
    assert verified["independent_verification_performed"] is True
    assert verified["plan_modified"] is False
    assert verified["approval_modified"] is False
    assert verified["execution_performed"] is False

    compiled = compile_interface_plan_recipe(
        InterfacePlanRecipeCompilationRequest(
            action="compile_plan_recipe",
            plan_filename=stored["plan_filename"],
            confirmed_plan_sha256=stored["plan_sha256"],
            confirmed_approval_request_sha256=prepared["approval_request_sha256"],
            approval_filename=recorded["approval_filename"],
        ),
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
        approval_root=approval_root,
    )
    assert compiled["status"] == "compiled_not_saved"
    assert compiled["recipe"]["steps"][0]["skill_id"] == "convert_vector"
    assert compiled["recipe_saved"] is False
    assert compiled["recipe_approval_performed"] is False
    assert compiled["execution_performed"] is False

    recipe_root = tmp_path / "workflow-recipes"
    saved_recipe = save_interface_plan_recipe(
        InterfacePlanRecipeSaveRequest(
            action="save_reviewed_plan_recipe",
            plan_filename=stored["plan_filename"],
            confirmed_plan_sha256=stored["plan_sha256"],
            confirmed_approval_request_sha256=prepared["approval_request_sha256"],
            approval_filename=recorded["approval_filename"],
            confirmed_recipe_sha256=compiled["recipe_sha256"],
        ),
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
        approval_root=approval_root,
        recipe_root=recipe_root,
    )
    assert saved_recipe["status"] == "stored"
    assert saved_recipe["recipe_sha256"] == compiled["recipe_sha256"]
    assert saved_recipe["recipe_created"] is True
    assert saved_recipe["recipe_modified"] is False
    assert saved_recipe["approval_performed"] is False
    assert saved_recipe["execution_performed"] is False
    assert (recipe_root / saved_recipe["recipe_filename"]).is_file()

    resumed_recipe = save_interface_plan_recipe(
        InterfacePlanRecipeSaveRequest(
            action="save_reviewed_plan_recipe",
            plan_filename=stored["plan_filename"],
            confirmed_plan_sha256=stored["plan_sha256"],
            confirmed_approval_request_sha256=prepared["approval_request_sha256"],
            approval_filename=recorded["approval_filename"],
            confirmed_recipe_sha256=compiled["recipe_sha256"],
        ),
        project_root=PROJECT_ROOT,
        plan_root=plan_root,
        approval_root=approval_root,
        recipe_root=recipe_root,
    )
    assert resumed_recipe["status"] == "stored"
    assert resumed_recipe["recipe_created"] is False
    assert resumed_recipe["recipe_modified"] is False

    with pytest.raises(InterfaceApiError, match="digest no longer matches"):
        save_interface_plan_recipe(
            InterfacePlanRecipeSaveRequest(
                action="save_reviewed_plan_recipe",
                plan_filename=stored["plan_filename"],
                confirmed_plan_sha256=stored["plan_sha256"],
                confirmed_approval_request_sha256=prepared["approval_request_sha256"],
                approval_filename=recorded["approval_filename"],
                confirmed_recipe_sha256="0" * 64,
            ),
            project_root=PROJECT_ROOT,
            plan_root=plan_root,
            approval_root=approval_root,
            recipe_root=tmp_path / "mismatch-recipes",
        )

    with pytest.raises(InterfaceApiError, match="request digest no longer matches"):
        record_interface_plan_approval(
            InterfacePlanApprovalDecisionRequest(
                action="record_plan_approval",
                plan_filename=stored["plan_filename"],
                confirmed_plan_sha256=stored["plan_sha256"],
                confirmed_approval_request_sha256="0" * 64,
                decision="denied",
                approver="test operator",
                reason="Stale request.",
            ),
            project_root=PROJECT_ROOT,
            plan_root=plan_root,
            approval_root=approval_root,
        )


def test_interface_planner_catalog_exposes_only_implemented_safe_metadata() -> None:
    catalog = interface_planner_skill_catalog(PROJECT_ROOT)

    assert catalog["catalog_validated"] is True
    assert catalog["execution_performed"] is False
    assert catalog["skill_count"] == len(catalog["skills"])
    assert "inspect_vector" in {skill["id"] for skill in catalog["skills"]}
    assert all("entrypoint" not in skill for skill in catalog["skills"])


def test_interface_catalog_is_validated_and_non_executing() -> None:
    result = interface_recipe_template_catalog(PROJECT_ROOT)

    assert len(result["templates"]) == 5
    vector_conversion = next(
        template for template in result["templates"]
        if template["template_id"] == "inspect_and_convert_vector"
    )
    assert vector_conversion["optional_parameters"] == [
        "source_layer", "target_layer", "target_format"
    ]
    assert vector_conversion["parameter_roots"] == {
        "path": "data/input",
        "target_path": "data/output",
    }
    assert result["catalog_validated"] is True
    assert result["files_modified"] is False
    assert result["execution_performed"] is False


def test_interface_data_inventory_lists_only_bounded_resources(tmp_path: Path) -> None:
    input_root = tmp_path / "data" / "input"
    output_root = tmp_path / "data" / "output" / "exports"
    input_root.mkdir(parents=True)
    output_root.mkdir(parents=True)
    (input_root / "sample.geojson").write_text("{}", encoding="utf-8")
    (input_root / "notes.txt").write_text("not listed", encoding="utf-8")

    result = interface_data_resource_inventory(tmp_path)

    assert result["inputs"] == [{
        "path": "data/input/sample.geojson",
        "name": "sample.geojson",
        "extension": ".geojson",
        "size_bytes": 2,
    }]
    assert result["output_directories"] == ["data/output", "data/output/exports"]
    assert result["files_modified"] is False
    assert result["execution_performed"] is False


def test_interface_compilation_matches_cli_boundary() -> None:
    response = compile_interface_recipe_proposal(
        proposal_payload(),
        project_root=PROJECT_ROOT,
    )

    result = response["result"]
    assert response["status"] == "compiled"
    assert [step["skill_id"] for step in result["recipe"]["steps"]] == [
        "inspect_vector",
        "convert_vector",
    ]
    assert result["recipe_validation"]["valid"] is True
    assert result["recipe_saved"] is False
    assert result["approval_performed"] is False
    assert result["execution_performed"] is False
    assert response["files_modified"] is False
    assert len(response["recipe_sha256"]) == 64


def test_interface_compilation_resolves_filename_only_data_paths() -> None:
    payload = proposal_payload()
    payload["selection"]["parameters"]["path"] = "sample_points.geojson"
    payload["selection"]["parameters"]["target_path"] = "interface_result.gpkg"

    response = compile_interface_recipe_proposal(payload, project_root=PROJECT_ROOT)
    steps = response["result"]["recipe"]["steps"]

    assert steps[0]["arguments"]["path"] == "data/input/sample_points.geojson"
    assert steps[1]["arguments"]["path"] == "data/input/sample_points.geojson"
    assert steps[1]["arguments"]["target_path"] == "data/output/interface_result.gpkg"


def test_interface_compilation_preserves_explicit_paths() -> None:
    payload = proposal_payload()
    payload["selection"]["parameters"]["path"] = "data/input/nested/source.geojson"
    payload["selection"]["parameters"]["target_path"] = "data/output/nested/result.gpkg"

    response = compile_interface_recipe_proposal(payload, project_root=PROJECT_ROOT)
    steps = response["result"]["recipe"]["steps"]

    assert steps[0]["arguments"]["path"] == "data/input/nested/source.geojson"
    assert steps[1]["arguments"]["target_path"] == "data/output/nested/result.gpkg"


def test_filename_only_recipe_can_be_saved_with_compiled_digest(tmp_path: Path) -> None:
    payload = proposal_payload()
    payload["selection"]["parameters"]["path"] = "sample_points.geojson"
    payload["selection"]["parameters"]["target_path"] = "saved_result.gpkg"
    compiled = compile_interface_recipe_proposal(payload, project_root=PROJECT_ROOT)

    stored = save_interface_reviewed_recipe(
        payload,
        confirmed_recipe_sha256=compiled["recipe_sha256"],
        project_root=PROJECT_ROOT,
        recipe_root=tmp_path / "recipes",
    )

    assert stored["status"] == "stored"
    assert stored["recipe_sha256"] == compiled["recipe_sha256"]


def test_interface_target_format_is_enforced_by_real_compiler() -> None:
    payload = proposal_payload()
    payload["selection"]["parameters"]["target_format"] = "geojson"

    with pytest.raises(RecipeCompilationError, match="not ready"):
        compile_interface_recipe_proposal(payload, project_root=PROJECT_ROOT)


def test_reviewed_save_recompiles_and_writes_only_immutable_recipe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proposal = proposal_payload()
    compilation = compile_interface_recipe_proposal(
        proposal,
        project_root=PROJECT_ROOT,
    )
    recipe_root = tmp_path / "workflow-recipes"

    stored = save_interface_reviewed_recipe(
        proposal,
        confirmed_recipe_sha256=compilation["recipe_sha256"],
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
    )

    assert stored["status"] == "stored"
    assert stored["recipe_saved"] is True
    assert stored["approval_performed"] is False
    assert stored["execution_performed"] is False
    assert stored["recipe_sha256"] == compilation["recipe_sha256"]
    assert [path.name for path in recipe_root.iterdir()] == [
        stored["recipe_filename"]
    ]

    inventory = interface_saved_recipe_inventory(
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
    )
    assert inventory["recipe_count"] == 1
    assert inventory["recipe_modified"] is False
    assert inventory["approval_performed"] is False
    assert inventory["execution_performed"] is False
    assert inventory["recipes"][0]["recipe_sha256"] == stored["recipe_sha256"]
    assert datetime.fromisoformat(
        inventory["recipes"][0]["saved_at"]
    ).tzinfo is not None
    assert inventory["recipes"][0]["approval_required_step_ids"] == ["step_2"]
    assert [step["skill_id"] for step in inventory["recipes"][0]["steps"]] == [
        "inspect_vector",
        "convert_vector",
    ]

    approval_request = prepare_interface_recipe_approval(
        recipe_filename=stored["recipe_filename"],
        confirmed_recipe_sha256=stored["recipe_sha256"],
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
    )
    assert approval_request["status"] == "prepared_not_recorded"
    assert approval_request["approval_required_step_ids"] == ["step_2"]
    assert len(approval_request["approval_request_sha256"]) == 64
    assert approval_request["approval_recorded"] is False
    assert approval_request["execution_performed"] is False

    with pytest.raises(InterfaceApiError, match="filename is invalid"):
        prepare_interface_recipe_approval(
            recipe_filename="../escaped.json",
            confirmed_recipe_sha256=stored["recipe_sha256"],
            project_root=PROJECT_ROOT,
            recipe_root=recipe_root,
        )

    approval_root = tmp_path / "approvals"
    decision = InterfaceApprovalDecision.model_validate({
        "action": "record_recipe_approval",
        "recipe_filename": stored["recipe_filename"],
        "confirmed_recipe_sha256": stored["recipe_sha256"],
        "confirmed_approval_request_sha256": approval_request["approval_request_sha256"],
        "decision": "approved",
        "approver": "interface operator",
        "reason": "Reviewed the exact conversion step and target.",
        "valid_for_minutes": None,
    })
    recorded = record_interface_recipe_approval(
        decision,
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
        approval_root=approval_root,
        now=datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc),
    )
    assert recorded["status"] == "recorded"
    assert recorded["decision"] == "approved"
    assert recorded["approved_step_ids"] == ["step_2"]
    assert recorded["approval_recorded"] is True
    assert recorded["execution_performed"] is False
    assert [path.name for path in approval_root.iterdir()] == [
        recorded["approval_filename"]
    ]

    verification = verify_interface_recipe_approval(
        InterfaceApprovalVerificationRequest.model_validate({
            "action": "verify_recipe_approval",
            "recipe_filename": stored["recipe_filename"],
            "confirmed_recipe_sha256": stored["recipe_sha256"],
            "confirmed_approval_request_sha256": approval_request["approval_request_sha256"],
            "approval_filename": recorded["approval_filename"],
        }),
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
        approval_root=approval_root,
        now=datetime(2026, 9, 16, 12, 1, tzinfo=timezone.utc),
    )
    assert verification["status"] == "verified"
    assert verification["approved"] is True
    assert verification["required_step_ids"] == ["step_2"]
    assert verification["independent_verification_performed"] is True
    assert verification["approval_modified"] is False
    assert verification["execution_performed"] is False

    preview = prepare_interface_execution_preview(
        InterfaceExecutionPreviewRequest.model_validate({
            "action": "prepare_execution_preview",
            "recipe_filename": stored["recipe_filename"],
            "confirmed_recipe_sha256": stored["recipe_sha256"],
            "confirmed_approval_request_sha256": approval_request["approval_request_sha256"],
            "approval_filename": recorded["approval_filename"],
        }),
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
        approval_root=approval_root,
        now=datetime(2026, 9, 16, 12, 1, tzinfo=timezone.utc),
    )
    assert preview["status"] == "previewed_not_executed"
    assert preview["topological_step_ids"] == ["step_1", "step_2"]
    assert [step["skill_id"] for step in preview["steps"]] == [
        "inspect_vector", "convert_vector"
    ]
    assert preview["steps"][1]["access"] == "artifact_write"
    assert preview["steps"][1]["validation_required"] is True
    assert preview["evidence_destinations"] == ["recipe-runs/", "recipe-evidence/"]
    assert preview["execution_available"] is False
    assert preview["execution_performed"] is False
    assert len(preview["execution_preview_sha256"]) == 64

    monkeypatch.setattr(
        interface_api_module,
        "load_settings",
        lambda: load_settings({"ENABLE_WRITE_TOOLS": "true"}),
    )
    enabled_preview = prepare_interface_execution_preview(
        InterfaceExecutionPreviewRequest.model_validate({
            "action": "prepare_execution_preview",
            "recipe_filename": stored["recipe_filename"],
            "confirmed_recipe_sha256": stored["recipe_sha256"],
            "confirmed_approval_request_sha256": approval_request["approval_request_sha256"],
            "approval_filename": recorded["approval_filename"],
        }),
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
        approval_root=approval_root,
        now=datetime(2026, 9, 16, 12, 1, tzinfo=timezone.utc),
    )
    assert enabled_preview["execution_available"] is True

    fake_record = SimpleNamespace(
        final_status="validated_success",
        recipe_id=enabled_preview["recipe_id"],
        recipe_sha256=enabled_preview["recipe_sha256"],
        approval_id=enabled_preview["approval_id"],
        run_result_sha256="1" * 64,
        run_result_path="recipe-runs/test.json",
        evidence_sha256="2" * 64,
        evidence_path="recipe-evidence/test.json",
        report_path="reports/test.md",
    )
    fake_run = SimpleNamespace(step_results=[
        SimpleNamespace(step_id="step_1", skill_id="inspect_vector", status="completed", validation_performed=False, execution=SimpleNamespace(output_ids=["source_metadata"], result={"feature_count": 3}), validation_result=None),
        SimpleNamespace(step_id="step_2", skill_id="convert_vector", status="validated_success", validation_performed=True, execution=SimpleNamespace(output_ids=["converted_vector"], result={"target": "data/output/test.gpkg"}), validation_result={"passed": True}),
    ])
    def fake_execute(**kwargs):
        progress = kwargs["progress_callback"]
        progress("step_1", "inspect_vector", "running")
        progress("step_1", "inspect_vector", "completed")
        progress("step_2", "convert_vector", "running")
        progress("step_2", "convert_vector", "validated_success")
        return SimpleNamespace(execution_record=fake_record, run_result=fake_run)

    monkeypatch.setattr(
        interface_api_module,
        "execute_approved_recipe",
        fake_execute,
    )
    executed = execute_interface_recipe(
        InterfaceRecipeExecutionRequest.model_validate({
            "action": "execute_exact_preview",
            "recipe_filename": stored["recipe_filename"],
            "confirmed_recipe_sha256": stored["recipe_sha256"],
            "confirmed_approval_request_sha256": approval_request["approval_request_sha256"],
            "approval_filename": recorded["approval_filename"],
            "confirmed_execution_preview_sha256": enabled_preview["execution_preview_sha256"],
            "confirmation": "execute_exact_preview",
        }),
        project_root=PROJECT_ROOT,
        recipe_root=recipe_root,
        approval_root=approval_root,
        progress_root=tmp_path / "execution-progress",
    )
    assert executed["status"] == "validated_success"
    assert executed["execution_performed"] is True
    assert executed["evidence_recorded"] is True
    assert executed["report_written"] is True
    progress = interface_api_module._EXECUTION_PROGRESS[
        enabled_preview["execution_preview_sha256"]
    ]
    assert progress["status"] == "validated_success"
    assert [step["status"] for step in progress["steps"]] == [
        "completed",
        "validated_success",
    ]
    assert progress["failed_step_id"] is None
    assert progress["interruption_detected"] is False
    assert progress["recovery_guidance"] is None
    progress_artifact = (
        tmp_path
        / "execution-progress"
        / f'{enabled_preview["execution_preview_sha256"]}.json'
    )
    assert json.loads(progress_artifact.read_text(encoding="utf-8")) == progress
    assert executed["step_results"][0]["outcome"] == {"feature_count": 3}
    assert executed["step_results"][1]["validation_outcome"] == {"passed": True}

    mismatch_root = tmp_path / "mismatched-approvals"
    with pytest.raises(InterfaceApiError, match="request digest no longer matches"):
        record_interface_recipe_approval(
            decision.model_copy(update={
                "confirmed_approval_request_sha256": "0" * 64,
            }),
            project_root=PROJECT_ROOT,
            recipe_root=recipe_root,
            approval_root=mismatch_root,
        )
    assert not mismatch_root.exists()

    with pytest.raises(InterfaceApiError, match="digest no longer matches"):
        save_interface_reviewed_recipe(
            {**proposal, "recipe_id_hint": "changed-after-review"},
            confirmed_recipe_sha256=compilation["recipe_sha256"],
            project_root=PROJECT_ROOT,
            recipe_root=tmp_path / "mismatch",
        )
    assert not (tmp_path / "mismatch").exists()


def test_durable_running_progress_is_classified_as_interrupted(
    tmp_path: Path,
) -> None:
    digest = "a" * 64
    progress_root = tmp_path / "execution-progress"
    state = {
        "schema_version": "1.0",
        "status": "running",
        "execution_preview_sha256": digest,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "failed_step_id": None,
        "interruption_detected": False,
        "recovery_guidance": None,
        "steps": [
            {"step_id": "step_1", "skill_id": "inspect_vector", "status": "completed"},
            {"step_id": "step_2", "skill_id": "convert_vector", "status": "running"},
        ],
        "execution_performed": False,
    }
    interface_api_module._persist_execution_progress(
        PROJECT_ROOT,
        state,
        progress_root=progress_root,
    )
    interface_api_module._ACTIVE_PROGRESS.discard(digest)

    loaded = interface_api_module._load_execution_progress(
        PROJECT_ROOT,
        digest,
        progress_root=progress_root,
    )

    assert loaded is not None
    assert loaded["status"] == "interrupted"
    assert loaded["interruption_detected"] is True
    assert loaded["failed_step_id"] == "step_2"
    assert loaded["steps"][1]["status"] == "interrupted"
    assert "fresh target and new approval" in loaded["recovery_guidance"]
    assert json.loads((progress_root / f"{digest}.json").read_text())["status"] == "interrupted"


def test_active_durable_progress_remains_running(tmp_path: Path) -> None:
    digest = "b" * 64
    progress_root = tmp_path / "execution-progress"
    state = {
        "schema_version": "1.0",
        "status": "running",
        "execution_preview_sha256": digest,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "failed_step_id": None,
        "interruption_detected": False,
        "recovery_guidance": None,
        "steps": [{"step_id": "step_1", "skill_id": "inspect_vector", "status": "running"}],
        "execution_performed": False,
    }
    interface_api_module._persist_execution_progress(
        PROJECT_ROOT,
        state,
        progress_root=progress_root,
    )
    interface_api_module._ACTIVE_PROGRESS.add(digest)
    try:
        loaded = interface_api_module._load_execution_progress(
            PROJECT_ROOT,
            digest,
            progress_root=progress_root,
        )
    finally:
        interface_api_module._ACTIVE_PROGRESS.discard(digest)

    assert loaded is not None
    assert loaded["status"] == "running"
    assert loaded["steps"][0]["status"] == "running"


def test_execution_inventory_reopens_durable_attempts_without_execution(
    tmp_path: Path,
) -> None:
    progress_root = tmp_path / "execution-progress"
    digest = "c" * 64
    state = {
        "schema_version": "1.0",
        "status": "validated_success",
        "execution_preview_sha256": digest,
        "recipe_id": "inventory_recipe",
        "recipe_filename": f"inventory_recipe.{('d' * 64)}.json",
        "recipe_sha256": "d" * 64,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "failed_step_id": None,
        "interruption_detected": False,
        "recovery_guidance": None,
        "steps": [{
            "step_id": "step_1",
            "skill_id": "inspect_vector",
            "depends_on": [],
            "status": "completed",
        }],
        "execution_performed": True,
    }
    interface_api_module._persist_execution_progress(
        PROJECT_ROOT,
        state,
        progress_root=progress_root,
    )

    inventory = interface_execution_inventory(
        PROJECT_ROOT,
        progress_root=progress_root,
    )

    assert inventory["attempt_count"] == 1
    assert inventory["inventory_truncated"] is False
    assert inventory["execution_performed"] is False
    assert inventory["attempts"][0] == {
        "execution_preview_sha256": digest,
        "status": "validated_success",
        "recipe_id": "inventory_recipe",
        "recipe_filename": f"inventory_recipe.{('d' * 64)}.json",
        "recipe_sha256": "d" * 64,
        "started_at": state["started_at"],
        "finished_at": state["finished_at"],
        "failed_step_id": None,
        "interruption_detected": False,
        "step_count": 1,
    }


def test_interface_server_refuses_non_loopback_binding() -> None:
    with pytest.raises(InterfaceApiError, match="127.0.0.1"):
        serve_interface_api(project_root=PROJECT_ROOT, host="0.0.0.0")


def test_http_boundary_compiles_json_and_rejects_foreign_origin() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(PROJECT_ROOT))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        body = json.dumps(proposal_payload())
        connection.request(
            "POST",
            "/api/v1/recipe-proposals/compile",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Origin": "http://localhost:5173",
            },
        )
        response = connection.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert payload["status"] == "compiled"
        assert payload["execution_performed"] is False
        connection.close()

        routed = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        routed.request(
            "POST",
            "/api/v1/plans/save-reviewed-recipe",
            body="{}",
            headers={
                "Content-Type": "application/json",
                "Origin": "http://localhost:5173",
            },
        )
        routed_response = routed.getresponse()
        routed_payload = json.loads(routed_response.read())
        assert routed_response.status == 400
        assert routed_payload == {"error": "request payload is invalid"}
        routed.close()

        rejected = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        rejected.request(
            "POST",
            "/api/v1/recipe-proposals/compile",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://example.invalid",
            },
        )
        rejected_response = rejected.getresponse()
        assert rejected_response.status == 403
        assert json.loads(rejected_response.read()) == {
            "error": "request origin is not allowed"
        }
        rejected.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_planner_policy_rejection_returns_safe_actionable_finding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def rejected_plan(*_args, **_kwargs):
        raise interface_api_module.PlannerAgentError(
            "Planner plan failed deterministic policy: "
            "inspect_vector is missing required arguments: path"
        )

    monkeypatch.setattr(interface_api_module, "plan_interface_task", rejected_plan)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(PROJECT_ROOT))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        connection.request(
            "POST",
            "/api/v1/plans/create",
            body=json.dumps({
                "action": "plan_task",
                "request": "Inspect the selected vector.",
                "allowed_skill_ids": ["inspect_vector"],
                "input_paths": ["data/input/sample_points.geojson"],
            }),
            headers={"Content-Type": "application/json", "Origin": "http://localhost:5173"},
        )
        response = connection.getresponse()
        payload = json.loads(response.read())
        assert response.status == 422
        assert payload["code"] == "planner_policy_rejected"
        assert payload["finding"] == "inspect_vector is missing required arguments: path"
        assert payload["retryable"] is True
        assert payload["plan_returned"] is False
        assert payload["plan_saved"] is False
        assert payload["approval_performed"] is False
        assert payload["execution_performed"] is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
