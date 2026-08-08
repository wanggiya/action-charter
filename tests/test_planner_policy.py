import pytest

from geoagent_harness.planner.policy import (
    PlannerPolicyError,
    validate_plan_policy,
)
from geoagent_harness.planner.schemas import WorkflowPlan

ALLOWED = {
    "inspect_vector",
    "load_vector_to_postgis",
    "validate_postgis_layer",
    "generate_report",
}

SAFE_ARGUMENTS = {
    "inspect_vector": {
        "path": "data/input/sample_points.geojson",
    },
    "load_vector_to_postgis": {
        "path": "data/input/sample_points.geojson",
        "target_schema": "agent_sandbox",
        "target_table": "sample_points",
    },
    "validate_postgis_layer": {
        "target_schema": "agent_sandbox",
        "target_table": "sample_points",
    },
    "generate_report": {
        "task_id": "sample-points",
    },
}


def make_plan(
    steps: list[dict],
) -> WorkflowPlan:
    return WorkflowPlan.model_validate(
        {
            "schema_version": "1.0",
            "status": "planned",
            "summary": "Test plan.",
            "steps": steps,
            "assumptions": [],
            "risks": [],
            "execution_performed": False,
            "validation_performed": False,
        }
    )


def step(
    number: int,
    skill: str,
    *,
    approval: bool = False,
    validation: bool = False,
    arguments: dict | None = None,
) -> dict:
    return {
        "step_id": f"step_{number}",
        "skill": skill,
        "purpose": f"Use {skill}.",
        "arguments": (
            arguments
            if arguments is not None
            else SAFE_ARGUMENTS.get(skill, {})
        ),
        "requires_approval": approval,
        "expected_artifacts": [],
        "validation_required": validation,
    }


def test_accepts_safe_vertical_slice_plan() -> None:
    plan = make_plan(
        [
            step(1, "inspect_vector"),
            step(
                2,
                "load_vector_to_postgis",
                approval=True,
            ),
            step(
                3,
                "validate_postgis_layer",
                validation=True,
            ),
            step(
                4,
                "generate_report",
                approval=True,
            ),
        ]
    )

    validate_plan_policy(
        plan,
        available_skills=ALLOWED,
    )


def test_rejects_unimplemented_skill() -> None:
    plan = make_plan(
        [
            step(1, "run_arbitrary_command"),
        ]
    )

    with pytest.raises(
        PlannerPolicyError,
        match="not implemented",
    ):
        validate_plan_policy(
            plan,
            available_skills=ALLOWED,
        )


def test_rejects_sql_argument() -> None:
    plan = make_plan(
        [
            step(
                1,
                "inspect_vector",
                arguments={
                    "path": (
                        "data/input/sample_points.geojson"
                    ),
                    "sql": "select * from users",
                },
            ),
        ]
    )

    with pytest.raises(
        PlannerPolicyError,
        match="forbidden argument",
    ):
        validate_plan_policy(
            plan,
            available_skills=ALLOWED,
        )


def test_requires_approval_for_writes() -> None:
    plan = make_plan(
        [
            step(1, "inspect_vector"),
            step(
                2,
                "load_vector_to_postgis",
                approval=False,
            ),
            step(
                3,
                "validate_postgis_layer",
                validation=True,
            ),
        ]
    )

    with pytest.raises(
        PlannerPolicyError,
        match="require approval",
    ):
        validate_plan_policy(
            plan,
            available_skills=ALLOWED,
        )


def test_requires_validation_after_load() -> None:
    plan = make_plan(
        [
            step(1, "inspect_vector"),
            step(
                2,
                "load_vector_to_postgis",
                approval=True,
            ),
        ]
    )

    with pytest.raises(
        PlannerPolicyError,
        match="followed by",
    ):
        validate_plan_policy(
            plan,
            available_skills=ALLOWED,
        )


def test_report_must_follow_validation() -> None:
    plan = make_plan(
        [
            step(
                1,
                "generate_report",
                approval=True,
            ),
        ]
    )

    with pytest.raises(
        PlannerPolicyError,
        match="follow validation",
    ):
        validate_plan_policy(
            plan,
            available_skills=ALLOWED,
        )