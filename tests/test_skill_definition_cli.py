"""CLI tests for declarative skill contracts."""

import json
import yaml
from pathlib import Path

from typer.testing import CliRunner

from geoagent_harness.cli import app
from geoagent_harness.skill_registry import (
    load_skill_registry,
)


PROJECT_ROOT = Path(__file__).parents[1]
DEFINITION_ROOT = PROJECT_ROOT / "skill-definitions"
DEFINITION_FILE = (
    DEFINITION_ROOT
    / "inspect_raster.skill.yaml"
)

runner = CliRunner()

def project_without_candidate(
    tmp_path: Path,
) -> Path:
    """Create a test project where inspect_raster is new."""

    registry = load_skill_registry(
        PROJECT_ROOT
    )

    filtered = registry.model_copy(
        update={
            "skills": [
                skill
                for skill in registry.skills
                if skill.id != "inspect_raster"
            ]
        }
    )

    project = tmp_path / "project"
    context = project / "context"

    context.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        context / "SKILLS_INDEX.yaml"
    ).write_text(
        yaml.safe_dump(
            filtered.model_dump(
                mode="json",
                exclude_none=True,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return project


def test_skill_definition_commands_are_registered(
) -> None:
    for command in (
        "assess-skill-definition",
        "generate-skill-contract",
        "validate-skill-contract",
    ):
        result = runner.invoke(
            app,
            [command, "--help"],
        )

        assert result.exit_code == 0


def test_assesses_raster_definition() -> None:
    result = runner.invoke(
        app,
        [
            "assess-skill-definition",
            str(DEFINITION_FILE),
            "--definition-root",
            str(DEFINITION_ROOT),
        ],
    )

    assert result.exit_code == 0

    payload = json.loads(result.stdout)

    assert payload["skill_id"] == (
        "inspect_raster"
    )
    assert payload["profile"] == (
        "read_only_inspection"
    )
    assert payload["ready_for_generation"] is True
    assert payload["execution_performed"] is False


def test_generates_and_validates_contract(
    tmp_path: Path,
) -> None:
    contract_root = tmp_path / "contracts"

    generated = runner.invoke(
        app,
        [
            "generate-skill-contract",
            str(DEFINITION_FILE),
            "--definition-root",
            str(DEFINITION_ROOT),
            "--contract-root",
            str(contract_root),
        ],
    )

    assert generated.exit_code == 0

    generation_payload = json.loads(
        generated.stdout
    )

    bundle_path = generation_payload[
        "bundle_path"
    ]

    assert generation_payload[
        "registry_modified"
    ] is False
    assert generation_payload[
        "execution_performed"
    ] is False

    validated = runner.invoke(
        app,
        [
            "validate-skill-contract",
            bundle_path,
            "--contract-root",
            str(contract_root),
        ],
    )

    assert validated.exit_code == 0

    validation_payload = json.loads(
        validated.stdout
    )

    assert validation_payload["passed"] is True
    assert validation_payload[
        "implementation_imported"
    ] is False
    assert validation_payload[
        "implementation_executed"
    ] is False
    assert validation_payload[
        "registry_modified"
    ] is False
    assert validation_payload[
        "execution_performed"
    ] is False

def test_generate_skill_candidate_is_registered(
) -> None:
    result = runner.invoke(
        app,
        [
            "generate-skill-candidate",
            "--help",
        ],
    )

    assert result.exit_code == 0


def test_generates_untrusted_skill_candidate(
    tmp_path: Path,
) -> None:
    project = project_without_candidate(
        tmp_path
    )

    result = runner.invoke(
        app,
        [
            "generate-skill-candidate",
            str(DEFINITION_FILE),
            "--definition-root",
            str(DEFINITION_ROOT),
            "--scaffold-root",
            str(tmp_path / "scaffolds"),
            "--candidate-root",
            str(tmp_path / "candidates"),
            "--project-root",
            str(project),
        ],
    )

    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)

    candidate = Path(
        payload["candidate_path"]
    )

    assert candidate.is_dir()
    assert (
        candidate
        / "src"
        / "geoagent_harness"
        / "skills"
        / "inspect_raster"
        / "service.py"
    ).is_file()

    assert payload[
        "candidate_materialized"
    ] is True
    assert payload[
        "static_contract_passed"
    ] is True

    assert payload[
        "source_scaffold_modified"
    ] is False
    assert payload["registry_modified"] is False
    assert payload[
        "implementation_trusted"
    ] is False
    assert payload[
        "promotion_performed"
    ] is False
    assert payload[
        "execution_performed"
    ] is False
    
