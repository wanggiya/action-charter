"""Build concise context from fixed, trusted project files."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from geoagent_harness.context_pack.redaction import (
    redact_text,
    redact_value,
)
from geoagent_harness.context_pack.schemas import (
    ContextReference,
    DatasetContext,
    DecisionContext,
    SkillContext,
    TaskContextPack,
)

from geoagent_harness.skill_registry import (
    SkillRegistryError,
    parse_skill_registry,
)

CONTEXT_FILES = (
    "context/PROJECT_SUMMARY.md",
    "context/ARCHITECTURE.md",
    "context/CURRENT_STATUS.md",
    "context/DATASET_CATALOG.json",
    "context/SKILLS_INDEX.yaml",
    "context/DECISIONS.jsonl",
)

MAX_FILE_BYTES = 128_000
MAX_DECISIONS = 8
MAX_CURRENT_STATUS_CHARACTERS = 16_000

CURRENT_STATUS_TRUNCATION_MARKER = (
    "\n\n[... context/CURRENT_STATUS.md truncated for model context ...]\n\n"
)

SECURITY_DECISIONS = {
    "D-001",
    "D-002",
    "D-003",
    "D-007",
    "D-008",
}


class ContextPackError(RuntimeError):
    """Raised when trusted context cannot be loaded safely."""


def _bound_current_status(value: str) -> tuple[str, bool]:
    """Preserve the overview and latest status within a fixed bound."""

    if len(value) <= MAX_CURRENT_STATUS_CHARACTERS:
        return value, False

    available = (
        MAX_CURRENT_STATUS_CHARACTERS
        - len(CURRENT_STATUS_TRUNCATION_MARKER)
    )
    head_size = available // 2
    tail_size = available - head_size
    return (
        value[:head_size]
        + CURRENT_STATUS_TRUNCATION_MARKER
        + value[-tail_size:],
        True,
    )


def _read_trusted_file(
    project_root: Path,
    relative_path: str,
) -> tuple[str, ContextReference]:
    root = project_root.resolve()
    path = (root / relative_path).resolve()

    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ContextPackError(
            "context path escaped the project root"
        ) from exc

    if not path.is_file():
        raise ContextPackError(
            f"required context file is unavailable: {relative_path}"
        )

    if path.stat().st_size > MAX_FILE_BYTES:
        raise ContextPackError(
            f"context file exceeds size limit: {relative_path}"
        )

    content = path.read_text(encoding="utf-8")

    reference = ContextReference(
        path=relative_path,
        sha256=hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
    )

    return content, reference


def _tokens(value: str) -> set[str]:
    """Split prose and snake_case identifiers into comparable tokens."""

    return {
        token
        for token in re.findall(
            r"[a-z0-9]+",
            value.lower(),
        )
        if len(token) >= 3
    }


def _is_relevant(
    request_tokens: set[str],
    *values: str,
) -> bool:
    candidate_tokens = _tokens(" ".join(values))
    return bool(request_tokens & candidate_tokens)


def _load_datasets(
    content: str,
    request_tokens: set[str],
) -> list[DatasetContext]:
    payload = json.loads(content)
    raw_datasets = payload.get("datasets", [])

    selected: list[DatasetContext] = []

    for raw in raw_datasets:
        redacted = redact_value(raw)
        dataset = DatasetContext.model_validate(redacted)

        if _is_relevant(
            request_tokens,
            dataset.id,
            dataset.path,
            dataset.format,
            dataset.purpose,
        ):
            selected.append(dataset)

    if not selected and len(raw_datasets) == 1:
        selected.append(
            DatasetContext.model_validate(
                redact_value(raw_datasets[0])
            )
        )

    return selected


def _load_skills(
    content: str,
    request_tokens: set[str],
) -> list[SkillContext]:
    try:
        registry = parse_skill_registry(content)
    except SkillRegistryError as exc:
        raise ContextPackError(
            "trusted skill registry is invalid"
        ) from exc

    implemented = [
        SkillContext.model_validate(
            redact_value(
                skill.model_dump(mode="json")
            )
        )
        for skill in registry.implemented_skills()
    ]

    relevant = [
        skill
        for skill in implemented
        if _is_relevant(
            request_tokens,
            skill.id,
            skill.entrypoint or "",
        )
    ]

    # The implemented list is currently small. Supplying it all allows
    # the planner to assemble prerequisite workflow steps.
    return relevant or implemented


def _load_decisions(
    content: str,
    request_tokens: set[str],
) -> list[DecisionContext]:
    selected: list[DecisionContext] = []

    for line_number, line in enumerate(
        content.splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            raw: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContextPackError(
                "invalid decision JSON on line "
                f"{line_number}"
            ) from exc

        if raw.get("status") != "accepted":
            continue

        decision = DecisionContext.model_validate(
            {
                "id": raw["id"],
                "decision": redact_text(
                    str(raw["decision"])
                ),
                "status": raw["status"],
            }
        )

        if (
            decision.id in SECURITY_DECISIONS
            or _is_relevant(
                request_tokens,
                decision.decision,
            )
        ):
            selected.append(decision)

    return selected[-MAX_DECISIONS:]


def build_context_pack(
    original_request: str,
    project_root: Path = Path("."),
) -> TaskContextPack:
    """Build one bounded context pack from fixed context files."""

    clean_request = redact_text(original_request).strip()

    if not clean_request:
        raise ContextPackError(
            "original request cannot be empty"
        )

    if len(clean_request) > 8000:
        raise ContextPackError(
            "original request exceeds 8000 characters"
        )

    contents: dict[str, str] = {}
    references: list[ContextReference] = []

    for relative_path in CONTEXT_FILES:
        content, reference = _read_trusted_file(
            project_root,
            relative_path,
        )
        contents[relative_path] = content
        references.append(reference)

    request_tokens = _tokens(clean_request)

    current_status, status_truncated = _bound_current_status(
        redact_text(contents["context/CURRENT_STATUS.md"])
    )
    warnings: list[str] = []
    if status_truncated:
        warnings.append(
            "context/CURRENT_STATUS.md was truncated to "
            f"{MAX_CURRENT_STATUS_CHARACTERS} characters for model context"
        )

    return TaskContextPack(
        original_request=clean_request,
        project_summary=redact_text(
            contents["context/PROJECT_SUMMARY.md"]
        ),
        architecture=redact_text(
            contents["context/ARCHITECTURE.md"]
        ),
        current_status=current_status,
        datasets=_load_datasets(
            contents["context/DATASET_CATALOG.json"],
            request_tokens,
        ),
        available_skills=_load_skills(
            contents["context/SKILLS_INDEX.yaml"],
            request_tokens,
        ),
        decisions=_load_decisions(
            contents["context/DECISIONS.jsonl"],
            request_tokens,
        ),
        context_references=references,
        warnings=warnings,
    )
