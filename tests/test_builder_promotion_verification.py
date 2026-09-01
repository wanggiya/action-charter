"""Tests for independent Builder-bundle verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import geoagent_harness.builder as builder
from geoagent_harness.builder import (
    BuilderPromotionVerificationError,
    verify_builder_promotion_bundle,
)
from geoagent_harness.cli import app
from tests.test_builder_promotion import (
    prepared_persisted_plan,
    promote,
)


runner = CliRunner()


def prepared_bundle(
    tmp_path: Path,
) -> dict[str, object]:
    """Create one valid promoted bundle and its plan."""

    prepared = prepared_persisted_plan(
        tmp_path
    )
    promotion = promote(prepared)

    return {
        **prepared,
        "promotion": promotion,
        "promotion_directory": Path(
            promotion.promotion_directory
        ),
        "promotion_manifest": Path(
            promotion.promotion_manifest
        ),
    }


def verify(prepared: dict[str, object]):
    """Verify one prepared bundle."""

    return verify_builder_promotion_bundle(
        prepared["promotion_directory"],
        promotion_root=prepared["promotion_root"],
        plan_file=prepared["plan_file"],
        plan_root=prepared["plan_root"],
    )


def test_verifies_exact_promoted_bundle_read_only(
    tmp_path: Path,
) -> None:
    prepared = prepared_bundle(tmp_path)
    promotion_directory = prepared[
        "promotion_directory"
    ]
    manifest_file = prepared[
        "promotion_manifest"
    ]

    manifest_before = manifest_file.read_bytes()
    file_states_before = {
        path.relative_to(
            promotion_directory
        ).as_posix(): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in promotion_directory.rglob("*")
        if path.is_file()
    }

    result = verify(prepared)

    assert result.manifest_canonical is True
    assert result.directory_identity_verified is True
    assert result.exact_file_set_verified is True
    assert (
        result.promoted_file_digests_verified
        is True
    )
    assert result.bundle_unchanged is True
    assert result.post_promotion_verified is True
    assert (
        result.eligible_for_activation_review
        is True
    )

    assert (
        result.verification_evidence_persisted
        is False
    )
    assert result.activation_performed is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is True
    assert result.execution_performed is False

    assert manifest_file.read_bytes() == (
        manifest_before
    )

    file_states_after = {
        path.relative_to(
            promotion_directory
        ).as_posix(): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in promotion_directory.rglob("*")
        if path.is_file()
    }

    assert file_states_after == file_states_before


def test_rejects_changed_promoted_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_bundle(tmp_path)
    plan = prepared["plan"]

    changed = (
        prepared["promotion_directory"]
        / "files"
        / plan.files[0].destination_path
    )
    changed.write_text(
        '"""Changed after promotion."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionVerificationError,
        match="file digest does not match",
    ):
        verify(prepared)


def test_rejects_extra_bundle_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_bundle(tmp_path)

    extra = (
        prepared["promotion_directory"]
        / "files"
        / "unexpected.txt"
    )
    extra.write_text(
        "unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderPromotionVerificationError,
        match="file set does not match",
    ):
        verify(prepared)


def test_rejects_missing_promoted_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_bundle(tmp_path)
    plan = prepared["plan"]

    missing = (
        prepared["promotion_directory"]
        / "files"
        / plan.files[0].destination_path
    )
    missing.unlink()

    with pytest.raises(
        BuilderPromotionVerificationError,
        match="file set does not match",
    ):
        verify(prepared)


def test_rejects_noncanonical_manifest(
    tmp_path: Path,
) -> None:
    prepared = prepared_bundle(tmp_path)
    manifest_file = prepared[
        "promotion_manifest"
    ]

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
        BuilderPromotionVerificationError,
        match="manifest is not canonical",
    ):
        verify(prepared)


def test_rejects_symlinked_promoted_file(
    tmp_path: Path,
) -> None:
    prepared = prepared_bundle(tmp_path)
    plan = prepared["plan"]

    promoted = (
        prepared["promotion_directory"]
        / "files"
        / plan.files[0].destination_path
    )
    candidate = (
        Path(plan.candidate_path)
        / plan.files[0].source_path
    )

    promoted.unlink()
    promoted.symlink_to(candidate)

    with pytest.raises(
        BuilderPromotionVerificationError,
        match="cannot contain symlinks",
    ):
        verify(prepared)


def test_cli_verifies_builder_promotion(
    tmp_path: Path,
) -> None:
    prepared = prepared_bundle(tmp_path)

    result = runner.invoke(
        app,
        [
            "verify-builder-promotion",
            str(prepared["promotion_directory"]),
            str(prepared["plan_file"]),
            "--promotion-root",
            str(prepared["promotion_root"]),
            "--plan-root",
            str(prepared["plan_root"]),
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
        is False
    )
    assert payload["activation_performed"] is False
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["execution_performed"] is False


def test_cli_reports_verification_failure(
    monkeypatch,
) -> None:
    def reject(*args, **kwargs):
        raise BuilderPromotionVerificationError(
            "Builder promotion bundle file set "
            "does not match"
        )

    monkeypatch.setattr(
        builder,
        "verify_builder_promotion_bundle",
        reject,
    )

    result = runner.invoke(
        app,
        [
            "verify-builder-promotion",
            "example.promotion",
            "example.plan/PLAN.json",
        ],
    )

    assert result.exit_code == 2
    assert "file set does not match" in (
        result.output
    )
