"""Read-only assessment for the fixed pilot demonstration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from geoagent_harness.pilot_demo.schemas import (
    PilotDemoCaseResult,
    PilotDemoDefinition,
    PilotDemoNextAction,
    PilotDemoReadiness,
)
from geoagent_harness.spatial_contracts import (
    assess_spatial_data_contract,
    load_spatial_data_contract,
    spatial_data_contract_sha256,
)


MAX_DEMO_DEFINITION_BYTES = 100_000
MAX_BENCHMARK_MANIFEST_BYTES = 250_000


class PilotDemoError(RuntimeError):
    """Raised when the demonstration definition is unsafe or invalid."""


def _safe_file(path: Path, *, project_root: Path, maximum: int) -> Path:
    if project_root.is_symlink():
        raise PilotDemoError("project root cannot be a symlink")
    try:
        root = project_root.resolve(strict=True)
    except OSError as exc:
        raise PilotDemoError("project root is unavailable") from exc
    candidate = path if path.is_absolute() else root / path
    if candidate.is_symlink():
        raise PilotDemoError("demonstration input cannot be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise PilotDemoError("demonstration input is unavailable") from exc
    if not resolved.is_file() or not resolved.is_relative_to(root):
        raise PilotDemoError("demonstration input escaped the project root")
    size = resolved.stat().st_size
    if size < 1 or size > maximum:
        raise PilotDemoError("demonstration input has an invalid size")
    return resolved


def _load_json(path: Path, *, project_root: Path, maximum: int) -> tuple[dict[str, Any], str]:
    safe = _safe_file(path, project_root=project_root, maximum=maximum)
    raw = safe.read_bytes()
    try:
        value: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PilotDemoError("demonstration JSON is invalid") from exc
    if not isinstance(value, dict):
        raise PilotDemoError("demonstration JSON must contain one object")
    return value, hashlib.sha256(raw).hexdigest()


def load_pilot_demo_definition(
    definition_file: Path,
    *,
    project_root: Path,
) -> tuple[PilotDemoDefinition, str]:
    """Securely load one bounded demonstration definition."""

    payload, digest = _load_json(
        definition_file,
        project_root=project_root,
        maximum=MAX_DEMO_DEFINITION_BYTES,
    )
    try:
        return PilotDemoDefinition.model_validate(payload), digest
    except ValidationError as exc:
        raise PilotDemoError("demonstration definition failed schema validation") from exc


def assess_pilot_demo_readiness(
    definition_file: Path,
    *,
    project_root: Path,
) -> PilotDemoReadiness:
    """Verify the fixed dirty/corrected story without taking action."""

    definition, definition_sha256 = load_pilot_demo_definition(
        definition_file,
        project_root=project_root,
    )
    benchmark, benchmark_sha256 = _load_json(
        Path(definition.benchmark_manifest),
        project_root=project_root,
        maximum=MAX_BENCHMARK_MANIFEST_BYTES,
    )
    manifest_cases = {
        item.get("id"): item
        for item in benchmark.get("cases", [])
        if isinstance(item, dict)
    }
    root = project_root.resolve(strict=True)
    contract_path = root / definition.contract_file
    contract_root = contract_path.parent
    data_root = root / definition.data_root
    contract = load_spatial_data_contract(
        contract_path,
        contract_root=contract_root,
    )
    workflow_dataset = _safe_file(
        Path(definition.workflow_dataset),
        project_root=project_root,
        maximum=250_000_000,
    )
    workflow_dataset_sha256 = hashlib.sha256(
        workflow_dataset.read_bytes()
    ).hexdigest()
    case_results: list[PilotDemoCaseResult] = []
    violations: list[str] = []

    for case in (definition.dirty_case, definition.corrected_case):
        manifest_case = manifest_cases.get(case.case_id)
        expected_manifest = {
            "dataset": case.dataset,
            "expected_failed_checks": case.expected_failed_checks,
        }
        if not manifest_case or any(
            manifest_case.get(key) != value
            for key, value in expected_manifest.items()
        ):
            violations.append(
                f"benchmark case {case.case_id} does not match the demo definition"
            )
        assessment = assess_spatial_data_contract(
            path=data_root / case.dataset,
            contract=contract,
            input_root=data_root,
        )
        observed = sorted(
            check.check_id for check in assessment.checks if not check.passed
        )
        expected = sorted(case.expected_failed_checks)
        matched = observed == expected and assessment.dataset_unchanged
        if not matched:
            violations.append(
                f"benchmark case {case.case_id} did not produce its expected result"
            )
        case_results.append(
            PilotDemoCaseResult(
                case_id=case.case_id,
                dataset=case.dataset,
                expected_failed_checks=expected,
                observed_failed_checks=observed,
                expectation_matched=matched,
                dataset_unchanged=assessment.dataset_unchanged,
            )
        )

    ready = not violations
    return PilotDemoReadiness(
        demo_id=definition.demo_id,
        definition_sha256=definition_sha256,
        benchmark_sha256=benchmark_sha256,
        contract_sha256=spatial_data_contract_sha256(contract),
        workflow_dataset=definition.workflow_dataset,
        workflow_dataset_sha256=workflow_dataset_sha256,
        cases=case_results,
        repository_ready=ready,
        next_action=(
            PilotDemoNextAction.PROPOSE_WORKFLOW
            if ready
            else PilotDemoNextAction.FIX_REPOSITORY
        ),
        violations=violations,
    )
