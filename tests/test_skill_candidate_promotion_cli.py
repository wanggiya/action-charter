"""CLI tests for skill-candidate promotion assessment."""

import json
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.skill_definitions import (
    SkillCandidateTestRecord,
    candidate_tree_sha256,
    generate_declarative_skill_scaffold,
    load_skill_definition,
    materialize_trusted_adapter_candidate,
)
from geoagent_harness.skill_registry import (
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

runner = CliRunner()

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


def prepared_inputs(
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    definition = load_skill_definition(
        DEFINITION_FILE,
        definition_root=DEFINITION_ROOT,
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

    digest = candidate_tree_sha256(
        candidate
    )

    record = SkillCandidateTestRecord(
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

    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()

    record_path = evidence_root / "result.json"
    record_path.write_text(
        json.dumps(
            record.model_dump(mode="json")
        ),
        encoding="utf-8",
    )

    return (
        candidate,
        candidate_root,
        record_path,
    )


def test_assess_skill_candidate_is_registered(
) -> None:
    result = runner.invoke(
        app,
        [
            "assess-skill-candidate",
            "--help",
        ],
    )

    assert result.exit_code == 0


def test_exact_candidate_reaches_promotion_review(
    tmp_path: Path,
) -> None:
    (
        candidate,
        candidate_root,
        record_path,
    ) = prepared_inputs(tmp_path)

    result = runner.invoke(
        app,
        [
            "assess-skill-candidate",
            str(DEFINITION_FILE),
            str(candidate),
            str(record_path),
            "--definition-root",
            str(DEFINITION_ROOT),
            "--candidate-root",
            str(candidate_root),
            "--evidence-root",
            str(record_path.parent),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    assert payload[
        "ready_for_promotion_review"
    ] is True
    assert payload[
        "static_contract_passed"
    ] is True
    assert payload[
        "evidence_matches_candidate"
    ] is True
    assert payload[
        "isolated_tests_passed"
    ] is True

    assert payload[
        "implementation_trusted"
    ] is False
    assert payload["registry_modified"] is False
    assert payload[
        "promotion_performed"
    ] is False
    assert payload[
        "execution_performed"
    ] is False

def test_skill_promotion_commands_are_registered(
) -> None:
    for command in (
        "plan-skill-promotion",
        "promote-skill-candidate",
    ):
        result = runner.invoke(
            app,
            [
                command,
                "--help",
            ],
        )

        assert result.exit_code == 0


def test_promotion_requires_exact_confirmation(
) -> None:
    result = runner.invoke(
        app,
        [
            "promote-skill-candidate",
            "definition.skill.yaml",
            "candidate",
            "record.json",
        ],
        terminal_width=200,
    )

    assert result.exit_code != 0
    assert "--confirm-skill-id" in (
        result.output
    )

