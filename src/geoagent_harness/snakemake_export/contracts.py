"""Static validation for generated Snakemake exports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from geoagent_harness.snakemake_export.generator import (
    canonical_snakefile,
)
from geoagent_harness.snakemake_export.schemas import (
    SnakemakeExportContractResult,
)


MAX_SNAKEMAKE_EXPORT_FILE_BYTES = 250_000

_EXPECTED_FILES = {
    "Snakefile",
    "geoagent-replay.json",
    "snakemake-export-manifest.json",
}

_REPLAY_ENTRYPOINT = (
    "geoagent_harness.snakemake_export."
    "replay:run_approved_recipe_replay"
)


class SnakemakeExportContractError(RuntimeError):
    """Raised when an export package cannot be inspected."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json_object(
    path: Path,
) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise SnakemakeExportContractError(
            f"{path.name} is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise SnakemakeExportContractError(
            f"{path.name} must contain an object"
        )

    return payload


def _contained_file(
    root: Path,
    filename: str,
) -> Path:
    path = (
        root
        / filename
    ).resolve()

    if root not in path.parents:
        raise SnakemakeExportContractError(
            "export file escaped its package"
        )

    if path.is_symlink():
        raise SnakemakeExportContractError(
            "export files cannot be symlinks"
        )

    return path


def validate_snakemake_export_contract(
    export_path: Path,
) -> SnakemakeExportContractResult:
    """Validate an export without running Snakemake."""

    root = export_path.resolve()

    if not root.is_dir():
        raise SnakemakeExportContractError(
            "Snakemake export does not exist"
        )

    if root.is_symlink():
        raise SnakemakeExportContractError(
            "Snakemake export cannot be a symlink"
        )

    manifest_path = _contained_file(
        root,
        "snakemake-export-manifest.json",
    )
    configuration_path = _contained_file(
        root,
        "geoagent-replay.json",
    )
    workflow_path = _contained_file(
        root,
        "Snakefile",
    )

    if not manifest_path.is_file():
        raise SnakemakeExportContractError(
            "Snakemake export manifest does not exist"
        )

    if not configuration_path.is_file():
        raise SnakemakeExportContractError(
            "replay configuration does not exist"
        )

    if not workflow_path.is_file():
        raise SnakemakeExportContractError(
            "Snakefile does not exist"
        )

    manifest = _load_json_object(
        manifest_path
    )
    configuration = _load_json_object(
        configuration_path
    )

    violations: list[str] = []
    checked_files: list[str] = []

    generated_files = manifest.get(
        "generated_files"
    )

    if (
        not isinstance(generated_files, list)
        or set(generated_files) != _EXPECTED_FILES
        or len(generated_files) != len(
            _EXPECTED_FILES
        )
    ):
        violations.append(
            "manifest generated file set is invalid"
        )

    for filename in sorted(_EXPECTED_FILES):
        path = _contained_file(
            root,
            filename,
        )

        try:
            size = path.stat().st_size
        except OSError:
            violations.append(
                f"{filename} could not be inspected"
            )
            continue

        if size > MAX_SNAKEMAKE_EXPORT_FILE_BYTES:
            violations.append(
                f"{filename} exceeds the size limit"
            )
            continue

        checked_files.append(filename)

    try:
        workflow_bytes = workflow_path.read_bytes()
        configuration_bytes = (
            configuration_path.read_bytes()
        )
    except OSError as exc:
        raise SnakemakeExportContractError(
            "export content could not be read"
        ) from exc

    workflow_digest = _sha256_bytes(
        workflow_bytes
    )
    configuration_digest = _sha256_bytes(
        configuration_bytes
    )

    if workflow_digest != manifest.get(
        "workflow_sha256"
    ):
        violations.append(
            "Snakefile digest conflicts with manifest"
        )

    if configuration_digest != manifest.get(
        "configuration_sha256"
    ):
        violations.append(
            "replay configuration digest conflicts "
            "with manifest"
        )

    try:
        workflow_text = workflow_bytes.decode(
            "utf-8"
        )
    except UnicodeDecodeError:
        violations.append(
            "Snakefile is not UTF-8"
        )
    else:
        if workflow_text != canonical_snakefile():
            violations.append(
                "Snakefile does not match the trusted "
                "canonical workflow"
            )

        prohibited_fragments = (
            "shell:",
            "subprocess",
            "os.system",
            "os.popen",
            "convert_vector",
            "inspect_vector",
            "psycopg",
            "sqlalchemy",
        )

        for fragment in prohibited_fragments:
            if fragment in workflow_text:
                violations.append(
                    "Snakefile contains prohibited "
                    f"content: {fragment}"
                )

    identity_fields = (
        "recipe_id",
        "recipe_sha256",
        "approval_id",
    )

    for field in identity_fields:
        if configuration.get(field) != (
            manifest.get(field)
        ):
            violations.append(
                f"{field} conflicts between "
                "configuration and manifest"
            )

    if configuration.get(
        "replay_entrypoint"
    ) != _REPLAY_ENTRYPOINT:
        violations.append(
            "replay entrypoint is not the trusted adapter"
        )

    if manifest.get(
        "replay_entrypoint"
    ) != _REPLAY_ENTRYPOINT:
        violations.append(
            "manifest replay entrypoint is not trusted"
        )

    recipe_filename = configuration.get(
        "recipe_filename"
    )
    approval_filename = configuration.get(
        "approval_filename"
    )

    for label, value in (
        ("recipe_filename", recipe_filename),
        ("approval_filename", approval_filename),
    ):
        if (
            not isinstance(value, str)
            or Path(value).name != value
            or Path(value).suffix != ".json"
            or value in {".json", ".."}
        ):
            violations.append(
                f"{label} must be a plain JSON filename"
            )

    approved_steps = configuration.get(
        "approved_step_ids"
    )
    topological_steps = configuration.get(
        "topological_step_ids"
    )

    if (
        not isinstance(approved_steps, list)
        or not approved_steps
        or len(approved_steps)
        != len(set(approved_steps))
    ):
        violations.append(
            "approved step scope is invalid"
        )

    if (
        not isinstance(topological_steps, list)
        or not topological_steps
        or len(topological_steps)
        != len(set(topological_steps))
    ):
        violations.append(
            "topological step scope is invalid"
        )

    if (
        isinstance(approved_steps, list)
        and isinstance(topological_steps, list)
        and not set(approved_steps).issubset(
            set(topological_steps)
        )
    ):
        violations.append(
            "approved steps are outside "
            "the topological scope"
        )

    for field in (
        "workflow_executed",
        "recipe_execution_performed",
        "approval_modified",
        "recipe_modified",
    ):
        if configuration.get(field) is not False:
            violations.append(
                f"configuration must record {field}=false"
            )

        if manifest.get(field) is not False:
            violations.append(
                f"manifest must record {field}=false"
            )

    recipe_id = manifest.get("recipe_id")
    recipe_sha256 = manifest.get(
        "recipe_sha256"
    )
    approval_id = manifest.get(
        "approval_id"
    )

    if not isinstance(recipe_id, str):
        raise SnakemakeExportContractError(
            "manifest recipe ID is invalid"
        )

    if not isinstance(recipe_sha256, str):
        raise SnakemakeExportContractError(
            "manifest recipe digest is invalid"
        )

    if not isinstance(approval_id, str):
        raise SnakemakeExportContractError(
            "manifest approval ID is invalid"
        )

    return SnakemakeExportContractResult(
        recipe_id=recipe_id,
        recipe_sha256=recipe_sha256,
        approval_id=approval_id,
        export_path=root.as_posix(),
        passed=not violations,
        checked_files=checked_files,
        violations=list(
            dict.fromkeys(violations)
        ),
        warnings=[
            (
                "Static contract validation does not "
                "execute Snakemake or the recipe."
            )
        ],
    )

