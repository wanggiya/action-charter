"""Checkpoint 17B browser-safe trace projection tests."""

import json
from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.interface_projection import InterfaceProjectionError, export_workflow_catalog, project_workflow_trace
from geoagent_harness.trace import TraceTimestamps, WorkflowTrace


def _trace(task_id: str = "demo-run") -> WorkflowTrace:
    now = datetime.now(UTC)
    return WorkflowTrace(
        task_id=task_id,
        original_request="private operator request",
        context_references=["context/private.md"],
        selected_skills=["inspect_vector"],
        plan_sha256="a" * 64,
        approval_id="approval-private-id",
        approved_step_ids=["step-1"],
        tool_arguments={"inspect_vector": {"path": "secret/location.geojson"}},
        tool_results={"inspect_vector": {"token": "should-not-project"}},
        validation_results={"status": "passed"},
        artifacts=["private/result.json"],
        warnings=[],
        final_status="validated_success",
        timestamps=TraceTimestamps(started_at=now, finished_at=now),
        versions={"actioncharter": "0.9.0"},
    )


def _write_trace(root, trace: WorkflowTrace) -> None:
    root.mkdir(exist_ok=True)
    (root / f"{trace.task_id}.json").write_text(trace.model_dump_json(), encoding="utf-8")


def test_projection_exposes_graph_but_not_trace_payloads(tmp_path) -> None:
    root = tmp_path / "traces"
    _write_trace(root, _trace())
    result = project_workflow_trace(task_id="demo-run", trace_root=root)
    payload = result.model_dump_json(by_alias=True)
    assert result.source == "validated_trace"
    assert result.read_only is True
    assert len(result.nodes) == 8
    assert "private operator request" not in payload
    assert "secret/location.geojson" not in payload
    assert "should-not-project" not in payload
    assert "approval-private-id" not in payload
    assert all(node.details is not None for node in result.nodes)
    assert result.nodes[0].details.observed_facts[0].label == "Context references"
    assert result.nodes[0].details.observed_facts[0].value == "1"


def test_projection_rejects_unbounded_identity(tmp_path) -> None:
    root = tmp_path / "traces"
    root.mkdir()
    with pytest.raises(InterfaceProjectionError, match="could not be loaded"):
        project_workflow_trace(task_id="../escape", trace_root=root)


def test_projection_rejects_false_redaction_claim(tmp_path) -> None:
    root = tmp_path / "traces"
    trace = _trace()
    trace.secrets_redacted = False
    _write_trace(root, trace)
    with pytest.raises(InterfaceProjectionError, match="redaction claim"):
        project_workflow_trace(task_id="demo-run", trace_root=root)


def test_projection_json_uses_frontend_field_names(tmp_path) -> None:
    root = tmp_path / "traces"
    _write_trace(root, _trace())
    result = project_workflow_trace(task_id="demo-run", trace_root=root)
    payload = json.loads(result.model_dump_json(by_alias=True))
    assert payload["schemaVersion"] == "1.0"
    assert payload["correlationId"] == "demo-run"
    assert payload["readOnly"] is True
    assert payload["edges"][0] == {"from": "request", "to": "planner"}


def test_projection_cli_emits_browser_contract(tmp_path) -> None:
    root = tmp_path / "traces"
    _write_trace(root, _trace())
    result = CliRunner().invoke(app, ["project-interface-workflow", "demo-run", "--trace-root", str(root)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["source"] == "validated_trace"


def test_catalog_export_writes_only_sanitized_runtime_files(tmp_path) -> None:
    root = tmp_path / "traces"
    _write_trace(root, _trace("first-run"))
    _write_trace(root, _trace("second-run"))
    output = tmp_path / "runtime"
    result = export_workflow_catalog(trace_root=root, output_root=output)
    catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
    assert result.workflow_count == 2
    assert {item["taskId"] for item in catalog["workflows"]} == {"first-run", "second-run"}
    assert (output / "first-run.json").is_file()
    assert "private operator request" not in (output / "first-run.json").read_text(encoding="utf-8")


def test_catalog_export_cli_reports_bounded_files(tmp_path) -> None:
    root = tmp_path / "traces"
    _write_trace(root, _trace())
    output = tmp_path / "runtime"
    result = CliRunner().invoke(app, ["export-interface-workflows", "--trace-root", str(root), "--output-root", str(output)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["projection_files"] == ["demo-run.json"]
    assert (output / "catalog.json").is_file()


def test_detail_projection_contains_only_bounded_aggregate_facts(tmp_path) -> None:
    root = tmp_path / "traces"
    _write_trace(root, _trace())
    result = project_workflow_trace(task_id="demo-run", trace_root=root)
    executor = next(node for node in result.nodes if node.id == "executor")
    evidence = next(node for node in result.nodes if node.id == "evidence")
    assert executor.details.duration_ms == 0
    assert {fact.label for fact in evidence.details.observed_facts} == {
        "Artifacts recorded", "Warnings recorded", "Secrets redacted"
    }
