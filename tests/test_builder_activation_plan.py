"""Tests for read-only Builder activation planning."""

from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest
from pydantic import ValidationError

from geoagent_harness.builder import (
    BuilderActivationPlan,
    BuilderActivationPlanError,
    create_builder_activation_review_decision,
    persist_builder_activation_review_decision,
    plan_builder_activation,
)
from tests.test_builder_activation_review_storage import (
    prepared_activation_decision,
    persist,
)
from tests.test_builder_activation_review import (
    prepared_persisted_verification,
)


def prepared_activation_plan(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = prepared_activation_decision(
        tmp_path
    )
    persisted = persist(prepared)

    plan = plan_builder_activation(
        activation_decision_file=Path(
            persisted.decision_file
        ),
        activation_decision_root=prepared[
            "activation_decision_root"
        ],
        verification_root=prepared[
            "verification_root"
        ],
        promotion_root=prepared[
            "promotion_root"
        ],
        promotion_plan_root=prepared[
            "plan_root"
        ],
        project_root=prepared["project_root"],
    )

    return {
        **prepared,
        "persisted_activation_decision": (
            persisted
        ),
        "activation_plan": plan,
    }


def test_plans_exact_verified_bundle_writes(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_plan(
        tmp_path
    )
    plan = prepared["activation_plan"]
    decision = prepared[
        "activation_decision"
    ]
    verification = prepared["verification"]

    assert plan.task_id == decision.task_id
    assert (
        plan.activation_decision_id
        == decision.decision_id
    )
    assert (
        plan.activation_decision_sha256
        == prepared[
            "persisted_activation_decision"
        ].activation_decision_sha256
    )
    assert (
        plan.verification_sha256
        == decision.verification_sha256
    )
    assert (
        plan.promotion_plan_sha256
        == verification.promotion_plan_sha256
    )
    assert (
        plan.candidate_tree_sha256
        == verification.candidate_tree_sha256
    )

    assert [
        item.destination_path
        for item in plan.files
    ] == sorted(verification.verified_paths)

    assert all(
        item.source_path
        == f"files/{item.destination_path}"
        for item in plan.files
    )
    assert all(
        item.destination_exists is False
        for item in plan.files
    )

    for item in plan.files:
        source = (
            Path(plan.promotion_directory)
            / item.source_path
        )
        destination = (
            Path(plan.project_root)
            / item.destination_path
        )

        assert source.is_file()
        assert not destination.exists()

    assert plan.human_approval_verified is True
    assert (
        plan.verification_evidence_verified
        is True
    )
    assert plan.bundle_reverified is True
    assert plan.activation_ready is True
    assert plan.planning_performed is True

    assert plan.files_copied is False
    assert plan.activation_performed is False
    assert plan.registry_modified is False
    assert plan.implementation_trusted is False
    assert plan.promotion_performed is True
    assert plan.execution_performed is False


def test_rejects_rejected_activation_decision(
    tmp_path: Path,
) -> None:
    prepared = (
        prepared_persisted_verification(
            tmp_path
        )
    )
    decision_root = (
        tmp_path / "activation-decisions"
    )

    decision = (
        create_builder_activation_review_decision(
            verification_file=prepared[
                "verification_file"
            ],
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
            decision_id="activation-rejected-v1",
            reviewer_id="operator@example.com",
            decided_at=datetime(
                2026,
                9,
                1,
                15,
                0,
                tzinfo=timezone.utc,
            ),
            decision="rejected",
            rationale=(
                "Rejected the bundle for activation."
            ),
        )
    )

    persisted = (
        persist_builder_activation_review_decision(
            decision,
            decision_root=decision_root,
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
        )
    )

    with pytest.raises(
        BuilderActivationPlanError,
        match="does not authorize",
    ):
        plan_builder_activation(
            activation_decision_file=Path(
                persisted.decision_file
            ),
            activation_decision_root=(
                decision_root
            ),
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            promotion_plan_root=prepared[
                "plan_root"
            ],
            project_root=prepared[
                "project_root"
            ],
        )


def test_rejects_changed_promotion_bundle(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )
    persisted = persist(prepared)
    decision = prepared[
        "activation_decision"
    ]

    promoted_file = (
        Path(decision.promotion_directory)
        / "files"
        / decision.reviewed_paths[0]
    )
    promoted_file.write_text(
        '"""Changed before activation planning."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationPlanError,
        match="could not be reverified",
    ):
        plan_builder_activation(
            activation_decision_file=Path(
                persisted.decision_file
            ),
            activation_decision_root=prepared[
                "activation_decision_root"
            ],
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            promotion_plan_root=prepared[
                "plan_root"
            ],
            project_root=prepared[
                "project_root"
            ],
        )


def test_rejects_existing_trusted_destination(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )
    persisted = persist(prepared)
    decision = prepared[
        "activation_decision"
    ]

    destination = (
        Path(prepared["project_root"])
        / decision.reviewed_paths[0]
    )
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    destination.write_text(
        '"""Existing trusted file."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationPlanError,
        match="destination already exists",
    ):
        plan_builder_activation(
            activation_decision_file=Path(
                persisted.decision_file
            ),
            activation_decision_root=prepared[
                "activation_decision_root"
            ],
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            promotion_plan_root=prepared[
                "plan_root"
            ],
            project_root=prepared[
                "project_root"
            ],
        )


def test_rejects_symlinked_project_root(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )
    persisted = persist(prepared)

    real_root = Path(
        prepared["project_root"]
    )
    linked_root = tmp_path / "project-link"
    linked_root.symlink_to(
        real_root,
        target_is_directory=True,
    )

    with pytest.raises(
        BuilderActivationPlanError,
        match="project root cannot be a symlink",
    ):
        plan_builder_activation(
            activation_decision_file=Path(
                persisted.decision_file
            ),
            activation_decision_root=prepared[
                "activation_decision_root"
            ],
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            promotion_plan_root=prepared[
                "plan_root"
            ],
            project_root=linked_root,
        )


def test_schema_rejects_duplicate_destinations(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_plan(
        tmp_path
    )
    plan = prepared["activation_plan"]
    payload = plan.model_dump(mode="json")

    duplicate_destination = dict(
        payload["files"][0]
    )
    duplicate_destination["source_path"] = (
        "files/unique-duplicate-source.py"
    )
    payload["files"].append(
        duplicate_destination
    )

    with pytest.raises(
        ValidationError,
        match="destinations must be unique",
    ):
        BuilderActivationPlan.model_validate(
            payload
        )
