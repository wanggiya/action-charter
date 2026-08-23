"""Static validation of generated skill contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.skill_definitions.generation import (
    build_skill_contract,
    canonical_skill_definition_json,
    skill_definition_sha256,
)
from geoagent_harness.skill_definitions.schemas import (
    DeclarativeSkillDefinition,
    SkillContractBundle,
    SkillContractValidationResult,
)


MAX_CONTRACT_FILE_BYTES = 250_000

_EXPECTED_FILES = frozenset(
    {
        "skill-definition.json",
        "contract.json",
    }
)


class SkillContractValidationError(RuntimeError):
    """Raised when a contract bundle is invalid."""


def _read_json_object(
    path: Path,
    *,
    label: str,
) -> dict[str, Any]:
    """Read one bounded UTF-8 JSON object."""

    if not path.is_file():
        raise SkillContractValidationError(
            f"{label} does not exist"
        )

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SkillContractValidationError(
            f"{label} could not be inspected"
        ) from exc

    if size > MAX_CONTRACT_FILE_BYTES:
        raise SkillContractValidationError(
            f"{label} exceeds the size limit"
        )

    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError as exc:
        raise SkillContractValidationError(
            f"{label} is not UTF-8"
        ) from exc
    except OSError as exc:
        raise SkillContractValidationError(
            f"{label} could not be read"
        ) from exc

    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SkillContractValidationError(
            f"{label} is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillContractValidationError(
            f"{label} must contain a JSON object"
        )

    return payload


def _safe_bundle_path(
    bundle_path: Path,
    *,
    contract_root: Path,
) -> Path:
    """Require the bundle beneath its approved root."""

    root = contract_root.resolve()
    resolved = bundle_path.resolve()

    if not resolved.is_relative_to(root):
        raise SkillContractValidationError(
            "skill contract bundle escaped its "
            "approved root"
        )

    if not resolved.is_dir():
        raise SkillContractValidationError(
            "skill contract bundle does not exist"
        )

    if not resolved.name.endswith(".contract"):
        raise SkillContractValidationError(
            "skill contract bundle has an invalid suffix"
        )

    return resolved


def validate_skill_contract_bundle(
    bundle_path: Path,
    *,
    contract_root: Path,
) -> SkillContractValidationResult:
    """Validate a bundle without importing or executing code."""

    bundle = _safe_bundle_path(
        bundle_path,
        contract_root=contract_root,
    )

    try:
        filenames = frozenset(
            child.name
            for child in bundle.iterdir()
        )
    except OSError as exc:
        raise SkillContractValidationError(
            "skill contract bundle could not be inspected"
        ) from exc

    if filenames != _EXPECTED_FILES:
        raise SkillContractValidationError(
            "skill contract bundle contains an "
            "unexpected file set"
        )

    definition_payload = _read_json_object(
        bundle / "skill-definition.json",
        label="skill definition",
    )
    contract_payload = _read_json_object(
        bundle / "contract.json",
        label="skill contract",
    )

    try:
        definition = (
            DeclarativeSkillDefinition
            .model_validate(
                definition_payload
            )
        )
        supplied_contract = (
            SkillContractBundle.model_validate(
                contract_payload
            )
        )
    except ValidationError as exc:
        raise SkillContractValidationError(
            "skill contract bundle failed schema "
            "validation"
        ) from exc

    digest = skill_definition_sha256(
        definition
    )

    expected_name = (
        f"{definition.skill_id}."
        f"{digest}.contract"
    )

    if bundle.name != expected_name:
        raise SkillContractValidationError(
            "skill contract bundle name does not "
            "match its definition"
        )

    definition_text = (
        bundle
        / "skill-definition.json"
    ).read_text(encoding="utf-8")

    expected_definition_text = (
        canonical_skill_definition_json(
            definition
        )
        + "\n"
    )

    if definition_text != expected_definition_text:
        raise SkillContractValidationError(
            "skill definition is not canonical"
        )

    expected_contract = build_skill_contract(
        definition
    )

    if supplied_contract != expected_contract:
        raise SkillContractValidationError(
            "skill contract does not match the "
            "trusted profile policy"
        )

    return SkillContractValidationResult(
        skill_id=definition.skill_id,
        definition_sha256=digest,
        bundle_path=str(bundle),
        passed=True,
        checks=[
            "approved_root",
            "exact_file_set",
            "definition_schema",
            "contract_schema",
            "canonical_definition",
            "definition_digest",
            "canonical_bundle_name",
            "trusted_profile_policy",
        ],
        files_modified=False,
        implementation_imported=False,
        implementation_executed=False,
        registry_modified=False,
        promotion_performed=False,
        execution_performed=False,
    )

