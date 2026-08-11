"""Deterministic Markdown workflow reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geoagent_harness.trace import (
    TraceError,
    WorkflowTrace,
    artifact_path,
    redact_value,
)


def _markdown(value: Any) -> str:
    """Escape a value for a compact Markdown table."""
    if value is None:
        return ""

    return (
        str(value)
        .replace("|", r"\|")
        .replace("\n", " ")
    )


def render_report(trace: WorkflowTrace) -> str:
    """Render a report strictly from structured trace data."""
    payload = redact_value(
        trace.model_dump(mode="json")
    )

    validation = (
        payload.get("validation_results")
        or {}
    )
    failure = payload.get("failure")

    lines = [
        f"# GeoAgent Task Report: {payload['task_id']}",
        "",
        f"- Final status: `{payload['final_status']}`",
        (
            "- Started: "
            f"`{payload['timestamps']['started_at']}`"
        ),
        (
            "- Finished: "
            f"`{payload['timestamps']['finished_at']}`"
        ),
        "- Secrets redacted: `true`",
        "",
        "## Original request",
        "",
        _markdown(payload["original_request"]),
        "",
        "## Selected skills",
        "",
    ]

    for skill in payload["selected_skills"]:
        lines.append(f"- `{_markdown(skill)}`")
    
    lines.extend(
        [
            "",
            "## Approval evidence",
            "",
            (
                "- Plan SHA-256: "
                f"`{_markdown(payload.get('plan_sha256'))}`"
            ),
            (
                "- Approval ID: "
                f"`{_markdown(payload.get('approval_id'))}`"
            ),
            "- Approved steps:",
        ]
    )

    approved_steps = payload.get(
        "approved_step_ids",
        [],
    )

    if approved_steps:
        for step_id in approved_steps:
            lines.append(
                f"  - `{_markdown(step_id)}`"
            )
    else:
        lines.append("  - None recorded")

    lines.extend(
        [
            "",
            "## Context references",
            "",
        ]
    )

    for reference in payload["context_references"]:
        lines.append(f"- `{_markdown(reference)}`")

    lines.extend(
        [
            "",
            "## Validation summary",
            "",
            "| Fact | Value |",
            "|---|---|",
        ]
    )

    summary_fields = [
        "status",
        "passed",
        "target_schema",
        "target_table",
        "table_exists",
        "geometry_column_exists",
        "geometry_column",
        "row_count",
        "srid",
        "geometry_type",
        "invalid_geometry_count",
        "null_geometry_count",
        "extent",
    ]

    for field in summary_fields:
        if field in validation:
            lines.append(
                f"| {_markdown(field)} "
                f"| {_markdown(validation[field])} |"
            )

    checks = validation.get("checks", [])

    lines.extend(
        [
            "",
            "## Deterministic checks",
            "",
            "| Check | Passed | Expected | Actual |",
            "|---|---:|---|---|",
        ]
    )

    for check in checks:
        lines.append(
            "| "
            f"{_markdown(check.get('name'))} | "
            f"{_markdown(check.get('passed'))} | "
            f"{_markdown(check.get('expected'))} | "
            f"{_markdown(check.get('actual'))} |"
        )
    lines.extend(
        [
            "",
            "## Failure evidence",
            "",
        ]
    )

    if failure:
        lines.extend(
            [
                "| Fact | Value |",
                "|---|---|",
                (
                    "| Category | "
                    f"{_markdown(failure['category'])} |"
                ),
                (
                    "| Code | "
                    f"{_markdown(failure['code'])} |"
                ),
                (
                    "| Stage | "
                    f"{_markdown(failure['stage'])} |"
                ),
                (
                    "| Message | "
                    f"{_markdown(failure['message'])} |"
                ),
                (
                    "| Retry | "
                    f"{_markdown(failure['retry'])} |"
                ),
                (
                    "| Exit code | "
                    f"{_markdown(failure['exit_code'])} |"
                ),
                (
                    "| Cause type | "
                    f"{_markdown(failure['cause_type'])} |"
                ),
                "| Secrets redacted | true |",
            ]
        )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
        ]
    )

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
        ]
    )

    for artifact in payload["artifacts"]:
        lines.append(f"- `{_markdown(artifact)}`")

    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )

    if payload["warnings"]:
        for warning in payload["warnings"]:
            lines.append(f"- {_markdown(warning)}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Human corrections",
            "",
        ]
    )

    if payload["human_corrections"]:
        for correction in payload["human_corrections"]:
            lines.append(
                f"- {_markdown(correction)}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Software and container versions",
            "",
            "| Component | Version |",
            "|---|---|",
        ]
    )

    for component, version in sorted(
        payload["versions"].items()
    ):
        lines.append(
            f"| {_markdown(component)} "
            f"| {_markdown(version)} |"
        )

    lines.extend(
        [
            "",
            (
                "Final success is reported only when all "
                "deterministic validation checks pass."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def write_report(
    trace: WorkflowTrace,
    *,
    report_root: Path,
) -> Path:
    """Write one Markdown report without overwriting."""
    path = artifact_path(
        root=report_root,
        task_id=trace.task_id,
        suffix=".md",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = render_report(trace)

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise TraceError(
            f"report already exists for task "
            f"{trace.task_id!r}"
        ) from exc

    return path