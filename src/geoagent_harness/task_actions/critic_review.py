"""Existing critic review coordination, independent of HTTP."""
from __future__ import annotations
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
from geoagent_harness.platform.workspace import WorkspaceLayout, runtime_reference, runtime_reference_path
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from geoagent_harness.contracts.redaction import redact_text, redact_value
from geoagent_harness.platform.evidence import CriticEvidenceError, MAX_TRACE_BYTES, MAX_REPORT_BYTES, build_critic_evidence
from geoagent_harness.agents.roles.critic.recipe_trace import RecipeTraceAdapterError, build_recipe_trace_candidate, persist_recipe_trace_candidate, recipe_trace_sha256, render_recipe_trace_report
from geoagent_harness.agents.roles.critic import critique_task
from geoagent_harness.platform.storage.critic_records import CriticResultRecordError, build_critic_result_record, critic_result_sha256
from geoagent_harness.platform.storage.critic_record_storage import CriticResultStorageError, load_critic_result_record, persist_critic_result_record
from geoagent_harness.core.ledger.trace import WorkflowTrace
from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError, create_recipe_approval, load_recipe_approval, verify_recipe_approval
from geoagent_harness.capabilities.recipes.execution import RecipeEvidenceStorageError, load_recipe_evidence, load_recipe_run_result, recipe_evidence_sha256, recipe_run_result_sha256
from geoagent_harness.capabilities.recipes.execution import RecipePolicyError, validate_recipe_policy
from geoagent_harness.capabilities.recipes.execution import RecipeStorageError, load_recipe, recipe_path, save_recipe
from geoagent_harness.core.ledger.releases import AuthoritativeReleaseStorageError, load_authoritative_release, persist_authoritative_release
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.contracts.interface_requests import (
    InterfaceCriticRecordRequest,
    InterfaceCriticRunRequest,
    InterfaceRecipeTraceSaveRequest,
)
from geoagent_harness.contracts.interface_limits import (
    MAX_INTERFACE_CRITIC_EVIDENCE,
    MAX_INTERFACE_EXECUTION_ATTEMPTS,
    MAX_INTERFACE_OUTCOME_BYTES,
)


def interface_critic_evidence_inventory(project_root: Path) -> dict[str, Any]:
    """Inspect trace/report pairs through the existing deterministic Critic boundary."""

    root = _trusted_root(project_root)
    trace_root = runtime_store_path(root, "traces")
    report_root = runtime_store_path(root, "reports")
    items: list[dict[str, Any]] = []
    truncated = False

    if trace_root.exists() and trace_root.is_symlink():
        raise InterfaceApiError("trace root cannot be a symlink")
    if report_root.exists() and report_root.is_symlink():
        raise InterfaceApiError("report root cannot be a symlink")

    critic_root = runtime_store_path(root, "critic-results")
    if critic_root.is_symlink() or (critic_root.exists() and not critic_root.is_dir()):
        raise InterfaceApiError("Critic-result root is unsafe")
    critic_paths = sorted(critic_root.glob("*.critic-result/CRITIC_RESULT.json"), key=lambda path: path.lstat().st_mtime, reverse=True) if critic_root.is_dir() else []
    if len(critic_paths) > MAX_INTERFACE_CRITIC_EVIDENCE:
        critic_paths = critic_paths[:MAX_INTERFACE_CRITIC_EVIDENCE]
        truncated = True
    critic_records = []
    for path in critic_paths:
        try:
            critic_records.append((path, load_critic_result_record(path, record_root=critic_root)))
        except CriticResultStorageError:
            continue
    release_root = runtime_store_path(root, "releases")
    if release_root.is_symlink() or (release_root.exists() and not release_root.is_dir()):
        raise InterfaceApiError("release root is unsafe")
    release_paths = sorted(release_root.glob("*.release/RELEASE.json"), key=lambda path: path.lstat().st_mtime, reverse=True) if release_root.is_dir() else []
    if len(release_paths) > 25:
        release_paths = release_paths[:25]
        truncated = True
    releases = []
    for path in release_paths:
        try:
            releases.append((path, load_authoritative_release(path, release_root=release_root)))
        except AuthoritativeReleaseStorageError:
            continue

    trace_paths = sorted(trace_root.glob("*.json"), key=lambda path: path.lstat().st_mtime, reverse=True) if trace_root.is_dir() else []
    if len(trace_paths) > MAX_INTERFACE_CRITIC_EVIDENCE:
        trace_paths = trace_paths[:MAX_INTERFACE_CRITIC_EVIDENCE]
        truncated = True

    for trace_path in trace_paths:
        if trace_path.is_symlink() or not trace_path.is_file():
            continue
        report_path = report_root / f"{trace_path.stem}.md"
        if report_path.is_symlink() or not report_path.is_file():
            items.append({
                "trace_name": trace_path.name,
                "report_name": None,
                "available": False,
                "finding": "matching Markdown report is unavailable",
                "evidence": None,
            })
            continue
        try:
            pack = build_critic_evidence(
                trace_path=trace_path,
                report_path=report_path,
                trace_root=trace_root,
                report_root=report_root,
            )
        except (CriticEvidenceError, OSError, ValueError):
            items.append({
                "trace_name": trace_path.name,
                "report_name": report_path.name,
                "available": False,
                "finding": "trace and report did not pass deterministic Critic evidence checks",
                "evidence": None,
            })
            continue
        matching_records = [runtime_reference(root,path) for path, record in critic_records
                            if record.task_id == pack.task_id
                            and record.deterministic_status == pack.deterministic_status
                            and record.critic_result.evidence_references == pack.evidence_references
                            and record.critic_result.evidence_gaps == pack.evidence_gaps
                            and record.critic_result.workflow_warnings == pack.warnings
                            and record.critic_result.human_corrections == pack.human_corrections]
        references = {reference.path: reference.sha256 for reference in pack.evidence_references}
        release_links = []
        for record_path in matching_records:
            record_digest = hashlib.sha256(runtime_reference_path(root,record_path).read_bytes()).hexdigest()
            required = {**references, record_path: record_digest}
            for release_path, manifest in releases:
                components = {part.path: part.sha256 for part in manifest.components}
                if all(components.get(path) == digest for path, digest in required.items()):
                    release_links.append(runtime_reference(root,release_path))
        release_links = sorted(set(release_links))
        items.append({
            "trace_name": trace_path.name,
            "report_name": report_path.name,
            "available": True,
            "finding": None,
            "evidence": pack.model_dump(mode="json"),
            "critic_record_link": "verified" if matching_records else "unavailable",
            "critic_record_files": matching_records,
            "release_link": "verified" if release_links else "unavailable",
            "release_manifests": release_links,
        })

    recipe_candidates = _interface_recipe_trace_candidates(root)
    return {
        "schema_version": "1.0",
        "status": "inspected",
        "items": items,
        "item_count": len(items),
        "recipe_candidates": recipe_candidates,
        "recipe_candidate_count": len(recipe_candidates),
        "inventory_truncated": truncated,
        "critic_model_called": False,
        "critic_result_recorded": False,
        "release_created": False,
        "execution_performed": False,
    }


def _exact_recipe_progress(
    records: list[tuple[Path, dict[str, Any]]],
    *,
    recipe_id: str,
    recipe_digest: str,
    approval_id: str,
    evidence_digest: str,
    result_digest: str,
    final_status: str,
) -> tuple[Path, dict[str, Any]]:
    """Bind one evidence record to exactly one persisted interface attempt."""

    matching = [
        (path, payload) for path, payload in records
        if payload.get("recipe_id") == recipe_id
        and payload.get("recipe_sha256") == recipe_digest
        and payload.get("approval_id") == approval_id
        and payload.get("approval_filename") == f"{approval_id}.json"
        and payload.get("evidence_sha256") == evidence_digest
        and payload.get("run_result_sha256") == result_digest
        and payload.get("status") == final_status
        and payload.get("execution_performed") is True
        and payload.get("execution_preview_sha256") == path.stem
    ]
    if len(matching) != 1:
        raise RecipeTraceAdapterError(
            "exact durable interface execution identity is unavailable or ambiguous"
        )
    return matching[0]


def _stored_trace_pair_exact(root: Path, trace: WorkflowTrace, report_text: str) -> bool:
    """Compare stored trace and report with an exact in-memory candidate."""

    trace_path = runtime_store_path(root, "traces") / f"{trace.task_id}.json"
    report_path = runtime_store_path(root, "reports") / f"{trace.task_id}.md"
    if (not trace_path.is_file() or not report_path.is_file()
            or trace_path.is_symlink() or report_path.is_symlink()):
        return False
    try:
        return (
            trace_path.stat().st_size <= MAX_TRACE_BYTES
            and report_path.stat().st_size <= MAX_REPORT_BYTES
            and WorkflowTrace.model_validate(json.loads(trace_path.read_text(encoding="utf-8"))) == trace
            and report_path.read_text(encoding="utf-8") == report_text
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError):
        return False


def _interface_recipe_trace_candidates(root: Path) -> list[dict[str, Any]]:
    """Preview truthful recipe-run trace adaptations without writing artifacts."""

    evidence_root = runtime_store_path(root, "recipe-evidence")
    recipe_root = runtime_store_path(root, "workflow-recipes")
    approval_root = runtime_store_path(root, "approvals")
    progress_root = runtime_store_path(root, "workflow-state", "interface-executions")
    for candidate_root in (evidence_root, recipe_root, approval_root, progress_root):
        if candidate_root.exists() and candidate_root.is_symlink():
            raise InterfaceApiError("recipe trace source root cannot be a symlink")
    paths = sorted(evidence_root.glob("*.json"), reverse=True) if evidence_root.is_dir() else []
    if len(paths) > MAX_INTERFACE_CRITIC_EVIDENCE:
        paths = paths[:MAX_INTERFACE_CRITIC_EVIDENCE]

    progress_records: list[tuple[Path, dict[str, Any]]] = []
    if progress_root.is_dir():
        progress_paths = sorted(progress_root.glob("*.json"))
        if len(progress_paths) > MAX_INTERFACE_EXECUTION_ATTEMPTS:
            raise InterfaceApiError("recipe trace progress inventory exceeds its limit")
        for path in progress_paths:
            if path.is_symlink() or path.stat().st_size > MAX_INTERFACE_OUTCOME_BYTES:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                progress_records.append((path, payload))

    results: list[dict[str, Any]] = []
    for evidence_path in paths:
        base = {
            "evidence_name": evidence_path.name,
            "adaptable": False,
            "finding": None,
            "trace": None,
            "trace_sha256": None,
            "critic_status": None,
            "critic_gaps": [],
            "execution_preview_sha256": None,
            "stored": False,
            "files_modified": False,
        }
        try:
            if evidence_path.is_symlink():
                raise RecipeTraceAdapterError("recipe evidence cannot be a symlink")
            evidence = load_recipe_evidence(evidence_path, evidence_root=evidence_root)
            digest = recipe_evidence_sha256(evidence)
            recipe_path = recipe_root / f"{evidence.recipe_id}.{evidence.recipe_sha256}.json"
            approval_path = approval_root / f"{evidence.approval_id}.json"
            recipe = load_recipe(recipe_path, recipe_root=recipe_root)
            approval = load_recipe_approval(approval_path, approval_root=approval_root)
            run_digest = recipe_run_result_sha256(evidence.run_result)
            result_root = runtime_store_path(root, "recipe-runs")
            result = load_recipe_run_result(
                result_root / f"{evidence.recipe_id}.{run_digest}.json",
                result_root=result_root,
            )
            if result != evidence.run_result:
                raise RecipeTraceAdapterError("durable result does not match recipe evidence")
            progress_path, progress = _exact_recipe_progress(
                progress_records,
                recipe_id=evidence.recipe_id,
                recipe_digest=evidence.recipe_sha256,
                approval_id=evidence.approval_id,
                evidence_digest=digest,
                result_digest=run_digest,
                final_status=evidence.final_status,
            )
            references = [
                runtime_reference(root, recipe_path),
                runtime_reference(root, approval_path),
                runtime_reference(root, evidence_path),
                runtime_reference(root, progress_path),
            ]
            trace = build_recipe_trace_candidate(
                recipe=recipe,
                approval=approval,
                evidence=evidence,
                evidence_sha256=digest,
                progress=progress,
                context_references=references,
            )
            with tempfile.TemporaryDirectory(prefix="actioncharter-critic-preview-") as directory:
                preview_root = Path(directory)
                traces = preview_root / "traces"
                reports = preview_root / "reports"
                traces.mkdir()
                reports.mkdir()
                trace_path = traces / f"{trace.task_id}.json"
                report_path = reports / f"{trace.task_id}.md"
                trace_path.write_text(trace.model_dump_json(indent=2) + "\n", encoding="utf-8")
                report_path.write_text(render_recipe_trace_report(trace), encoding="utf-8")
                pack = build_critic_evidence(
                    trace_path=trace_path,
                    report_path=report_path,
                    trace_root=traces,
                    report_root=reports,
                )
            stored_exact = _stored_trace_pair_exact(root, trace, render_recipe_trace_report(trace))
            base.update({
                "adaptable": True,
                "trace": trace.model_dump(mode="json"),
                "trace_sha256": recipe_trace_sha256(trace),
                "critic_status": pack.deterministic_status,
                "critic_gaps": pack.evidence_gaps,
                "execution_preview_sha256": progress_path.stem,
                "stored": stored_exact,
            })
        except (
            RecipeTraceAdapterError,
            CriticEvidenceError,
            RecipePolicyError,
            RecipeStorageError,
            RecipeApprovalError,
            RecipeEvidenceStorageError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            base["finding"] = redact_text(str(exc))[:500]
        results.append(base)
    return results


def save_interface_recipe_trace(
    request: InterfaceRecipeTraceSaveRequest,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Rebuild and immutably store one exactly reviewed adapted trace."""

    root = _trusted_root(project_root)
    candidate = next(
        (
            item for item in _interface_recipe_trace_candidates(root)
            if item["evidence_name"] == request.evidence_name
        ),
        None,
    )
    if candidate is None or not candidate["adaptable"] or candidate["trace"] is None:
        raise InterfaceApiError("recipe evidence cannot enter the trace persistence boundary")
    trace = WorkflowTrace.model_validate(candidate["trace"])
    try:
        trace_path, report_path, trace_digest, report_digest = persist_recipe_trace_candidate(
            trace=trace,
            confirmed_trace_sha256=request.confirmed_trace_sha256,
            trace_root=runtime_store_path(root, "traces"),
            report_root=runtime_store_path(root, "reports"),
        )
    except RecipeTraceAdapterError as exc:
        raise InterfaceApiError(redact_text(str(exc))[:500]) from exc
    pack = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=runtime_store_path(root, "traces"),
        report_root=runtime_store_path(root, "reports"),
    )
    return {
        "schema_version": "1.0",
        "status": "stored",
        "task_id": trace.task_id,
        "trace_sha256": trace_digest,
        "report_sha256": report_digest,
        "trace_path": runtime_reference(root,trace_path),
        "report_path": runtime_reference(root,report_path),
        "critic_status": pack.deterministic_status,
        "critic_gaps": pack.evidence_gaps,
        "trace_stored": True,
        "report_stored": True,
        "critic_model_called": False,
        "critic_result_recorded": False,
        "release_created": False,
        "execution_performed": False,
    }


def run_interface_critic(
    request: InterfaceCriticRunRequest,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Run one schema-constrained Critic assessment without persisting it."""

    root = _trusted_root(project_root)
    trace_root = runtime_store_path(root, "traces")
    report_root = runtime_store_path(root, "reports")
    trace_path = trace_root / request.trace_name
    report_path = report_root / request.report_name
    evidence = build_critic_evidence(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
    )
    references = {Path(item.path).name: item.sha256 for item in evidence.evidence_references}
    if references.get(request.trace_name) != request.confirmed_trace_sha256:
        raise InterfaceApiError("reviewed trace digest no longer matches")
    if references.get(request.report_name) != request.confirmed_report_sha256:
        raise InterfaceApiError("reviewed report digest no longer matches")
    result = critique_task(
        trace_path=trace_path,
        report_path=report_path,
        trace_root=trace_root,
        report_root=report_root,
        agents_root=root / "agents",
    )
    return {
        "schema_version": "1.0",
        "status": "assessed_not_recorded",
        "critic_result_sha256": critic_result_sha256(result),
        "result": result.model_dump(mode="json"),
        "critic_model_called": True,
        "critic_result_recorded": False,
        "release_created": False,
        "execution_performed": False,
    }


def record_interface_critic_result(
    request: InterfaceCriticRecordRequest,
    *,
    project_root: Path,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Reverify evidence and immutably record one exact Critic result."""

    root = _trusted_root(project_root)
    trace_root = runtime_store_path(root, "traces")
    report_root = runtime_store_path(root, "reports")
    evidence = build_critic_evidence(
        trace_path=trace_root / request.trace_name,
        report_path=report_root / request.report_name,
        trace_root=trace_root,
        report_root=report_root,
    )
    references = {Path(item.path).name: item.sha256 for item in evidence.evidence_references}
    if references.get(request.trace_name) != request.confirmed_trace_sha256:
        raise InterfaceApiError("reviewed trace digest no longer matches")
    if references.get(request.report_name) != request.confirmed_report_sha256:
        raise InterfaceApiError("reviewed report digest no longer matches")
    result = request.result
    if critic_result_sha256(result) != request.confirmed_critic_result_sha256:
        raise InterfaceApiError("reviewed Critic-result digest no longer matches")
    if (
        result.task_id != evidence.task_id
        or result.deterministic_status != evidence.deterministic_status
        or result.evidence_references != evidence.evidence_references
        or result.evidence_gaps != evidence.evidence_gaps
        or result.workflow_warnings != evidence.warnings
        or result.human_corrections != evidence.human_corrections
    ):
        raise InterfaceApiError("Critic result no longer matches deterministic evidence")
    record = build_critic_result_record(
        result=result,
        recorded_at=now or datetime.now(timezone.utc),
    )
    stored = persist_critic_result_record(
        record,
        record_root=runtime_store_path(root, "critic-results"),
    )
    record_directory = runtime_reference(root,Path(stored.record_directory))
    record_file = runtime_reference(root,Path(stored.record_file))
    return {
        **stored.model_dump(mode="json"),
        "status": "recorded",
        "record_directory": record_directory,
        "record_file": record_file,
        "critic_model_called": False,
        "critic_result_recorded": True,
        "release_created": False,
        "execution_performed": False,
    }


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
interface_critic_evidence_inventory = _task_entrypoint(interface_critic_evidence_inventory, audit=False)
save_interface_recipe_trace = _task_entrypoint(save_interface_recipe_trace)
run_interface_critic = _task_entrypoint(run_interface_critic)
record_interface_critic_result = _task_entrypoint(record_interface_critic_result)
