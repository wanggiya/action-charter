"""Tests for trusted Snakemake approved replay."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import geoagent_harness.snakemake_export.replay as replay_module

from geoagent_harness.recipes.evidence_schemas import (
    RecipeExecutionRecord,
)
from geoagent_harness.recipes.schemas import (
    RecipeRunResult,
    RecipeStepExecutionResult,
    RecipeStepRunResult,
)
from geoagent_harness.snakemake_export import (
    SnakemakeRecipeExportPlan,
    SnakemakeReplayError,
    SnakemakeReplaySettings,
    generate_snakemake_recipe_export,
    run_approved_recipe_replay,
)


DIGEST = "a" * 64
APPROVAL_ID = (
    "recipe-approval-"
    "20260822t000000z-1234abcd"
)


def generated_export(
    tmp_path: Path,
) -> Path:
    plan = SnakemakeRecipeExportPlan(
        recipe_id="snakemake-test",
        recipe_sha256=DIGEST,
        approval_id=APPROVAL_ID,
        recipe_filename="recipe.json",
        approval_filename="approval.json",
        approved_step_ids=["step_2"],
        topological_step_ids=[
            "step_1",
            "step_2",
        ],
    )

    result = generate_snakemake_recipe_export(
        plan,
        export_root=tmp_path / "exports",
    )

    return Path(result.export_path)


def executor_result():
    from geoagent_harness.executor.schemas import (
        ExecutorRecipeRunResult,
    )

    execution = RecipeStepExecutionResult(
        step_id="step_2",
        skill_id="convert_vector",
        status="completed_pending_validation",
        output_ids=["converted_vector"],
        result={"status": "converted"},
        validation_performed=False,
    )

    step = RecipeStepRunResult(
        step_id="step_2",
        skill_id="convert_vector",
        status="validated_success",
        execution=execution,
        validation_result={
            "passed": True
        },
        validation_performed=True,
    )

    recipe = RecipeRunResult(
        recipe_id="snakemake-test",
        recipe_sha256=DIGEST,
        approval_id=APPROVAL_ID,
        final_status="validated_success",
        step_results=[step],
        validation_performed=True,
    )

    record = RecipeExecutionRecord(
        recipe_id="snakemake-test",
        recipe_sha256=DIGEST,
        approval_id=APPROVAL_ID,
        final_status="validated_success",
        run_result_sha256="b" * 64,
        run_result_path=(
            "recipe-runs/result.json"
        ),
        evidence_sha256="c" * 64,
        evidence_path=(
            "recipe-evidence/evidence.json"
        ),
        report_path="reports/report.md",
    )

    return ExecutorRecipeRunResult(
        recipe_sha256=DIGEST,
        approval_id=APPROVAL_ID,
        recipe=recipe,
        execution_record=record,
    )


def install_local_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        replay_module,
        "load_recipe",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        replay_module,
        "load_recipe_approval",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        replay_module,
        "load_skill_registry",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        replay_module,
        "build_recipe_execution_envelope",
        lambda **_kwargs: SimpleNamespace(
            recipe_id="snakemake-test",
            recipe_sha256=DIGEST,
            approval_id=APPROVAL_ID,
            approved_step_ids=["step_2"],
            topological_step_ids=[
                "step_1",
                "step_2",
            ],
        ),
    )


def replay_settings(
    tmp_path: Path,
) -> SnakemakeReplaySettings:
    return SnakemakeReplaySettings(
        project_root=tmp_path,
        agents_root=tmp_path / "agents",
        recipe_root=tmp_path / "recipes",
        approval_root=tmp_path / "approvals",
        export_root=tmp_path / "exports",
    )


def test_replay_writes_completion_only_after_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_path = generated_export(
        tmp_path
    )
    install_local_verification(
        monkeypatch
    )

    async def fake_executor(**_kwargs):
        return executor_result()

    completion_path = (
        export_path
        / ".geoagent-replay-complete.json"
    )

    result = run_approved_recipe_replay(
        configuration_path=(
            export_path
            / "geoagent-replay.json"
        ),
        completion_path=completion_path,
        settings=replay_settings(tmp_path),
        executor=fake_executor,
    )

    assert result.replay_completed is True
    assert result.workflow_executed is True
    assert (
        result.recipe_execution_performed
        is True
    )
    assert result.evidence_recorded is True
    assert completion_path.is_file()

    persisted = json.loads(
        completion_path.read_text(
            encoding="utf-8"
        )
    )

    assert persisted["final_status"] == (
        "validated_success"
    )


def test_envelope_conflict_blocks_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_path = generated_export(
        tmp_path
    )
    install_local_verification(
        monkeypatch
    )

    monkeypatch.setattr(
        replay_module,
        "build_recipe_execution_envelope",
        lambda **_kwargs: SimpleNamespace(
            recipe_id="snakemake-test",
            recipe_sha256="d" * 64,
            approval_id=APPROVAL_ID,
            approved_step_ids=["step_2"],
            topological_step_ids=[
                "step_1",
                "step_2",
            ],
        ),
    )

    called = False

    async def fake_executor(**_kwargs):
        nonlocal called
        called = True
        return executor_result()

    with pytest.raises(
        SnakemakeReplayError,
        match="rebuilt approved envelope",
    ):
        run_approved_recipe_replay(
            configuration_path=(
                export_path
                / "geoagent-replay.json"
            ),
            completion_path=(
                export_path
                / ".geoagent-replay-complete.json"
            ),
            settings=replay_settings(tmp_path),
            executor=fake_executor,
        )

    assert called is False


def test_failed_validation_writes_no_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_path = generated_export(
        tmp_path
    )
    install_local_verification(
        monkeypatch
    )

    failed = executor_result()
    failed = failed.model_copy(
        update={
            "recipe": failed.recipe.model_copy(
                update={
                    "final_status": (
                        "validation_failed"
                    ),
                    "validation_performed": True,
                    "failed_step_id": "step_2",
                }
            )
        }
    )

    async def fake_executor(**_kwargs):
        return failed

    completion_path = (
        export_path
        / ".geoagent-replay-complete.json"
    )

    with pytest.raises(
        SnakemakeReplayError,
        match="did not produce validated success",
    ):
        run_approved_recipe_replay(
            configuration_path=(
                export_path
                / "geoagent-replay.json"
            ),
            completion_path=completion_path,
            settings=replay_settings(tmp_path),
            executor=fake_executor,
        )

    assert not completion_path.exists()

