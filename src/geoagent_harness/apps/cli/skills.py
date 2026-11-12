"""Existing skills CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer


def plan_skill_scaffold_command(
    request_file: Annotated[
        Path,
        typer.Argument(
            help="Versioned skill scaffold request JSON."
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan a new GIS skill scaffold without writing files."""

    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry
    from geoagent_harness.capabilities.skills.scaffolding import SkillScaffoldPolicyError
    from geoagent_harness.capabilities.skills.scaffolding import SkillScaffoldStorageError
    from geoagent_harness.task_actions.command_actions import skill_scaffolding__load_skill_scaffold_request as load_skill_scaffold_request, skill_scaffolding__plan_skill_scaffold as plan_skill_scaffold

    try:
        request = load_skill_scaffold_request(
            request_file
        )
        registry = load_skill_registry(
            project_root
        )
        result = plan_skill_scaffold(
            request,
            registry=registry,
        )
    except (
        SkillRegistryError,
        SkillScaffoldPolicyError,
        SkillScaffoldStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def generate_skill_scaffold_command(
    request_file: Annotated[
        Path,
        typer.Argument(
            help="Versioned skill scaffold request JSON."
        ),
    ],
    scaffold_root: Annotated[
        Path,
        typer.Option("--scaffold-root"),
    ] = Path("skill-scaffolds"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate one isolated, untrusted skill scaffold."""

    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry
    from geoagent_harness.capabilities.skills.scaffolding import SkillScaffoldGenerationError
    from geoagent_harness.capabilities.skills.scaffolding import SkillScaffoldPolicyError
    from geoagent_harness.capabilities.skills.scaffolding import SkillScaffoldStorageError
    from geoagent_harness.task_actions.command_actions import skill_scaffolding__generate_skill_scaffold as generate_skill_scaffold, skill_scaffolding__load_skill_scaffold_request as load_skill_scaffold_request, skill_scaffolding__plan_skill_scaffold as plan_skill_scaffold

    try:
        request = load_skill_scaffold_request(
            request_file
        )
        registry = load_skill_registry(
            project_root
        )
        plan = plan_skill_scaffold(
            request,
            registry=registry,
        )
        result = generate_skill_scaffold(
            plan,
            scaffold_root=scaffold_root,
        )
    except (
        SkillRegistryError,
        SkillScaffoldGenerationError,
        SkillScaffoldPolicyError,
        SkillScaffoldStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def validate_skill_scaffold_command(
    scaffold_path: Annotated[
        Path,
        typer.Argument(
            help="Generated skill scaffold bundle."
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate a scaffold without importing or executing it."""

    from geoagent_harness.capabilities.skills.scaffolding import SkillScaffoldContractError
    from geoagent_harness.task_actions.command_actions import skill_scaffolding__validate_skill_scaffold_contract as validate_skill_scaffold_contract

    try:
        result = validate_skill_scaffold_contract(
            scaffold_path
        )
    except (
        SkillScaffoldContractError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not result.passed:
        raise typer.Exit(code=1)


def assess_skill_definition_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess a declarative skill without generating code."""

    from geoagent_harness.capabilities.skills.definitions import SkillDefinitionStorageError
    from geoagent_harness.task_actions.command_actions import skill_definitions__assess_declarative_skill as assess_declarative_skill, skill_definitions__load_skill_definition as load_skill_definition

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )
        result = assess_declarative_skill(
            definition
        )
    except (
        SkillDefinitionStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not result.ready_for_generation:
        raise typer.Exit(code=1)


def generate_skill_contract_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    contract_root: Annotated[
        Path,
        typer.Option("--contract-root"),
    ] = Path("skill-contracts"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate one isolated immutable skill contract."""

    from geoagent_harness.capabilities.skills.definitions import SkillContractGenerationError
    from geoagent_harness.capabilities.skills.definitions import SkillDefinitionStorageError
    from geoagent_harness.task_actions.command_actions import skill_definitions__generate_skill_contract_bundle as generate_skill_contract_bundle, skill_definitions__load_skill_definition as load_skill_definition

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )
        result = generate_skill_contract_bundle(
            definition,
            contract_root=contract_root,
        )
    except (
        SkillContractGenerationError,
        SkillDefinitionStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def validate_skill_contract_command(
    bundle_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Generated immutable skill "
                "contract bundle."
            )
        ),
    ],
    contract_root: Annotated[
        Path,
        typer.Option("--contract-root"),
    ] = Path("skill-contracts"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate a contract without importing or executing code."""

    from geoagent_harness.capabilities.skills.definitions import SkillContractGenerationError
    from geoagent_harness.capabilities.skills.definitions import SkillContractValidationError
    from geoagent_harness.task_actions.command_actions import skill_definitions__validate_skill_contract_bundle as validate_skill_contract_bundle

    try:
        result = validate_skill_contract_bundle(
            bundle_path,
            contract_root=contract_root,
        )
    except (
        SkillContractGenerationError,
        SkillContractValidationError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def generate_skill_candidate_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    scaffold_root: Annotated[
        Path,
        typer.Option("--scaffold-root"),
    ] = Path("skill-scaffolds"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate one isolated untrusted skill candidate."""

    from geoagent_harness.capabilities.skills.definitions import DeclarativeSkillScaffoldError
    from geoagent_harness.capabilities.skills.definitions import SkillDefinitionStorageError
    from geoagent_harness.capabilities.skills.definitions import TrustedAdapterMaterializationError
    from geoagent_harness.task_actions.command_actions import skill_definitions__generate_declarative_skill_scaffold as generate_declarative_skill_scaffold, skill_definitions__load_skill_definition as load_skill_definition, skill_definitions__materialize_trusted_adapter_candidate as materialize_trusted_adapter_candidate
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        registry = load_skill_registry(
            project_root
        )

        generated = (
            generate_declarative_skill_scaffold(
                definition,
                registry=registry,
                scaffold_root=scaffold_root,
            )
        )

        result = (
            materialize_trusted_adapter_candidate(
                definition=definition,
                scaffold=generated.scaffold,
                candidate_root=candidate_root,
            )
        )
    except (
        DeclarativeSkillScaffoldError,
        SkillDefinitionStorageError,
        SkillRegistryError,
        TrustedAdapterMaterializationError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def assess_skill_candidate_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Materialized skill candidate "
                "directory."
            )
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Isolated candidate-test JSON "
                "record."
            )
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("skill-test-results"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Assess exact candidate evidence before promotion."""

    from geoagent_harness.capabilities.skills.definitions import SkillCandidatePromotionError
    from geoagent_harness.capabilities.skills.definitions import SkillCandidateTestEvidenceError
    from geoagent_harness.capabilities.skills.definitions import SkillDefinitionStorageError
    from geoagent_harness.task_actions.command_actions import skill_definitions__assess_skill_candidate_for_promotion as assess_skill_candidate_for_promotion, skill_definitions__load_skill_candidate_test_record as load_skill_candidate_test_record, skill_definitions__load_skill_definition as load_skill_definition

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        test_record = (
            load_skill_candidate_test_record(
                test_record_file,
                evidence_root=evidence_root,
            )
        )

        result = (
            assess_skill_candidate_for_promotion(
                definition=definition,
                candidate_path=candidate_path,
                candidate_root=candidate_root,
                test_record=test_record,
            )
        )
    except (
        SkillCandidatePromotionError,
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )

    if not result.ready_for_promotion_review:
        raise typer.Exit(code=1)


def plan_skill_promotion_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help="Materialized candidate directory."
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help="Isolated candidate-test JSON record."
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("skill-test-results"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan exact trusted writes without performing them."""

    from geoagent_harness.capabilities.skills.definitions import SkillCandidateTestEvidenceError
    from geoagent_harness.capabilities.skills.definitions import SkillDefinitionStorageError
    from geoagent_harness.capabilities.skills.definitions import SkillPromotionPlanError
    from geoagent_harness.task_actions.command_actions import skill_definitions__load_skill_candidate_test_record as load_skill_candidate_test_record, skill_definitions__load_skill_definition as load_skill_definition, skill_definitions__plan_skill_candidate_promotion as plan_skill_candidate_promotion

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        test_record = (
            load_skill_candidate_test_record(
                test_record_file,
                evidence_root=evidence_root,
            )
        )

        result = plan_skill_candidate_promotion(
            definition=definition,
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record=test_record,
            project_root=project_root,
        )
    except (
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
        SkillPromotionPlanError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def promote_skill_candidate_command(
    definition_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical declarative skill "
                "definition YAML."
            )
        ),
    ],
    candidate_path: Annotated[
        Path,
        typer.Argument(
            help="Materialized candidate directory."
        ),
    ],
    test_record_file: Annotated[
        Path,
        typer.Argument(
            help="Isolated candidate-test JSON record."
        ),
    ],
    confirmed_skill_id: Annotated[
        str,
        typer.Option(
            "--confirm-skill-id",
            help=(
                "Exact skill ID explicitly approved "
                "for trusted promotion."
            ),
        ),
    ],
    definition_root: Annotated[
        Path,
        typer.Option("--definition-root"),
    ] = Path("skill-definitions"),
    candidate_root: Annotated[
        Path,
        typer.Option("--candidate-root"),
    ] = Path("skill-candidates"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("skill-test-results"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Explicitly promote one exact verified candidate."""

    from geoagent_harness.capabilities.skills.definitions import SkillCandidatePromotionExecutionError
    from geoagent_harness.capabilities.skills.definitions import SkillCandidateTestEvidenceError
    from geoagent_harness.capabilities.skills.definitions import SkillDefinitionStorageError
    from geoagent_harness.task_actions.command_actions import skill_definitions__load_skill_candidate_test_record as load_skill_candidate_test_record, skill_definitions__load_skill_definition as load_skill_definition, skill_definitions__promote_skill_candidate as promote_skill_candidate

    try:
        definition = load_skill_definition(
            definition_file,
            definition_root=definition_root,
        )

        test_record = (
            load_skill_candidate_test_record(
                test_record_file,
                evidence_root=evidence_root,
            )
        )

        result = promote_skill_candidate(
            definition=definition,
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record=test_record,
            project_root=project_root,
            confirmed_skill_id=(
                confirmed_skill_id
            ),
        )
    except (
        SkillCandidatePromotionExecutionError,
        SkillCandidateTestEvidenceError,
        SkillDefinitionStorageError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    typer.echo(
        json.dumps(
            result.model_dump(mode="json"),
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )
