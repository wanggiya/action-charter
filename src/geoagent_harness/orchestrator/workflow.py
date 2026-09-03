"""End-to-end validated vector-to-PostGIS workflow."""

from __future__ import annotations

import os

import platform
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from geoagent_harness.mcp_server.settings import MCPSettings
from geoagent_harness.mcp_server.tools import (
    inspect_vector_dataset,
    load_vector_to_postgis,
    plan_load_vector_to_postgis,
    validate_postgis_layer,
)
from geoagent_harness.reporting import write_report
from geoagent_harness.failures import (
    FailureCategory,
    FailureRecord,
    FailureStage,
    GeoAgentError,
    RetryDisposition,
    failure_from_exception,
)
from geoagent_harness.trace import (
    TraceError,
    TraceTimestamps,
    WorkflowTrace,
    artifact_path,
    write_trace,
)

class WorkflowError(RuntimeError):
    """Raised when a workflow cannot safely begin or finish."""


class WorkflowRunResult(BaseModel):
    """Compact result returned to the CLI."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    final_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
    ]
    validation_passed: bool
    report_path: str
    trace_path: str
    warnings: list[str]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_task_id() -> str:
    timestamp = _now().strftime("%Y%m%d-%H%M%S")

    return (
        f"task-{timestamp}-"
        f"{uuid.uuid4().hex[:8]}"
    )


def _package_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "not-installed"


def _versions(settings: MCPSettings) -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "actioncharter": _package_version(
            "actioncharter"
        ),
        "geopandas": _package_version("geopandas"),
        "psycopg": _package_version("psycopg"),
        "pyogrio": _package_version("pyogrio"),
        "sqlalchemy": _package_version("sqlalchemy"),
        "container_image": settings.container_image,
        "mcp": _package_version("mcp"),
    }


def _ensure_artifacts_available(
    *,
    task_id: str,
    settings: MCPSettings,
) -> tuple[Path, Path]:
    for root, label in (
        (settings.report_root, "report"),
        (settings.trace_root, "trace"),
    ):
        try:
            root.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as exc:
            raise WorkflowError(
                f"{label} root could not be prepared"
            ) from exc

        if not os.access(root, os.W_OK):
            raise WorkflowError(
                f"{label} root is not writable"
            )

    report_path = artifact_path(
        root=settings.report_root,
        task_id=task_id,
        suffix=".md",
    )

    trace_path = artifact_path(
        root=settings.trace_root,
        task_id=task_id,
        suffix=".json",
    )

    existing = [
        path.as_posix()
        for path in (report_path, trace_path)
        if path.exists()
    ]

    if existing:
        raise WorkflowError(
            "workflow artifact already exists; "
            "overwriting is blocked: "
            + ", ".join(existing)
        )

    return report_path, trace_path


def run_vector_postgis_workflow(
    *,
    path: Path,
    target_schema: str,
    target_table: str,
    original_request: str,
    settings: MCPSettings,
    source_layer: str | None = None,
    task_id: str | None = None,
    context_references: list[str] | None = None,
    human_corrections: list[str] | None = None,
    plan_sha256: str | None = None,
    approval_id: str | None = None,
    approved_step_ids: list[str] | None = None,
) -> WorkflowRunResult:
    """Run inspect, plan, load, validate, report, and trace."""
    active_task_id = task_id or _generate_task_id()

    report_path, trace_path = _ensure_artifacts_available(
        task_id=active_task_id,
        settings=settings,
    )

    started_at = _now()

    references = context_references or [
        "context/PROJECT_SUMMARY.md",
        "context/ARCHITECTURE.md",
        "context/SKILLS_INDEX.yaml",
        "context/CURRENT_STATUS.md",
    ]

    selected_skills = [
        "inspect_vector",
        "load_vector_to_postgis",
        "validate_postgis_layer",
        "generate_report",
    ]

    tool_arguments = {
        "inspect_vector_dataset": {
            "path": path.as_posix(),
        },
        "plan_load_vector_to_postgis": {
            "path": path.as_posix(),
            "target_schema": target_schema,
            "target_table": target_table,
        },
        "load_vector_to_postgis": {
            "path": path.as_posix(),
            "source_layer": source_layer,
            "target_schema": target_schema,
            "target_table": target_table,
        },
        "validate_postgis_layer": {
            "target_schema": target_schema,
            "target_table": target_table,
        },
    }

    tool_results: dict[str, object] = {}
    validation_results: dict[str, object] | None = None
    failure_record: FailureRecord | None = None
    active_stage = FailureStage.EXECUTION
    warnings: list[str] = []
    validation_passed = False
    final_status: Literal[
        "validated_success",
        "validation_failed",
        "execution_failed",
    ]

    try:
        inspected = inspect_vector_dataset(
            path.as_posix(),
            settings=settings,
        )

        tool_results["inspect_vector_dataset"] = (
            inspected.model_dump(mode="json")
        )

        plan = plan_load_vector_to_postgis(
            path=path.as_posix(),
            target_schema=target_schema,
            target_table=target_table,
            settings=settings,
        )

        tool_results["plan_load_vector_to_postgis"] = (
            plan.model_dump(mode="json")
        )

        loaded = load_vector_to_postgis(
            path=path.as_posix(),
            source_layer=source_layer,
            target_schema=target_schema,
            target_table=target_table,
            settings=settings,
        )

        tool_results["load_vector_to_postgis"] = (
            loaded.model_dump(mode="json")
        )
        
        active_stage = FailureStage.VALIDATION

        validation = validate_postgis_layer(
            target_schema=target_schema,
            target_table=target_table,
            expected_row_count=loaded.row_count,
            expected_srid=loaded.srid,
            expected_geometry_type=(
                inspected.result.layers[0].geometry_type
            ),
            settings=settings,
        )

        validation_results = validation.model_dump(
            mode="json"
        )

        tool_results["validate_postgis_layer"] = (
            validation_results
        )

        validation_passed = validation.passed

        if validation.passed:
            final_status = "validated_success"
        else:
            final_status = "validation_failed"
            warnings.extend(validation.warnings)

            failure_record = failure_from_exception(
                GeoAgentError(
                    (
                        "Deterministic PostGIS validation "
                        "did not pass"
                    ),
                    code="postgis_validation_failed",
                    category=(
                        FailureCategory.VALIDATION_FAILED
                    ),
                    retry=RetryDisposition.MANUAL_REVIEW,
                ),
                stage=FailureStage.VALIDATION,
            )

    except Exception as exc:
        final_status = "execution_failed"

        failure_record = failure_from_exception(
            exc,
            stage=active_stage,
        )

        if (
            failure_record.category
            == FailureCategory.INTERNAL_ERROR
        ):
            failure_record = failure_record.model_copy(
                update={
                    "category": (
                        FailureCategory.EXECUTION_FAILED
                    ),
                    "code": "workflow_execution_failed",
                    "retry": (
                        RetryDisposition.MANUAL_REVIEW
                    ),
                    "exit_code": 4,
                }
            )

        warnings.append(
            failure_record.message
        )

    finished_at = _now()

    trace = WorkflowTrace(
        task_id=active_task_id,
        original_request=original_request,
        context_references=references,
        selected_skills=selected_skills,
        plan_sha256=plan_sha256,
        approval_id=approval_id,
        approved_step_ids=(
            approved_step_ids or []
        ),
        tool_arguments=tool_arguments,
        tool_results=tool_results,
        validation_results=validation_results,
        failure=failure_record,
        artifacts=[
            report_path.as_posix(),
            trace_path.as_posix(),
        ],
        warnings=warnings,
        final_status=final_status,
        human_corrections=human_corrections or [],
        timestamps=TraceTimestamps(
            started_at=started_at,
            finished_at=finished_at,
        ),
        versions=_versions(settings),
    )

    try:
        written_report = write_report(
            trace,
            report_root=settings.report_root,
        )

        written_trace = write_trace(
            trace,
            trace_root=settings.trace_root,
        )
    except TraceError as exc:
        raise WorkflowError(str(exc)) from exc

    return WorkflowRunResult(
        task_id=active_task_id,
        final_status=final_status,
        validation_passed=validation_passed,
        report_path=written_report.as_posix(),
        trace_path=written_trace.as_posix(),
        warnings=warnings,
    )
