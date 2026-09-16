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
