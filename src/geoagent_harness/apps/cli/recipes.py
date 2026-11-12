"""Existing recipes CLI commands; shared services retain policy and execution."""

import json
from pathlib import Path
from typing import Annotated, NoReturn
from datetime import datetime
import typer
from geoagent_harness.contracts.failures import FailureStage
from geoagent_harness.apps.cli.common import _raise_typed_failure


def save_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="JSON recipe draft to validate and store.",
        ),
    ],
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
    """Validate and immutably persist a reusable recipe."""

    from geoagent_harness.capabilities.recipes.execution import RecipePolicyError
    from geoagent_harness.capabilities.recipes.execution import RecipeStorageError
    from geoagent_harness.task_actions.command_actions import recipes__load_recipe_draft as load_recipe_draft, recipes__recipe_sha256 as recipe_sha256, recipes__save_recipe as save_recipe, recipes__validate_recipe_policy as validate_recipe_policy
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

    try:
        draft = load_recipe_draft(
            recipe_file
        )
        registry = load_skill_registry(
            project_root
        )
        validation = validate_recipe_policy(
            draft,
            registry=registry,
        )
        stored, path = save_recipe(
            draft,
            recipe_root=recipe_root,
        )
    except (
        RecipePolicyError,
        RecipeStorageError,
        SkillRegistryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    payload = {
        "status": "stored",
        "recipe_id": stored.recipe_id,
        "recipe_sha256": recipe_sha256(
            stored
        ),
        "recipe_path": path.as_posix(),
        "policy": validation.model_dump(
            mode="json"
        ),
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


def approve_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root.",
        ),
    ],
    step_ids: Annotated[
        list[str],
        typer.Option(
            "--step",
            help=(
                "Approval-required recipe step; "
                "repeat for multiple steps."
            ),
        ),
    ],
    approver: Annotated[
        str,
        typer.Option("--approver"),
    ],
    reason: Annotated[
        str,
        typer.Option("--reason"),
    ],
    decision: Annotated[
        str,
        typer.Option("--decision"),
    ] = "approved",
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
    valid_for_minutes: Annotated[
        int | None,
        typer.Option("--valid-for-minutes"),
    ] = None,
    corrections: Annotated[
        list[str] | None,
        typer.Option("--correction"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Approve explicit write steps in one exact recipe."""

    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError
    from geoagent_harness.capabilities.recipes.execution import RecipeStorageError
    from geoagent_harness.task_actions.command_actions import recipes__create_recipe_approval as create_recipe_approval, recipes__load_recipe as load_recipe
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

    if decision not in {
        "approved",
        "denied",
    }:
        typer.echo(
            "Error: decision must be approved or denied",
            err=True,
        )
        raise typer.Exit(code=2)

    if (
        valid_for_minutes is not None
        and valid_for_minutes <= 0
    ):
        typer.echo(
            "Error: valid-for-minutes must be positive",
            err=True,
        )
        raise typer.Exit(code=2)

    active_now = datetime.now(
        timezone.utc
    )

    expires_at = (
        active_now
        + timedelta(
            minutes=valid_for_minutes
        )
        if valid_for_minutes is not None
        else None
    )

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=recipe_root,
        )
        registry = load_skill_registry(
            project_root
        )
        record, path = create_recipe_approval(
            recipe=recipe,
            registry=registry,
            step_ids=step_ids,
            decision=decision,
            approver=approver,
            reason=reason,
            approval_root=approval_root,
            project_root=project_root,
            human_corrections=corrections,
            expires_at=expires_at,
            now=active_now,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
        SkillRegistryError,
        OSError,
        ValueError,
    ) as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    payload = {
        "status": "recorded",
        "approval_path": path.as_posix(),
        "approval": record.model_dump(
            mode="json"
        ),
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


def verify_recipe_approval_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root.",
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
    """Verify approval against an exact stored recipe."""

    from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError
    from geoagent_harness.capabilities.recipes.execution import RecipeStorageError
    from geoagent_harness.task_actions.command_actions import recipes__load_recipe as load_recipe, recipes__load_recipe_approval as load_recipe_approval, recipes__verify_recipe_approval as verify_recipe_approval
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

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
        result = verify_recipe_approval(
            approval=approval,
            recipe=recipe,
            registry=registry,
        )
    except (
        RecipeApprovalError,
        RecipeStorageError,
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

    if not result.approved:
        raise typer.Exit(code=1)


def run_approved_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help="Canonical recipe beneath the recipe root.",
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help="Recipe approval beneath the approval root.",
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
    """Run and validate one exact approved recipe."""

    from geoagent_harness.task_actions.command_actions import platform_settings__load_settings as load_settings
    from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError
    from geoagent_harness.capabilities.recipes.execution import RecipeRunError
    from geoagent_harness.capabilities.recipes.execution import RecipeStorageError
    from geoagent_harness.task_actions.command_actions import recipes__run_approved_recipe as run_approved_recipe
    from geoagent_harness.task_actions.command_actions import recipes__load_recipe as load_recipe, recipes__load_recipe_approval as load_recipe_approval
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

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

        result = run_approved_recipe(
            recipe=recipe,
            approval=approval,
            registry=registry,
            settings=load_settings(),
        )
    except (
        RecipeApprovalError,
        RecipeRunError,
        RecipeStorageError,
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

    if (
        result.final_status
        != "validated_success"
    ):
        raise typer.Exit(code=1)


def execute_approved_recipe_command(
    recipe_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Canonical recipe JSON beneath "
                "the recipe root."
            ),
        ),
    ],
    approval_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Recipe approval JSON beneath "
                "the approval root."
            ),
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
    agents_root: Annotated[
        Path,
        typer.Option("--agents-root"),
    ] = Path("agents"),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Execute one exact approved recipe through MCP."""

    import asyncio

    from geoagent_harness.agents.roles.executor.service import ExecutorServiceError
    from geoagent_harness.task_actions.command_actions import executor_service__execute_approved_recipe_via_mcp as execute_approved_recipe_via_mcp
    from geoagent_harness.platform.internal_mcp import MCPClientError
    from geoagent_harness.platform.internal_mcp import MCPClientSettingsError
    from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError
    from geoagent_harness.capabilities.recipes.execution import RecipeExecutionPolicyError
    from geoagent_harness.capabilities.recipes.execution import RecipeStorageError
    from geoagent_harness.platform.skill_registry import SkillRegistryError

    try:
        result = asyncio.run(
            execute_approved_recipe_via_mcp(
                recipe_file=recipe_file,
                approval_file=approval_file,
                recipe_root=recipe_root,
                approval_root=approval_root,
                project_root=project_root,
                agents_root=agents_root,
            )
        )
    except KeyboardInterrupt as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.EXECUTION,
        )
    except MCPClientError as exc:
        _raise_typed_failure(
            exc,
            stage=FailureStage.MCP,
        )
    except (
        ExecutorServiceError,
        MCPClientSettingsError,
        RecipeApprovalError,
        RecipeExecutionPolicyError,
        RecipeStorageError,
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

    if (
        result.recipe.final_status
        != "validated_success"
    ):
        raise typer.Exit(code=1)


def build_recipe_evidence_command(
    result_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Raw RecipeRunResult JSON beneath "
                "the trusted result root."
            ),
        ),
    ],
    result_root: Annotated[
        Path,
        typer.Option("--result-root"),
    ] = Path("recipe-runs"),
    evidence_root: Annotated[
        Path,
        typer.Option("--evidence-root"),
    ] = Path("recipe-evidence"),
    input_root: Annotated[
        Path,
        typer.Option("--input-root"),
    ] = Path("data/input"),
    output_root: Annotated[
        Path,
        typer.Option("--output-root"),
    ] = Path("data/output"),
    project_root: Annotated[
        Path,
        typer.Option("--project-root"),
    ] = Path("."),
    pretty: Annotated[
        bool,
        typer.Option("--pretty"),
    ] = False,
) -> None:
    """Build and immutably store recipe lineage evidence."""

    from geoagent_harness.capabilities.recipes.execution import RecipeEvidenceError
    from geoagent_harness.capabilities.recipes.execution import RecipeEvidenceStorageError
    from geoagent_harness.task_actions.command_actions import recipes__build_recipe_run_evidence as build_recipe_run_evidence
    from geoagent_harness.task_actions.command_actions import recipes__load_recipe_run_result as load_recipe_run_result, recipes__recipe_evidence_sha256 as recipe_evidence_sha256, recipes__write_recipe_evidence as write_recipe_evidence
    from geoagent_harness.platform.skill_registry import SkillRegistryError
    from geoagent_harness.task_actions.command_actions import skill_registry__load_skill_registry as load_skill_registry

    try:
        run_result = load_recipe_run_result(
            result_file,
            result_root=result_root,
        )

        registry = load_skill_registry(
            project_root
        )

        evidence = build_recipe_run_evidence(
            run_result=run_result,
            registry=registry,
            input_root=input_root,
            output_root=output_root,
        )

        written_path = write_recipe_evidence(
            evidence,
            evidence_root=evidence_root,
        )

        response = {
            "status": "stored",
            "recipe_id": evidence.recipe_id,
            "recipe_sha256": (
                evidence.recipe_sha256
            ),
            "evidence_sha256": (
                recipe_evidence_sha256(
                    evidence
                )
            ),
            "evidence_path": (
                written_path.as_posix()
            ),
            "final_status": (
                evidence.final_status
            ),
            "artifact_count": len(
                evidence.artifacts
            ),
            "lineage_edge_count": len(
                evidence.lineage
            ),
            "secrets_redacted": True,
        }

    except (
        RecipeEvidenceError,
        RecipeEvidenceStorageError,
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
            response,
            indent=2 if pretty else None,
            separators=(
                None
                if pretty
                else (",", ":")
            ),
        )
    )
