"""Tests for server-side approved recipe verification."""

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest

import geoagent_harness.mcp_server.approved_recipe as approved_recipe_module

from geoagent_harness.mcp_server.approved_recipe import (
    ApprovedRecipeError,
    run_approved_recipe,
    validate_approved_recipe_request,
)
from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes import (
    WorkflowRecipe,
    build_recipe_execution_envelope,
    create_recipe_approval,
    save_recipe,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)

# import geoagent_harness.mcp_server.approved_recipe as (
#     approved_recipe_module
# )

from geoagent_harness.recipes.evidence_persistence import (
    RecipeEvidencePersistenceError,
)
from geoagent_harness.recipes.evidence_schemas import (
    RecipeExecutionRecord,
)
from tests.test_recipe_evidence_schemas import (
    evidence as example_evidence,
)


PROJECT_ROOT = Path(__file__).parents[1]
NOW = datetime(
    2026,
    8,
    16,
    20,
    0,
    tzinfo=timezone.utc,
)


def prepared_request(
    tmp_path: Path,
):
    recipe_root = tmp_path / "recipes"
    approval_root = tmp_path / "approvals"
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"

    input_root.mkdir()
    output_root.mkdir()

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    draft = WorkflowRecipe.model_validate(
        {
            "recipe_id": "server-recipe-test",
            "summary": "Convert sample points.",
            "original_request": (
                "Convert sample points."
            ),
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_id": "inspect_vector",
                    "arguments": {
                        "path": "input.geojson"
                    },
                    "output_ids": [
                        "source_metadata"
                    ],
                },
                {
                    "step_id": "step_2",
                    "skill_id": "convert_vector",
                    "depends_on": [
                        "step_1"
                    ],
                    "arguments": {
                        "path": "input.geojson",
                        "target_path": "output.gpkg",
                    },
                    "output_ids": [
                        "converted_vector"
                    ],
                },
            ],
        }
    )

    recipe, recipe_path = save_recipe(
        draft,
        recipe_root=recipe_root,
    )

    approval, approval_path = (
        create_recipe_approval(
            recipe=recipe,
            registry=registry,
            step_ids=["step_2"],
            decision="approved",
            approver="test-operator",
            reason="Approved server test.",
            approval_root=approval_root,
            now=NOW,
        )
    )

    envelope = (
        build_recipe_execution_envelope(
            recipe=recipe,
            approval=approval,
            registry=registry,
        )
    )

    settings = MCPSettings(
        input_root=input_root,
        output_root=output_root,
        recipe_root=recipe_root,
        approval_root=approval_root,
        project_root=PROJECT_ROOT,
        enable_write_tools=True,
    )

    return (
        recipe_path,
        approval_path,
        envelope,
        settings,
    )

def completed_result(
    envelope,
):
    """Return a completed result matching one envelope."""

    return example_evidence().run_result.model_copy(
        update={
            "recipe_id": envelope.recipe_id,
            "recipe_sha256": (
                envelope.recipe_sha256
            ),
            "approval_id": envelope.approval_id,
        }
    )


def execution_record(
    envelope,
) -> RecipeExecutionRecord:
    """Return durable references matching one envelope."""

    return RecipeExecutionRecord(
        recipe_id=envelope.recipe_id,
        recipe_sha256=envelope.recipe_sha256,
        approval_id=envelope.approval_id,
        final_status="validated_success",
        run_result_sha256="b" * 64,
        run_result_path=(
            "recipe-runs/server-result.json"
        ),
        evidence_sha256="c" * 64,
        evidence_path=(
            "recipe-evidence/server-evidence.json"
        ),
        report_path=(
            "reports/server-report.md"
        ),
        execution_performed=True,
        evidence_recorded=True,
        report_written=True,
    )

def test_server_rebuilds_exact_envelope(
    tmp_path: Path,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    verified = validate_approved_recipe_request(
        execution_envelope=(
            envelope.model_dump(mode="json")
        ),
        recipe_filename=recipe_path.name,
        approval_filename=approval_path.name,
        settings=settings,
    )

    assert verified == envelope


def test_changed_envelope_is_rejected(
    tmp_path: Path,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    payload = envelope.model_dump(
        mode="json"
    )
    payload["steps"][1]["arguments"][
        "target_path"
    ] = "changed.gpkg"

    with pytest.raises(
        ApprovedRecipeError,
        match="does not match",
    ):
        validate_approved_recipe_request(
            execution_envelope=payload,
            recipe_filename=recipe_path.name,
            approval_filename=(
                approval_path.name
            ),
            settings=settings,
        )


def test_recipe_path_traversal_is_rejected(
    tmp_path: Path,
) -> None:
    (
        _recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    with pytest.raises(
        ApprovedRecipeError,
        match="plain JSON filename",
    ):
        validate_approved_recipe_request(
            execution_envelope=(
                envelope.model_dump(
                    mode="json"
                )
            ),
            recipe_filename="../recipe.json",
            approval_filename=(
                approval_path.name
            ),
            settings=settings,
        )


def test_writes_disabled_blocks_server(
    tmp_path: Path,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    blocked = settings.model_copy(
        update={
            "enable_write_tools": False
        }
    )

    with pytest.raises(
        ApprovedRecipeError,
        match="write tools are disabled",
    ):
        run_approved_recipe(
            execution_envelope=(
                envelope.model_dump(
                    mode="json"
                )
            ),
            recipe_filename=recipe_path.name,
            approval_filename=(
                approval_path.name
            ),
            settings=blocked,
        )

def test_server_persists_completed_recipe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    run_result = completed_result(envelope)
    record = execution_record(envelope)
    captured: dict[str, object] = {}

    # Replace the real GIS recipe execution.
    monkeypatch.setattr(
        approved_recipe_module,
        "execute_approved_recipe",
        lambda **_kwargs: run_result,
    )

    # Replace real filesystem persistence.
    def fake_persist(**kwargs):
        captured.update(kwargs)
        return record

    monkeypatch.setattr(
        approved_recipe_module,
        "persist_recipe_run",
        fake_persist,
    )

    response = run_approved_recipe(
        execution_envelope=(
            envelope.model_dump(mode="json")
        ),
        recipe_filename=recipe_path.name,
        approval_filename=approval_path.name,
        settings=settings,
    )

    assert response.run_result == run_result
    assert response.execution_record == record

    assert captured["run_result"] == run_result
    assert captured["settings"] == settings
    assert captured["registry"] is not None

    recorded_at = captured["recorded_at"]

    assert isinstance(
        recorded_at,
        datetime,
    )
    assert recorded_at.tzinfo is not None
    
def test_persistence_failure_requires_manual_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    run_result = completed_result(envelope)

    monkeypatch.setattr(
        approved_recipe_module,
        "execute_approved_recipe",
        lambda **_kwargs: run_result,
    )

    def fail_persistence(**_kwargs):
        raise RecipeEvidencePersistenceError(
            "simulated persistence failure"
        )

    monkeypatch.setattr(
        approved_recipe_module,
        "persist_recipe_run",
        fail_persistence,
    )

    with pytest.raises(
        ApprovedRecipeError,
        match="manual review is required",
    ):
        run_approved_recipe(
            execution_envelope=(
                envelope.model_dump(
                    mode="json"
                )
            ),
            recipe_filename=recipe_path.name,
            approval_filename=(
                approval_path.name
            ),
            settings=settings,
        )



def test_persistence_failure_requires_manual_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    run_result = completed_result(envelope)

    monkeypatch.setattr(
        approved_recipe_module,
        "execute_approved_recipe",
        lambda **_kwargs: run_result,
    )

    def fail_persistence(**_kwargs):
        raise RecipeEvidencePersistenceError(
            "simulated persistence failure"
        )

    monkeypatch.setattr(
        approved_recipe_module,
        "persist_recipe_run",
        fail_persistence,
    )

    with pytest.raises(
        ApprovedRecipeError,
        match="manual review is required",
    ):
        run_approved_recipe(
            execution_envelope=(
                envelope.model_dump(
                    mode="json"
                )
            ),
            recipe_filename=recipe_path.name,
            approval_filename=(
                approval_path.name
            ),
            settings=settings,
        )

def test_invalid_result_is_not_persisted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        recipe_path,
        approval_path,
        envelope,
        settings,
    ) = prepared_request(tmp_path)

    invalid_result = completed_result(
        envelope
    ).model_copy(
        update={
            "recipe_sha256": "f" * 64,
        }
    )

    persistence_called = False

    monkeypatch.setattr(
        approved_recipe_module,
        "execute_approved_recipe",
        lambda **_kwargs: invalid_result,
    )

    def unexpected_persistence(**_kwargs):
        nonlocal persistence_called
        persistence_called = True
        return execution_record(envelope)

    monkeypatch.setattr(
        approved_recipe_module,
        "persist_recipe_run",
        unexpected_persistence,
    )

    with pytest.raises(
        ApprovedRecipeError,
        match="digest conflicts",
    ):
        run_approved_recipe(
            execution_envelope=(
                envelope.model_dump(
                    mode="json"
                )
            ),
            recipe_filename=recipe_path.name,
            approval_filename=(
                approval_path.name
            ),
            settings=settings,
        )

    assert persistence_called is False
