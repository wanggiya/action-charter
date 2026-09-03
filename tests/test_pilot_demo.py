"""Tests for the read-only pilot demonstration readiness boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.pilot_demo import (
    PilotDemoError,
    PilotDemoNextAction,
    assess_pilot_demo_readiness,
    load_pilot_demo_definition,
)


PROJECT_ROOT = Path(__file__).parents[1]
DEFINITION = Path("demonstrations/checkpoint14f/DEMO.json")


def test_fixed_demo_is_ready_without_mutation() -> None:
    result = assess_pilot_demo_readiness(
        DEFINITION,
        project_root=PROJECT_ROOT,
    )

    assert result.repository_ready is True
    assert result.next_action == PilotDemoNextAction.PROPOSE_WORKFLOW
    assert result.violations == []
    assert [case.case_id for case in result.cases] == [
        "invalid_geometry",
        "clean",
    ]
    assert result.cases[0].observed_failed_checks == ["invalid_geometry"]
    assert result.cases[1].observed_failed_checks == []
    assert result.workflow_dataset == "data/input/sample_points.geojson"
    assert len(result.workflow_dataset_sha256) == 64
    assert all(case.dataset_unchanged for case in result.cases)
    assert result.model_called is False
    assert result.approval_created is False
    assert result.workflow_executed is False
    assert result.filesystem_modified is False
    assert result.database_modified is False
    assert result.release_created is False
    assert result.snakemake_invoked is False


def test_definition_rejects_automatic_clean_failure_claim(tmp_path: Path) -> None:
    payload = json.loads((PROJECT_ROOT / DEFINITION).read_text(encoding="utf-8"))
    payload["corrected_case"]["expected_failed_checks"] = ["crs"]
    path = tmp_path / "DEMO.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PilotDemoError, match="schema validation"):
        load_pilot_demo_definition(path, project_root=tmp_path)


def test_definition_rejects_workflow_dataset_outside_input(tmp_path: Path) -> None:
    payload = json.loads((PROJECT_ROOT / DEFINITION).read_text(encoding="utf-8"))
    payload["workflow_dataset"] = "benchmarks/clean.geojson"
    path = tmp_path / "DEMO.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PilotDemoError, match="schema validation"):
        load_pilot_demo_definition(path, project_root=tmp_path)


def test_definition_rejects_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    real.write_text((PROJECT_ROOT / DEFINITION).read_text(encoding="utf-8"), encoding="utf-8")
    linked = tmp_path / "DEMO.json"
    linked.symlink_to(real)

    with pytest.raises(PilotDemoError, match="symlink"):
        load_pilot_demo_definition(linked, project_root=tmp_path)
