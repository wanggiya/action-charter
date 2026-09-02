"""Tests for immutable Builder trust evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from geoagent_harness.builder import (
    BuilderPostActivationVerificationStorageError,
    builder_trust_evidence_sha256,
    load_builder_trust_evidence,
    persist_builder_trust_evidence,
)
from geoagent_harness.cli import app
from tests.test_builder_post_activation_verification import (
    prepared_activated_bundle,
    verify,
)


runner = CliRunner()


def prepared_trust_evidence(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    verification = verify(prepared)

    return {
        **prepared,
        "post_activation_verification": (
            verification
        ),
        "trust_evidence_root": (
            tmp_path / "trust-evidence"
        ),
    }


def persist(
    prepared: dict[str, object],
):
    return persist_builder_trust_evidence(
        prepared[
            "post_activation_verification"
        ],
        evidence_root=prepared[
            "trust_evidence_root"
        ],
        activation_root=prepared[
            "activation_root"
        ],
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


def test_persists_trust_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_trust_evidence(
        tmp_path
    )
    verification = prepared[
        "post_activation_verification"
    ]

    result = persist(prepared)
    evidence_file = Path(
        result.evidence_file
    )

    assert evidence_file.is_file()
    assert evidence_file.name == (
        "POST_ACTIVATION_VERIFICATION.json"
    )
    assert result.post_activation_verified is True
    assert result.trust_evidence_persisted is True
    assert result.implementation_trusted is True
    assert result.activation_performed is True
    assert result.files_copied is True
    assert result.registry_modified is False
    assert result.execution_performed is False

    assert result.trust_evidence_sha256 == (
        builder_trust_evidence_sha256(
            verification
        )
    )

    loaded, digest, safe_file = (
        load_builder_trust_evidence(
            evidence_file,
            evidence_root=prepared[
                "trust_evidence_root"
            ],
        )
    )

    assert loaded == verification
    assert digest == result.trust_evidence_sha256
    assert safe_file == evidence_file.resolve()


def test_refuses_duplicate_trust_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_trust_evidence(
        tmp_path
    )

    persist(prepared)

    with pytest.raises(
        BuilderPostActivationVerificationStorageError,
        match="already exists",
    ):
        persist(prepared)


def test_rejects_changed_file_before_persistence(
    tmp_path: Path,
) -> None:
    prepared = prepared_trust_evidence(
        tmp_path
    )
    verification = prepared[
        "post_activation_verification"
    ]

    destination = (
        Path(verification.project_root)
        / verification.verified_paths[0]
    )
    destination.write_text(
        '"""Changed before trust persistence."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPostActivationVerificationStorageError,
        match="could not be reverified",
    ):
        persist(prepared)


def test_rejects_noncanonical_trust_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_trust_evidence(
        tmp_path
    )
    result = persist(prepared)
    evidence_file = Path(
        result.evidence_file
    )

    payload = json.loads(
        evidence_file.read_text(
            encoding="utf-8"
        )
    )
    evidence_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPostActivationVerificationStorageError,
        match="directory digest is invalid",
    ):
        load_builder_trust_evidence(
            evidence_file,
            evidence_root=prepared[
                "trust_evidence_root"
            ],
        )


def test_rejects_symlinked_trust_root(
    tmp_path: Path,
) -> None:
    prepared = prepared_trust_evidence(
        tmp_path
    )

    real_root = tmp_path / "real-trust"
    real_root.mkdir()

    linked_root = tmp_path / "trust-link"
    linked_root.symlink_to(
        real_root,
        target_is_directory=True,
    )
    prepared["trust_evidence_root"] = (
        linked_root
    )

    with pytest.raises(
        BuilderPostActivationVerificationStorageError,
        match="root cannot be a symlink",
    ):
        persist(prepared)

    assert list(real_root.iterdir()) == []


def _cli_arguments(
    prepared: dict[str, object],
) -> list[str]:
    activation = prepared[
        "activation_result"
    ]
    persisted_plan = prepared[
        "persisted_activation_plan"
    ]

    return [
        str(activation.activation_directory),
        str(persisted_plan.plan_file),
        "--activation-root",
        str(prepared["activation_root"]),
        "--activation-plan-root",
        str(prepared["activation_plan_root"]),
        "--activation-decision-root",
        str(prepared["activation_decision_root"]),
        "--verification-root",
        str(prepared["verification_root"]),
        "--promotion-root",
        str(prepared["promotion_root"]),
        "--promotion-plan-root",
        str(prepared["plan_root"]),
        "--project-root",
        str(prepared["project_root"]),
    ]


def test_cli_verifies_activation(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )

    result = runner.invoke(
        app,
        [
            "verify-builder-activation",
            *_cli_arguments(prepared),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["post_activation_verified"] is True
    assert payload["trust_evidence_persisted"] is False
    assert payload["implementation_trusted"] is True
    assert payload["registry_modified"] is False
    assert payload["execution_performed"] is False


def test_cli_creates_trust_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_activated_bundle(
        tmp_path
    )
    trust_root = tmp_path / "trust-evidence"

    result = runner.invoke(
        app,
        [
            "create-builder-trust-evidence",
            *_cli_arguments(prepared),
            "--trust-evidence-root",
            str(trust_root),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["post_activation_verified"] is True
    assert payload["trust_evidence_persisted"] is True
    assert payload["implementation_trusted"] is True
    assert payload["activation_performed"] is True
    assert payload["registry_modified"] is False
    assert payload["execution_performed"] is False
    assert Path(payload["evidence_file"]).is_file()
