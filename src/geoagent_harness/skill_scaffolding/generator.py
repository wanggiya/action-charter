"""Safe deterministic generation of skill scaffold bundles."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from geoagent_harness.skill_scaffolding.schemas import (
    SkillScaffoldGenerationResult,
    SkillScaffoldPlan,
)


class SkillScaffoldGenerationError(RuntimeError):
    """Raised when a scaffold cannot be safely generated."""


def _contained_path(
    root: Path,
    relative_path: str,
) -> Path:
    """Resolve one path and require containment in root."""

    resolved_root = root.resolve()
    candidate = (
        resolved_root
        / relative_path
    ).resolve()

    if (
        candidate == resolved_root
        or resolved_root not in candidate.parents
    ):
        raise SkillScaffoldGenerationError(
            "scaffold path escaped its approved root"
        )

    return candidate


def _module_docstring(
    *,
    skill_id: str,
    module_name: str,
) -> str:
    return (
        f'"""Generated {module_name} skeleton for '
        f'{skill_id}.\n\n'
        "This scaffold is not trusted or implemented.\n"
        '"""\n'
    )


def _render_source_file(
    *,
    skill_id: str,
    relative_path: str,
) -> str:
    filename = Path(relative_path).name

    if filename == "__init__.py":
        return (
            _module_docstring(
                skill_id=skill_id,
                module_name="package",
            )
            + "\n"
            + "__all__: list[str] = []\n"
        )

    if filename == "schemas.py":
        return (
            _module_docstring(
                skill_id=skill_id,
                module_name="schema",
            )
            + "\n"
            + "from __future__ import annotations\n\n"
            + "from typing import Literal\n\n"
            + "from pydantic import BaseModel, ConfigDict\n\n\n"
            + "class SkillResult(BaseModel):\n"
            + '    """Placeholder typed skill result."""\n\n'
            + '    model_config = ConfigDict(extra="forbid")\n\n'
            + '    schema_version: Literal["1.0"] = "1.0"\n'
            + '    status: Literal["not_implemented"] = (\n'
            + '        "not_implemented"\n'
            + "    )\n"
        )

    if filename == "policy.py":
        return (
            _module_docstring(
                skill_id=skill_id,
                module_name="policy",
            )
            + "\n"
            + "from __future__ import annotations\n\n\n"
            + "class SkillPolicyError(ValueError):\n"
            + '    """Raised when skill policy rejects a request."""\n'
        )

    if filename == "service.py":
        return (
            _module_docstring(
                skill_id=skill_id,
                module_name="service",
            )
            + "\n"
            + "from __future__ import annotations\n\n\n"
            + "class SkillNotImplementedError(RuntimeError):\n"
            + '    """Raised because this scaffold is not implemented."""\n\n\n'
            + "def execute_skill() -> None:\n"
            + '    """Refuse execution until implementation review."""\n\n'
            + "    raise SkillNotImplementedError(\n"
            + '        "generated skill scaffold is not implemented"\n'
            + "    )\n"
        )

    if filename == "validation.py":
        return (
            _module_docstring(
                skill_id=skill_id,
                module_name="validation",
            )
            + "\n"
            + "from __future__ import annotations\n\n\n"
            + "class SkillValidationNotImplementedError(\n"
            + "    RuntimeError\n"
            + "):\n"
            + '    """Raised until deterministic validation exists."""\n\n\n'
            + "def validate_skill_result() -> None:\n"
            + '    """Refuse validation until implemented."""\n\n'
            + "    raise SkillValidationNotImplementedError(\n"
            + '        "generated skill validation is not implemented"\n'
            + "    )\n"
        )

    raise SkillScaffoldGenerationError(
        f"unsupported scaffold source file: {filename}"
    )


def _render_test_file(
    *,
    skill_id: str,
    relative_path: str,
) -> str:
    filename = Path(relative_path).name

    return (
        f'"""Generated contract placeholder for {skill_id}."""\n\n'
        "import pytest\n\n\n"
        f"def test_{skill_id}_remains_unimplemented() -> None:\n"
        '    pytest.skip(\n'
        f'        "{filename} requires operator implementation"\n'
        "    )\n"
    )


def _write_new_text(
    path: Path,
    content: str,
) -> None:
    """Write a new UTF-8 file without overwriting."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise SkillScaffoldGenerationError(
            f"scaffold file already exists: {path.name}"
        ) from exc


def generate_skill_scaffold(
    plan: SkillScaffoldPlan,
    *,
    scaffold_root: Path = Path(
        "skill-scaffolds"
    ),
) -> SkillScaffoldGenerationResult:
    """Generate an isolated, untrusted scaffold bundle."""

    root = scaffold_root.resolve()

    bundle = _contained_path(
        root,
        plan.skill_id,
    )

    if bundle.exists():
        raise SkillScaffoldGenerationError(
            "skill scaffold bundle already exists"
        )

    generated_files: list[str] = []

    try:
        for relative_path in plan.files:
            target = _contained_path(
                bundle,
                relative_path,
            )

            _write_new_text(
                target,
                _render_source_file(
                    skill_id=plan.skill_id,
                    relative_path=relative_path,
                ),
            )

            generated_files.append(
                target.relative_to(
                    bundle
                ).as_posix()
            )

        for relative_path in plan.test_files:
            target = _contained_path(
                bundle,
                relative_path,
            )

            _write_new_text(
                target,
                _render_test_file(
                    skill_id=plan.skill_id,
                    relative_path=relative_path,
                ),
            )

            generated_files.append(
                target.relative_to(
                    bundle
                ).as_posix()
            )

        registry_fragment = _contained_path(
            bundle,
            "registry-fragment.yaml",
        )

        registry_payload = {
            "skill": (
                plan.registry_entry.model_dump(
                    mode="json",
                    exclude_none=True,
                )
            )
        }

        _write_new_text(
            registry_fragment,
            yaml.safe_dump(
                registry_payload,
                sort_keys=False,
            ),
        )

        generated_files.append(
            "registry-fragment.yaml"
        )

        manifest = _contained_path(
            bundle,
            "scaffold-manifest.json",
        )

        manifest_payload = {
            "schema_version": "1.0",
            "skill_id": plan.skill_id,
            "summary": plan.summary,
            "kind": plan.kind.value,
            "access": plan.access.value,
            "approval_required": (
                plan.approval_required
            ),
            "validation_required": (
                plan.validation_required
            ),
            "generated_files": (
                generated_files
            ),
            "registry_modified": False,
            "implementation_trusted": False,
            "promotion_performed": False,
            "execution_performed": False,
        }

        _write_new_text(
            manifest,
            json.dumps(
                manifest_payload,
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )

        generated_files.append(
            "scaffold-manifest.json"
        )

    except (
        OSError,
        SkillScaffoldGenerationError,
    ) as exc:
        raise SkillScaffoldGenerationError(
            "skill scaffold generation failed"
        ) from exc

    return SkillScaffoldGenerationResult(
        skill_id=plan.skill_id,
        scaffold_path=bundle.as_posix(),
        generated_files=generated_files,
        registry_fragment_path=(
            registry_fragment.relative_to(
                bundle
            ).as_posix()
        ),
        manifest_path=(
            manifest.relative_to(
                bundle
            ).as_posix()
        ),
    )

