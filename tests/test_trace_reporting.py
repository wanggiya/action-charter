import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from geoagent_harness.reporting import (
    render_report,
    write_report,
)
from geoagent_harness.trace import (
    TraceError,
    TraceTimestamps,
    WorkflowTrace,
    redact_text,
    write_trace,
)


def make_trace() -> WorkflowTrace:
    started = datetime(
        2026,
        8,
        4,
        12,
        0,
        tzinfo=timezone.utc,
    )

    finished = datetime(
        2026,
        8,
        4,
        12,
        1,
        tzinfo=timezone.utc,
    )

    return WorkflowTrace(
        task_id="task-3e-test",
        original_request=(
            "Load sample data with password=unsafe-value"
        ),
        context_references=[
            "context/PROJECT_SUMMARY.md",
            "context/SKILLS_INDEX.yaml",
        ],
        selected_skills=[
            "inspect_vector",
            "load_vector_to_postgis",
            "validate_postgis_layer",
            "generate_report",
        ],
        tool_arguments={
            "load_vector_to_postgis": {
                "path": "data/input/sample_points.geojson",
                "target_schema": "agent_sandbox",
                "target_table": "sample_points",
                "password": "must-not-survive",
            }
        },
        tool_results={
            "load_vector_to_postgis": {
                "status": "loaded_pending_validation",
                "row_count": 2,
            }
        },
        validation_results={
            "status": "validation_passed",
            "passed": True,
            "target_schema": "agent_sandbox",
            "target_table": "sample_points",
            "table_exists": True,
            "geometry_column_exists": True,
            "geometry_column": "geometry",
            "row_count": 2,
            "srid": 4326,
            "geometry_type": "POINT",
            "invalid_geometry_count": 0,
            "null_geometry_count": 0,
            "extent": {
                "min_x": -71.1,
                "min_y": 42.3,
                "max_x": -71.0,
                "max_y": 42.4,
            },
            "checks": [
                {
                    "name": "table_exists",
                    "passed": True,
                    "expected": True,
                    "actual": True,
                }
            ],
        },
        artifacts=[
            "reports/task-3e-test.md",
            "traces/task-3e-test.json",
        ],
        warnings=[],
        final_status="validated_success",
        timestamps=TraceTimestamps(
            started_at=started,
            finished_at=finished,
        ),
        versions={
            "python": "3.11",
            "container_image": "geoagent-gis-tools:local",
        },
    )


def test_redact_text() -> None:
    value = (
        "password=hello token:world "
        "postgresql://user:secret@postgis/geoagent"
    )

    redacted = redact_text(value)

    assert "hello" not in redacted
    assert "world" not in redacted
    assert ":secret@" not in redacted
    assert "[REDACTED]" in redacted


def test_trace_is_redacted(
    tmp_path: Path,
) -> None:
    path = write_trace(
        make_trace(),
        trace_root=tmp_path / "traces",
    )

    payload = path.read_text(encoding="utf-8")

    assert "unsafe-value" not in payload
    assert "must-not-survive" not in payload
    assert "[REDACTED]" in payload

    parsed = json.loads(payload)

    assert parsed["final_status"] == "validated_success"
    assert parsed["secrets_redacted"] is True


def test_report_is_redacted() -> None:
    report = render_report(make_trace())

    assert "unsafe-value" not in report
    assert "must-not-survive" not in report
    assert "[REDACTED]" in report
    assert "validation_passed" in report


def test_report_is_written(
    tmp_path: Path,
) -> None:
    path = write_report(
        make_trace(),
        report_root=tmp_path / "reports",
    )

    assert path.exists()
    assert path.suffix == ".md"


def test_trace_refuses_overwrite(
    tmp_path: Path,
) -> None:
    trace = make_trace()
    root = tmp_path / "traces"

    write_trace(trace, trace_root=root)

    with pytest.raises(
        TraceError,
        match="already exists",
    ):
        write_trace(trace, trace_root=root)


def test_report_refuses_overwrite(
    tmp_path: Path,
) -> None:
    trace = make_trace()
    root = tmp_path / "reports"

    write_report(trace, report_root=root)

    with pytest.raises(
        TraceError,
        match="already exists",
    ):
        write_report(trace, report_root=root)


@pytest.mark.parametrize(
    "task_id",
    [
        "../escape",
        "UPPERCASE",
        "bad task",
        "/absolute",
        "task.json",
    ],
)
def test_unsafe_task_id_is_rejected(
    tmp_path: Path,
    task_id: str,
) -> None:
    trace = make_trace().model_copy(
        update={"task_id": task_id}
    )

    with pytest.raises(TraceError):
        write_trace(
            trace,
            trace_root=tmp_path,
        )