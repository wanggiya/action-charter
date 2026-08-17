"""Tests for approved recipe execution through the Executor."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

import geoagent_harness.executor.service as service
from geoagent_harness.executor import (
    ExecutorServiceError,
    execute_approved_recipe_via_mcp,
)
from geoagent_harness.mcp_client.executor import (
    APPROVED_RECIPE_TOOL,
)
from geoagent_harness.mcp_client.schemas import (
    MCPToolCallResult,
)
from geoagent_harness.recipes import (
    RecipeExecutionEnvelope,
)


DIGEST = "a" * 64
APPROVAL_ID = (
    "recipe-approval-20260816t200000z-1234abcd"
)


def execution_envelope() -> RecipeExecutionEnvelope:
    return RecipeExecutionEnvelope(
        recipe_id="executor-recipe-test",
        recipe_sha256=DIGEST,
        approval_id=APPROVAL_ID,
        approved_step_ids=["step_2"],
        topological_step_ids=[
            "step_1",
            "step_2",
        ],
        steps=[
            {
                "step_id": "step_1",
                "skill_id": "inspect_vector",
                "depends_on": [],
                "arguments": {
                    "path": (
                        "data/input/"
                        "sample_points.geojson"
                    ),
                },
                "output_ids": [
                    "source_metadata",
                ],
            },
            {
                "step_id": "step_2",
                "skill_id": "convert_vector",
                "depends_on": [
                    "step_1",
                ],
                "arguments": {
                    "path": (
                        "data/input/"
                        "sample_points.geojson"
                    ),
                    "target_path": (
                        "data/output/"
                        "executor_recipe_test.gpkg"
                    ),
                    "target_layer": (
                        "executor_recipe_test"
                    ),
                },
                "output_ids": [
                    "converted_vector",
                ],
            },
        ],
        execution_performed=False,
    )


def successful_recipe_result(
    *,
    digest: str = DIGEST,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "recipe_id": "executor-recipe-test",
        "recipe_sha256": digest,
        "approval_id": APPROVAL_ID,
        "final_status": "validated_success",
        "step_results": [
            {
                "step_id": "step_1",
                "skill_id": "inspect_vector",
                "status": "completed",
                "execution": {
                    "schema_version": "1.0",
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
                    "status": "completed",
                    "output_ids": [
                        "source_metadata",
                    ],
                    "result": {
                        "status": "inspected",
                    },
                    "execution_performed": True,
                    "validation_performed": False,
                },
                "validation_result": None,
                "execution_performed": True,
                "validation_performed": False,
            },
            {
                "step_id": "step_2",
                "skill_id": "convert_vector",
                "status": "validated_success",
                "execution": {
                    "schema_version": "1.0",
                    "step_id": "step_2",
                    "skill_id": "convert_vector",
                    "status": (
                        "completed_pending_validation"
                    ),
                    "output_ids": [
                        "converted_vector",
                    ],
                    "result": {
                        "status": (
                            "converted_pending_validation"
                        ),
                    },
                    "execution_performed": True,
                    "validation_performed": False,
                },
                "validation_result": {
                    "passed": True,
                },
                "execution_performed": True,
                "validation_performed": True,
            },
        ],
        "failed_step_id": None,
        "warnings": [],
        "execution_performed": True,
        "validation_performed": True,
    }


class FakeRecipeClient:
    def __init__(
        self,
        result: dict[str, Any],
        *,
        tool_name: str = APPROVED_RECIPE_TOOL,
    ) -> None:
        self.result = result
        self.tool_name = tool_name
        self.calls: list[dict[str, Any]] = []

    async def execute_approved_recipe(
        self,
        *,
        envelope: RecipeExecutionEnvelope,
        recipe_filename: str,
        approval_filename: str,
    ) -> MCPToolCallResult:
        self.calls.append(
            {
                "envelope": envelope,
                "recipe_filename": recipe_filename,
                "approval_filename": (
                    approval_filename
                ),
            }
        )

        return MCPToolCallResult(
            tool_name=self.tool_name,
            result=self.result,
        )


def install_trusted_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> RecipeExecutionEnvelope:
    envelope = execution_envelope()

    monkeypatch.setattr(
        service,
        "load_agent_manifest",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        service,
        "_validate_executor_manifest",
        lambda manifest: None,
    )
    monkeypatch.setattr(
        service,
        "load_recipe",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        service,
        "load_recipe_approval",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        service,
        "load_skill_registry",
        lambda *args, **kwargs: object(),
    )
    monkeypatch.setattr(
        service,
        "build_recipe_execution_envelope",
        lambda **kwargs: envelope,
    )

    return envelope


def test_executor_runs_approved_recipe_through_mcp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = install_trusted_inputs(
        monkeypatch
    )
    client = FakeRecipeClient(
        successful_recipe_result()
    )

    result = asyncio.run(
        execute_approved_recipe_via_mcp(
            recipe_file=Path(
                "workflow-recipes/"
                "executor-recipe-test.json"
            ),
            approval_file=Path(
                "approvals/"
                f"{APPROVAL_ID}.json"
            ),
            recipe_root=Path(
                "workflow-recipes"
            ),
            approval_root=Path("approvals"),
            project_root=Path("."),
            agents_root=Path("agents"),
            mcp_client=client,
        )
    )

    assert result.agent_id == "executor"
    assert result.tool_name == APPROVED_RECIPE_TOOL
    assert result.recipe_sha256 == DIGEST
    assert result.approval_id == APPROVAL_ID
    assert result.execution_performed is True
    assert (
        result.recipe.final_status
        == "validated_success"
    )

    assert len(client.calls) == 1
    assert (
        client.calls[0]["envelope"]
        == envelope
    )
    assert (
        client.calls[0]["recipe_filename"]
        == "executor-recipe-test.json"
    )
    assert (
        client.calls[0]["approval_filename"]
        == f"{APPROVAL_ID}.json"
    )


def test_executor_rejects_mismatched_recipe_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_trusted_inputs(monkeypatch)

    client = FakeRecipeClient(
        successful_recipe_result(
            digest="b" * 64,
        )
    )

    with pytest.raises(
        ExecutorServiceError,
        match="digest does not match",
    ):
        asyncio.run(
            execute_approved_recipe_via_mcp(
                recipe_file=Path(
                    "workflow-recipes/"
                    "executor-recipe-test.json"
                ),
                approval_file=Path(
                    "approvals/"
                    f"{APPROVAL_ID}.json"
                ),
                recipe_root=Path(
                    "workflow-recipes"
                ),
                approval_root=Path(
                    "approvals"
                ),
                project_root=Path("."),
                agents_root=Path("agents"),
                mcp_client=client,
            )
        )


def test_executor_rejects_unexpected_mcp_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_trusted_inputs(monkeypatch)

    client = FakeRecipeClient(
        successful_recipe_result(),
        tool_name=(
            "run_approved_vector_postgis_workflow"
        ),
    )

    with pytest.raises(
        ExecutorServiceError,
        match="unexpected tool",
    ):
        asyncio.run(
            execute_approved_recipe_via_mcp(
                recipe_file=Path(
                    "workflow-recipes/"
                    "executor-recipe-test.json"
                ),
                approval_file=Path(
                    "approvals/"
                    f"{APPROVAL_ID}.json"
                ),
                recipe_root=Path(
                    "workflow-recipes"
                ),
                approval_root=Path(
                    "approvals"
                ),
                project_root=Path("."),
                agents_root=Path("agents"),
                mcp_client=client,
            )
        )


def test_executor_rejects_invalid_success_step_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_trusted_inputs(monkeypatch)

    payload = successful_recipe_result()

    payload["step_results"][1][
        "status"
    ] = "completed"

    client = FakeRecipeClient(payload)

    with pytest.raises(
        ExecutorServiceError,
        match="success conflicts",
    ):
        asyncio.run(
            execute_approved_recipe_via_mcp(
                recipe_file=Path(
                    "workflow-recipes/"
                    "executor-recipe-test.json"
                ),
                approval_file=Path(
                    "approvals/"
                    f"{APPROVAL_ID}.json"
                ),
                recipe_root=Path(
                    "workflow-recipes"
                ),
                approval_root=Path(
                    "approvals"
                ),
                project_root=Path("."),
                agents_root=Path("agents"),
                mcp_client=client,
            )
        )
