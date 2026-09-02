"""Tests for transactional Builder activation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from typer.testing import CliRunner

from geoagent_harness.cli import app

import geoagent_harness.builder.activation as activation_module
from geoagent_harness.builder import (
    BuilderActivationError,
    BuilderActivationManifest,
    activate_builder_bundle,
)
from tests.test_builder_activation_plan_storage import (
    prepared_persisted_activation_plan,
)

runner = CliRunner()

def activate(
    prepared: dict[str, object],
):
    plan = prepared["activation_plan"]
    persisted = prepared[
        "persisted_activation_plan"
    ]

    return activate_builder_bundle(
        plan_file=Path(persisted.plan_file),
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
        activation_root=prepared[
            "activation_root"
        ],
        confirm_activation_decision_id=(
            plan.activation_decision_id
        ),
        confirm_activation_plan_sha256=(
            persisted.activation_plan_sha256
        ),
    )


def prepared_activation(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = (
        prepared_persisted_activation_plan(
            tmp_path
        )
    )

    return {
        **prepared,
        "activation_root": (
            tmp_path / "activations"
        ),
    }


def test_activates_exact_files_and_writes_evidence(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation(tmp_path)
    plan = prepared["activation_plan"]

    result = activate(prepared)

    activation_directory = Path(
        result.activation_directory
    )
    manifest_file = Path(
        result.activation_manifest
    )

    assert activation_directory.is_dir()
    assert manifest_file.is_file()

    payload = json.loads(
        manifest_file.read_text(
            encoding="utf-8"
        )
    )
    manifest = (
        BuilderActivationManifest
        .model_validate(payload)
    )

    assert (
        manifest.activation_plan_sha256
        == prepared[
            "persisted_activation_plan"
        ].activation_plan_sha256
    )
    assert manifest.files_copied is True
    assert manifest.activation_performed is True
    assert (
        manifest.post_activation_verified
        is False
    )
    assert manifest.registry_modified is False
    assert manifest.implementation_trusted is False
    assert manifest.execution_performed is False

    assert result.files_copied is True
    assert result.activation_performed is True
    assert result.post_activation_verified is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is True
    assert result.execution_performed is False

    assert result.activated_paths == [
        item.destination_path
        for item in plan.files
    ]

    for item in plan.files:
        source = (
            Path(plan.promotion_directory)
            / item.source_path
        )
        destination = (
            Path(plan.project_root)
            / item.destination_path
        )

        assert destination.is_file()
        assert (
            destination.read_bytes()
            == source.read_bytes()
        )


@pytest.mark.parametrize(
    ("decision_id", "plan_digest", "message"),
    [
        (
            "wrong-activation-decision",
            None,
            "activation-decision confirmation",
        ),
        (
            None,
            "0" * 64,
            "activation-plan confirmation",
        ),
    ],
)
def test_rejects_incorrect_confirmation(
    tmp_path: Path,
    decision_id: str | None,
    plan_digest: str | None,
    message: str,
) -> None:
    prepared = prepared_activation(tmp_path)
    plan = prepared["activation_plan"]
    persisted = prepared[
        "persisted_activation_plan"
    ]

    with pytest.raises(
        BuilderActivationError,
        match=message,
    ):
        activate_builder_bundle(
            plan_file=Path(persisted.plan_file),
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
            project_root=prepared[
                "project_root"
            ],
            activation_root=prepared[
                "activation_root"
            ],
            confirm_activation_decision_id=(
                decision_id
                if decision_id is not None
                else plan.activation_decision_id
            ),
            confirm_activation_plan_sha256=(
                plan_digest
                if plan_digest is not None
                else persisted.activation_plan_sha256
            ),
        )

    for item in plan.files:
        assert not (
            Path(plan.project_root)
            / item.destination_path
        ).exists()


def test_rejects_destination_created_after_plan(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation(tmp_path)
    plan = prepared["activation_plan"]

    destination = (
        Path(plan.project_root)
        / plan.files[0].destination_path
    )
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    destination.write_text(
        '"""Appeared after planning."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationError,
        match="could not be reverified",
    ):
        activate(prepared)

    assert destination.read_text(
        encoding="utf-8"
    ) == '"""Appeared after planning."""\n'


def test_refuses_duplicate_activation(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation(tmp_path)

    first = activate(prepared)

    with pytest.raises(
        BuilderActivationError,
        match="evidence already exists",
    ):
        activate(prepared)

    assert Path(
        first.activation_directory
    ).is_dir()


def test_rejects_symlinked_activation_root(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation(tmp_path)

    real_root = tmp_path / "real-activations"
    real_root.mkdir()

    linked_root = tmp_path / "activation-link"
    linked_root.symlink_to(
        real_root,
        target_is_directory=True,
    )
    prepared["activation_root"] = linked_root

    with pytest.raises(
        BuilderActivationError,
        match="root cannot be a symlink",
    ):
        activate(prepared)

    assert list(real_root.iterdir()) == []


def test_rolls_back_partial_activation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    prepared = prepared_activation(tmp_path)
    plan = prepared["activation_plan"]

    real_replace = (
        activation_module.os.replace
    )
    call_count = 0

    def fail_second_replace(
        source,
        destination,
    ):
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise OSError(
                "injected activation failure"
            )

        return real_replace(
            source,
            destination,
        )

    monkeypatch.setattr(
        activation_module.os,
        "replace",
        fail_second_replace,
    )

    with pytest.raises(
        BuilderActivationError,
        match="transaction failed",
    ):
        activate(prepared)

    for item in plan.files:
        destination = (
            Path(plan.project_root)
            / item.destination_path
        )
        assert not destination.exists()

    activation_root = Path(
        prepared["activation_root"]
    )

    assert (
        not activation_root.exists()
        or not list(
            activation_root.glob("*.activation")
        )
    )

    temporary_files = [
        path
        for path in Path(
            plan.project_root
        ).rglob(
            "*.geoagent-activation-*"
        )
    ]
    assert temporary_files == []

def test_cli_activates_exact_builder_bundle(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation(tmp_path)
    plan = prepared["activation_plan"]
    persisted = prepared[
        "persisted_activation_plan"
    ]

    result = runner.invoke(
        app,
        [
            "activate-builder-bundle",
            str(persisted.plan_file),
            "--activation-plan-root",
            str(prepared["activation_plan_root"]),
            "--activation-decision-root",
            str(
                prepared[
                    "activation_decision_root"
                ]
            ),
            "--verification-root",
            str(prepared["verification_root"]),
            "--promotion-root",
            str(prepared["promotion_root"]),
            "--promotion-plan-root",
            str(prepared["plan_root"]),
            "--project-root",
            str(prepared["project_root"]),
            "--activation-root",
            str(prepared["activation_root"]),
            "--confirm-activation-decision-id",
            plan.activation_decision_id,
            "--confirm-activation-plan-sha256",
            persisted.activation_plan_sha256,
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["files_copied"] is True
    assert payload["activation_performed"] is True
    assert (
        payload["post_activation_verified"]
        is False
    )
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["promotion_performed"] is True
    assert payload["execution_performed"] is False

    for item in plan.files:
        assert (
            Path(plan.project_root)
            / item.destination_path
        ).is_file()


def test_cli_requires_exact_activation_confirmations(
) -> None:
    result = runner.invoke(
        app,
        [
            "activate-builder-bundle",
            "example/ACTIVATION_PLAN.json",
        ],
    )

    assert result.exit_code == 2
    assert (
        "--confirm-activation-decision-id "
        "is required"
        in result.output
    )
