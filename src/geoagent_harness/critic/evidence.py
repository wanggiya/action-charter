"""Build a trusted, deterministic evidence pack for the Critic Agent."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.critic.schemas import (
    ApprovalEvidence,
    CriticEvidencePack,
    EvidenceReference,
    ValidationEvidence,
)
from geoagent_harness.trace import (
    WorkflowTrace,
    redact_text,
    redact_value,
)

MAX_TRACE_BYTES = 2 * 1024 * 1024
MAX_REPORT_BYTES = 256 * 1024
MAX_REPORT_EXCERPT = 12_000


class CriticEvidenceError(RuntimeError):
    """Raised when critic evidence is unsafe or contradictory."""


def _approved_path(
    *,
    path: Path,
    root: Path,
    suffix: str,
) -> Path:
    resolved_root = root.resolve()
    candidate = path

    if not candidate.is_absolute():
        if candidate.parts[:1] == (root.name,):
            candidate = resolved_root.parent / candidate
        else:
            candidate = resolved_root / candidate

    resolved = candidate.resolve()

    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise CriticEvidenceError(
            f"evidence path is outside approved {root.name} root"
        ) from exc

    if resolved.suffix.lower() != suffix:
        raise CriticEvidenceError(
            f"evidence file must use the {suffix} suffix"
        )

    if not resolved.is_file():
        raise CriticEvidenceError(
            f"evidence file does not exist: {resolved.name}"
        )

    return resolved


def _read_bounded(
    path: Path,
    *,
    maximum_bytes: int,
) -> str:
    size = path.stat().st_size

    if size > maximum_bytes:
        raise CriticEvidenceError(
            f"evidence file is larger than {maximum_bytes} bytes"
        )

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CriticEvidenceError(
            "evidence file is not valid UTF-8"
        ) from exc


def _reference(
    path: Path,
    *,
    root: Path,
) -> EvidenceReference:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    relative = path.relative_to(root.resolve())

    return EvidenceReference(
        path=(Path(root.name) / relative).as_posix(),
        sha256=digest,
    )


def _optional_bool(
    payload: dict[str, Any],
    key: str,
    gaps: list[str],
) -> bool | None:
    value = payload.get(key)

    if value is None:
        gaps.append(f"validation field {key!r} is missing")
        return None

    if not isinstance(value, bool):
        gaps.append(f"validation field {key!r} is not Boolean")
        return None

    return value


def _optional_int(
    payload: dict[str, Any],
    key: str,
    gaps: list[str],
) -> int | None:
    value = payload.get(key)

    if value is None:
        gaps.append(f"validation field {key!r} is missing")
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        gaps.append(f"validation field {key!r} is not an integer")
        return None

    return value


def _failed_checks(
    validation: dict[str, Any],
) -> list[str]:
    failed: list[str] = []

    checks = validation.get("checks", [])
    if not isinstance(checks, list):
        return failed

    for check in checks:
        if not isinstance(check, dict):
            continue

        if check.get("passed") is False:
            failed.append(
                str(check.get("name", "unnamed_check"))
            )

    return failed


def build_critic_evidence(
    *,
    trace_path: Path,
    report_path: Path,
    trace_root: Path = Path("traces"),
    report_root: Path = Path("reports"),
) -> CriticEvidencePack:
    """Build a concise evidence pack without invoking a model."""

    approved_trace = _approved_path(
        path=trace_path,
        root=trace_root,
        suffix=".json",
    )
    approved_report = _approved_path(
        path=report_path,
        root=report_root,
        suffix=".md",
    )

    trace_text = _read_bounded(
        approved_trace,
        maximum_bytes=MAX_TRACE_BYTES,
    )
    report_text = _read_bounded(
        approved_report,
        maximum_bytes=MAX_REPORT_BYTES,
    )

    try:
        trace = WorkflowTrace.model_validate_json(trace_text)
    except ValidationError as exc:
        raise CriticEvidenceError(
            "trace does not match the WorkflowTrace schema"
        ) from exc

    gaps: list[str] = []

    if trace.secrets_redacted is not True:
        raise CriticEvidenceError(
            "trace does not confirm secret redaction"
        )

    validation_payload = trace.validation_results or {}

    if not isinstance(validation_payload, dict):
        raise CriticEvidenceError(
            "validation_results must be an object"
        )

    validation_passed = _optional_bool(
        validation_payload,
        "passed",
        gaps,
    )

    if (
        trace.final_status == "validated_success"
        and validation_passed is not True
    ):
        raise CriticEvidenceError(
            "trace claims validated success without passing validation"
        )

    if (
        trace.final_status == "validation_failed"
        and validation_passed is True
    ):
        raise CriticEvidenceError(
            "trace claims validation failure but validation passed"
        )

    if (
        trace.final_status == "execution_failed"
        and validation_passed is True
    ):
        raise CriticEvidenceError(
            "execution-failed trace cannot contain passing validation"
        )

    approval_complete = bool(
        trace.approval_id
        and trace.plan_sha256
        and trace.approved_step_ids
    )

    if not approval_complete:
        gaps.append(
            "complete plan-bound approval evidence is missing"
        )

    redacted_report = redact_text(report_text)

    required_report_values = [
        trace.task_id,
        trace.final_status,
    ]

    if trace.approval_id:
        required_report_values.append(trace.approval_id)

    for value in required_report_values:
        if value not in redacted_report:
            gaps.append(
                f"report does not contain required evidence {value!r}"
            )

    if len(redacted_report) > MAX_REPORT_EXCERPT:
        report_excerpt = redacted_report[:MAX_REPORT_EXCERPT]
        gaps.append(
            "report excerpt was truncated for the critic context pack"
        )
    else:
        report_excerpt = redacted_report

    if trace.final_status == "validated_success":
        deterministic_status = (
            "validated_success"
            if not gaps
            else "incomplete_evidence"
        )
    elif trace.final_status == "validation_failed":
        deterministic_status = "validation_failed"
    else:
        deterministic_status = "execution_failed"

    warnings = list(trace.warnings)

    validation_warnings = validation_payload.get(
        "warnings",
        [],
    )
    if isinstance(validation_warnings, list):
        warnings.extend(
            str(item)
            for item in validation_warnings
        )

    validation = ValidationEvidence(
        passed=validation_passed,
        table_exists=_optional_bool(
            validation_payload,
            "table_exists",
            gaps,
        ),
        geometry_column_exists=_optional_bool(
            validation_payload,
            "geometry_column_exists",
            gaps,
        ),
        row_count=_optional_int(
            validation_payload,
            "row_count",
            gaps,
        ),
        srid=_optional_int(
            validation_payload,
            "srid",
            gaps,
        ),
        geometry_type=(
            str(validation_payload["geometry_type"])
            if validation_payload.get("geometry_type") is not None
            else None
        ),
        invalid_geometry_count=_optional_int(
            validation_payload,
            "invalid_geometry_count",
            gaps,
        ),
        null_geometry_count=_optional_int(
            validation_payload,
            "null_geometry_count",
            gaps,
        ),
        extent=redact_value(
            validation_payload.get("extent")
        ),
        failed_checks=_failed_checks(
            validation_payload
        ),
    )

    if (
        deterministic_status == "validated_success"
        and gaps
    ):
        deterministic_status = "incomplete_evidence"

    timestamps = {
        key: str(value)
        for key, value in trace.timestamps.model_dump(
            mode="json"
        ).items()
    }

    return CriticEvidencePack(
        task_id=trace.task_id,
        original_request=redact_text(
            trace.original_request
        ),
        deterministic_status=deterministic_status,
        trace_final_status=trace.final_status,
        validation_passed=validation_passed,
        selected_skills=list(trace.selected_skills),
        validation=validation,
        approval=ApprovalEvidence(
            approval_id=trace.approval_id,
            plan_sha256=trace.plan_sha256,
            approved_step_ids=list(
                trace.approved_step_ids
            ),
            complete=approval_complete,
        ),
        artifacts=[
            redact_text(item)
            for item in trace.artifacts
        ],
        warnings=[
            redact_text(item)
            for item in warnings
        ],
        human_corrections=[
            redact_text(item)
            for item in trace.human_corrections
        ],
        evidence_gaps=gaps,
        timestamps=timestamps,
        versions={
            key: redact_text(str(value))
            for key, value in trace.versions.items()
        },
        report_excerpt=report_excerpt,
        evidence_references=[
            _reference(
                approved_trace,
                root=trace_root,
            ),
            _reference(
                approved_report,
                root=report_root,
            ),
        ],
    )