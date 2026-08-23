"""Read-only promotion readiness for skill candidates."""

from __future__ import annotations

from pathlib import Path

from geoagent_harness.skill_definitions.generation import (
    SkillContractGenerationError,
    build_skill_contract,
)
from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
    SkillCandidatePromotionAssessment,
    SkillCandidateTestRecord,
)
from geoagent_harness.skill_definitions.test_evidence import (
    SkillCandidateTestEvidenceError,
    candidate_tree_sha256,
)
from geoagent_harness.skill_scaffolding import (
    SkillScaffoldContractError,
    validate_skill_scaffold_contract,
)


class SkillCandidatePromotionError(RuntimeError):
    """Raised when promotion assessment is unsafe."""


def _safe_candidate_path(
    candidate_path: Path,
    *,
    candidate_root: Path,
) -> Path:
    """Require one non-symlink candidate beneath its root."""

    if candidate_path.is_symlink():
        raise SkillCandidatePromotionError(
            "skill candidate cannot be a symlink"
        )

    root = candidate_root.resolve()
    candidate = candidate_path.resolve()

    if not candidate.is_relative_to(root):
        raise SkillCandidatePromotionError(
            "skill candidate escaped its approved root"
        )

    if not candidate.is_dir():
        raise SkillCandidatePromotionError(
            "skill candidate does not exist"
        )

    return candidate


def assess_skill_candidate_for_promotion(
    *,
    definition: DeclarativeSkillDefinition,
    candidate_path: Path,
    candidate_root: Path,
    test_record: SkillCandidateTestRecord,
) -> SkillCandidatePromotionAssessment:
    """Assess exact evidence without promoting anything."""

    candidate = _safe_candidate_path(
        candidate_path,
        candidate_root=candidate_root,
    )

    try:
        contract = build_skill_contract(
            definition
        )
        current_tree_sha256 = (
            candidate_tree_sha256(
                candidate
            )
        )
    except (
        SkillContractGenerationError,
        SkillCandidateTestEvidenceError,
    ) as exc:
        raise SkillCandidatePromotionError(
            "candidate promotion inputs could "
            "not be verified"
        ) from exc

    expected_name = (
        f"{definition.skill_id}."
        f"{contract.definition_sha256}."
        "candidate"
    )

    violations: list[str] = []

    if candidate.name != expected_name:
        violations.append(
            "candidate directory name does not "
            "match the declarative definition"
        )

    try:
        static_result = (
            validate_skill_scaffold_contract(
                candidate
            )
        )
    except SkillScaffoldContractError:
        static_contract_passed = False
        violations.append(
            "candidate failed static scaffold "
            "validation"
        )
    else:
        static_contract_passed = (
            static_result.passed
        )

        if not static_contract_passed:
            violations.append(
                "candidate contains static "
                "contract violations"
            )

    skill_matches = (
        test_record.skill_id
        == definition.skill_id
    )

    if not skill_matches:
        violations.append(
            "test record skill ID does not "
            "match the definition"
        )

    evidence_matches = (
        test_record.candidate_tree_sha256
        == current_tree_sha256
        and test_record.candidate_tree_sha256_after
        == current_tree_sha256
    )

    if not evidence_matches:
        violations.append(
            "test evidence does not match the "
            "current candidate contents"
        )

    if not test_record.candidate_unchanged:
        violations.append(
            "candidate changed during isolated tests"
        )

    if not test_record.passed:
        violations.append(
            "isolated candidate tests did not pass"
        )

    ready = not violations

    return SkillCandidatePromotionAssessment(
        skill_id=definition.skill_id,
        adapter_id=definition.adapter_id,
        definition_sha256=(
            contract.definition_sha256
        ),
        candidate_tree_sha256=(
            current_tree_sha256
        ),
        static_contract_passed=(
            static_contract_passed
        ),
        evidence_matches_candidate=(
            evidence_matches
        ),
        isolated_tests_passed=(
            test_record.passed
        ),
        candidate_unchanged=(
            test_record.candidate_unchanged
        ),
        ready_for_promotion_review=ready,
        violations=list(
            dict.fromkeys(violations)
        ),
        assessment_performed=True,
        candidate_tests_executed=True,
        implementation_trusted=False,
        registry_modified=False,
        promotion_performed=False,
        execution_performed=False,
    )

