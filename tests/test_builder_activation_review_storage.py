"""Tests for immutable Builder activation decisions."""

from __future__ import annotations

import json
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pytest
from typer.testing import CliRunner

from geoagent_harness.builder import (
    BuilderActivationReviewDecisionStorageError,
    builder_activation_review_sha256,
    create_builder_activation_review_decision,
    load_builder_activation_review_decision,
    persist_builder_activation_review_decision,
)
from geoagent_harness.cli import app
from tests.test_builder_activation_review import (
    prepared_persisted_verification,
)


runner = CliRunner()

DECIDED_AT = datetime(
    2026,
    9,
    1,
    14,
    0,
    tzinfo=timezone.utc,
)


def prepared_activation_decision(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = (
        prepared_persisted_verification(
            tmp_path
        )
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
            decision_id="activation-storage-v1",
            reviewer_id="operator@example.com",
            decided_at=DECIDED_AT,
            decision="approved",
            rationale=(
                "Approved the exact verified bundle "
                "for activation planning."
            ),
        )
    )

    return {
        **prepared,
        "activation_decision": decision,
        "activation_decision_root": (
            tmp_path / "activation-decisions"
        ),
    }


def persist(
    prepared: dict[str, object],
):
    return persist_builder_activation_review_decision(
        prepared["activation_decision"],
        decision_root=prepared[
            "activation_decision_root"
        ],
        verification_root=prepared[
            "verification_root"
        ],
        promotion_root=prepared[
            "promotion_root"
        ],
        plan_root=prepared["plan_root"],
    )


def test_persists_activation_review_decision(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )
    decision = prepared[
        "activation_decision"
    ]

    result = persist(prepared)

    decision_file = Path(result.decision_file)

    assert decision_file.is_file()
    assert decision_file.name == (
        "ACTIVATION_DECISION.json"
    )
    assert result.decision == "approved"
    assert result.decision_persisted is True
    assert result.human_review_performed is True
    assert (
        result.verification_evidence_verified
        is True
    )
    assert result.bundle_reverified is True
    assert result.approval_granted is True
    assert (
        result.activation_planning_authorized
        is True
    )
    assert result.activation_performed is False
    assert result.files_copied is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is True
    assert result.execution_performed is False

    assert (
        result.activation_decision_sha256
        == builder_activation_review_sha256(
            decision
        )
    )

    loaded, digest, safe_file = (
        load_builder_activation_review_decision(
            decision_file,
            decision_root=prepared[
                "activation_decision_root"
            ],
        )
    )

    assert loaded == decision
    assert digest == (
        result.activation_decision_sha256
    )
    assert safe_file == decision_file.resolve()


def test_refuses_duplicate_activation_decision(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )

    persist(prepared)

    with pytest.raises(
        BuilderActivationReviewDecisionStorageError,
        match="already exists",
    ):
        persist(prepared)


def test_rejects_changed_bundle_before_storage(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )
    decision = prepared[
        "activation_decision"
    ]

    promoted_file = (
        Path(decision.promotion_directory)
        / "files"
        / decision.reviewed_paths[0]
    )
    promoted_file.write_text(
        '"""Changed before decision storage."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationReviewDecisionStorageError,
        match="could not be reverified",
    ):
        persist(prepared)


def test_rejects_noncanonical_activation_decision(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )
    result = persist(prepared)
    decision_file = Path(result.decision_file)

    payload = json.loads(
        decision_file.read_text(
            encoding="utf-8"
        )
    )
    decision_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationReviewDecisionStorageError,
        match="directory digest is invalid",
    ):
        load_builder_activation_review_decision(
            decision_file,
            decision_root=prepared[
                "activation_decision_root"
            ],
        )


def test_rejects_symlinked_decision_root(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_decision(
        tmp_path
    )

    real_root = tmp_path / "real-decisions"
    real_root.mkdir()

    linked_root = tmp_path / "decision-link"
    linked_root.symlink_to(
        real_root,
        target_is_directory=True,
    )
    prepared[
        "activation_decision_root"
    ] = linked_root

    with pytest.raises(
        BuilderActivationReviewDecisionStorageError,
        match="root cannot be a symlink",
    ):
        persist(prepared)

    assert list(real_root.iterdir()) == []


def test_cli_creates_activation_review_decision(
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

    result = runner.invoke(
        app,
        [
            "create-builder-activation-review",
            str(prepared["verification_file"]),
            "--verification-root",
            str(prepared["verification_root"]),
            "--promotion-root",
            str(prepared["promotion_root"]),
            "--plan-root",
            str(prepared["plan_root"]),
            "--decision-root",
            str(decision_root),
            "--decision-id",
            "activation-cli-v1",
            "--reviewer-id",
            "operator@example.com",
            "--decided-at",
            "2026-09-01T14:00:00+00:00",
            "--decision",
            "approved",
            "--rationale",
            "Approved exact verified bundle.",
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["decision"] == "approved"
    assert payload["decision_persisted"] is True
    assert payload["approval_granted"] is True
    assert (
        payload["activation_planning_authorized"]
        is True
    )
    assert payload["activation_performed"] is False
    assert payload["files_copied"] is False
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is True
    assert payload["execution_performed"] is False
    assert Path(payload["decision_file"]).is_file()
