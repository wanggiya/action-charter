"""Existing recipe_planning CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
import typer
from geoagent_harness.capabilities.recipes.proposals.compiler import RecipeCompilationError
from geoagent_harness.agents.roles.planner.recipe_proposal import RecipeProposalAgentError
from geoagent_harness.task_actions.command_actions import recipe_proposals__render_recipe_operator_review as render_recipe_operator_review, recipe_proposals__review_recipe_request as review_recipe_request


def recipe_template_catalog_command(
    project_root: Annotated[
        Path,
        typer.Option(
            "--project-root",
            help=(
                "Trusted project root containing "
                "context/RECIPE_TEMPLATES.yaml."
            ),
        ),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Validate and display the recipe-template catalog."""

    from geoagent_harness.capabilities.recipes.catalog import RecipeTemplateCatalogError
    from geoagent_harness.task_actions.command_actions import recipe_catalog__load_recipe_template_catalog as load_recipe_template_catalog

    try:
        catalog = load_recipe_template_catalog(
            project_root
        )
    except RecipeTemplateCatalogError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    payload = {
        "schema_version": (
            catalog.schema_version
        ),
        "templates": [
            template.model_dump(
                mode="json"
            )
            for template in catalog.templates
        ],
        "catalog_validated": True,
        "files_modified": False,
        "execution_performed": False,
    }

    typer.echo(
        json.dumps(
            payload,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )


def compile_recipe_proposal_command(
    proposal_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Recipe proposal JSON beneath the "
                "approved proposal root."
            ),
        ),
    ],
    proposal_root: Annotated[
        Path,
        typer.Option("--proposal-root"),
    ] = Path("recipe-proposals"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Compile a safe proposal without saving or executing."""

    from geoagent_harness.capabilities.recipes.proposals.compiler import RecipeCompilationError
    from geoagent_harness.capabilities.recipes.proposals.storage import RecipeProposalStorageError
    from geoagent_harness.task_actions.command_actions import recipe_proposals__compile_recipe_proposal as compile_recipe_proposal, recipe_proposals__load_recipe_proposal as load_recipe_proposal
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

    try:
        proposal = load_recipe_proposal(
            proposal_file,
            proposal_root=proposal_root,
        )

        registry = load_skill_registry(
            project_root
        )

        result = compile_recipe_proposal(
            proposal,
            registry=registry,
        )
    except (
        RecipeCompilationError,
        RecipeProposalStorageError,
        SkillRegistryError,
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


def propose_recipe_command(
    original_request: Annotated[
        str,
        typer.Argument(
            help=(
                "Natural-language GIS request. "
                "Quote requests containing spaces."
            ),
        ),
    ],
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate a non-executable recipe proposal."""

    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError
    from geoagent_harness.agents.roles.planner.recipe_proposal import RecipeProposalAgentError
    from geoagent_harness.task_actions.command_actions import recipe_proposals__propose_recipe_with_shared_model as propose_recipe_with_shared_model

    try:
        result = (
            propose_recipe_with_shared_model(
                original_request=(
                    original_request
                ),
                agents_root=agents_root,
            )
        )
    except (
        ModelClientError,
        ModelSettingsError,
        RecipeProposalAgentError,
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


def propose_and_compile_recipe_command(
    original_request: Annotated[
        str,
        typer.Argument(
            help=(
                "Natural-language GIS request. "
                "Quote requests containing spaces."
            ),
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Generate and compile without saving or executing."""

    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError
    from geoagent_harness.capabilities.recipes.proposals.compiler import RecipeCompilationError
    from geoagent_harness.agents.roles.planner.recipe_proposal import RecipeProposalAgentError
    from geoagent_harness.task_actions.command_actions import recipe_proposals__propose_and_compile_recipe as propose_and_compile_recipe
    from geoagent_harness.platform.skill_registry import SkillRegistryError

    try:
        result = propose_and_compile_recipe(
            original_request=original_request,
            project_root=project_root,
            agents_root=agents_root,
        )
    except (
        ModelClientError,
        ModelSettingsError,
        RecipeCompilationError,
        RecipeProposalAgentError,
        SkillRegistryError,
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


def review_recipe_request_command(
    original_request: Annotated[
        str,
        typer.Argument(
            help=(
                "Natural-language GIS request to "
                "prepare for operator review."
            ),
        ),
    ],
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            help="Output format: json or summary.",
        ),
    ] = "json",
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Prepare a recipe review without saving or executing."""

    from geoagent_harness.platform.model_gateway import ModelClientError
    from geoagent_harness.platform.model_gateway import ModelSettingsError
    from geoagent_harness.capabilities.recipes.proposals.compiler import RecipeCompilationError
    from geoagent_harness.agents.roles.planner.recipe_proposal import RecipeProposalAgentError
    from geoagent_harness.task_actions.command_actions import recipe_proposals__review_recipe_request as review_recipe_request
    from geoagent_harness.platform.skill_registry import SkillRegistryError

    try:
        result = review_recipe_request(
            original_request=original_request,
            project_root=project_root,
            agents_root=agents_root,
        )
    except (
        ModelClientError,
        ModelSettingsError,
        RecipeCompilationError,
        RecipeProposalAgentError,
        SkillRegistryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    if output_format not in {
        "json",
        "summary",
    }:
        typer.echo(
            "Error: output format must be "
            "'json' or 'summary'",
            err=True,
        )
        raise typer.Exit(code=2)

    if output_format == "summary":
        typer.echo(
            render_recipe_operator_review(
                result
            )
        )
        return

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


def save_reviewed_recipe_command(
    review_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Ready operator-review JSON beneath "
                "the approved review root."
            ),
        ),
    ],
    review_root: Annotated[
        Path,
        typer.Option("--review-root"),
    ] = Path("recipe-reviews"),
    recipe_root: Annotated[
        Path,
        typer.Option("--recipe-root"),
    ] = Path("workflow-recipes"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Explicitly save one exact reviewed recipe."""

    from geoagent_harness.capabilities.recipes.proposals.operator_save import RecipeOperatorSaveError
    from geoagent_harness.capabilities.recipes.proposals.review_storage import RecipeReviewStorageError
    from geoagent_harness.task_actions.command_actions import recipe_proposals__load_recipe_operator_review as load_recipe_operator_review, recipe_proposals__save_reviewed_recipe as save_reviewed_recipe
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

    try:
        review = load_recipe_operator_review(
            review_file,
            review_root=review_root,
        )

        registry = load_skill_registry(
            project_root
        )

        result = save_reviewed_recipe(
            review=review,
            registry=registry,
            recipe_root=recipe_root,
        )
    except (
        RecipeOperatorSaveError,
        RecipeReviewStorageError,
        SkillRegistryError,
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


def list_approved_recipes_command(
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
    """List deterministic recipe and approval matches."""

    from geoagent_harness.capabilities.recipes.execution import RecipeInventoryError
    from geoagent_harness.task_actions.command_actions import recipes__build_recipe_approval_inventory as build_recipe_approval_inventory
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

    try:
        registry = load_skill_registry(
            project_root
        )

        result = build_recipe_approval_inventory(
            recipe_root=recipe_root,
            approval_root=approval_root,
            registry=registry,
        )
    except (
        RecipeInventoryError,
        SkillRegistryError,
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
