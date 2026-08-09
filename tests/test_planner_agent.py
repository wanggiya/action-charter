"""Tests for the non-executing Planner Agent."""

from __future__ import annotations

from pathlib import Path

import pytest

from geoagent_harness.agent_manifest import (
    AgentManifest,
    AgentPermissions,
    load_agent_manifest,
)
from geoagent_harness.context_pack import (
    TaskContextPack,
    build_context_pack,
)
from geoagent_harness.model.schemas import (
    ModelRequest,
    ModelResult,
)
from geoagent_harness.planner.agent import (
    PlannerAgentError,
    run_planner_agent,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeModelClient:
    """Return fixed model output without contacting Ollama."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.request: ModelRequest | None = None

    def complete(
        self,
        request: ModelRequest,
    ) -> ModelResult:
        self.request = request

        return ModelResult(
            model="qwen-test",
            content=self.content,
            finish_reason="stop",
        )


VALID_PLAN = """
{
  "schema_version": "1.0",
  "status": "planned",
  "summary": "Inspect, load, validate, and report.",
  "steps": [
    {
      "step_id": "step_1",
      "skill": "inspect_vector",
      "purpose": "Inspect the approved source.",
      "arguments": {
        "path": "data/input/sample_points.geojson"
      },
      "requires_approval": false,
      "expected_artifacts": [],
      "validation_required": false
    },
    {
      "step_id": "step_2",
      "skill": "load_vector_to_postgis",
      "purpose": "Load into an approved schema.",
      "arguments": {
        "path": "data/input/sample_points.geojson",
        "target_schema": "agent_sandbox",
        "target_table": "planned_sample_points"
      },
      "requires_approval": true,
      "expected_artifacts": [
        "agent_sandbox.planned_sample_points"
      ],
      "validation_required": false
    },
    {
      "step_id": "step_3",
      "skill": "validate_postgis_layer",
      "purpose": "Deterministically validate the layer.",
      "arguments": {
        "target_schema": "agent_sandbox",
        "target_table": "planned_sample_points"
      },
      "requires_approval": false,
      "expected_artifacts": [],
      "validation_required": true
    },
    {
      "step_id": "step_4",
      "skill": "generate_report",
      "purpose": "Generate a report after validation.",
      "arguments": {
        "task_id": "planned-sample-points"
      },
      "requires_approval": true,
      "expected_artifacts": [
        "reports/planned-sample-points.md"
      ],
      "validation_required": false
    }
  ],
  "assumptions": [],
  "risks": [
    "Target table creation requires human approval."
  ],
  "execution_performed": false,
  "validation_performed": false
}
"""


@pytest.fixture
def context_pack() -> TaskContextPack:
    return build_context_pack(
        (
            "Inspect sample_points, load it into PostGIS, "
            "validate it, and generate a report."
        ),
        PROJECT_ROOT,
    )


@pytest.fixture
def planner_manifest() -> AgentManifest:
    return load_agent_manifest(
        "planner",
        PROJECT_ROOT / "agents",
    )


def test_agent_accepts_valid_model_plan(
    context_pack: TaskContextPack,
    planner_manifest: AgentManifest,
) -> None:
    client = FakeModelClient(VALID_PLAN)

    result = run_planner_agent(
        context_pack=context_pack,
        manifest=planner_manifest,
        model_client=client,
    )

    assert result.agent_id == "planner"
    assert result.model == "qwen-test"
    assert result.plan.status == "planned"
    assert result.plan.execution_performed is False
    assert result.plan.validation_performed is False
    assert len(result.plan.steps) == 4
    assert client.request is not None
    assert client.request.json_mode is True
    assert result.original_request == (
        context_pack.original_request
    )


def test_agent_returns_context_references(
    context_pack: TaskContextPack,
    planner_manifest: AgentManifest,
) -> None:
    result = run_planner_agent(
        context_pack=context_pack,
        manifest=planner_manifest,
        model_client=FakeModelClient(VALID_PLAN),
    )

    assert result.context_references
    assert "context/PROJECT_SUMMARY.md" in (
        result.context_references
    )
    assert "context/SKILLS_INDEX.yaml" in (
        result.context_references
    )


def test_agent_rejects_non_json(
    context_pack: TaskContextPack,
    planner_manifest: AgentManifest,
) -> None:
    with pytest.raises(
        PlannerAgentError,
        match="invalid JSON",
    ):
        run_planner_agent(
            context_pack=context_pack,
            manifest=planner_manifest,
            model_client=FakeModelClient(
                "I would inspect the dataset."
            ),
        )


def test_agent_rejects_markdown_json_fence(
    context_pack: TaskContextPack,
    planner_manifest: AgentManifest,
) -> None:
    fenced = f"```json\n{VALID_PLAN}\n```"

    with pytest.raises(
        PlannerAgentError,
        match="invalid JSON",
    ):
        run_planner_agent(
            context_pack=context_pack,
            manifest=planner_manifest,
            model_client=FakeModelClient(fenced),
        )


def test_agent_rejects_invalid_plan_schema(
    context_pack: TaskContextPack,
    planner_manifest: AgentManifest,
) -> None:
    invalid_schema = """
    {
      "status": "planned",
      "summary": "Missing required steps.",
      "steps": [],
      "execution_performed": false,
      "validation_performed": false
    }
    """

    with pytest.raises(
        PlannerAgentError,
        match="invalid plan schema",
    ):
        run_planner_agent(
            context_pack=context_pack,
            manifest=planner_manifest,
            model_client=FakeModelClient(
                invalid_schema
            ),
        )


def test_agent_rejects_unapproved_skill(
    context_pack: TaskContextPack,
    planner_manifest: AgentManifest,
) -> None:
    unsafe = VALID_PLAN.replace(
        '"inspect_vector"',
        '"run_shell"',
        1,
    )

    with pytest.raises(
        PlannerAgentError,
        match="deterministic policy",
    ):
        run_planner_agent(
            context_pack=context_pack,
            manifest=planner_manifest,
            model_client=FakeModelClient(unsafe),
        )


def test_agent_rejects_execution_claim(
    context_pack: TaskContextPack,
    planner_manifest: AgentManifest,
) -> None:
    false_claim = VALID_PLAN.replace(
        '"execution_performed": false',
        '"execution_performed": true',
    )

    with pytest.raises(
        PlannerAgentError,
        match="invalid plan schema",
    ):
        run_planner_agent(
            context_pack=context_pack,
            manifest=planner_manifest,
            model_client=FakeModelClient(false_claim),
        )


def test_agent_rejects_tool_enabled_manifest(
    context_pack: TaskContextPack,
) -> None:
    manifest = AgentManifest(
        id="planner",
        model_ref="shared_ollama_runtime",
        purpose="Unsafe test manifest.",
        permissions=AgentPermissions(
            tools=["shell"],
        ),
        instructions=["Plan."],
    )

    with pytest.raises(
        PlannerAgentError,
        match="cannot have executable tools",
    ):
        run_planner_agent(
            context_pack=context_pack,
            manifest=manifest,
            model_client=FakeModelClient(VALID_PLAN),
        )


@pytest.mark.parametrize(
    ("permission", "message"),
    [
        ("arbitrary_shell", "arbitrary shell"),
        ("unrestricted_sql", "unrestricted SQL"),
        ("filesystem_write", "filesystem write"),
        ("database_write", "database write"),
    ],
)
def test_agent_rejects_unsafe_manifest_permissions(
    context_pack: TaskContextPack,
    permission: str,
    message: str,
) -> None:
    permission_values = {
        "arbitrary_shell": False,
        "unrestricted_sql": False,
        "filesystem_write": False,
        "database_write": False,
    }
    permission_values[permission] = True

    manifest = AgentManifest(
        id="planner",
        model_ref="shared_ollama_runtime",
        purpose="Unsafe test manifest.",
        permissions=AgentPermissions(
            **permission_values
        ),
        instructions=["Plan."],
    )

    with pytest.raises(
        PlannerAgentError,
        match=message,
    ):
        run_planner_agent(
            context_pack=context_pack,
            manifest=manifest,
            model_client=FakeModelClient(VALID_PLAN),
        )