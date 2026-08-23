"""Explicit atomic promotion of one verified candidate."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

import yaml

from geoagent_harness.skill_definitions.promotion_plan import (
    SkillPromotionPlanError,
    plan_skill_candidate_promotion,
)
from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
    SkillCandidatePromotionResult,
    SkillCandidateTestRecord,
)
from geoagent_harness.skill_definitions.test_evidence import (
    SkillCandidateTestEvidenceError,
    candidate_tree_sha256,
)
from geoagent_harness.skill_registry import (
    SkillRegistry,
    SkillRegistryError,
    load_skill_registry,
)


class SkillCandidatePromotionExecutionError(
    RuntimeError
):
    """Raised when explicit promotion cannot complete atomically."""


def _sha256_bytes(
    content: bytes,
) -> str:
    return hashlib.sha256(
        content
    ).hexdigest()


def _read_bytes(
    path: Path,
    *,
    label: str,
) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SkillCandidatePromotionExecutionError(
            f"{label} could not be read"
        ) from exc


def _stage_bytes(
    *,
    destination: Path,
    content: bytes,
    mode: int,
) -> Path:
    """Stage bytes beside their final destination."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=(
            f".{destination.name}."
            "geoagent-promotion-"
        ),
        dir=destination.parent,
    )

    temporary = Path(temporary_name)

    try:
        with os.fdopen(
            descriptor,
            "wb",
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(
            temporary,
            mode,
        )
    except OSError:
        temporary.unlink(
            missing_ok=True
        )
        raise

    return temporary


def _atomic_replace(
    source: Path,
    destination: Path,
) -> None:
    """Replace one exact destination atomically."""

    os.replace(
        source,
        destination,
    )


def _remove_new_file(
    path: Path,
) -> None:
    """Roll back only a file created by this promotion."""

    try:
        path.unlink(
            missing_ok=True
        )
    except OSError:
        # The original promotion error remains primary.
        pass


def promote_skill_candidate(
    *,
    definition: DeclarativeSkillDefinition,
    candidate_path: Path,
    candidate_root: Path,
    test_record: SkillCandidateTestRecord,
    project_root: Path,
    confirmed_skill_id: str,
) -> SkillCandidatePromotionResult:
    """Explicitly promote one exact tested candidate."""

    if confirmed_skill_id != definition.skill_id:
        raise SkillCandidatePromotionExecutionError(
            "promotion confirmation does not match "
            "the exact skill ID"
        )

    try:
        plan = plan_skill_candidate_promotion(
            definition=definition,
            candidate_path=candidate_path,
            candidate_root=candidate_root,
            test_record=test_record,
            project_root=project_root,
        )
    except SkillPromotionPlanError as exc:
        raise SkillCandidatePromotionExecutionError(
            "candidate failed final promotion planning"
        ) from exc

    root = project_root.resolve()
    candidate = candidate_path.resolve()
    registry_path = Path(
        plan.registry_path
    )

    try:
        current_candidate_digest = (
            candidate_tree_sha256(
                candidate
            )
        )
    except SkillCandidateTestEvidenceError as exc:
        raise SkillCandidatePromotionExecutionError(
            "candidate could not be rehashed"
        ) from exc

    if (
        current_candidate_digest
        != plan.candidate_tree_sha256
    ):
        raise SkillCandidatePromotionExecutionError(
            "candidate changed after promotion planning"
        )

    registry_before = _read_bytes(
        registry_path,
        label="trusted registry",
    )

    if (
        _sha256_bytes(registry_before)
        != plan.registry_before_sha256
    ):
        raise SkillCandidatePromotionExecutionError(
            "trusted registry changed after "
            "promotion planning"
        )

    try:
        registry = load_skill_registry(
            root
        )
    except SkillRegistryError as exc:
        raise SkillCandidatePromotionExecutionError(
            "trusted registry could not be reloaded"
        ) from exc

    try:
        registry.get_skill(
            definition.skill_id
        )
    except KeyError:
        pass
    else:
        raise SkillCandidatePromotionExecutionError(
            "skill became registered before promotion"
        )

    updated_registry = SkillRegistry(
        schema_version=registry.schema_version,
        skills=[
            *registry.skills,
            plan.registry_entry,
        ],
    )

    registry_content = yaml.safe_dump(
        updated_registry.model_dump(
            mode="json",
            exclude_none=True,
        ),
        sort_keys=False,
    ).encode("utf-8")

    registry_after_sha256 = (
        _sha256_bytes(
            registry_content
        )
    )

    staged_files: list[
        tuple[Path, Path]
    ] = []
    copied_destinations: list[Path] = []
    registry_temporary: Path | None = None

    try:
        for promotion_file in plan.files:
            source = (
                candidate
                / promotion_file.source_path
            ).resolve()
            destination = (
                root
                / promotion_file.destination_path
            ).resolve()

            if candidate not in source.parents:
                raise (
                    SkillCandidatePromotionExecutionError(
                        "promotion source escaped "
                        "the candidate"
                    )
                )

            if root not in destination.parents:
                raise (
                    SkillCandidatePromotionExecutionError(
                        "promotion destination escaped "
                        "the project"
                    )
                )

            if (
                not source.is_file()
                or source.is_symlink()
            ):
                raise (
                    SkillCandidatePromotionExecutionError(
                        "promotion source became unsafe"
                    )
                )

            if destination.exists():
                raise (
                    SkillCandidatePromotionExecutionError(
                        "promotion destination appeared "
                        "after planning"
                    )
                )

            source_content = _read_bytes(
                source,
                label="promotion source",
            )

            if (
                _sha256_bytes(source_content)
                != promotion_file.sha256
            ):
                raise (
                    SkillCandidatePromotionExecutionError(
                        "promotion source digest changed"
                    )
                )

            temporary = _stage_bytes(
                destination=destination,
                content=source_content,
                mode=0o644,
            )

            staged_files.append(
                (
                    temporary,
                    destination,
                )
            )

        # Verify the entire candidate once more after staging.
        if (
            candidate_tree_sha256(candidate)
            != plan.candidate_tree_sha256
        ):
            raise SkillCandidatePromotionExecutionError(
                "candidate changed while files "
                "were being staged"
            )

        registry_mode = (
            registry_path.stat().st_mode
            & 0o777
        )

        registry_temporary = _stage_bytes(
            destination=registry_path,
            content=registry_content,
            mode=registry_mode,
        )

        # Copy new files first. The registry remains unchanged
        # until all source and test files exist.
        for temporary, destination in (
            staged_files
        ):
            if destination.exists():
                raise (
                    SkillCandidatePromotionExecutionError(
                        "promotion destination appeared "
                        "during commit"
                    )
                )

            _atomic_replace(
                temporary,
                destination,
            )
            copied_destinations.append(
                destination
            )

        # Recheck registry immediately before committing it.
        if (
            _sha256_bytes(
                _read_bytes(
                    registry_path,
                    label="trusted registry",
                )
            )
            != plan.registry_before_sha256
        ):
            raise SkillCandidatePromotionExecutionError(
                "trusted registry changed during promotion"
            )

        _atomic_replace(
            registry_temporary,
            registry_path,
        )
        registry_temporary = None

    except (
        OSError,
        SkillCandidateTestEvidenceError,
        SkillCandidatePromotionExecutionError,
        ValueError,
    ) as exc:
        for temporary, _destination in (
            staged_files
        ):
            temporary.unlink(
                missing_ok=True
            )

        if registry_temporary is not None:
            registry_temporary.unlink(
                missing_ok=True
            )

        for destination in reversed(
            copied_destinations
        ):
            _remove_new_file(
                destination
            )

        if isinstance(
            exc,
            SkillCandidatePromotionExecutionError,
        ):
            raise

        raise SkillCandidatePromotionExecutionError(
            "skill promotion transaction failed"
        ) from exc

    return SkillCandidatePromotionResult(
        skill_id=definition.skill_id,
        adapter_id=definition.adapter_id,
        definition_sha256=(
            plan.definition_sha256
        ),
        candidate_tree_sha256=(
            plan.candidate_tree_sha256
        ),
        registry_before_sha256=(
            plan.registry_before_sha256
        ),
        registry_after_sha256=(
            registry_after_sha256
        ),
        copied_files=[
            file.destination_path
            for file in plan.files
        ],
        registry_entry=plan.registry_entry,
        files_copied=True,
        registry_modified=True,
        implementation_trusted=True,
        promotion_performed=True,
        execution_performed=False,
    )

