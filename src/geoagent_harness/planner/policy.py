"""Deterministic policy checks for untrusted model plans."""

from __future__ import annotations

import json
import re
from collections.abc import Collection

from geoagent_harness.planner.schemas import WorkflowPlan

FORBIDDEN_ARGUMENT_KEYS = {
    "command",
    "shell",
    "shell_command",
    "sql",
    "query",
    "database_url",
    "connection_string",
    "password",
    "token",
    "secret",
    "api_key",
}

FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"(?i)\b(drop|delete|truncate)\s+"
               r"(table|schema|database|from)\b"),
    re.compile(r"(?i)\brm\s+-[a-z]*r[a-z]*f\b"),
    re.compile(r"(?i)\bsudo\b"),
    re.compile(r"(?i)\bos\.system\b"),
    re.compile(r"(?i)\bsubprocess\b"),
)

WRITE_SKILLS = {
    "convert_vector",
    "load_vector_to_postgis",
    "generate_report",
}

REQUIRED_SKILL_ARGUMENTS = {
    "inspect_vector": {
        "path",
    },
    "load_vector_to_postgis": {
        "path",
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

class PlannerPolicyError(ValueError):
    """Raised when a model-generated plan violates policy."""


def _argument_keys(value: object) -> set[str]:
    keys: set[str] = set()

    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key).lower())
            keys.update(_argument_keys(item))

    elif isinstance(value, list):
        for item in value:
            keys.update(_argument_keys(item))

    return keys


def validate_plan_policy(
    plan: WorkflowPlan,
    *,
    available_skills: Collection[str],
) -> None:
    """Reject unapproved, unsafe, or unverifiable plans."""

    allowed = set(available_skills)

    for step in plan.steps:
        if step.skill not in allowed:
            raise PlannerPolicyError(
                f"skill is not implemented and approved: "
                f"{step.skill}"
            )
        required_arguments = (
            REQUIRED_SKILL_ARGUMENTS.get(
                step.skill,
                set(),
            )
        )

        missing_arguments = {
            name
            for name in required_arguments
            if (
                name not in step.arguments
                or step.arguments[name] is None
                or (
                    isinstance(
                        step.arguments[name],
                        str,
                    )
                    and not step.arguments[name].strip()
                )
            )
        }

        if missing_arguments:
            names = ", ".join(
                sorted(missing_arguments)
            )
            raise PlannerPolicyError(
                f"{step.skill} is missing required "
                f"arguments: {names}"
            )

        unsafe_keys = (
            _argument_keys(step.arguments)
            & FORBIDDEN_ARGUMENT_KEYS
        )

        if unsafe_keys:
            names = ", ".join(sorted(unsafe_keys))
            raise PlannerPolicyError(
                f"forbidden argument keys: {names}"
            )

        serialized = json.dumps(
            step.model_dump(mode="json"),
            sort_keys=True,
        )

        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(serialized):
                raise PlannerPolicyError(
                    "plan contains a forbidden destructive "
                    "or shell operation"
                )

        if (
            step.skill in WRITE_SKILLS
            and not step.requires_approval
        ):
            raise PlannerPolicyError(
                f"{step.skill} must require approval"
            )

    skill_order = [
        step.skill
        for step in plan.steps
    ]

    if "load_vector_to_postgis" in skill_order:
        load_index = skill_order.index(
            "load_vector_to_postgis"
        )

        if "inspect_vector" not in skill_order[:load_index]:
            raise PlannerPolicyError(
                "PostGIS loading must follow vector inspection"
            )

        if (
            "validate_postgis_layer"
            not in skill_order[load_index + 1:]
        ):
            raise PlannerPolicyError(
                "PostGIS loading must be followed by "
                "deterministic validation"
            )

    if "generate_report" in skill_order:
        report_index = skill_order.index("generate_report")

        if (
            "validate_postgis_layer"
            not in skill_order[:report_index]
        ):
            raise PlannerPolicyError(
                "report generation must follow validation"
            )

    for step in plan.steps:
        if step.skill == "validate_postgis_layer":
            if not step.validation_required:
                raise PlannerPolicyError(
                    "validation step must set "
                    "validation_required=true"
                )