"""Immutable storage for recipe-run evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.recipes.evidence_schemas import (
    RecipeRunEvidence,
)
from geoagent_harness.redaction import (
    redact_value,
)
from geoagent_harness.schema_registry import (
    ArtifactType,
    require_supported_schema,
)

from geoagent_harness.recipes.schemas import (
    RecipeRunResult,
)

MAX_RECIPE_RUN_RESULT_BYTES = 5_000_000
MAX_RECIPE_EVIDENCE_BYTES = 5_000_000


class RecipeEvidenceStorageError(RuntimeError):
    """Raised when recipe evidence cannot be stored safely."""


def canonical_recipe_evidence_json(
    evidence: RecipeRunEvidence,
) -> str:
    """Return the canonical representation used for identity."""

    payload = redact_value(
        evidence.model_dump(mode="json")
    )

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def recipe_evidence_sha256(
    evidence: RecipeRunEvidence,
) -> str:
    """Return the digest of one exact evidence record."""

    return hashlib.sha256(
        canonical_recipe_evidence_json(
            evidence
        ).encode("utf-8")
    ).hexdigest()


def recipe_evidence_path(
    *,
    evidence: RecipeRunEvidence,
    evidence_root: Path,
) -> Path:
    """Return the immutable digest-addressed evidence path."""

    root = evidence_root.resolve()

    digest = recipe_evidence_sha256(
        evidence
    )

    candidate = (
        root
        / f"{evidence.recipe_id}.{digest}.json"
    ).resolve()

    if candidate.parent != root:
        raise RecipeEvidenceStorageError(
            "recipe evidence path escaped its "
            "trusted root"
        )

    return candidate


def write_recipe_evidence(
    evidence: RecipeRunEvidence,
    *,
    evidence_root: Path,
) -> Path:
    """Write evidence once without overwriting."""

    try:
        evidence_root.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence root could not "
            "be prepared"
        ) from exc

    path = recipe_evidence_path(
        evidence=evidence,
        evidence_root=evidence_root,
    )

    content = (
        canonical_recipe_evidence_json(
            evidence
        )
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as stream:
            stream.write(content)
            stream.write("\n")
    except FileExistsError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence already exists; "
            "overwriting is blocked"
        ) from exc
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence could not be written"
        ) from exc

    return path

def canonical_recipe_run_result_json(
    result: RecipeRunResult,
) -> str:
    """Return canonical JSON for one recipe-run result."""

    payload = redact_value(
        result.model_dump(mode="json")
    )

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def recipe_run_result_sha256(
    result: RecipeRunResult,
) -> str:
    """Return the digest of one exact recipe result."""

    return hashlib.sha256(
        canonical_recipe_run_result_json(
            result
        ).encode("utf-8")
    ).hexdigest()


def recipe_run_result_path(
    *,
    result: RecipeRunResult,
    result_root: Path,
) -> Path:
    """Return the immutable result path."""

    root = result_root.resolve()

    digest = recipe_run_result_sha256(
        result
    )

    candidate = (
        root
        / f"{result.recipe_id}.{digest}.json"
    ).resolve()

    if candidate.parent != root:
        raise RecipeEvidenceStorageError(
            "recipe-run result path escaped its "
            "trusted root"
        )

    return candidate


def write_recipe_run_result(
    result: RecipeRunResult,
    *,
    result_root: Path,
) -> Path:
    """Write one recipe result without overwriting."""

    try:
        result_root.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result root could not "
            "be prepared"
        ) from exc

    path = recipe_run_result_path(
        result=result,
        result_root=result_root,
    )

    content = canonical_recipe_run_result_json(
        result
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as stream:
            stream.write(content)
            stream.write("\n")
    except FileExistsError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result already exists; "
            "overwriting is blocked"
        ) from exc
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result could not be written"
        ) from exc

    return path

def load_recipe_run_result(
    path: Path,
    *,
    result_root: Path,
) -> RecipeRunResult:
    """Load one raw recipe-run result from a trusted root."""

    root = result_root.resolve()
    resolved = path.resolve()

    if resolved.parent != root:
        raise RecipeEvidenceStorageError(
            "recipe-run result path escaped its "
            "trusted root"
        )

    if not resolved.is_file():
        raise RecipeEvidenceStorageError(
            "recipe-run result file does not exist"
        )

    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result could not be inspected"
        ) from exc

    if size > MAX_RECIPE_RUN_RESULT_BYTES:
        raise RecipeEvidenceStorageError(
            "recipe-run result exceeds the size limit"
        )

    try:
        payload: Any = json.loads(
            resolved.read_text(encoding="utf-8")
        )

        if not isinstance(payload, dict):
            raise RecipeEvidenceStorageError(
                "recipe-run result must be an object"
            )

        require_supported_schema(
            payload,
            artifact_type=(
                ArtifactType.RECIPE_RUN_RESULT
            ),
        )

        result = RecipeRunResult.model_validate(
            payload
        )
    except UnicodeDecodeError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result is not UTF-8"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result is not valid JSON"
        ) from exc
    except ValidationError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result failed schema validation"
        ) from exc
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe-run result could not be read"
        ) from exc
        
    expected_name = (
        f"{result.recipe_id}."
        f"{recipe_run_result_sha256(result)}"
        ".json"
    )

    if resolved.name != expected_name:
        raise RecipeEvidenceStorageError(
            "recipe-run result filename does not "
            "match its content digest"
        )

    return result

def load_recipe_evidence(
    path: Path,
    *,
    evidence_root: Path,
) -> RecipeRunEvidence:
    """Load evidence only from its trusted root."""

    root = evidence_root.resolve()
    resolved = path.resolve()

    if resolved.parent != root:
        raise RecipeEvidenceStorageError(
            "recipe evidence path escaped its "
            "trusted root"
        )

    if not resolved.is_file():
        raise RecipeEvidenceStorageError(
            "recipe evidence file does not exist"
        )

    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence could not be inspected"
        ) from exc

    if size > MAX_RECIPE_EVIDENCE_BYTES:
        raise RecipeEvidenceStorageError(
            "recipe evidence exceeds the size limit"
        )

    try:
        payload: Any = json.loads(
            resolved.read_text(encoding="utf-8")
        )

        if not isinstance(payload, dict):
            raise RecipeEvidenceStorageError(
                "recipe evidence must be an object"
            )

        require_supported_schema(
            payload,
            artifact_type=(
                ArtifactType.RECIPE_RUN_EVIDENCE
            ),
        )

        evidence = RecipeRunEvidence.model_validate(
            payload
        )
    except UnicodeDecodeError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence is not UTF-8"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence is not valid JSON"
        ) from exc
    except ValidationError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence failed schema validation"
        ) from exc
    except OSError as exc:
        raise RecipeEvidenceStorageError(
            "recipe evidence could not be read"
        ) from exc

    expected_name = (
        f"{evidence.recipe_id}."
        f"{recipe_evidence_sha256(evidence)}"
        ".json"
    )

    if resolved.name != expected_name:
        raise RecipeEvidenceStorageError(
            "recipe evidence filename does not "
            "match its content digest"
        )

    return evidence

