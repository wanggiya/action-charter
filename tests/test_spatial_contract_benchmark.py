"""Regression tests for the dirty-vector contract benchmark."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geoagent_harness.spatial_contracts import (
    assess_spatial_data_contract,
    load_spatial_data_contract,
)


PROJECT_ROOT = Path(__file__).parents[1]
BENCHMARK_ROOT = (
    PROJECT_ROOT
    / "benchmarks"
    / "spatial-contracts"
    / "vector"
)
DATA_ROOT = BENCHMARK_ROOT / "data"


def _manifest() -> dict:
    return json.loads(
        (BENCHMARK_ROOT / "BENCHMARK.json").read_text(
            encoding="utf-8"
        )
    )


CASES = _manifest()["cases"]


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[case["id"] for case in CASES],
)
def test_benchmark_case_matches_expected_checks(case: dict) -> None:
    contract = load_spatial_data_contract(
        BENCHMARK_ROOT / "contract.yaml",
        contract_root=BENCHMARK_ROOT,
    )

    result = assess_spatial_data_contract(
        path=DATA_ROOT / case["dataset"],
        contract=contract,
        input_root=DATA_ROOT,
    )

    failed = sorted(
        check.check_id
        for check in result.checks
        if not check.passed
    )

    assert failed == sorted(case["expected_failed_checks"])
    assert result.passed is (not failed)
    assert result.dataset_unchanged is True
    assert result.filesystem_modified is False
    assert result.database_modified is False
    assert result.execution_performed is False


def test_manifest_contains_required_presentation_failures() -> None:
    case_ids = {case["id"] for case in CASES}

    assert {
        "clean",
        "wrong_crs",
        "missing_crs",
        "invalid_geometry",
        "null_geometry",
        "duplicate_identifiers",
        "missing_fields",
        "incorrect_field_types",
        "unexpected_extent",
        "empty_data",
        "mixed_geometry",
    }.issubset(case_ids)
