"""Deterministic contract checks for skill scaffold bundles."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import yaml

from geoagent_harness.skill_registry import (
    SkillDefinition,
    SkillStatus,
)
from geoagent_harness.skill_scaffolding.schemas import (
    SkillScaffoldContractResult,
)


MAX_SCAFFOLD_FILE_BYTES = 250_000

_PROHIBITED_IMPORTS = {
    "subprocess",
}

_PROHIBITED_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "os.system",
    "os.popen",
}


class SkillScaffoldContractError(RuntimeError):
    """Raised when a scaffold cannot be safely inspected."""


def _bundle_path(
    scaffold_path: Path,
) -> Path:
    bundle = scaffold_path.resolve()

    if not bundle.is_dir():
        raise SkillScaffoldContractError(
            "skill scaffold bundle does not exist"
        )

    if bundle.is_symlink():
        raise SkillScaffoldContractError(
            "skill scaffold bundle cannot be a symlink"
        )

    return bundle


def _contained_file(
    bundle: Path,
    relative_path: str,
) -> Path:
    candidate = (
        bundle
        / relative_path
    ).resolve()

    if bundle not in candidate.parents:
        raise SkillScaffoldContractError(
            "scaffold file path escaped its bundle"
        )

    if candidate.is_symlink():
        raise SkillScaffoldContractError(
            "scaffold files cannot be symlinks"
        )

    return candidate


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
        raise SkillScaffoldContractError(
            f"{path.name} is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillScaffoldContractError(
            f"{path.name} must contain an object"
        )

    return payload


def _load_yaml_object(
    path: Path,
) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(
            path.read_text(encoding="utf-8")
        )
    except (
        OSError,
        UnicodeDecodeError,
        yaml.YAMLError,
    ) as exc:
        raise SkillScaffoldContractError(
            f"{path.name} is not valid YAML"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillScaffoldContractError(
            f"{path.name} must contain an object"
        )

    return payload


def _call_name(
    node: ast.Call,
) -> str | None:
    function = node.func

    if isinstance(function, ast.Name):
        return function.id

    if (
        isinstance(function, ast.Attribute)
        and isinstance(function.value, ast.Name)
    ):
        return (
            f"{function.value.id}."
            f"{function.attr}"
        )

    return None


def _python_violations(
    path: Path,
) -> list[str]:
    try:
        source = path.read_text(
            encoding="utf-8"
        )
    except (
        OSError,
        UnicodeDecodeError,
    ) as exc:
        raise SkillScaffoldContractError(
            f"{path.name} could not be read"
        ) from exc

    try:
        tree = ast.parse(
            source,
            filename=path.as_posix(),
        )
    except SyntaxError:
        return [
            f"{path.name}: invalid Python syntax"
        ]

    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(
                    ".",
                    maxsplit=1,
                )[0]

                if root_name in _PROHIBITED_IMPORTS:
                    violations.append(
                        f"{path.name}: prohibited import "
                        f"{root_name}"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_name = node.module.split(
                    ".",
                    maxsplit=1,
                )[0]

                if root_name in _PROHIBITED_IMPORTS:
                    violations.append(
                        f"{path.name}: prohibited import "
                        f"{root_name}"
                    )

        elif isinstance(node, ast.Call):
            name = _call_name(node)

            if name in _PROHIBITED_CALLS:
                violations.append(
                    f"{path.name}: prohibited call {name}"
                )

            for keyword in node.keywords:
                if (
                    keyword.arg == "shell"
                    and isinstance(
                        keyword.value,
                        ast.Constant,
                    )
                    and keyword.value.value is True
                ):
                    violations.append(
                        f"{path.name}: shell=True is prohibited"
                    )

    return violations


def validate_skill_scaffold_contract(
    scaffold_path: Path,
) -> SkillScaffoldContractResult:
    """Validate one generated bundle without importing it."""

    bundle = _bundle_path(scaffold_path)

    manifest_path = _contained_file(
        bundle,
        "scaffold-manifest.json",
    )
    registry_path = _contained_file(
        bundle,
        "registry-fragment.yaml",
    )

    if not manifest_path.is_file():
        raise SkillScaffoldContractError(
            "scaffold manifest does not exist"
        )

    if not registry_path.is_file():
        raise SkillScaffoldContractError(
            "registry fragment does not exist"
        )

    manifest = _load_json_object(
        manifest_path
    )
    registry_payload = _load_yaml_object(
        registry_path
    )

    skill_id = manifest.get("skill_id")

    if not isinstance(skill_id, str):
        raise SkillScaffoldContractError(
            "scaffold manifest has no valid skill ID"
        )

    violations: list[str] = []
    checked_files: list[str] = []

    generated_files = manifest.get(
        "generated_files"
    )

    if not isinstance(generated_files, list):
        raise SkillScaffoldContractError(
            "manifest generated_files must be a list"
        )

    if len(generated_files) != len(
        set(generated_files)
    ):
        violations.append(
            "manifest contains duplicate generated files"
        )

    required_metadata = {
        "registry-fragment.yaml",
    }

    if not required_metadata.issubset(
        set(generated_files)
    ):
        violations.append(
            "manifest omits required scaffold metadata"
        )

    for relative_path in generated_files:
        if not isinstance(relative_path, str):
            violations.append(
                "manifest contains a non-string file path"
            )
            continue

        try:
            path = _contained_file(
                bundle,
                relative_path,
            )
        except SkillScaffoldContractError as exc:
            violations.append(str(exc))
            continue

        if not path.is_file():
            violations.append(
                f"generated file is missing: "
                f"{relative_path}"
            )
            continue

        try:
            size = path.stat().st_size
        except OSError:
            violations.append(
                f"generated file cannot be inspected: "
                f"{relative_path}"
            )
            continue

        if size > MAX_SCAFFOLD_FILE_BYTES:
            violations.append(
                f"generated file exceeds size limit: "
                f"{relative_path}"
            )
            continue

        checked_files.append(relative_path)

        if path.suffix == ".py":
            violations.extend(
                _python_violations(path)
            )

    try:
        registry_entry = (
            SkillDefinition.model_validate(
                registry_payload.get("skill")
            )
        )
    except (TypeError, ValueError):
        violations.append(
            "registry fragment failed schema validation"
        )
    else:
        if registry_entry.id != skill_id:
            violations.append(
                "registry skill ID conflicts with manifest"
            )

        if (
            registry_entry.status
            != SkillStatus.PLANNED
        ):
            violations.append(
                "generated registry entry must remain planned"
            )

        if registry_entry.entrypoint is not None:
            violations.append(
                "planned registry entry cannot expose an entrypoint"
            )

        if registry_entry.verifier is not None:
            violations.append(
                "planned registry entry cannot expose a verifier"
            )

    for field in (
        "registry_modified",
        "implementation_trusted",
        "promotion_performed",
        "execution_performed",
    ):
        if manifest.get(field) is not False:
            violations.append(
                f"manifest must record {field}=false"
            )

    return SkillScaffoldContractResult(
        skill_id=skill_id,
        scaffold_path=bundle.as_posix(),
        passed=not violations,
        checked_files=checked_files,
        violations=list(
            dict.fromkeys(violations)
        ),
        warnings=[
            (
                "Passing scaffold contracts does not make "
                "the generated implementation trusted."
            )
        ],
    )

