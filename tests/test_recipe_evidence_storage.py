"""Tests for immutable recipe evidence storage."""

import json
from pathlib import Path

import pytest

from geoagent_harness.recipes import (
    RecipeEvidenceStorageError,
    load_recipe_evidence,
    recipe_evidence_sha256,
    write_recipe_evidence,
    load_recipe_run_result,
    recipe_run_result_sha256,
    write_recipe_run_result,
)
from tests.test_recipe_evidence_schemas import (
    evidence as example_evidence,
)

from tests.test_recipe_evidence_builder import (
    run_result,
)


def example_run_result():
    return run_result(
        source="data/input/sample.geojson",
        target="data/output/sample.gpkg",
        target_size=100,
    )


def test_recipe_run_result_round_trip(
    tmp_path: Path,
) -> None:
    result = example_run_result()

    path = write_recipe_run_result(
        result,
        result_root=tmp_path,
    )

    assert recipe_run_result_sha256(
        result
    ) in path.name

    loaded = load_recipe_run_result(
        path,
        result_root=tmp_path,
    )

    assert loaded == result


def test_recipe_run_result_overwrite_is_blocked(
    tmp_path: Path,
) -> None:
    result = example_run_result()

    write_recipe_run_result(
        result,
        result_root=tmp_path,
    )

    with pytest.raises(
        RecipeEvidenceStorageError,
        match="overwriting is blocked",
    ):
        write_recipe_run_result(
            result,
            result_root=tmp_path,
        )


def test_recipe_run_result_tampering_is_rejected(
    tmp_path: Path,
) -> None:
    result = example_run_result()

    path = write_recipe_run_result(
        result,
        result_root=tmp_path,
    )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    payload["warnings"].append("tampered")

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        RecipeEvidenceStorageError,
        match="filename does not match",
    ):
        load_recipe_run_result(
            path,
            result_root=tmp_path,
        )

def test_evidence_round_trip(
    tmp_path: Path,
) -> None:
    evidence = example_evidence()

    path = write_recipe_evidence(
        evidence,
        evidence_root=tmp_path,
    )

    assert path.is_file()
    assert recipe_evidence_sha256(
        evidence
    ) in path.name

    loaded = load_recipe_evidence(
        path,
        evidence_root=tmp_path,
    )

    assert loaded == evidence


def test_evidence_overwrite_is_blocked(
    tmp_path: Path,
) -> None:
    evidence = example_evidence()

    write_recipe_evidence(
        evidence,
        evidence_root=tmp_path,
    )

    with pytest.raises(
        RecipeEvidenceStorageError,
        match="overwriting is blocked",
    ):
        write_recipe_evidence(
            evidence,
            evidence_root=tmp_path,
        )


def test_evidence_outside_root_is_rejected(
    tmp_path: Path,
) -> None:
    outside = (
        tmp_path.parent
        / "outside-evidence.json"
    )
    outside.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        RecipeEvidenceStorageError,
        match="escaped its trusted root",
    ):
        load_recipe_evidence(
            outside,
            evidence_root=tmp_path,
        )


def test_tampered_evidence_is_rejected(
    tmp_path: Path,
) -> None:
    evidence = example_evidence()

    path = write_recipe_evidence(
        evidence,
        evidence_root=tmp_path,
    )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    payload["warnings"].append("tampered")

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        RecipeEvidenceStorageError,
        match="filename does not match",
    ):
        load_recipe_evidence(
            path,
            evidence_root=tmp_path,
        )

