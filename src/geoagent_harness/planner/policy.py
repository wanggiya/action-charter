"""Deterministic policy checks for untrusted model plans."""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from collections.abc import Collection

from geoagent_harness.planner.schemas import WorkflowPlan
from geoagent_harness.planner.topology import plan_dependencies, plan_topological_order, ancestors

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
    "export_snakemake_workflow",
    "convert_vector",
    "load_vector_to_postgis",
    "generate_report",
}

REQUIRED_SKILL_ARGUMENTS = {
    "export_snakemake_workflow": {"source_plan_filename", "source_plan_sha256"},
    "inspect_vector": {
        "path",
    },
    "convert_vector": {
        "path",
        "target_path",
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


def normalize_plan_input_filenames(plan: WorkflowPlan) -> None:
    """Resolve model-proposed bare input filenames before policy and hashing."""
    for step in plan.steps:
        value = step.arguments.get("path")
        if isinstance(value, str) and value and "/" not in value and "\\" not in value and value not in {".", ".."}:
            step.arguments["path"] = "data/input/" + value


def _validate_argument_paths(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "path" or key.endswith("_path"):
                if not isinstance(item, str) or not item or len(item) > 960:
                    raise PlannerPolicyError("file paths must be bounded normalized relative paths")
                parsed = PurePosixPath(item)
                if (parsed.is_absolute() or ".." in parsed.parts or "\\" in item
                        or any(ord(char) < 32 for char in item) or str(parsed) != item
                        or item in {".", ".."}):
                    raise PlannerPolicyError("file paths must be safe normalized relative paths")
            _validate_argument_paths(item)
    elif isinstance(value, list):
        for item in value:
            _validate_argument_paths(item)


def validate_plan_policy(
    plan: WorkflowPlan,
    *,
    available_skills: Collection[str],
) -> None:
    """Reject unapproved, unsafe, or unverifiable plans."""

    allowed = set(available_skills)
    try:
        dependencies = plan_dependencies(plan)
        ordered_ids = plan_topological_order(plan)
    except ValueError as error:
        raise PlannerPolicyError(str(error)) from error
    by_id = {step.step_id: step for step in plan.steps}

    for step in plan.steps:
        _validate_argument_paths(step.arguments)
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

    export_steps = [step for step in plan.steps if step.skill == "export_snakemake_workflow"]
    verify_steps = [step for step in plan.steps if step.skill == "verify_snakemake_export"]
    if export_steps or verify_steps:
        if len(export_steps) != 1 or len(verify_steps) != 1:
            raise PlannerPolicyError("Snakemake export requires exactly one export and one verification step")
        export, verify = export_steps[0], verify_steps[0]
        if not export.validation_required or not verify.validation_required:
            raise PlannerPolicyError("Snakemake export and verification must require static validation")
        if export.step_id not in ancestors(verify.step_id, dependencies) or ordered_ids[-2:] != [export.step_id, verify.step_id]:
            raise PlannerPolicyError("Snakemake verification must follow export at the end of the workflow")

    skill_order = [by_id[step_id].skill for step_id in ordered_ids]

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
        preceding = ancestors(step.step_id, dependencies)
        if step.skill == "load_vector_to_postgis":
            if not any(by_id[parent].skill == "inspect_vector" for parent in preceding):
                raise PlannerPolicyError("PostGIS loading must depend on vector inspection")
            if not any(candidate.skill == "validate_postgis_layer" and step.step_id in ancestors(candidate.step_id, dependencies) for candidate in plan.steps):
                raise PlannerPolicyError("PostGIS loading must be followed by dependent deterministic validation")
        if step.skill == "generate_report" and not any(by_id[parent].skill == "validate_postgis_layer" for parent in preceding):
            raise PlannerPolicyError("report generation must depend on validation")
        if step.skill == "validate_postgis_layer":
            if not step.validation_required:
                raise PlannerPolicyError(
                    "validation step must set "
                    "validation_required=true"
                )
