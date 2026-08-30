"""Tests for atomic immutable Builder-bundle promotion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import geoagent_harness.builder as builder
from geoagent_harness.builder import (
    BuilderPromotionError,
    builder_promotion_plan_sha256,
    persist_builder_promotion_plan,
    plan_builder_promotion,
    promote_builder_candidate,
)
from geoagent_harness.cli import app
from tests.test_builder_promotion_plan import (
    prepared_promotion,
)


runner = CliRunner()


def prepared_persisted_plan(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = prepared_promotion(tmp_path)

    plan = plan_builder_promotion(
        decision_file=prepared["decision_file"],
        decision_root=prepared["decision_root"],
        review_root=prepared["review_root"],
        candidate_root=prepared["candidate_root"],
        project_root=prepared["project_root"],
    )

    plan_root = tmp_path / "plans"

    persisted = persist_builder_promotion_plan(
        plan,
        plan_root=plan_root,
        decision_root=prepared["decision_root"],
        review_root=prepared["review_root"],
        candidate_root=prepared["candidate_root"],
        project_root=prepared["project_root"],
    )

    return {
        **prepared,
        "plan": plan,
        "plan_root": plan_root,
        "plan_file": Path(persisted.plan_file),
        "plan_sha256": (
            builder_promotion_plan_sha256(plan)
        ),
        "promotion_root": tmp_path / "promotions",
    }


def promote(prepared: dict[str, object]):
    plan = prepared["plan"]

    return promote_builder_candidate(
        plan_file=prepared["plan_file"],
        plan_root=prepared["plan_root"],
        decision_root=prepared["decision_root"],
        review_root=prepared["review_root"],
        candidate_root=prepared["candidate_root"],
        project_root=prepared["project_root"],
        promotion_root=prepared["promotion_root"],
        confirm_decision_id=plan.decision_id,
        confirm_plan_sha256=(
            prepared["plan_sha256"]
        ),
    )


def test_promotes_one_atomic_immutable_bundle(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_plan(tmp_path)
    plan = prepared["plan"]

    result = promote(prepared)

    promotion_directory = Path(
        result.promotion_directory
    )
    manifest_file = Path(
        result.promotion_manifest
    )

    assert promotion_directory.is_dir()
    assert manifest_file.is_file()

    manifest = json.loads(
        manifest_file.read_text(encoding="utf-8")
    )

    assert (
        manifest["promotion_plan_sha256"]
        == prepared["plan_sha256"]
    )
    assert manifest["bundle_promoted"] is True
    assert manifest["files_copied"] is True
    assert (
        manifest["post_promotion_verified"]
        is False
    )
    assert manifest["activation_performed"] is False
    assert manifest["implementation_trusted"] is False
    assert manifest["execution_performed"] is False

    for item in plan.files:
        promoted_file = (
            promotion_directory
            / "files"
            / item.destination_path
        )
        candidate_file = (
            Path(plan.candidate_path)
            / item.source_path
        )

        assert promoted_file.read_bytes() == (
            candidate_file.read_bytes()
        )

        trusted_destination = (
            Path(prepared["project_root"])
            / item.destination_path
        )
        assert not trusted_destination.exists()

    assert result.bundle_promoted is True
    assert result.files_copied is True
    assert result.post_promotion_verified is False
    assert result.activation_performed is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is True
    assert result.execution_performed is False


@pytest.mark.parametrize(
    ("decision_id", "plan_sha256", "message"),
    [
        (
            "wrong-decision",
            None,
            "decision confirmation",
        ),
        (
            None,
            "0" * 64,
            "promotion-plan confirmation",
        ),
    ],
)
def test_rejects_incorrect_operator_confirmation(
    tmp_path: Path,
    decision_id: str | None,
    plan_sha256: str | None,
    message: str,
) -> None:
    prepared = prepared_persisted_plan(tmp_path)
    plan = prepared["plan"]

    with pytest.raises(
        BuilderPromotionError,
        match=message,
    ):
        promote_builder_candidate(
            plan_file=prepared["plan_file"],
            plan_root=prepared["plan_root"],
            decision_root=prepared["decision_root"],
            review_root=prepared["review_root"],
            candidate_root=prepared["candidate_root"],
            project_root=prepared["project_root"],
            promotion_root=prepared["promotion_root"],
            confirm_decision_id=(
                decision_id
                if decision_id is not None
                else plan.decision_id
            ),
            confirm_plan_sha256=(
                plan_sha256
                if plan_sha256 is not None
                else prepared["plan_sha256"]
            ),
        )

    assert not Path(
        prepared["promotion_root"]
    ).exists()


def test_rejects_changed_candidate_after_plan(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_plan(tmp_path)
    plan = prepared["plan"]

    changed = (
        Path(plan.candidate_path)
        / plan.files[0].source_path
    )
    changed.write_text(
        '"""Changed after approval."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionError,
        match="could not be reverified",
    ):
        promote(prepared)

    promotion_root = Path(
        prepared["promotion_root"]
    )

    assert (
        not promotion_root.exists()
        or not list(promotion_root.glob("*.promotion"))
    )


def test_refuses_existing_promotion_bundle(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_plan(tmp_path)

    first = promote(prepared)

    with pytest.raises(
        BuilderPromotionError,
        match="already exists",
    ):
        promote(prepared)

    assert Path(first.promotion_directory).is_dir()


def test_rejects_symlinked_promotion_root(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_plan(tmp_path)

    real_root = tmp_path / "real-promotions"
    real_root.mkdir()

    symlink_root = tmp_path / "promotion-link"
    symlink_root.symlink_to(
        real_root,
        target_is_directory=True,
    )

    prepared["promotion_root"] = symlink_root

    with pytest.raises(
        BuilderPromotionError,
        match="root cannot be a symlink",
    ):
        promote(prepared)

    assert list(real_root.iterdir()) == []


def test_cli_promotes_builder_bundle(
    tmp_path: Path,
) -> None:
    prepared = prepared_persisted_plan(tmp_path)
    plan = prepared["plan"]

    result = runner.invoke(
        app,
        [
            "promote-builder-candidate",
            str(prepared["plan_file"]),
            "--plan-root",
            str(prepared["plan_root"]),
            "--decision-root",
            str(prepared["decision_root"]),
            "--review-root",
            str(prepared["review_root"]),
            "--candidate-root",
            str(prepared["candidate_root"]),
            "--project-root",
            str(prepared["project_root"]),
            "--promotion-root",
            str(prepared["promotion_root"]),
            "--confirm-decision-id",
            plan.decision_id,
            "--confirm-plan-sha256",
            str(prepared["plan_sha256"]),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["bundle_promoted"] is True
    assert payload["files_copied"] is True
    assert payload["post_promotion_verified"] is False
    assert payload["activation_performed"] is False
    assert payload["implementation_trusted"] is False
    assert payload["execution_performed"] is False


def test_cli_requires_exact_confirmations() -> None:
    result = runner.invoke(
        app,
        [
            "promote-builder-candidate",
            "example/PLAN.json",
        ],
    )

    assert result.exit_code == 2
    assert "--confirm-decision-id is required" in (
        result.output
    )


def test_cli_reports_promotion_failure(
    monkeypatch,
) -> None:
    def reject(*args, **kwargs):
        raise BuilderPromotionError(
            "Builder promotion bundle already exists"
        )

    monkeypatch.setattr(
        builder,
        "promote_builder_candidate",
        reject,
    )

    result = runner.invoke(
        app,
        [
            "promote-builder-candidate",
            "example/PLAN.json",
            "--confirm-decision-id",
            "decision-1",
            "--confirm-plan-sha256",
            "a" * 64,
        ],
    )

    assert result.exit_code == 2
    assert (
        "Builder promotion bundle already exists"
        in result.output
    )
