"""Safe construction of artifact and lineage evidence."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from geoagent_harness.recipes.evidence_schemas import (
    ArtifactReference,
    ArtifactRole,
    LineageEdge,
    RecipeRunEvidence,
)
from geoagent_harness.recipes.schemas import (
    RecipeRunResult,
)
from geoagent_harness.redaction import (
    redact_text,
    redact_value,
)
from geoagent_harness.skill_registry import (
    SkillAccess,
    SkillRegistry,
    SkillStatus,
)
from geoagent_harness.skills.convert_vector.schemas import (
    ConvertVectorResult,
    ConvertVectorValidationResult,
)


MAX_EVIDENCE_ARTIFACT_BYTES = 2_000_000_000
_HASH_CHUNK_BYTES = 1024 * 1024

_MEDIA_TYPES = {
    ".geojson": "application/geo+json",
    ".gpkg": "application/geopackage+sqlite3",
}


class RecipeEvidenceError(RuntimeError):
    """Raised when recipe evidence cannot be built safely."""


def _resolve_artifact(
    *,
    value: str,
    root: Path,
    role: ArtifactRole,
) -> Path:
    trusted_root = root.resolve()

    candidate = Path(value)

    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate

    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise RecipeEvidenceError(
            f"{role.value} artifact does not exist"
        ) from exc

    try:
        resolved.relative_to(trusted_root)
    except ValueError as exc:
        raise RecipeEvidenceError(
            f"{role.value} artifact escaped its "
            "trusted root"
        ) from exc

    if not resolved.is_file():
        raise RecipeEvidenceError(
            f"{role.value} artifact is not a file"
        )

    suffix = resolved.suffix.lower()

    if suffix == ".shp":
        raise RecipeEvidenceError(
            "Shapefile evidence requires a "
            "complete sidecar-bundle manifest"
        )

    if suffix not in _MEDIA_TYPES:
        raise RecipeEvidenceError(
            "artifact format is not supported "
            "for recipe evidence"
        )

    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise RecipeEvidenceError(
            "artifact size could not be inspected"
        ) from exc

    if size > MAX_EVIDENCE_ARTIFACT_BYTES:
        raise RecipeEvidenceError(
            "artifact exceeds the evidence size limit"
        )

    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    try:
        with path.open("rb") as stream:
            while chunk := stream.read(
                _HASH_CHUNK_BYTES
            ):
                digest.update(chunk)
    except OSError as exc:
        raise RecipeEvidenceError(
            "artifact could not be hashed"
        ) from exc

    return digest.hexdigest()


def _display_path(
    path: Path,
    *,
    trusted_root: Path,
) -> str:
    working_directory = Path.cwd().resolve()

    try:
        return path.relative_to(
            working_directory
        ).as_posix()
    except ValueError:
        return path.relative_to(
            trusted_root.resolve()
        ).as_posix()


def _input_artifact_id(
    display_path: str,
) -> str:
    digest = hashlib.sha256(
        display_path.encode("utf-8")
    ).hexdigest()

    return f"input_{digest[:16]}"


def _artifact_reference(
    *,
    path_value: str,
    root: Path,
    role: ArtifactRole,
    artifact_id: str,
    producer_step_id: str | None = None,
) -> ArtifactReference:
    resolved = _resolve_artifact(
        value=path_value,
        root=root,
        role=role,
    )

    return ArtifactReference(
        artifact_id=artifact_id,
        role=role,
        path=_display_path(
            resolved,
            trusted_root=root,
        ),
        sha256=_sha256(resolved),
        size_bytes=resolved.stat().st_size,
        media_type=_MEDIA_TYPES[
            resolved.suffix.lower()
        ],
        producer_step_id=producer_step_id,
    )


def build_recipe_run_evidence(
    *,
    run_result: RecipeRunResult,
    registry: SkillRegistry,
    input_root: Path = Path("data/input"),
    output_root: Path = Path("data/output"),
    recorded_at: datetime | None = None,
) -> RecipeRunEvidence:
    """Build trusted evidence from one completed recipe result."""

    sanitized_result = RecipeRunResult.model_validate(
        redact_value(
            run_result.model_dump(mode="json")
        )
    )

    artifacts_by_path: dict[
        tuple[ArtifactRole, str],
        ArtifactReference,
    ] = {}
    lineage: list[LineageEdge] = []
    skill_versions: dict[str, str] = {}

    for step in sanitized_result.step_results:
        try:
            skill = registry.get_skill(
                step.skill_id
            )
        except KeyError as exc:
            raise RecipeEvidenceError(
                "recipe result references an "
                "unregistered skill"
            ) from exc

        if (
            skill.status
            != SkillStatus.IMPLEMENTED
            or skill.version is None
        ):
            raise RecipeEvidenceError(
                "recipe result references a skill "
                "without an implemented version"
            )

        skill_versions[skill.id] = skill.version

        if step.skill_id == "inspect_vector":
            source_value = step.execution.result.get(
                "source"
            )

            if not isinstance(source_value, str):
                raise RecipeEvidenceError(
                    "inspect_vector result is missing "
                    "its source artifact"
                )

            source = _artifact_reference(
                path_value=source_value,
                root=input_root,
                role=ArtifactRole.INPUT,
                artifact_id=_input_artifact_id(
                    source_value
                ),
            )

            artifacts_by_path[
                (ArtifactRole.INPUT, source.path)
            ] = source

            continue

        if step.skill_id == "convert_vector":
            try:
                conversion = (
                    ConvertVectorResult.model_validate(
                        step.execution.result
                    )
                )

                validation = (
                    ConvertVectorValidationResult
                    .model_validate(
                        step.validation_result
                    )
                )
            except ValidationError as exc:
                raise RecipeEvidenceError(
                    "conversion result failed its "
                    "registered schema"
                ) from exc

            if (
                conversion.source
                != validation.source
                or conversion.target
                != validation.target
            ):
                raise RecipeEvidenceError(
                    "conversion and validation paths "
                    "do not match"
                )

            if (
                sanitized_result.final_status
                == "validated_success"
                and validation.passed is not True
            ):
                raise RecipeEvidenceError(
                    "successful recipe lacks passing "
                    "conversion validation"
                )

            source = _artifact_reference(
                path_value=conversion.source,
                root=input_root,
                role=ArtifactRole.INPUT,
                artifact_id=_input_artifact_id(
                    conversion.source
                ),
            )

            artifacts_by_path[
                (ArtifactRole.INPUT, source.path)
            ] = source

            if step.execution.output_ids:
                output_id = (
                    step.execution.output_ids[0]
                )
            else:
                output_id = (
                    f"output_{step.step_id}"
                )

            output = _artifact_reference(
                path_value=conversion.target,
                root=output_root,
                role=ArtifactRole.OUTPUT,
                artifact_id=output_id,
                producer_step_id=step.step_id,
            )

            if (
                output.size_bytes
                != conversion.target_size_bytes
            ):
                raise RecipeEvidenceError(
                    "recorded output size conflicts "
                    "with the artifact"
                )

            artifacts_by_path[
                (ArtifactRole.OUTPUT, output.path)
            ] = output

            lineage.append(
                LineageEdge(
                    source_artifact_id=(
                        source.artifact_id
                    ),
                    target_artifact_id=(
                        output.artifact_id
                    ),
                    step_id=step.step_id,
                    skill_id=step.skill_id,
                )
            )

            continue

        if skill.access in {
            SkillAccess.ARTIFACT_WRITE,
            SkillAccess.DATABASE_WRITE,
        }:
            raise RecipeEvidenceError(
                "evidence extraction is not "
                "implemented for a write skill"
            )

    if not artifacts_by_path:
        raise RecipeEvidenceError(
            "recipe result contains no physical "
            "artifact evidence"
        )

    return RecipeRunEvidence(
        recipe_id=sanitized_result.recipe_id,
        recipe_sha256=(
            sanitized_result.recipe_sha256
        ),
        approval_id=(
            sanitized_result.approval_id
        ),
        final_status=(
            sanitized_result.final_status
        ),
        run_result=sanitized_result,
        artifacts=list(
            artifacts_by_path.values()
        ),
        lineage=lineage,
        skill_versions=skill_versions,
        warnings=[
            redact_text(warning)
            for warning in sanitized_result.warnings
        ],
        recorded_at=(
            recorded_at
            or datetime.now(timezone.utc)
        ),
        secrets_redacted=True,
    )

