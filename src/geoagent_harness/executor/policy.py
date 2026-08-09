"""Translate an approved plan into one fixed execution envelope."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from geoagent_harness.approvals import (
    ApprovalRecord,
    plan_sha256,
    verify_approval,
)
from geoagent_harness.executor.schemas import (
    ExecutionEnvelope,
    WorkflowToolArguments,
)
from geoagent_harness.planner.policy import (
    validate_plan_policy,
)
from geoagent_harness.planner.schemas import (
    PlannerResult,
    PlanStep,
)
from geoagent_harness.trace import (
    redact_text,
    validate_task_id,
)

SUPPORTED_SKILL_SEQUENCE = (
    "inspect_vector",
    "load_vector_to_postgis",
    "validate_postgis_layer",
    "generate_report",
)

ALLOWED_ARGUMENTS = {
    "inspect_vector": {
        "path",
    },
    "load_vector_to_postgis": {
        "path",
        "source_layer",
        "target_schema",
        "target_table",
    },
    "validate_postgis_layer": {
        "target_schema",
        "target_table",
    },
    "generate_report": {
        "task_id",
    },
}

_IDENTIFIER = re.compile(
    r"^[a-z_][a-z0-9_]{0,62}$"
)


class ExecutorPolicyError(ValueError):
    """Raised when a plan cannot become an execution request."""


def _safe_relative_input_path(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExecutorPolicyError(
            "vector path must be a non-empty string"
        )

    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)

    if path.is_absolute() or ".." in path.parts:
        raise ExecutorPolicyError(
            "vector path must remain beneath data/input"
        )

    if path.parts[:2] != ("data", "input"):
        raise ExecutorPolicyError(
            "vector path must remain beneath data/input"
        )

    if len(path.parts) < 3:
        raise ExecutorPolicyError(
            "vector path must identify an input file"
        )

    return path.as_posix()


def _safe_identifier(
    value: object,
    *,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or not _IDENTIFIER.fullmatch(value)
    ):
        raise ExecutorPolicyError(
            f"{label} is not a safe identifier"
        )

    return value


def _check_argument_allowlist(
    step: PlanStep,
) -> None:
    allowed = ALLOWED_ARGUMENTS[step.skill]
    unexpected = (
        set(step.arguments)
        - allowed
    )

    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise ExecutorPolicyError(
            f"{step.skill} contains unsupported "
            f"arguments: {names}"
        )


def build_execution_envelope(
    *,
    planner_result: PlannerResult,
    approval: ApprovalRecord,
    allowed_schemas: set[str] | frozenset[str],
) -> ExecutionEnvelope:
    """Build a non-executed request for the fixed workflow tool."""

    validate_plan_policy(
        planner_result.plan,
        available_skills=set(
            SUPPORTED_SKILL_SEQUENCE
        ),
    )

    skills = tuple(
        step.skill
        for step in planner_result.plan.steps
    )

    if skills != SUPPORTED_SKILL_SEQUENCE:
        raise ExecutorPolicyError(
            "plan does not match the supported vertical slice"
        )

    steps = {
        step.skill: step
        for step in planner_result.plan.steps
    }

    for step in planner_result.plan.steps:
        _check_argument_allowlist(step)

    inspect_step = steps["inspect_vector"]
    load_step = steps["load_vector_to_postgis"]
    validate_step = steps["validate_postgis_layer"]
    report_step = steps["generate_report"]

    inspect_path = _safe_relative_input_path(
        inspect_step.arguments["path"]
    )
    load_path = _safe_relative_input_path(
        load_step.arguments["path"]
    )

    if inspect_path != load_path:
        raise ExecutorPolicyError(
            "inspection and loading paths do not match"
        )

    target_schema = _safe_identifier(
        load_step.arguments["target_schema"],
        label="target_schema",
    )
    target_table = _safe_identifier(
        load_step.arguments["target_table"],
        label="target_table",
    )

    if target_schema not in allowed_schemas:
        raise ExecutorPolicyError(
            "target schema is not allowed"
        )

    validation_schema = _safe_identifier(
        validate_step.arguments["target_schema"],
        label="validation target_schema",
    )
    validation_table = _safe_identifier(
        validate_step.arguments["target_table"],
        label="validation target_table",
    )

    if (
        validation_schema != target_schema
        or validation_table != target_table
    ):
        raise ExecutorPolicyError(
            "loading and validation targets do not match"
        )

    task_id_value = report_step.arguments["task_id"]

    if not isinstance(task_id_value, str):
        raise ExecutorPolicyError(
            "task_id must be a string"
        )

    try:
        task_id = validate_task_id(task_id_value)
    except Exception as exc:
        raise ExecutorPolicyError(
            "task_id is invalid"
        ) from exc

    source_layer_value = load_step.arguments.get(
        "source_layer"
    )

    if (
        source_layer_value is not None
        and not isinstance(source_layer_value, str)
    ):
        raise ExecutorPolicyError(
            "source_layer must be a string or null"
        )

    required_step_ids = [
        step.step_id
        for step in planner_result.plan.steps
        if step.requires_approval
    ]

    verification = verify_approval(
        approval=approval,
        plan=planner_result.plan,
        required_step_ids=required_step_ids,
    )

    if not verification.approved:
        raise ExecutorPolicyError(
            f"plan approval failed: "
            f"{verification.reason}"
        )

    return ExecutionEnvelope(
        plan_sha256=plan_sha256(
            planner_result.plan
        ),
        approval_id=approval.approval_id,
        approved_step_ids=(
            verification.approved_step_ids
        ),
        selected_skills=list(skills),
        tool_arguments=WorkflowToolArguments(
            path=inspect_path,
            source_layer=source_layer_value,
            target_schema=target_schema,
            target_table=target_table,
            original_request=redact_text(
                planner_result.original_request
            ),
            task_id=task_id,
            context_references=(
                planner_result.context_references
            ),
            human_corrections=(
                approval.human_corrections
            ),
        ),
        execution_performed=False,
    )