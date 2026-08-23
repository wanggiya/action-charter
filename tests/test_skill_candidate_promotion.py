"""Tests for candidate promotion readiness."""

from pathlib import Path

from geoagent_harness.skill_definitions import (
    SkillCandidateTestRecord,
    assess_skill_candidate_for_promotion,
    candidate_tree_sha256,
    generate_declarative_skill_scaffold,
    load_skill_definition,
    materialize_trusted_adapter_candidate,
)
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]


def registry_without_candidate():
    """Return a test-only pre-promotion registry."""

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    return registry.model_copy(
        update={
            "skills": [
                skill
                for skill in registry.skills
                if skill.id != "inspect_raster"
            ]
        }
    )

def prepared_candidate(
    tmp_path: Path,
):
    definition_root = (
        PROJECT_ROOT / "skill-definitions"
    )

    definition = load_skill_definition(
        (
            definition_root
            / "inspect_raster.skill.yaml"
        ),
        definition_root=definition_root,
    )

    generated = (
        generate_declarative_skill_scaffold(
            definition,
            registry=registry_without_candidate(),
            scaffold_root=(
                tmp_path / "scaffolds"
            ),
        )
    )

    candidate_root = tmp_path / "candidates"

    materialized = (
        materialize_trusted_adapter_candidate(
            definition=definition,
            scaffold=generated.scaffold,
            candidate_root=candidate_root,
        )
    )

    candidate = Path(
        materialized.candidate_path
    )

    return (
        definition,
        candidate,
        candidate_root,
    )


def successful_record(
    candidate: Path,
) -> SkillCandidateTestRecord:
    digest = candidate_tree_sha256(
        candidate
    )

    return SkillCandidateTestRecord(
        skill_id="inspect_raster",
        candidate_tree_sha256=digest,
        candidate_tree_sha256_after=digest,
        candidate_unchanged=True,
        pytest_exit_code=0,
        collected=6,
        passed_count=6,
        failed_count=0,
        skipped_count=0,
        error_count=0,
        passed=True,
        network_available=False,
        candidate_mount_read_only=True,
        tests_executed=True,
        implementation_executed=True,
        registry_modified=False,
        promotion_performed=False,
    )


def test_exact_candidate_is_ready_for_review(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
    ) = prepared_candidate(tmp_path)

    result = assess_skill_candidate_for_promotion(
        definition=definition,
        candidate_path=candidate,
        candidate_root=candidate_root,
        test_record=successful_record(
            candidate
        ),
    )

    assert result.ready_for_promotion_review is True
    assert result.static_contract_passed is True
    assert result.evidence_matches_candidate is True
    assert result.isolated_tests_passed is True
    assert result.violations == []

    assert result.implementation_trusted is False
    assert result.registry_modified is False
    assert result.promotion_performed is False
    assert result.execution_performed is False


def test_change_after_testing_blocks_review(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
    ) = prepared_candidate(tmp_path)

    record = successful_record(candidate)

    service = (
        candidate
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    )

    service.write_text(
        service.read_text(encoding="utf-8")
        + "\n# changed after tests\n",
        encoding="utf-8",
    )

    result = assess_skill_candidate_for_promotion(
        definition=definition,
        candidate_path=candidate,
        candidate_root=candidate_root,
        test_record=record,
    )

    assert result.ready_for_promotion_review is False
    assert result.evidence_matches_candidate is False
    assert (
        "test evidence does not match the "
        "current candidate contents"
        in result.violations
    )
    assert result.promotion_performed is False

