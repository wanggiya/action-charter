"""Immutable generation of declarative skill contracts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from geoagent_harness.skill_definitions.policy import (
    assess_declarative_skill,
)
from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
    SkillContractBundle,
    SkillContractGenerationResult,
    SkillProfile,
)


class SkillContractGenerationError(RuntimeError):
    """Raised when a contract bundle cannot be generated."""


_COMMON_CHECKS = (
    "definition_schema_validated",
    "result_schema_validated",
    "reject_path_escape",
    "reject_symlink_escape",
    "reject_unknown_arguments",
)


_PROFILE_CHECKS: dict[
    SkillProfile,
    tuple[str, ...],
] = {
    SkillProfile.READ_ONLY_INSPECTION: (
        *_COMMON_CHECKS,
        "fixture_exists",
        "fixture_is_readable",
        "filesystem_unchanged",
        "database_unchanged",
    ),
    SkillProfile.ARTIFACT_TRANSFORMATION: (
        *_COMMON_CHECKS,
        "approval_required",
        "output_beneath_approved_root",
        "overwrite_rejected",
        "deterministic_validation_required",
        "success_withheld_before_validation",
    ),
    SkillProfile.DATABASE_WRITE: (
        *_COMMON_CHECKS,
        "approval_required",
        "schema_allowlist_enforced",
        "unrestricted_sql_rejected",
        "deterministic_validation_required",
        "uncertain_write_requires_manual_review",
    ),
    SkillProfile.READ_ONLY_VALIDATION: (
        *_COMMON_CHECKS,
        "fixture_exists",
        "filesystem_unchanged",
        "database_unchanged",
        "unsupported_success_claim_rejected",
    ),
    SkillProfile.EVIDENCE_REPORTING: (
        *_COMMON_CHECKS,
        "output_beneath_evidence_root",
        "secret_redaction_required",
        "source_artifacts_unchanged",
        "database_unchanged",
    ),
}


def canonical_skill_definition_json(
    definition: DeclarativeSkillDefinition,
) -> str:
    """Return canonical JSON for one definition."""

    return json.dumps(
        definition.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def skill_definition_sha256(
    definition: DeclarativeSkillDefinition,
) -> str:
    """Return the canonical definition digest."""

    return hashlib.sha256(
        canonical_skill_definition_json(
            definition
        ).encode("utf-8")
    ).hexdigest()


def build_skill_contract(
    definition: DeclarativeSkillDefinition,
) -> SkillContractBundle:
    """Build one contract without writing files."""

    assessment = assess_declarative_skill(
        definition
    )

    if not assessment.ready_for_generation:
        raise SkillContractGenerationError(
            "skill definition is not ready for "
            "contract generation"
        )

    return SkillContractBundle(
        skill_id=definition.skill_id,
        definition_sha256=(
            skill_definition_sha256(definition)
        ),
        profile=definition.profile,
        kind=assessment.kind,
        access=assessment.access,
        approval_required=(
            assessment.approval_required
        ),
        validation_required=(
            assessment.validation_required
        ),
        verifier_required=(
            assessment.verifier_required
        ),
        required_checks=list(
            _PROFILE_CHECKS[definition.profile]
        ),
        implementation_trusted=False,
        promotion_performed=False,
        execution_performed=False,
    )


def generate_skill_contract_bundle(
    definition: DeclarativeSkillDefinition,
    *,
    contract_root: Path,
) -> SkillContractGenerationResult:
    """Generate one immutable isolated contract bundle."""

    contract = build_skill_contract(
        definition
    )

    root = contract_root.resolve()
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    digest = contract.definition_sha256

    bundle = (
        root
        / (
            f"{definition.skill_id}."
            f"{digest}.contract"
        )
    )

    if bundle.exists():
        raise SkillContractGenerationError(
            "skill contract bundle already exists"
        )

    temporary = Path(
        tempfile.mkdtemp(
            prefix=".geoagent-contract-",
            dir=root,
        )
    )

    definition_path = (
        temporary / "skill-definition.json"
    )
    contract_path = temporary / "contract.json"

    try:
        definition_path.write_text(
            (
                canonical_skill_definition_json(
                    definition
                )
                + "\n"
            ),
            encoding="utf-8",
        )

        contract_path.write_text(
            (
                json.dumps(
                    contract.model_dump(
                        mode="json"
                    ),
                    sort_keys=True,
                    indent=2,
                )
                + "\n"
            ),
            encoding="utf-8",
        )

        os.replace(
            temporary,
            bundle,
        )
    except OSError as exc:
        if temporary.exists():
            shutil.rmtree(
                temporary,
                ignore_errors=True,
            )

        raise SkillContractGenerationError(
            "skill contract bundle could not "
            "be written"
        ) from exc

    return SkillContractGenerationResult(
        skill_id=definition.skill_id,
        definition_sha256=digest,
        bundle_path=str(bundle),
        definition_path=str(
            bundle / "skill-definition.json"
        ),
        contract_path=str(
            bundle / "contract.json"
        ),
        definition_validated=True,
        assessment_performed=True,
        contract_generated=True,
        implementation_generated=False,
        registry_modified=False,
        implementation_trusted=False,
        promotion_performed=False,
        execution_performed=False,
    )

