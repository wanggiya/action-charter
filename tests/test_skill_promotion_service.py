"""Tests for atomic explicit skill promotion."""

from pathlib import Path

import pytest
import yaml

import geoagent_harness.skill_definitions.promotion_service as promotion_service

from geoagent_harness.skill_definitions import (
    SkillCandidatePromotionExecutionError,
    SkillCandidateTestRecord,
    candidate_tree_sha256,
    generate_declarative_skill_scaffold,
    load_skill_definition,
    materialize_trusted_adapter_candidate,
    promote_skill_candidate,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]

DEFINITION_ROOT = (
    PROJECT_ROOT / "skill-definitions"
)
DEFINITION_FILE = (
    DEFINITION_ROOT
    / "inspect_raster.skill.yaml"
)


def registry_without_candidate(
) -> SkillRegistry:
    """Return a registry without inspect_raster."""

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


def write_temporary_registry(
    project: Path,
) -> Path:
    """Write a valid baseline registry."""

    context = project / "context"

    context.mkdir(
        parents=True,
        exist_ok=True,
    )

    registry_path = (
        context / "SKILLS_INDEX.yaml"
    )

    registry_path.write_text(
        yaml.safe_dump(
            registry_without_candidate().model_dump(
                mode="json",
                exclude_none=True,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return registry_path


def prepared_promotion(
    tmp_path: Path,
):
    """Prepare exact candidate, evidence, and project."""

    definition = load_skill_definition(
        DEFINITION_FILE,
        definition_root=DEFINITION_ROOT,
    )

    registry = registry_without_candidate()

    generated = (
        generate_declarative_skill_scaffold(
            definition,
            registry=registry,
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

    candidate_digest = (
        candidate_tree_sha256(
            candidate
        )
    )

    record = SkillCandidateTestRecord(
        skill_id="inspect_raster",
        candidate_tree_sha256=(
            candidate_digest
        ),
        candidate_tree_sha256_after=(
            candidate_digest
        ),
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

    project = tmp_path / "project"
    registry_path = write_temporary_registry(
        project
    )

    return (
        definition,
        candidate,
        candidate_root,
        record,
        project,
        registry_path,
    )


def test_promotes_files_and_registry_atomically(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
        record,
        project,
        registry_path,
    ) = prepared_promotion(tmp_path)

    candidate_before = (
        candidate_tree_sha256(
            candidate
        )
    )
    registry_before = (
        registry_path.read_bytes()
    )

    result = promote_skill_candidate(
        definition=definition,
        candidate_path=candidate,
        candidate_root=candidate_root,
        test_record=record,
        project_root=project,
        confirmed_skill_id="inspect_raster",
    )

    assert result.skill_id == "inspect_raster"
    assert len(result.copied_files) == 8

    for relative_path in result.copied_files:
        assert (
            project / relative_path
        ).is_file()

    promoted_registry = load_skill_registry(
        project
    )
    promoted_skill = (
        promoted_registry.get_skill(
            "inspect_raster"
        )
    )

    assert promoted_skill.version == "0.1.0"
    assert promoted_skill.status.value == (
        "implemented"
    )
    assert promoted_skill.kind.value == (
        "inspection"
    )
    assert promoted_skill.access.value == (
        "read_only"
    )
    assert promoted_skill.entrypoint == (
        "geoagent_harness.skills.inspect_raster."
        "service:inspect_raster"
    )
    assert promoted_skill.verifier is None

    assert (
        registry_path.read_bytes()
        != registry_before
    )
    assert (
        candidate_tree_sha256(candidate)
        == candidate_before
    )

    assert result.files_copied is True
    assert result.registry_modified is True
    assert result.implementation_trusted is True
    assert result.promotion_performed is True
    assert result.execution_performed is False


def test_wrong_confirmation_performs_no_writes(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
        record,
        project,
        registry_path,
    ) = prepared_promotion(tmp_path)

    registry_before = (
        registry_path.read_bytes()
    )

    with pytest.raises(
        SkillCandidatePromotionExecutionError,
        match="confirmation does not match",
    ):
        promote_skill_candidate(
            definition=definition,
            candidate_path=candidate,
            candidate_root=candidate_root,
            test_record=record,
            project_root=project,
            confirmed_skill_id="wrong_skill",
        )

    assert (
        registry_path.read_bytes()
        == registry_before
    )

    with pytest.raises(KeyError):
        load_skill_registry(
            project
        ).get_skill(
            "inspect_raster"
        )

    assert not (
        project
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
    ).exists()


def test_registry_commit_failure_rolls_back_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
        record,
        project,
        registry_path,
    ) = prepared_promotion(tmp_path)

    registry_before = (
        registry_path.read_bytes()
    )

    original_replace = (
        promotion_service._atomic_replace
    )

    def fail_registry_replace(
        source: Path,
        destination: Path,
    ) -> None:
        if destination.name == (
            "SKILLS_INDEX.yaml"
        ):
            raise OSError(
                "forced registry replacement failure"
            )

        original_replace(
            source,
            destination,
        )

    monkeypatch.setattr(
        promotion_service,
        "_atomic_replace",
        fail_registry_replace,
    )

    with pytest.raises(
        SkillCandidatePromotionExecutionError,
        match="transaction failed",
    ):
        promote_skill_candidate(
            definition=definition,
            candidate_path=candidate,
            candidate_root=candidate_root,
            test_record=record,
            project_root=project,
            confirmed_skill_id="inspect_raster",
        )

    assert (
        registry_path.read_bytes()
        == registry_before
    )

    with pytest.raises(KeyError):
        load_skill_registry(
            project
        ).get_skill(
            "inspect_raster"
        )

    expected_destinations = (
        candidate
        / "scaffold-manifest.json"
    )

    assert expected_destinations.is_file()

    assert not (
        project
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "__init__.py"
    ).exists()

    assert not (
        project
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    ).exists()

    assert not (
        project
        / "tests"
        / "test_inspect_raster_service.py"
    ).exists()


def test_existing_destination_blocks_promotion(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
        record,
        project,
        registry_path,
    ) = prepared_promotion(tmp_path)

    existing = (
        project
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    )

    existing.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    existing.write_text(
        "existing source must remain\n",
        encoding="utf-8",
    )

    registry_before = (
        registry_path.read_bytes()
    )

    with pytest.raises(
        SkillCandidatePromotionExecutionError,
        match="final promotion planning",
    ):
        promote_skill_candidate(
            definition=definition,
            candidate_path=candidate,
            candidate_root=candidate_root,
            test_record=record,
            project_root=project,
            confirmed_skill_id="inspect_raster",
        )

    assert existing.read_text(
        encoding="utf-8"
    ) == "existing source must remain\n"

    assert (
        registry_path.read_bytes()
        == registry_before
    )

