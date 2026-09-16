"""Tests for the loopback-only non-mutating interface API."""

from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

import pytest

from geoagent_harness.interface_api import (
    InterfaceApiError,
    compile_interface_recipe_proposal,
    interface_recipe_template_catalog,
    interface_saved_recipe_inventory,
    prepare_interface_recipe_approval,
    save_interface_reviewed_recipe,
    serve_interface_api,
)
from geoagent_harness.interface_api.server import _handler


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


def test_reviewed_save_recompiles_and_writes_only_immutable_recipe(
    tmp_path: Path,
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
