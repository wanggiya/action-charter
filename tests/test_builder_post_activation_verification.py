"""Tests for Builder post-activation verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.builder import (
    BuilderPostActivationVerificationError,
    verify_builder_activation,
)
from tests.test_builder_activation import (
    activate,
    prepared_activation,
)


def prepared_activated_bundle(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = prepared_activation(
        tmp_path
    )
    activation = activate(prepared)

    return {
        **prepared,
        "activation_result": activation,
    }


def verify(
    prepared: dict[str, object],
):
    activation = prepared[
        "activation_result"
    ]
    persisted_plan = prepared[
        "persisted_activation_plan"
    ]

    return verify_builder_activation(
        activation_directory=Path(
            activation.activation_directory
        ),
        activation_root=prepared[
            "activation_root"
        ],
        activation_plan_file=Path(
            persisted_plan.plan_file
        ),
        activation_plan_root=prepared[
            "activation_plan_root"
        ],
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


def test_verifies_activated_files_and_establishes_trust(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    plan = prepared["activation_plan"]

    result = verify(prepared)

    assert result.task_id == plan.task_id
    assert (
        result.activation_decision_id
        == plan.activation_decision_id
    )
    assert (
        result.activation_plan_sha256
        == prepared[
            "persisted_activation_plan"
        ].activation_plan_sha256
    )
    assert result.verified_paths == [
        item.destination_path
        for item in plan.files
    ]

    assert (
        result.activation_manifest_canonical
        is True
    )
    assert (
        result.activation_directory_identity_verified
        is True
    )
    assert result.activation_plan_bound is True
    assert result.upstream_evidence_verified is True
    assert (
        result.exact_activated_file_set_verified
        is True
    )
    assert (
        result.activated_file_digests_verified
        is True
    )
    assert result.activated_files_unchanged is True

    assert result.post_activation_verified is True
    assert result.trust_evidence_persisted is False
    assert result.implementation_trusted is True

    assert result.activation_performed is True
    assert result.files_copied is True
    assert result.registry_modified is False
    assert result.promotion_performed is True
    assert result.execution_performed is False


def test_rejects_changed_installed_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    plan = prepared["activation_plan"]

    destination = (
        Path(plan.project_root)
        / plan.files[0].destination_path
    )
    destination.write_text(
        '"""Changed after activation."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPostActivationVerificationError,
        match="digest does not match",
    ):
        verify(prepared)


def test_rejects_missing_installed_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    plan = prepared["activation_plan"]

    destination = (
        Path(plan.project_root)
        / plan.files[0].destination_path
    )
    destination.unlink()

    with pytest.raises(
        BuilderPostActivationVerificationError,
        match="file is unavailable",
    ):
        verify(prepared)


def test_rejects_symlinked_installed_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    plan = prepared["activation_plan"]

    destination = (
        Path(plan.project_root)
        / plan.files[0].destination_path
    )
    source = (
        Path(plan.promotion_directory)
        / plan.files[0].source_path
    )

    destination.unlink()
    destination.symlink_to(source)

    with pytest.raises(
        BuilderPostActivationVerificationError,
        match="contains a symlink",
    ):
        verify(prepared)


def test_rejects_unexpected_activation_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    activation = prepared[
        "activation_result"
    ]

    extra = (
        Path(activation.activation_directory)
        / "unexpected.txt"
    )
    extra.write_text(
        "unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPostActivationVerificationError,
        match="unexpected entries",
    ):
        verify(prepared)


def test_rejects_changed_upstream_promotion(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    plan = prepared["activation_plan"]

    promoted_file = (
        Path(plan.promotion_directory)
        / plan.files[0].source_path
    )
    promoted_file.write_text(
        '"""Changed promoted source."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPostActivationVerificationError,
        match="could not be reverified",
    ):
        verify(prepared)


def test_rejects_noncanonical_activation_manifest(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    manifest_file = Path(
        prepared[
            "activation_result"
        ].activation_manifest
    )

    payload = json.loads(
        manifest_file.read_text(
            encoding="utf-8"
        )
    )
    manifest_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPostActivationVerificationError,
        match="not canonical",
    ):
        verify(prepared)
