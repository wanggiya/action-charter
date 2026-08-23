"""Read-only planning for explicit skill promotion."""

from __future__ import annotations

import hashlib
from pathlib import Path

from geoagent_harness.skill_definitions.adapters import (
    RasterInspectionRendererError,
    render_raster_inspection_candidate,
)
from geoagent_harness.skill_definitions.catalog import (
    TrustedAdapterError,
    get_trusted_adapter,
)
from geoagent_harness.skill_definitions.promotion import (
    SkillCandidatePromotionError,
    assess_skill_candidate_for_promotion,
)
from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
    SkillCandidatePromotionPlan,
    SkillCandidateTestRecord,
    SkillPromotionFile,
)
from geoagent_harness.skill_registry import (
    SkillDefinition,
    SkillRegistryError,
    SkillStatus,
    load_skill_registry,
    skill_registry_path,
)
from geoagent_harness.skill_definitions.generation import (
    build_skill_contract,
)

class SkillPromotionPlanError(RuntimeError):
    """Raised when promotion cannot be safely planned."""


def _file_sha256(
    path: Path,
) -> str:
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise SkillPromotionPlanError(
            "promotion source file could not be read"
        ) from exc

    return hashlib.sha256(
        content
    ).hexdigest()


def _expected_candidate_files(
    definition: DeclarativeSkillDefinition,
) -> tuple[str, ...]:
    if definition.adapter_id != (
        "raster_inspection"
    ):
        raise SkillPromotionPlanError(
            "adapter has no promotion file policy"
        )

    try:
        rendered = (
            render_raster_inspection_candidate(
                skill_id=definition.skill_id
            )
        )
    except RasterInspectionRendererError as exc:
        raise SkillPromotionPlanError(
            "adapter promotion files could "
            "not be determined"
        ) from exc

    return tuple(sorted(rendered))


def plan_skill_candidate_promotion(
    *,
    definition: DeclarativeSkillDefinition,
    candidate_path: Path,
    candidate_root: Path,
    test_record: SkillCandidateTestRecord,
    project_root: Path,
) -> SkillCandidatePromotionPlan:
    """Plan exact copies and registry change without writing."""

    root = project_root.resolve()

    try:
        registry = load_skill_registry(
            root
        )
        registry_file = skill_registry_path(
            root
        )
        adapter = get_trusted_adapter(
            definition.adapter_id
        )
        assessment = (
            assess_skill_candidate_for_promotion(
                definition=definition,
                candidate_path=candidate_path,
                candidate_root=candidate_root,
                test_record=test_record,
            )
        )
    except (
        SkillCandidatePromotionError,
        SkillRegistryError,
        TrustedAdapterError,
    ) as exc:
        raise SkillPromotionPlanError(
            "promotion inputs could not be verified"
        ) from exc

    if not assessment.ready_for_promotion_review:
        raise SkillPromotionPlanError(
            "candidate is not ready for "
            "promotion review"
        )

    try:
        registry.get_skill(
            definition.skill_id
        )
    except KeyError:
        pass
    else:
        raise SkillPromotionPlanError(
            "skill is already registered"
        )

    candidate = candidate_path.resolve()
    files: list[SkillPromotionFile] = []

    for relative_path in (
        _expected_candidate_files(
            definition
        )
    ):
        source = (
            candidate / relative_path
        ).resolve()

        if candidate not in source.parents:
            raise SkillPromotionPlanError(
                "promotion source escaped candidate"
            )

        if (
            not source.is_file()
            or source.is_symlink()
        ):
            raise SkillPromotionPlanError(
                "promotion source is missing or unsafe"
            )

        destination = (
            root / relative_path
        ).resolve()

        if root not in destination.parents:
            raise SkillPromotionPlanError(
                "promotion destination escaped "
                "the project root"
            )

        if destination.exists():
            raise SkillPromotionPlanError(
                "promotion destination already exists"
            )

        files.append(
            SkillPromotionFile(
                source_path=(
                    source.relative_to(
                        candidate
                    ).as_posix()
                ),
                destination_path=(
                    destination.relative_to(
                        root
                    ).as_posix()
                ),
                sha256=_file_sha256(source),
            )
        )

    try:
        registry_digest = hashlib.sha256(
            registry_file.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise SkillPromotionPlanError(
            "trusted registry could not be hashed"
        ) from exc



    contract = build_skill_contract(
        definition
    )

    registry_entry = SkillDefinition(
        id=definition.skill_id,
        version=definition.version,
        status=SkillStatus.IMPLEMENTED,
        kind=contract.kind,
        access=contract.access,
        approval_required=(
            contract.approval_required
        ),
        validation_required=(
            contract.validation_required
        ),
        entrypoint=adapter.entrypoint,
        verifier=None,
    )

    return SkillCandidatePromotionPlan(
        skill_id=definition.skill_id,
        adapter_id=definition.adapter_id,
        definition_sha256=(
            assessment.definition_sha256
        ),
        candidate_tree_sha256=(
            assessment.candidate_tree_sha256
        ),
        registry_before_sha256=(
            registry_digest
        ),
        candidate_path=candidate.as_posix(),
        project_root=root.as_posix(),
        registry_path=(
            registry_file.as_posix()
        ),
        files=files,
        registry_entry=registry_entry,
        ready_for_promotion=True,
        planning_performed=True,
        files_copied=False,
        registry_modified=False,
        promotion_performed=False,
        execution_performed=False,
    )

