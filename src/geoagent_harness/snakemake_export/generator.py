"""Deterministic generation of Snakemake replay packages."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from geoagent_harness.snakemake_export.schemas import (
    SnakemakeRecipeExportPlan,
    SnakemakeRecipeExportResult,
    SnakemakeReplayConfiguration,
)


class SnakemakeExportGenerationError(RuntimeError):
    """Raised when a replay package cannot be generated."""


def _sha256_text(content: str) -> str:
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def _canonical_json(
    payload: dict,
) -> str:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            separators=(",", ": "),
        )
        + "\n"
    )


def _export_directory_name(
    plan: SnakemakeRecipeExportPlan,
) -> str:
    return (
        f"{plan.recipe_id}."
        f"{plan.recipe_sha256}."
        "snakemake"
    )


def _render_configuration(
    plan: SnakemakeRecipeExportPlan,
) -> str:
    configuration = SnakemakeReplayConfiguration(
        recipe_id=plan.recipe_id,
        recipe_sha256=plan.recipe_sha256,
        approval_id=plan.approval_id,
        recipe_filename=(
            plan.recipe_filename
        ),
        approval_filename=(
            plan.approval_filename
        ),
        approved_step_ids=(
            plan.approved_step_ids
        ),
        topological_step_ids=(
            plan.topological_step_ids
        ),
        replay_entrypoint=(
            plan.replay_entrypoint
        ),
    )

    return _canonical_json(
        configuration.model_dump(
            mode="json"
        )
    )

def canonical_snakefile() -> str:
    return '''"""Generated GeoAgent approved-recipe replay workflow."""

from pathlib import Path

from geoagent_harness.snakemake_export.replay import (
    run_approved_recipe_replay,
)


configfile: "geoagent-replay.json"


rule all:
    input:
        ".geoagent-replay-complete.json"


rule replay_approved_recipe:
    output:
        ".geoagent-replay-complete.json"

    run:
        workflow_root = Path(workflow.basedir)

        run_approved_recipe_replay(
            configuration_path=(
                workflow_root
                / "geoagent-replay.json"
            ),
            completion_path=(
                workflow_root
                / str(output[0])
            ),
        )
'''


def _write_text(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )


def generate_snakemake_recipe_export(
    plan: SnakemakeRecipeExportPlan,
    *,
    export_root: Path = Path(
        "snakemake-exports"
    ),
) -> SnakemakeRecipeExportResult:
    """Generate one immutable replay package."""

    root = export_root.resolve()

    try:
        root.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise SnakemakeExportGenerationError(
            "Snakemake export root could not be created"
        ) from exc

    export_path = (
        root
        / _export_directory_name(plan)
    ).resolve()

    if root not in export_path.parents:
        raise SnakemakeExportGenerationError(
            "Snakemake export path escaped its root"
        )

    if export_path.exists():
        raise SnakemakeExportGenerationError(
            "Snakemake export already exists"
        )

    temporary_path: Path | None = None

    try:
        temporary_path = Path(
            tempfile.mkdtemp(
                prefix=".geoagent-snakemake-",
                dir=root,
            )
        )

        workflow_content = (
            canonical_snakefile()
        )
        configuration_content = (
            _render_configuration(plan)
        )

        workflow_sha256 = _sha256_text(
            workflow_content
        )
        configuration_sha256 = _sha256_text(
            configuration_content
        )

        workflow_path = (
            temporary_path
            / plan.workflow_filename
        )
        configuration_path = (
            temporary_path
            / plan.configuration_filename
        )
        manifest_path = (
            temporary_path
            / plan.manifest_filename
        )

        _write_text(
            workflow_path,
            workflow_content,
        )
        _write_text(
            configuration_path,
            configuration_content,
        )

        manifest_content = _canonical_json(
            {
                "schema_version": "1.0",
                "recipe_id": plan.recipe_id,
                "recipe_sha256": (
                    plan.recipe_sha256
                ),
                "approval_id": plan.approval_id,
                "workflow_path": (
                    plan.workflow_filename
                ),
                "workflow_sha256": (
                    workflow_sha256
                ),
                "configuration_path": (
                    plan.configuration_filename
                ),
                "configuration_sha256": (
                    configuration_sha256
                ),
                "replay_entrypoint": (
                    plan.replay_entrypoint
                ),
                "generated_files": [
                    plan.workflow_filename,
                    plan.configuration_filename,
                    plan.manifest_filename,
                ],
                "export_performed": True,
                "workflow_executed": False,
                "recipe_execution_performed": False,
                "approval_modified": False,
                "recipe_modified": False,
            }
        )

        _write_text(
            manifest_path,
            manifest_content,
        )

        temporary_path.rename(
            export_path
        )
        temporary_path = None

    except OSError as exc:
        raise SnakemakeExportGenerationError(
            "Snakemake export generation failed"
        ) from exc
    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            shutil.rmtree(
                temporary_path
            )

    return SnakemakeRecipeExportResult(
        recipe_id=plan.recipe_id,
        recipe_sha256=plan.recipe_sha256,
        approval_id=plan.approval_id,
        export_path=export_path.as_posix(),
        workflow_path=(
            plan.workflow_filename
        ),
        workflow_sha256=workflow_sha256,
        configuration_path=(
            plan.configuration_filename
        ),
        configuration_sha256=(
            configuration_sha256
        ),
        manifest_path=(
            plan.manifest_filename
        ),
        generated_files=[
            plan.workflow_filename,
            plan.configuration_filename,
            plan.manifest_filename,
        ],
    )

