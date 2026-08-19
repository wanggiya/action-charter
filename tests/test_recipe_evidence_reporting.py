"""Tests for deterministic recipe evidence reports."""

from pathlib import Path

import pytest

from geoagent_harness.recipes.evidence_reporting import (
    RecipeEvidenceReportError,
    recipe_evidence_report_path,
    render_recipe_evidence_report,
    write_recipe_evidence_report,
)
from tests.test_recipe_evidence_schemas import (
    evidence as example_evidence,
)


def test_report_contains_authoritative_evidence() -> None:
    evidence = example_evidence()

    report = render_recipe_evidence_report(
        evidence
    )

    assert evidence.recipe_id in report
    assert evidence.recipe_sha256 in report
    assert evidence.approval_id in report
    assert evidence.final_status in report

    for artifact in evidence.artifacts:
        assert artifact.path in report
        assert artifact.sha256 in report

    assert (
        "No model determined the final status."
        in report
    )


def test_report_rendering_is_deterministic() -> None:
    evidence = example_evidence()

    first = render_recipe_evidence_report(
        evidence
    )
    second = render_recipe_evidence_report(
        evidence
    )

    assert first == second


def test_report_path_is_digest_addressed(
    tmp_path: Path,
) -> None:
    evidence = example_evidence()

    path = recipe_evidence_report_path(
        evidence,
        report_root=tmp_path,
    )

    assert path.parent == tmp_path.resolve()
    assert path.name.startswith(
        f"{evidence.recipe_id}."
    )
    assert path.suffix == ".md"


def test_report_write_is_immutable(
    tmp_path: Path,
) -> None:
    evidence = example_evidence()

    path = write_recipe_evidence_report(
        evidence,
        report_root=tmp_path,
    )

    assert path.is_file()

    with pytest.raises(
        RecipeEvidenceReportError,
        match="overwriting is blocked",
    ):
        write_recipe_evidence_report(
            evidence,
            report_root=tmp_path,
        )

