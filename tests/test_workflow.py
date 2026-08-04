from pathlib import Path

import pytest

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.skills.load_vector_to_postgis.service import (
    LoadVectorResult,
)
from geoagent_harness.verifier.postgis import (
    LayerExtent,
    PostGISValidationResult,
)
from geoagent_harness.orchestrator import workflow


class Dumpable:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def model_dump(self, mode: str = "python") -> dict:
        return self.payload


class Inspected:
    def __init__(self) -> None:
        self.result = Dumpable(
            {
                "source": "data/input/sample_points.geojson",
                "driver": "GeoJSON",
                "layers": [
                    {
                        "name": "sample_points",
                        "geometry_type": "POINT",
                    }
                ],
            }
        )

        self.result.layers = [
            type(
                "Layer",
                (),
                {"geometry_type": "POINT"},
            )()
        ]

    def model_dump(self, mode: str = "python") -> dict:
        return {
            "status": "inspected",
            "result": self.result.model_dump(mode=mode),
        }

def test_unwritable_artifact_root_blocks_execution(
    settings: MCPSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def should_not_run(*args, **kwargs):
        nonlocal called
        called = True
        return Inspected()

    monkeypatch.setattr(
        workflow,
        "inspect_vector_dataset",
        should_not_run,
    )

    monkeypatch.setattr(
        workflow.os,
        "access",
        lambda *args, **kwargs: False,
    )

    with pytest.raises(
        workflow.WorkflowError,
        match="root is not writable",
    ):
        workflow.run_vector_postgis_workflow(
            path=Path(
                "data/input/sample_points.geojson"
            ),
            target_schema="agent_sandbox",
            target_table="must_not_execute",
            original_request="Do not execute.",
            task_id="unwritable-root",
            settings=settings,
        )

    assert called is False

@pytest.fixture
def settings(tmp_path: Path) -> MCPSettings:
    return MCPSettings(
        input_root=tmp_path / "input",
        output_root=tmp_path / "output",
        trace_root=tmp_path / "traces",
        report_root=tmp_path / "reports",
        enable_write_tools=True,
        allow_overwrite=False,
        allowed_schemas=frozenset({"agent_sandbox"}),
    )


def successful_load() -> LoadVectorResult:
    return LoadVectorResult(
        source="data/input/sample_points.geojson",
        source_layer="sample_points",
        target_schema="agent_sandbox",
        target_table="workflow_points",
        row_count=2,
        geometry_column="geometry",
        srid=4326,
        validation_required=True,
        warnings=[],
    )


def successful_validation() -> PostGISValidationResult:
    return PostGISValidationResult(
        status="validation_passed",
        passed=True,
        target_schema="agent_sandbox",
        target_table="workflow_points",
        table_exists=True,
        geometry_column_exists=True,
        geometry_column="geometry",
        row_count=2,
        srid=4326,
        geometry_type="POINT",
        invalid_geometry_count=0,
        null_geometry_count=0,
        extent=LayerExtent(
            min_x=-71.1,
            min_y=42.3,
            max_x=-71.0,
            max_y=42.4,
        ),
        checks=[],
        warnings=[],
    )


def test_successful_workflow_writes_artifacts(
    settings: MCPSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        workflow,
        "inspect_vector_dataset",
        lambda *args, **kwargs: Inspected(),
    )

    monkeypatch.setattr(
        workflow,
        "plan_load_vector_to_postgis",
        lambda *args, **kwargs: Dumpable(
            {"status": "planned_not_executed"}
        ),
    )

    monkeypatch.setattr(
        workflow,
        "load_vector_to_postgis",
        lambda *args, **kwargs: successful_load(),
    )

    monkeypatch.setattr(
        workflow,
        "validate_postgis_layer",
        lambda *args, **kwargs: successful_validation(),
    )

    result = workflow.run_vector_postgis_workflow(
        path=Path("data/input/sample_points.geojson"),
        target_schema="agent_sandbox",
        target_table="workflow_points",
        original_request="Load and validate sample points.",
        task_id="workflow-success",
        settings=settings,
    )

    assert result.final_status == "validated_success"
    assert result.validation_passed is True
    assert Path(result.report_path).exists()
    assert Path(result.trace_path).exists()


def test_execution_failure_is_traced_and_reported(
    settings: MCPSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        workflow,
        "inspect_vector_dataset",
        lambda *args, **kwargs: Inspected(),
    )

    monkeypatch.setattr(
        workflow,
        "plan_load_vector_to_postgis",
        lambda *args, **kwargs: Dumpable(
            {"status": "planned_not_executed"}
        ),
    )

    def fail_load(*args, **kwargs):
        raise RuntimeError(
            "password=must-not-appear"
        )

    monkeypatch.setattr(
        workflow,
        "load_vector_to_postgis",
        fail_load,
    )

    result = workflow.run_vector_postgis_workflow(
        path=Path("data/input/sample_points.geojson"),
        target_schema="agent_sandbox",
        target_table="workflow_points",
        original_request="Test a failed workflow.",
        task_id="workflow-failure",
        settings=settings,
    )

    assert result.final_status == "execution_failed"
    assert result.validation_passed is False

    trace = Path(result.trace_path).read_text(
        encoding="utf-8"
    )

    report = Path(result.report_path).read_text(
        encoding="utf-8"
    )

    assert "must-not-appear" not in trace
    assert "must-not-appear" not in report
    assert "[REDACTED]" in trace
    assert "[REDACTED]" in report


def test_existing_artifacts_block_workflow_before_execution(
    settings: MCPSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings.report_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = (
        settings.report_root
        / "existing-task.md"
    )

    existing.write_text(
        "existing",
        encoding="utf-8",
    )

    called = False

    def should_not_run(*args, **kwargs):
        nonlocal called
        called = True
        return Inspected()

    monkeypatch.setattr(
        workflow,
        "inspect_vector_dataset",
        should_not_run,
    )

    with pytest.raises(
        workflow.WorkflowError,
        match="overwriting is blocked",
    ):
        workflow.run_vector_postgis_workflow(
            path=Path(
                "data/input/sample_points.geojson"
            ),
            target_schema="agent_sandbox",
            target_table="workflow_points",
            original_request="Do not execute.",
            task_id="existing-task",
            settings=settings,
        )

    assert called is False