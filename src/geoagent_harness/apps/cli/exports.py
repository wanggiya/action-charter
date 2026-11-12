"""Existing exports CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer


def plan_snakemake_export_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root."
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root."
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Plan a non-executing Snakemake recipe export."""

    from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError
    from geoagent_harness.capabilities.recipes.execution import RecipeStorageError
    from geoagent_harness.task_actions.command_actions import recipes__load_recipe as load_recipe, recipes__load_recipe_approval as load_recipe_approval
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry
    from geoagent_harness.data.export.snakemake.planner import SnakemakeExportPolicyError
    from geoagent_harness.task_actions.command_actions import snakemake_export__plan_snakemake_recipe_export as plan_snakemake_recipe_export

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        approval = load_recipe_approval(
            approval_file,
            approval_root=approval_root,
        )
        registry = load_skill_registry(
            project_root
        )

        result = plan_snakemake_recipe_export(
            recipe=recipe,
            approval=approval,
            registry=registry,
            recipe_path=recipe_file,
            approval_path=approval_file,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
        SkillRegistryError,
        SnakemakeExportPolicyError,
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


def export_approved_recipe_snakemake_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root."
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root."
        ),
    ],
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    approval_root: Annotated[
        Path,
        typer.Option("--approval-root"),
    ] = Path("approvals"),
    export_root: Annotated[
        Path,
        typer.Option("--export-root"),
    ] = Path("snakemake-exports"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Export one exact approved recipe for Snakemake replay."""

    from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError
    from geoagent_harness.capabilities.recipes.execution import RecipeStorageError
    from geoagent_harness.task_actions.command_actions import recipes__load_recipe as load_recipe, recipes__load_recipe_approval as load_recipe_approval
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry
    from geoagent_harness.data.export.snakemake.generator import SnakemakeExportGenerationError
    from geoagent_harness.data.export.snakemake.planner import SnakemakeExportPolicyError
    from geoagent_harness.task_actions.command_actions import snakemake_export__generate_snakemake_recipe_export as generate_snakemake_recipe_export, snakemake_export__plan_snakemake_recipe_export as plan_snakemake_recipe_export

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        approval = load_recipe_approval(
            approval_file,
            approval_root=approval_root,
        )
        registry = load_skill_registry(
            project_root
        )

        plan = plan_snakemake_recipe_export(
            recipe=recipe,
            approval=approval,
            registry=registry,
            recipe_path=recipe_file,
            approval_path=approval_file,
        )

        result = generate_snakemake_recipe_export(
            plan,
            export_root=export_root,
            project_root=project_root,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
        SkillRegistryError,
        SnakemakeExportGenerationError,
        SnakemakeExportPolicyError,
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


def validate_snakemake_export_command(
    export_path: Annotated[
        Path,
        typer.Argument(
            help="Generated Snakemake replay package."
        ),
    ],
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Statically validate a Snakemake replay package."""

    from geoagent_harness.data.export.snakemake.contracts import SnakemakeExportContractError
    from geoagent_harness.task_actions.command_actions import snakemake_export__validate_snakemake_export_contract as validate_snakemake_export_contract

    try:
        result = validate_snakemake_export_contract(
            export_path
        )
    except (
        SnakemakeExportContractError,
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
