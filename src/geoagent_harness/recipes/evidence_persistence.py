"""Durable persistence for completed recipe execution."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from geoagent_harness.mcp_server.settings import (
    MCPSettings,
)
from geoagent_harness.recipes.evidence import (
    RecipeEvidenceError,
    build_recipe_run_evidence,
)
from geoagent_harness.recipes.evidence_reporting import (
    RecipeEvidenceReportError,
    render_recipe_evidence_report,
    write_recipe_evidence_report,
)
from geoagent_harness.recipes.evidence_schemas import (
    RecipeExecutionRecord,
)
from geoagent_harness.recipes.evidence_storage import (
    RecipeEvidenceStorageError,
    recipe_evidence_sha256,
    recipe_run_result_sha256,
    write_recipe_evidence,
    write_recipe_run_result,
)
from geoagent_harness.recipes.schemas import (
    RecipeRunResult,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
)


class RecipeEvidencePersistenceError(RuntimeError):
    """Raised when completed execution cannot be recorded."""


def _reference_path(
    path: Path,
    *,
    project_root: Path,
) -> str:
    """Return a portable project-relative reference."""

    resolved_project = project_root.resolve()
    resolved_path = path.resolve()

    try:
        return resolved_path.relative_to(
            resolved_project
        ).as_posix()
    except ValueError as exc:
        raise RecipeEvidencePersistenceError(
            "persisted recipe artifact is outside "
            "the project root"
        ) from exc


def persist_recipe_run(
    *,
    run_result: RecipeRunResult,
    registry: SkillRegistry,
    settings: MCPSettings,
    recorded_at: datetime,
) -> RecipeExecutionRecord:
    """Persist one completed run and its evidence."""

    try:
        # Construct and validate everything possible
        # before performing persistence writes.
        evidence = build_recipe_run_evidence(
            run_result=run_result,
            registry=registry,
            input_root=settings.input_root,
            output_root=settings.output_root,
            recorded_at=recorded_at,
        )

        run_digest = recipe_run_result_sha256(
            run_result
        )
        evidence_digest = recipe_evidence_sha256(
            evidence
        )

        # Render before writing so formatting failures
        # cannot occur after the first durable write.
        render_recipe_evidence_report(evidence)

        # The raw result is written first because it can
        # be used to recover evidence after an interrupted
        # persistence sequence. Existing files are never
        # overwritten or deleted.
        run_path = write_recipe_run_result(
            run_result,
            result_root=settings.recipe_run_root,
        )

        evidence_path = write_recipe_evidence(
            evidence,
            evidence_root=(
                settings.recipe_evidence_root
            ),
        )

        report_path = write_recipe_evidence_report(
            evidence,
            report_root=settings.report_root,
        )

    except (
        RecipeEvidenceError,
        RecipeEvidenceReportError,
        RecipeEvidenceStorageError,
        OSError,
        ValueError,
    ) as exc:
        raise RecipeEvidencePersistenceError(
            "recipe execution completed but its "
            "durable evidence could not be fully "
            "persisted; manual review is required"
        ) from exc

    return RecipeExecutionRecord(
        recipe_id=run_result.recipe_id,
        recipe_sha256=run_result.recipe_sha256,
        approval_id=run_result.approval_id,
        final_status=run_result.final_status,
        run_result_sha256=run_digest,
        run_result_path=_reference_path(
            run_path,
            project_root=settings.project_root,
        ),
        evidence_sha256=evidence_digest,
        evidence_path=_reference_path(
            evidence_path,
            project_root=settings.project_root,
        ),
        report_path=_reference_path(
            report_path,
            project_root=settings.project_root,
        ),
        execution_performed=True,
        evidence_recorded=True,
        report_written=True,
    )

