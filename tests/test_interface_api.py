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
from geoagent_harness.mcp_server.settings import load_settings
from geoagent_harness.recipe_proposals import RecipeCompilationError


PROJECT_ROOT = Path(__file__).parents[1]
PROPOSAL_FILE = (
    PROJECT_ROOT
    / "examples"
    / "interface-parity"
    / "checkpoint17l-vector-conversion-proposal.json"
)


def proposal_payload() -> dict[str, object]:
    return json.loads(PROPOSAL_FILE.read_text(encoding="utf-8"))


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
    assert result["catalog_validated"] is True
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
    monkeypatch.setattr(
        interface_api_module,
        "execute_approved_recipe",
        lambda **_kwargs: SimpleNamespace(execution_record=fake_record, run_result=fake_run),
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
    )
    assert executed["status"] == "validated_success"
    assert executed["execution_performed"] is True
    assert executed["evidence_recorded"] is True
    assert executed["report_written"] is True
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
