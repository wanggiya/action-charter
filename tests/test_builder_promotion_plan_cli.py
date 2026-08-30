"""Offline CLI tests for Builder promotion planning."""

from __future__ import annotations

import json

from typer.testing import CliRunner

import geoagent_harness.builder as builder
from geoagent_harness.builder import (
    BuilderPromotionPlan,
    BuilderPromotionPlanError,
    BuilderPromotionPlanStorageError,
    BuilderPromotionPlanStorageResult,
)
from geoagent_harness.cli import app


runner = CliRunner()


def promotion_plan() -> BuilderPromotionPlan:
    return BuilderPromotionPlan(
        task_id="builder-promotion-cli",
        decision_id="builder-decision-cli",
        reviewer_id="operator@example.com",
        review_package_sha256="a" * 64,
        decision_sha256="b" * 64,
        generation_sha256="c" * 64,
        candidate_tree_sha256="d" * 64,
        candidate_path=(
            "/approved/candidates/example.candidate"
        ),
        project_root="/approved/project",
        review_file=(
            "/approved/reviews/example/REVIEW.json"
        ),
        decision_file=(
            "/approved/decisions/example/DECISION.json"
        ),
        files=[
            {
                "kind": "adapter",
                "source_path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "destination_path": (
                    "src/geoagent_harness/"
                    "skill_adapters/example.py"
                ),
                "sha256": "e" * 64,
            },
        ],
    )


def test_cli_plans_builder_promotion_without_writes(
    monkeypatch,
) -> None:
    def plan(**kwargs):
        assert str(
            kwargs["decision_file"]
        ) == "example.decision/DECISION.json"
        assert str(
            kwargs["project_root"]
        ) == "."

        return promotion_plan()

    monkeypatch.setattr(
        builder,
        "plan_builder_promotion",
        plan,
    )

    result = runner.invoke(
        app,
        [
            "plan-builder-promotion",
            "example.decision/DECISION.json",
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["human_approval_verified"] is True
    assert (
        payload["candidate_inspection_passed"]
        is True
    )
    assert payload["promotion_ready"] is True
    assert payload["planning_performed"] is True
    assert payload["files_copied"] is False
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_cli_rejects_invalid_promotion_inputs(
    monkeypatch,
) -> None:
    def reject(**kwargs):
        raise BuilderPromotionPlanError(
            "Builder decision does not authorize "
            "promotion planning"
        )

    monkeypatch.setattr(
        builder,
        "plan_builder_promotion",
        reject,
    )

    result = runner.invoke(
        app,
        [
            "plan-builder-promotion",
            "example.decision/DECISION.json",
        ],
    )

    assert result.exit_code == 2
    assert (
        "does not authorize promotion planning"
        in result.output
    )

def test_cli_creates_immutable_promotion_plan(
    monkeypatch,
) -> None:
    plan = promotion_plan()

    def create_plan(**kwargs):
        assert str(
            kwargs["decision_file"]
        ) == "example.decision/DECISION.json"
        assert str(kwargs["project_root"]) == "."

        return plan

    def persist(received_plan, **kwargs):
        assert received_plan == plan
        assert str(
            kwargs["plan_root"]
        ) == "builder-promotion-plans"
        assert str(
            kwargs["decision_root"]
        ) == "builder-decisions"
        assert str(
            kwargs["review_root"]
        ) == "builder-reviews"
        assert str(
            kwargs["candidate_root"]
        ) == "builder-candidates"
        assert str(kwargs["project_root"]) == "."

        return BuilderPromotionPlanStorageResult(
            task_id=plan.task_id,
            decision_id=plan.decision_id,
            review_package_sha256=(
                plan.review_package_sha256
            ),
            decision_sha256=plan.decision_sha256,
            candidate_tree_sha256=(
                plan.candidate_tree_sha256
            ),
            promotion_plan_sha256="f" * 64,
            plan_directory=(
                "builder-promotion-plans/example."
                f"{'f' * 64}.promotion-plan"
            ),
            plan_file=(
                "builder-promotion-plans/example."
                f"{'f' * 64}.promotion-plan/PLAN.json"
            ),
        )

    monkeypatch.setattr(
        builder,
        "plan_builder_promotion",
        create_plan,
    )
    monkeypatch.setattr(
        builder,
        "persist_builder_promotion_plan",
        persist,
    )

    result = runner.invoke(
        app,
        [
            "create-builder-promotion-plan",
            "example.decision/DECISION.json",
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["plan_persisted"] is True
    assert payload["files_copied"] is False
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is False
    assert payload["execution_performed"] is False


def test_cli_reports_promotion_plan_storage_failure(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        builder,
        "plan_builder_promotion",
        lambda **kwargs: promotion_plan(),
    )

    def reject(*args, **kwargs):
        raise BuilderPromotionPlanStorageError(
            "Builder promotion plan already exists"
        )

    monkeypatch.setattr(
        builder,
        "persist_builder_promotion_plan",
        reject,
    )

    result = runner.invoke(
        app,
        [
            "create-builder-promotion-plan",
            "example.decision/DECISION.json",
        ],
    )

    assert result.exit_code == 2
    assert (
        "Builder promotion plan already exists"
        in result.output
    )
