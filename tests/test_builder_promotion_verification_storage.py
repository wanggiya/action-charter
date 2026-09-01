"""Tests for immutable Builder verification evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from geoagent_harness.builder import (
    BuilderPromotionVerificationStorageError,
    builder_promotion_verification_sha256,
    load_builder_promotion_verification,
    persist_builder_promotion_verification,
    verify_builder_promotion_bundle,
)
from geoagent_harness.cli import app
from tests.test_builder_promotion import (
    prepared_persisted_plan,
    promote,
)


runner = CliRunner()


def prepared_verification(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = prepared_persisted_plan(
        tmp_path
    )
    promotion = promote(prepared)

    verification = (
        verify_builder_promotion_bundle(
            promotion_directory=Path(
                promotion.promotion_directory
            ),
            promotion_root=Path(
                prepared["promotion_root"]
            ),
            plan_file=Path(
                prepared["plan_file"]
            ),
            plan_root=Path(
                prepared["plan_root"]
            ),
        )
    )

    return {
        **prepared,
        "promotion": promotion,
        "verification": verification,
        "verification_root": (
            tmp_path / "verifications"
        ),
    }


def test_persists_immutable_verification_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_verification(tmp_path)
    verification = prepared["verification"]

    result = (
        persist_builder_promotion_verification(
            verification,
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
        )
    )

    verification_file = Path(
        result.verification_file
    )

    assert verification_file.is_file()
    assert verification_file.name == (
        "VERIFICATION.json"
    )

    payload = json.loads(
        verification_file.read_text(
            encoding="utf-8"
        )
    )

    assert payload["post_promotion_verified"] is True
    assert (
        payload["eligible_for_activation_review"]
        is True
    )
    assert (
        payload["verification_evidence_persisted"]
        is False
    )
    assert payload["activation_performed"] is False
    assert payload["implementation_trusted"] is False

    assert result.verification_evidence_persisted is True
    assert result.post_promotion_verified is True
    assert (
        result.eligible_for_activation_review
        is True
    )
    assert result.activation_performed is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is True
    assert result.execution_performed is False

    assert result.verification_sha256 == (
        builder_promotion_verification_sha256(
            verification
        )
    )

    loaded = load_builder_promotion_verification(
        verification_file,
        verification_root=prepared[
            "verification_root"
        ],
    )

    assert loaded == verification


def test_refuses_existing_verification_package(
    tmp_path: Path,
) -> None:
    prepared = prepared_verification(tmp_path)
    verification = prepared["verification"]

    persist_builder_promotion_verification(
        verification,
        verification_root=prepared[
            "verification_root"
        ],
        promotion_root=prepared[
            "promotion_root"
        ],
        plan_root=prepared["plan_root"],
    )

    with pytest.raises(
        BuilderPromotionVerificationStorageError,
        match="already exists",
    ):
        persist_builder_promotion_verification(
            verification,
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
        )


def test_rejects_changed_bundle_before_persistence(
    tmp_path: Path,
) -> None:
    prepared = prepared_verification(tmp_path)
    verification = prepared["verification"]

    promoted_file = (
        Path(verification.promotion_directory)
        / "files"
        / verification.verified_paths[0]
    )
    promoted_file.write_text(
        '"""Changed after verification."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionVerificationStorageError,
        match="could not be reverified",
    ):
        persist_builder_promotion_verification(
            verification,
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
        )

    verification_root = Path(
        prepared["verification_root"]
    )

    assert (
        not verification_root.exists()
        or not list(
            verification_root.glob(
                "*.verification"
            )
        )
    )


def test_rejects_noncanonical_verification_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_verification(tmp_path)
    verification = prepared["verification"]

    result = (
        persist_builder_promotion_verification(
            verification,
            verification_root=prepared[
                "verification_root"
            ],
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
        )
    )

    verification_file = Path(
        result.verification_file
    )
    payload = json.loads(
        verification_file.read_text(
            encoding="utf-8"
        )
    )
    verification_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionVerificationStorageError,
        match="not canonical",
    ):
        load_builder_promotion_verification(
            verification_file,
            verification_root=prepared[
                "verification_root"
            ],
        )


def test_rejects_symlinked_verification_root(
    tmp_path: Path,
) -> None:
    prepared = prepared_verification(tmp_path)

    real_root = tmp_path / "real-verifications"
    real_root.mkdir()

    linked_root = tmp_path / "verification-link"
    linked_root.symlink_to(
        real_root,
        target_is_directory=True,
    )

    with pytest.raises(
        BuilderPromotionVerificationStorageError,
        match="root cannot be a symlink",
    ):
        persist_builder_promotion_verification(
            prepared["verification"],
            verification_root=linked_root,
            promotion_root=prepared[
                "promotion_root"
            ],
            plan_root=prepared["plan_root"],
        )

    assert list(real_root.iterdir()) == []


def test_cli_creates_persisted_verification(
    tmp_path: Path,
) -> None:
    prepared = prepared_verification(tmp_path)
    promotion = prepared["promotion"]

    result = runner.invoke(
        app,
        [
            "create-builder-promotion-verification",
            str(promotion.promotion_directory),
            str(prepared["plan_file"]),
            "--promotion-root",
            str(prepared["promotion_root"]),
            "--plan-root",
            str(prepared["plan_root"]),
            "--verification-root",
            str(prepared["verification_root"]),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["post_promotion_verified"] is True
    assert (
        payload["eligible_for_activation_review"]
        is True
    )
    assert (
        payload["verification_evidence_persisted"]
        is True
    )
    assert payload["activation_performed"] is False
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is True
    assert payload["execution_performed"] is False

    assert Path(
        payload["verification_file"]
    ).is_file()
