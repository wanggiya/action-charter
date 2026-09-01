"""Tests for immutable Builder activation plans."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from geoagent_harness.builder import (
    BuilderActivationPlanStorageError,
    builder_activation_plan_sha256,
    load_builder_activation_plan,
    persist_builder_activation_plan,
)
from geoagent_harness.cli import app
from tests.test_builder_activation_plan import (
    prepared_activation_plan,
)


runner = CliRunner()


def prepared_persisted_activation_plan(
    tmp_path: Path,
) -> dict[str, object]:
    prepared = prepared_activation_plan(
        tmp_path
    )
    activation_plan_root = (
        tmp_path / "activation-plans"
    )

    result = persist_builder_activation_plan(
        prepared["activation_plan"],
        plan_root=activation_plan_root,
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
        "activation_plan_root": (
            activation_plan_root
        ),
        "persisted_activation_plan": result,
    }


def test_persists_activation_plan(
    tmp_path: Path,
) -> None:
    prepared = (
        prepared_persisted_activation_plan(
            tmp_path
        )
    )
    plan = prepared["activation_plan"]
    result = prepared[
        "persisted_activation_plan"
    ]
    plan_file = Path(result.plan_file)

    assert plan_file.is_file()
    assert plan_file.name == (
        "ACTIVATION_PLAN.json"
    )
    assert result.plan_persisted is True
    assert result.human_approval_verified is True
    assert result.bundle_reverified is True
    assert result.activation_ready is True
    assert result.files_copied is False
    assert result.activation_performed is False
    assert result.registry_modified is False
    assert result.implementation_trusted is False
    assert result.promotion_performed is True
    assert result.execution_performed is False

    assert result.activation_plan_sha256 == (
        builder_activation_plan_sha256(plan)
    )

    loaded, digest, safe_file = (
        load_builder_activation_plan(
            plan_file,
            plan_root=prepared[
                "activation_plan_root"
            ],
        )
    )

    assert loaded == plan
    assert digest == (
        result.activation_plan_sha256
    )
    assert safe_file == plan_file.resolve()


def test_refuses_duplicate_activation_plan(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_plan(
        tmp_path
    )
    activation_plan_root = (
        tmp_path / "activation-plans"
    )

    arguments = {
        "plan_root": activation_plan_root,
        "activation_decision_root": prepared[
            "activation_decision_root"
        ],
        "verification_root": prepared[
            "verification_root"
        ],
        "promotion_root": prepared[
            "promotion_root"
        ],
        "promotion_plan_root": prepared[
            "plan_root"
        ],
        "project_root": prepared[
            "project_root"
        ],
    }

    persist_builder_activation_plan(
        prepared["activation_plan"],
        **arguments,
    )

    with pytest.raises(
        BuilderActivationPlanStorageError,
        match="already exists",
    ):
        persist_builder_activation_plan(
            prepared["activation_plan"],
            **arguments,
        )


def test_rejects_changed_bundle_before_plan_storage(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_plan(
        tmp_path
    )
    plan = prepared["activation_plan"]

    promoted_file = (
        Path(plan.promotion_directory)
        / plan.files[0].source_path
    )
    promoted_file.write_text(
        '"""Changed before plan persistence."""\n',
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationPlanStorageError,
        match="could not be reverified",
    ):
        persist_builder_activation_plan(
            plan,
            plan_root=(
                tmp_path / "activation-plans"
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


def test_rejects_noncanonical_activation_plan(
    tmp_path: Path,
) -> None:
    prepared = (
        prepared_persisted_activation_plan(
            tmp_path
        )
    )
    plan_file = Path(
        prepared[
            "persisted_activation_plan"
        ].plan_file
    )

    payload = json.loads(
        plan_file.read_text(
            encoding="utf-8"
        )
    )
    plan_file.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        BuilderActivationPlanStorageError,
        match="directory digest is invalid",
    ):
        load_builder_activation_plan(
            plan_file,
            plan_root=prepared[
                "activation_plan_root"
            ],
        )


def test_rejects_symlinked_activation_plan_root(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_plan(
        tmp_path
    )

    real_root = tmp_path / "real-plans"
    real_root.mkdir()

    linked_root = tmp_path / "plan-link"
    linked_root.symlink_to(
        real_root,
        target_is_directory=True,
    )

    with pytest.raises(
        BuilderActivationPlanStorageError,
        match="root cannot be a symlink",
    ):
        persist_builder_activation_plan(
            prepared["activation_plan"],
            plan_root=linked_root,
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

    assert list(real_root.iterdir()) == []


def test_cli_plans_activation_without_writes(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_plan(
        tmp_path
    )
    decision_file = prepared[
        "persisted_activation_decision"
    ].decision_file

    result = runner.invoke(
        app,
        [
            "plan-builder-activation",
            str(decision_file),
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
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["activation_ready"] is True
    assert payload["planning_performed"] is True
    assert payload["files_copied"] is False
    assert payload["activation_performed"] is False
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["execution_performed"] is False


def test_cli_creates_immutable_activation_plan(
    tmp_path: Path,
) -> None:
    prepared = prepared_activation_plan(
        tmp_path
    )
    decision_file = prepared[
        "persisted_activation_decision"
    ].decision_file
    activation_plan_root = (
        tmp_path / "activation-plans"
    )

    result = runner.invoke(
        app,
        [
            "create-builder-activation-plan",
            str(decision_file),
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
            "--activation-plan-root",
            str(activation_plan_root),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload["plan_persisted"] is True
    assert payload["activation_ready"] is True
    assert payload["files_copied"] is False
    assert payload["activation_performed"] is False
    assert payload["registry_modified"] is False
    assert payload["implementation_trusted"] is False
    assert payload["execution_performed"] is False
    assert Path(payload["plan_file"]).is_file()
