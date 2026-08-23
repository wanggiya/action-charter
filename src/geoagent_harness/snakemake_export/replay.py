"""Trusted adapter for approval-gated Snakemake replay."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import ValidationError

from concurrent.futures import ThreadPoolExecutor

from geoagent_harness.recipes.approval import (
    RecipeApprovalError,
    load_recipe_approval,
)
from geoagent_harness.recipes.execution import (
    RecipeExecutionPolicyError,
    build_recipe_execution_envelope,
)
from geoagent_harness.recipes.storage import (
    RecipeStorageError,
    load_recipe,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)
from geoagent_harness.skill_registry import (
    SkillRegistryError,
    load_skill_registry,
)
from geoagent_harness.snakemake_export.contracts import (
    SnakemakeExportContractError,
    validate_snakemake_export_contract,
)
from geoagent_harness.snakemake_export.schemas import (
    SnakemakeReplayCompletion,
    SnakemakeReplayConfiguration,
)
from geoagent_harness.snakemake_export.settings import (
    SnakemakeReplaySettings,
    load_snakemake_replay_settings,
)

if TYPE_CHECKING:
    from geoagent_harness.executor.schemas import (
        ExecutorRecipeRunResult,
    )


MAX_REPLAY_CONFIGURATION_BYTES = 250_000


class SnakemakeReplayError(RuntimeError):
    """Raised when approved replay cannot proceed safely."""


class ReplayExecutorProtocol(Protocol):
    """Narrow approved-recipe execution capability."""

    async def __call__(
        self,
        *,
        recipe_file: Path,
        approval_file: Path,
        recipe_root: Path,
        approval_root: Path,
        project_root: Path,
        agents_root: Path,
    ) -> ExecutorRecipeRunResult:
        ...


def _contained_path(
    root: Path,
    path: Path,
    *,
    label: str,
) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()

    if (
        resolved != resolved_root
        and resolved_root not in resolved.parents
    ):
        raise SnakemakeReplayError(
            f"{label} escaped its approved root"
        )

    return resolved


def _load_configuration(
    path: Path,
) -> SnakemakeReplayConfiguration:
    if not path.is_file():
        raise SnakemakeReplayError(
            "replay configuration does not exist"
        )

    if path.is_symlink():
        raise SnakemakeReplayError(
            "replay configuration cannot be a symlink"
        )

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SnakemakeReplayError(
            "replay configuration could not be inspected"
        ) from exc

    if size > MAX_REPLAY_CONFIGURATION_BYTES:
        raise SnakemakeReplayError(
            "replay configuration exceeds the size limit"
        )

    try:
        payload: Any = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise SnakemakeReplayError(
            "replay configuration is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise SnakemakeReplayError(
            "replay configuration must be an object"
        )

    try:
        require_supported_schema(
            payload,
            artifact_type=(
                ArtifactType
                .SNAKEMAKE_REPLAY_CONFIGURATION
            ),
        )

        return (
            SnakemakeReplayConfiguration
            .model_validate(payload)
        )
    except (
        ValidationError,
        ValueError,
    ) as exc:
        raise SnakemakeReplayError(
            "replay configuration failed validation"
        ) from exc


def _write_completion(
    path: Path,
    completion: SnakemakeReplayCompletion,
) -> None:
    content = (
        json.dumps(
            completion.model_dump(mode="json"),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise SnakemakeReplayError(
            "replay completion record already exists"
        ) from exc
    except OSError as exc:
        raise SnakemakeReplayError(
            "replay completion record could not be written"
        ) from exc


def _verify_configuration_against_envelope(
    *,
    configuration: SnakemakeReplayConfiguration,
    envelope: Any,
) -> None:
    comparisons = {
        "recipe_id": (
            configuration.recipe_id,
            envelope.recipe_id,
        ),
        "recipe_sha256": (
            configuration.recipe_sha256,
            envelope.recipe_sha256,
        ),
        "approval_id": (
            configuration.approval_id,
            envelope.approval_id,
        ),
        "approved_step_ids": (
            configuration.approved_step_ids,
            envelope.approved_step_ids,
        ),
        "topological_step_ids": (
            configuration.topological_step_ids,
            envelope.topological_step_ids,
        ),
    }

    conflicts = [
        field
        for field, (
            configured,
            expected,
        ) in comparisons.items()
        if configured != expected
    ]

    if conflicts:
        raise SnakemakeReplayError(
            "replay configuration conflicts with "
            "the rebuilt approved envelope: "
            + ", ".join(conflicts)
        )

def _run_async_executor(
    executor: ReplayExecutorProtocol,
    *,
    recipe_file: Path,
    approval_file: Path,
    recipe_root: Path,
    approval_root: Path,
    project_root: Path,
    agents_root: Path,
):
    """Run the async Executor from synchronous workflow code."""

    arguments = {
        "recipe_file": recipe_file,
        "approval_file": approval_file,
        "recipe_root": recipe_root,
        "approval_root": approval_root,
        "project_root": project_root,
        "agents_root": agents_root,
    }

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            executor(**arguments)
        )

    def run_in_thread():
        return asyncio.run(
            executor(**arguments)
        )

    with ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix=(
            "geoagent-approved-replay"
        ),
    ) as pool:
        return pool.submit(
            run_in_thread
        ).result()

def run_approved_recipe_replay(
    *,
    configuration_path: Path,
    completion_path: Path,
    settings: SnakemakeReplaySettings | None = None,
    executor: ReplayExecutorProtocol | None = None,
) -> SnakemakeReplayCompletion:
    """Replay only one exact server-approved recipe."""

    active = (
        settings
        or load_snakemake_replay_settings()
    )

    export_root = active.export_root.resolve()

    configuration_path = _contained_path(
        export_root,
        configuration_path,
        label="replay configuration",
    )

    package_root = configuration_path.parent

    if configuration_path.name != (
        "geoagent-replay.json"
    ):
        raise SnakemakeReplayError(
            "replay configuration filename is invalid"
        )

    completion_path = _contained_path(
        package_root,
        completion_path,
        label="replay completion",
    )

    if completion_path.name != (
        ".geoagent-replay-complete.json"
    ):
        raise SnakemakeReplayError(
            "replay completion filename is invalid"
        )

    if completion_path.exists():
        raise SnakemakeReplayError(
            "replay completion record already exists"
        )

    try:
        contract = (
            validate_snakemake_export_contract(
                package_root
            )
        )
    except SnakemakeExportContractError as exc:
        raise SnakemakeReplayError(
            "Snakemake export could not be validated"
        ) from exc

    if not contract.passed:
        raise SnakemakeReplayError(
            "Snakemake export failed static contract "
            "validation"
        )

    configuration = _load_configuration(
        configuration_path
    )

    if (
        configuration.recipe_id
        != contract.recipe_id
        or configuration.recipe_sha256
        != contract.recipe_sha256
        or configuration.approval_id
        != contract.approval_id
    ):
        raise SnakemakeReplayError(
            "replay configuration conflicts with "
            "the validated export manifest"
        )

    recipe_file = (
        active.recipe_root
        / configuration.recipe_filename
    )
    approval_file = (
        active.approval_root
        / configuration.approval_filename
    )

    try:
        recipe = load_recipe(
            recipe_file,
            recipe_root=active.recipe_root,
        )
        approval = load_recipe_approval(
            approval_file,
            approval_root=active.approval_root,
        )
        registry = load_skill_registry(
            active.project_root
        )
        envelope = build_recipe_execution_envelope(
            recipe=recipe,
            approval=approval,
            registry=registry,
        )
    except (
        RecipeApprovalError,
        RecipeExecutionPolicyError,
        RecipeStorageError,
        SkillRegistryError,
        OSError,
        ValueError,
    ) as exc:
        raise SnakemakeReplayError(
            "approved replay artifacts failed "
            "local verification"
        ) from exc

    _verify_configuration_against_envelope(
        configuration=configuration,
        envelope=envelope,
    )

    active_executor = executor

    if active_executor is None:
        from geoagent_harness.executor.service import (
            execute_approved_recipe_via_mcp,
        )

        active_executor = (
            execute_approved_recipe_via_mcp
        )

    try:
        result = _run_async_executor(
            active_executor,
            recipe_file=recipe_file,
            approval_file=approval_file,
            recipe_root=active.recipe_root,
            approval_root=active.approval_root,
            project_root=active.project_root,
            agents_root=active.agents_root,
        )
    except SnakemakeReplayError:
        raise
    except Exception as exc:
        raise SnakemakeReplayError(
            "approved recipe replay failed"
        ) from exc

    if (
        result.recipe_sha256
        != configuration.recipe_sha256
        or result.approval_id
        != configuration.approval_id
        or result.recipe.recipe_id
        != configuration.recipe_id
    ):
        raise SnakemakeReplayError(
            "Executor result conflicts with "
            "the approved replay identity"
        )

    if (
        result.recipe.final_status
        != "validated_success"
        or not result.recipe.validation_performed
    ):
        raise SnakemakeReplayError(
            "approved replay did not produce "
            "validated success"
        )

    record = result.execution_record

    completion = SnakemakeReplayCompletion(
        recipe_id=result.recipe.recipe_id,
        recipe_sha256=result.recipe_sha256,
        approval_id=result.approval_id,
        run_result_sha256=(
            record.run_result_sha256
        ),
        run_result_path=record.run_result_path,
        evidence_sha256=(
            record.evidence_sha256
        ),
        evidence_path=record.evidence_path,
        report_path=record.report_path,
        executor_result=(
            result.model_dump(mode="json")
        ),
    )

    _write_completion(
        completion_path,
        completion,
    )

    return completion

