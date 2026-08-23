"""Tests for read-only skill promotion planning."""

from pathlib import Path

import pytest
import yaml

from geoagent_harness.skill_definitions import (
    SkillCandidateTestRecord,
    SkillPromotionPlanError,
    candidate_tree_sha256,
    generate_declarative_skill_scaffold,
    load_skill_definition,
    materialize_trusted_adapter_candidate,
    plan_skill_candidate_promotion,
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


def registry_without_inspect_raster(
) -> SkillRegistry:
    """Return the trusted registry without the candidate skill."""

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
    """Generate one isolated candidate for planning tests."""

    definition = load_skill_definition(
        DEFINITION_FILE,
        definition_root=DEFINITION_ROOT,
    )

    generated = (
        generate_declarative_skill_scaffold(
            definition,
            registry=(
                registry_without_inspect_raster()
            ),
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
    """Build consistent isolated-test evidence."""

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


def temporary_project(
    tmp_path: Path,
) -> Path:
    """Create a project containing an unmodified baseline registry."""

    project = tmp_path / "project"
    context = project / "context"

    context.mkdir(
        parents=True,
        exist_ok=True,
    )

    registry = (
        registry_without_inspect_raster()
    )

    registry_payload = registry.model_dump(
        mode="json",
        exclude_none=True,
    )

    (
        context / "SKILLS_INDEX.yaml"
    ).write_text(
        yaml.safe_dump(
            registry_payload,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return project


def test_plans_exact_promotion_without_writing(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
    ) = prepared_candidate(tmp_path)

    record = successful_record(
        candidate
    )
    project = temporary_project(
        tmp_path
    )

    result = plan_skill_candidate_promotion(
        definition=definition,
        candidate_path=candidate,
        candidate_root=candidate_root,
        test_record=record,
        project_root=project,
    )

    assert result.ready_for_promotion is True
    assert result.skill_id == "inspect_raster"
    assert result.adapter_id == (
        "raster_inspection"
    )

    assert len(result.files) == 8

    assert {
        file.destination_path
        for file in result.files
    } == {
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/__init__.py"
        ),
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/schemas.py"
        ),
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/policy.py"
        ),
        (
            "src/geoagent_harness/skills/"
            "inspect_raster/service.py"
        ),
        "tests/test_inspect_raster_schemas.py",
        "tests/test_inspect_raster_policy.py",
        "tests/test_inspect_raster_service.py",
        "tests/test_inspect_raster_contract.py",
    }

    assert result.registry_entry.id == (
        "inspect_raster"
    )
    assert (
        result.registry_entry.version
        == "0.1.0"
    )
    assert (
        result.registry_entry.status.value
        == "implemented"
    )
    assert (
        result.registry_entry.kind.value
        == "inspection"
    )
    assert (
        result.registry_entry.access.value
        == "read_only"
    )
    assert (
        result.registry_entry.approval_required
        is False
    )
    assert (
        result.registry_entry.validation_required
        is False
    )
    assert result.registry_entry.entrypoint == (
        "geoagent_harness.skills.inspect_raster."
        "service:inspect_raster"
    )
    assert result.registry_entry.verifier is None

    assert result.planning_performed is True
    assert result.files_copied is False
    assert result.registry_modified is False
    assert result.promotion_performed is False
    assert result.execution_performed is False

    for file in result.files:
        assert not (
            project / file.destination_path
        ).exists()

    registry_after = load_skill_registry(
        project
    )

    with pytest.raises(KeyError):
        registry_after.get_skill(
            "inspect_raster"
        )


def test_existing_destination_blocks_plan(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
    ) = prepared_candidate(tmp_path)

    project = temporary_project(
        tmp_path
    )

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
        "existing trusted source\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SkillPromotionPlanError,
        match="destination already exists",
    ):
        plan_skill_candidate_promotion(
            definition=definition,
            candidate_path=candidate,
            candidate_root=candidate_root,
            test_record=successful_record(
                candidate
            ),
            project_root=project,
        )

    assert existing.read_text(
        encoding="utf-8"
    ) == "existing trusted source\n"


def test_changed_candidate_evidence_blocks_plan(
    tmp_path: Path,
) -> None:
    (
        definition,
        candidate,
        candidate_root,
    ) = prepared_candidate(tmp_path)

    record = successful_record(
        candidate
    )

    service = (
        candidate
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    )

    service.write_text(
        service.read_text(
            encoding="utf-8"
        )
        + "\n# changed after isolated tests\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SkillPromotionPlanError,
        match="not ready",
    ):
        plan_skill_candidate_promotion(
            definition=definition,
            candidate_path=candidate,
            candidate_root=candidate_root,
            test_record=record,
            project_root=temporary_project(
                tmp_path
            ),
        )