import pytest
from pydantic import ValidationError

from geoagent_harness.planner.schemas import (
    PlannerResult,
    WorkflowPlan,
)

def test_planner_result_requires_original_request() -> None:
    plan = WorkflowPlan.model_validate(
        valid_plan_payload()
    )

    with pytest.raises(ValidationError):
        PlannerResult(
            model="qwen-test",
            context_references=[],
            plan=plan,
        )
        
def valid_plan_payload() -> dict:
    return {
        "schema_version": "1.0",
        "status": "planned",
        "summary": "Inspect and validate a vector workflow.",
        "steps": [
            {
                "step_id": "step_1",
                "skill": "inspect_vector",
                "purpose": "Inspect the approved dataset.",
                "arguments": {
                    "path": "data/input/sample_points.geojson",
                },
                "requires_approval": False,
                "expected_artifacts": [],
                "validation_required": False,
            }
        ],
        "assumptions": [],
        "risks": [],
        "execution_performed": False,
        "validation_performed": False,
    }


def test_valid_workflow_plan() -> None:
    plan = WorkflowPlan.model_validate(
        valid_plan_payload()
    )

    assert plan.status == "planned"
    assert plan.execution_performed is False


def test_planner_cannot_claim_execution() -> None:
    payload = valid_plan_payload()
    payload["execution_performed"] = True

    with pytest.raises(ValidationError):
        WorkflowPlan.model_validate(payload)


def test_step_ids_must_be_sequential() -> None:
    payload = valid_plan_payload()
    payload["steps"][0]["step_id"] = "step_2"

    with pytest.raises(
        ValidationError,
        match="sequential",
    ):
        WorkflowPlan.model_validate(payload)


def test_extra_plan_fields_are_rejected() -> None:
    payload = valid_plan_payload()
    payload["shell_command"] = "echo unsafe"

    with pytest.raises(ValidationError):
        WorkflowPlan.model_validate(payload)