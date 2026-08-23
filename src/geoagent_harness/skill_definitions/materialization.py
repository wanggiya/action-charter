"""Safe materialization of trusted adapter candidates."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from geoagent_harness.skill_definitions.adapters import (
    RasterInspectionRendererError,
    render_raster_inspection_candidate,
)
from geoagent_harness.skill_definitions.generation import (
    SkillContractGenerationError,
    build_skill_contract,
)
from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
    TrustedAdapterMaterializationResult,
)
from geoagent_harness.skill_scaffolding import (
    SkillScaffoldContractError,
    SkillScaffoldGenerationResult,
    validate_skill_scaffold_contract,
)


class TrustedAdapterMaterializationError(
    RuntimeError
):
    """Raised when candidate materialization is unsafe."""


def _render_candidate(
    definition: DeclarativeSkillDefinition,
) -> dict[str, str]:
    """Dispatch only to a fixed trusted renderer."""

    if definition.adapter_id == (
        "raster_inspection"
    ):
        try:
            return (
                render_raster_inspection_candidate(
                    skill_id=definition.skill_id
                )
            )
        except RasterInspectionRendererError as exc:
            raise (
                TrustedAdapterMaterializationError(
                    "trusted raster adapter could "
                    "not render the candidate"
                )
            ) from exc

    raise TrustedAdapterMaterializationError(
        "definition does not select a materializable "
        "trusted adapter"
    )


def _candidate_root_path(
    candidate_root: Path,
) -> Path:
    root = candidate_root.resolve()

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return root


def _contained_target(
    bundle: Path,
    relative_path: str,
) -> Path:
    target = (
        bundle / relative_path
    ).resolve()

    if bundle not in target.parents:
        raise TrustedAdapterMaterializationError(
            "materialized file escaped the candidate"
        )

    if target.is_symlink():
        raise TrustedAdapterMaterializationError(
            "materialized file cannot be a symlink"
        )

    return target


def materialize_trusted_adapter_candidate(
    *,
    definition: DeclarativeSkillDefinition,
    scaffold: SkillScaffoldGenerationResult,
    candidate_root: Path,
) -> TrustedAdapterMaterializationResult:
    """Create a new candidate from one validated scaffold."""

    try:
        contract = build_skill_contract(
            definition
        )
    except SkillContractGenerationError as exc:
        raise TrustedAdapterMaterializationError(
            "skill definition is not ready for "
            "adapter materialization"
        ) from exc

    if scaffold.skill_id != definition.skill_id:
        raise TrustedAdapterMaterializationError(
            "scaffold skill ID does not match "
            "the declarative definition"
        )

    source = Path(
        scaffold.scaffold_path
    ).resolve()

    try:
        source_contract = (
            validate_skill_scaffold_contract(
                source
            )
        )
    except SkillScaffoldContractError as exc:
        raise TrustedAdapterMaterializationError(
            "source scaffold failed static validation"
        ) from exc

    if not source_contract.passed:
        raise TrustedAdapterMaterializationError(
            "source scaffold contains contract violations"
        )

    rendered = _render_candidate(
        definition
    )

    expected_python_files = {
        path
        for path in scaffold.generated_files
        if path.endswith(".py")
    }

    if set(rendered) != expected_python_files:
        raise TrustedAdapterMaterializationError(
            "trusted adapter file set does not match "
            "the scaffold plan"
        )

    root = _candidate_root_path(
        candidate_root
    )

    candidate = (
        root
        / (
            f"{definition.skill_id}."
            f"{contract.definition_sha256}."
            "candidate"
        )
    )

    if candidate.exists():
        raise TrustedAdapterMaterializationError(
            "materialized candidate already exists"
        )

    temporary_root = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-candidate-",
            dir=root,
        )
    )
    staged = temporary_root / "candidate"

    try:
        shutil.copytree(
            source,
            staged,
            symlinks=False,
        )

        for relative_path, content in (
            rendered.items()
        ):
            target = _contained_target(
                staged,
                relative_path,
            )

            if not target.is_file():
                raise (
                    TrustedAdapterMaterializationError(
                        "trusted adapter target does "
                        "not exist in the scaffold"
                    )
                )

            original = target.read_text(
                encoding="utf-8"
            )

            if relative_path.startswith("tests/"):
                expected_marker = "pytest.skip"
            else:
                expected_marker = (
                    "not trusted or implemented"
                )

            if expected_marker not in original.lower():
                raise (
                    TrustedAdapterMaterializationError(
                        "scaffold placeholder changed "
                        "before materialization"
                    )
                )

            target.write_text(
                content,
                encoding="utf-8",
                newline="\n",
            )

        candidate_contract = (
            validate_skill_scaffold_contract(
                staged
            )
        )

        if not candidate_contract.passed:
            raise TrustedAdapterMaterializationError(
                "materialized candidate failed "
                "static validation"
            )

        os.replace(
            staged,
            candidate,
        )

        temporary_root.rmdir()
    except (
        OSError,
        SkillScaffoldContractError,
        TrustedAdapterMaterializationError,
    ) as exc:
        shutil.rmtree(
            temporary_root,
            ignore_errors=True,
        )

        if isinstance(
            exc,
            TrustedAdapterMaterializationError,
        ):
            raise

        raise TrustedAdapterMaterializationError(
            "trusted adapter candidate could not "
            "be materialized"
        ) from exc

    return TrustedAdapterMaterializationResult(
        skill_id=definition.skill_id,
        adapter_id=definition.adapter_id,
        definition_sha256=(
            contract.definition_sha256
        ),
        source_scaffold_path=source.as_posix(),
        candidate_path=candidate.as_posix(),
        materialized_files=sorted(rendered),
        candidate_materialized=True,
        static_contract_passed=True,
        source_scaffold_modified=False,
        registry_modified=False,
        implementation_trusted=False,
        promotion_performed=False,
        execution_performed=False,
    )

