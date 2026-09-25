"""Read-only assessment of authoritative workflow releases."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from geoagent_harness.approvals import (
    ApprovalError,
    load_approval,
    load_planner_result,
    plan_sha256,
    verify_approval,
)
from geoagent_harness.critic import (
    CriticEvidenceError,
    CriticResultStorageError,
    build_critic_evidence,
    load_critic_result_record,
)
from geoagent_harness.operational_history import (
    OperationalHistoryError,
    build_operational_timeline,
    load_operational_events,
)
from geoagent_harness.redaction import redact_value
from geoagent_harness.recipes import (
    RecipeApprovalError,
    RecipeEvidenceStorageError,
    RecipeStorageError,
    load_recipe,
    load_recipe_approval,
    load_recipe_evidence,
    load_recipe_run_result,
    recipe_sha256,
    verify_recipe_approval,
)
from geoagent_harness.skill_registry import SkillRegistry
from geoagent_harness.releases.schemas import (
    AuthoritativeReleaseCandidate,
    ReleaseComponentKind,
    ReleaseComponentReference,
    ReleaseLifecycleState,
)


class ReleaseAssessmentError(RuntimeError):
    """Raised when release inputs cannot be safely assessed."""


def canonical_authoritative_release_candidate_json(
    candidate: AuthoritativeReleaseCandidate,
) -> str:
    """Return canonical JSON for one non-writing assessment."""

    original = candidate.model_dump(mode="json")
    if redact_value(original) != original:
        raise ReleaseAssessmentError(
            "release candidate contains content requiring redaction"
        )
    return json.dumps(
        original,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def authoritative_release_candidate_sha256(
    candidate: AuthoritativeReleaseCandidate,
) -> str:
    """Digest one complete release-readiness assessment."""

    return hashlib.sha256(
        canonical_authoritative_release_candidate_json(candidate).encode(
            "utf-8"
        )
    ).hexdigest()


def _safe_file(path: Path, *, root: Path) -> Path:
    if root.is_symlink():
        raise ReleaseAssessmentError(
            "release evidence root cannot be a symlink"
        )
    try:
        safe_root = root.resolve(strict=True)
    except OSError as exc:
        raise ReleaseAssessmentError(
            "release evidence root is unavailable"
        ) from exc
    if path.is_absolute():
        candidate = path
    else:
        direct = path.absolute()
        try:
            direct.relative_to(safe_root)
            candidate = direct
        except ValueError:
            candidate = safe_root / path
    try:
        relative_candidate = candidate.absolute().relative_to(safe_root)
    except ValueError as exc:
        raise ReleaseAssessmentError(
            "release evidence file escaped its approved root"
        ) from exc
    current = safe_root
    for part in relative_candidate.parts:
        current = current / part
        if current.is_symlink():
            raise ReleaseAssessmentError(
                "release evidence path cannot contain a symlink"
            )
    try:
        safe_path = candidate.resolve(strict=True)
        safe_path.relative_to(safe_root)
    except (OSError, ValueError) as exc:
        raise ReleaseAssessmentError(
            "release evidence file escaped its approved root"
        ) from exc
    if not safe_path.is_file():
        raise ReleaseAssessmentError(
            "release evidence path must be a file"
        )
    return safe_path


def _component(
    *,
    component_id: str,
    kind: ReleaseComponentKind,
    path: Path,
    root: Path,
    project_root: Path,
) -> ReleaseComponentReference:
    safe_path = _safe_file(path, root=root)
    try:
        relative = safe_path.relative_to(
            project_root.resolve(strict=True)
        ).as_posix()
        content = safe_path.read_bytes()
    except (OSError, ValueError) as exc:
        raise ReleaseAssessmentError(
            "release component is outside the project root"
        ) from exc
    if not content:
        raise ReleaseAssessmentError(
            "release component cannot be empty"
        )
    return ReleaseComponentReference(
        component_id=component_id,
        kind=kind,
        path=relative,
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
    )


def assess_workflow_release_candidate(
    *,
    release_id: str,
    trace_file: Path,
    report_file: Path,
    critic_record_file: Path,
    history_file: Path,
    trace_root: Path,
    report_root: Path,
    critic_root: Path,
    history_root: Path,
    project_root: Path,
    assessed_at: datetime,
    plan_file: Path | None = None,
    plan_root: Path | None = None,
    approval_file: Path | None = None,
    approval_root: Path | None = None,
) -> AuthoritativeReleaseCandidate:
    """Assess exact workflow evidence without copying or releasing it."""

    try:
        evidence = build_critic_evidence(
            trace_path=trace_file,
            report_path=report_file,
            trace_root=trace_root,
            report_root=report_root,
        )
        critic_record = load_critic_result_record(
            critic_record_file,
            record_root=critic_root,
        )
        events = load_operational_events(
            history_file,
            event_root=history_root,
        )
        timeline = build_operational_timeline(events)
    except (
        CriticEvidenceError,
        CriticResultStorageError,
        OperationalHistoryError,
    ) as exc:
        raise ReleaseAssessmentError(
            "release evidence could not be verified"
        ) from exc

    components = [
        _component(
            component_id="trace",
            kind=ReleaseComponentKind.TRACE,
            path=trace_file,
            root=trace_root,
            project_root=project_root,
        ),
        _component(
            component_id="report",
            kind=ReleaseComponentKind.REPORT,
            path=report_file,
            root=report_root,
            project_root=project_root,
        ),
        _component(
            component_id="critic_result",
            kind=ReleaseComponentKind.CRITIC_RESULT,
            path=critic_record_file,
            root=critic_root,
            project_root=project_root,
        ),
        _component(
            component_id="operational_history",
            kind=ReleaseComponentKind.OPERATIONAL_HISTORY,
            path=history_file,
            root=history_root,
            project_root=project_root,
        ),
    ]
    violations = list(evidence.evidence_gaps)

    task_ids = {
        evidence.task_id,
        critic_record.task_id,
        timeline.task_id,
    }
    if len(task_ids) != 1:
        raise ReleaseAssessmentError(
            "release task identities do not match"
        )

    evidence_refs = {
        (item.path, item.sha256)
        for item in evidence.evidence_references
    }
    critic_refs = {
        (item.path, item.sha256)
        for item in critic_record.critic_result.evidence_references
    }
    critic_complete = (
        critic_record.deterministic_status
        == evidence.deterministic_status
        and critic_refs == evidence_refs
    )
    if not critic_complete:
        violations.append(
            "Critic result does not match authoritative evidence"
        )

    validation_complete = evidence.validation.passed is True
    if not validation_complete:
        violations.append("deterministic validation did not pass")

    approval_complete = False
    if plan_file is None or approval_file is None:
        violations.append("plan or approval evidence is missing")
    elif plan_root is None or approval_root is None:
        raise ReleaseAssessmentError(
            "plan and approval roots are required with their files"
        )
    else:
        try:
            planner_result = load_planner_result(
                path=plan_file,
                plan_root=plan_root,
            )
            approval = load_approval(
                path=approval_file,
                approval_root=approval_root,
            )
            required_steps = [
                step.step_id
                for step in planner_result.plan.steps
                if step.requires_approval
            ]
            verification = verify_approval(
                approval=approval,
                plan=planner_result.plan,
                required_step_ids=required_steps,
                now=assessed_at,
            )
        except ApprovalError as exc:
            raise ReleaseAssessmentError(
                "release approval evidence could not be verified"
            ) from exc

        approval_complete = (
            verification.approved
            and evidence.approval.complete
            and evidence.approval.approval_id == approval.approval_id
            and evidence.approval.plan_sha256
            == plan_sha256(planner_result.plan)
            and set(evidence.approval.approved_step_ids)
            == set(approval.step_ids)
        )
        if not approval_complete:
            violations.append(
                "approval does not match authoritative workflow evidence"
            )
        components.extend(
            [
                _component(
                    component_id="plan",
                    kind=ReleaseComponentKind.PLAN,
                    path=plan_file,
                    root=plan_root,
                    project_root=project_root,
                ),
                _component(
                    component_id="approval",
                    kind=ReleaseComponentKind.APPROVAL,
                    path=approval_file,
                    root=approval_root,
                    project_root=project_root,
                ),
            ]
        )

    kinds = {item.kind for item in components}
    required = {
        ReleaseComponentKind.PLAN,
        ReleaseComponentKind.APPROVAL,
        ReleaseComponentKind.TRACE,
        ReleaseComponentKind.REPORT,
        ReleaseComponentKind.CRITIC_RESULT,
        ReleaseComponentKind.OPERATIONAL_HISTORY,
    }
    missing = sorted(
        item.value for item in required - kinds
    )
    if missing:
        violations.append(
            "missing release components: " + ", ".join(missing)
        )

    violations = list(dict.fromkeys(violations))
    evidence_complete = (
        approval_complete
        and validation_complete
        and critic_complete
        and not missing
    )
    ready = (
        evidence.deterministic_status == "validated_success"
        and evidence_complete
        and not violations
    )
    lifecycle = (
        ReleaseLifecycleState.VALIDATED
        if ready
        else (
            ReleaseLifecycleState.REJECTED
            if evidence.deterministic_status
            in {"validation_failed", "execution_failed"}
            else ReleaseLifecycleState.CANDIDATE
        )
    )

    return AuthoritativeReleaseCandidate(
        release_id=release_id,
        subject_type="workflow",
        subject_id=evidence.task_id,
        deterministic_status=evidence.deterministic_status,
        lifecycle_state=lifecycle,
        components=components,
        approval_complete=approval_complete,
        validation_complete=validation_complete,
        critic_complete=critic_complete,
        evidence_complete=evidence_complete,
        ready_for_release=ready,
        violations=violations,
        assessed_at=assessed_at,
    )


def assess_recipe_release_candidate(
    *,
    release_id: str,
    recipe_file: Path,
    approval_file: Path,
    run_result_file: Path,
    recipe_evidence_file: Path,
    trace_file: Path,
    report_file: Path,
    critic_record_file: Path,
    history_file: Path,
    recipe_root: Path,
    approval_root: Path,
    run_result_root: Path,
    recipe_evidence_root: Path,
    trace_root: Path,
    report_root: Path,
    critic_root: Path,
    history_root: Path,
    project_root: Path,
    registry: SkillRegistry,
    assessed_at: datetime,
    approval_verified_at: datetime | None = None,
) -> AuthoritativeReleaseCandidate:
    """Assess an exact recipe run without copying or releasing evidence."""

    try:
        recipe = load_recipe(recipe_file, recipe_root=recipe_root)
        approval = load_recipe_approval(
            approval_file, approval_root=approval_root
        )
        run_result = load_recipe_run_result(
            run_result_file, result_root=run_result_root
        )
        recipe_evidence = load_recipe_evidence(
            recipe_evidence_file, evidence_root=recipe_evidence_root
        )
        approval_verification = verify_recipe_approval(
            approval=approval,
            recipe=recipe,
            registry=registry,
            now=approval_verified_at or assessed_at,
        )
        evidence = build_critic_evidence(
            trace_path=trace_file,
            report_path=report_file,
            trace_root=trace_root,
            report_root=report_root,
        )
        critic_record = load_critic_result_record(
            critic_record_file, record_root=critic_root
        )
        timeline = build_operational_timeline(
            load_operational_events(history_file, event_root=history_root)
        )
    except (
        RecipeApprovalError,
        RecipeEvidenceStorageError,
        RecipeStorageError,
        CriticEvidenceError,
        CriticResultStorageError,
        OperationalHistoryError,
    ) as exc:
        raise ReleaseAssessmentError(
            "recipe release evidence could not be verified"
        ) from exc

    components = [
        _component(component_id="recipe", kind=ReleaseComponentKind.RECIPE,
                   path=recipe_file, root=recipe_root, project_root=project_root),
        _component(component_id="approval", kind=ReleaseComponentKind.APPROVAL,
                   path=approval_file, root=approval_root, project_root=project_root),
        _component(component_id="run_result", kind=ReleaseComponentKind.RUN_RESULT,
                   path=run_result_file, root=run_result_root, project_root=project_root),
        _component(component_id="recipe_evidence", kind=ReleaseComponentKind.RECIPE_EVIDENCE,
                   path=recipe_evidence_file, root=recipe_evidence_root, project_root=project_root),
        _component(component_id="trace", kind=ReleaseComponentKind.TRACE,
                   path=trace_file, root=trace_root, project_root=project_root),
        _component(component_id="report", kind=ReleaseComponentKind.REPORT,
                   path=report_file, root=report_root, project_root=project_root),
        _component(component_id="critic_result", kind=ReleaseComponentKind.CRITIC_RESULT,
                   path=critic_record_file, root=critic_root, project_root=project_root),
        _component(component_id="operational_history", kind=ReleaseComponentKind.OPERATIONAL_HISTORY,
                   path=history_file, root=history_root, project_root=project_root),
    ]
    violations = list(evidence.evidence_gaps)
    digest = recipe_sha256(recipe)

    identities_match = (
        recipe.recipe_id == run_result.recipe_id == recipe_evidence.recipe_id
        and digest == run_result.recipe_sha256 == recipe_evidence.recipe_sha256
        and approval.approval_id
        == run_result.approval_id
        == recipe_evidence.approval_id
        == evidence.approval.approval_id
        and evidence.approval.recipe_sha256 == digest
        and evidence.task_id == critic_record.task_id == timeline.task_id
        and recipe_evidence.run_result == run_result
        and recipe_evidence.final_status == run_result.final_status
    )
    if not identities_match:
        violations.append("recipe release identities or exact run evidence do not match")

    approval_complete = (
        identities_match
        and approval_verification.approved
        and evidence.approval.complete
        and set(evidence.approval.approved_step_ids) == set(approval.step_ids)
    )
    if not approval_complete:
        violations.append("approval does not match authoritative recipe evidence")

    evidence_refs = {(item.path, item.sha256) for item in evidence.evidence_references}
    critic_refs = {
        (item.path, item.sha256)
        for item in critic_record.critic_result.evidence_references
    }
    critic_complete = (
        critic_record.deterministic_status == evidence.deterministic_status
        and critic_refs == evidence_refs
    )
    if not critic_complete:
        violations.append("Critic result does not match authoritative evidence")

    validation_complete = (
        evidence.validation.passed is True
        and run_result.final_status == "validated_success"
    )
    if not validation_complete:
        violations.append("deterministic validation did not pass")

    required = {
        ReleaseComponentKind.RECIPE,
        ReleaseComponentKind.APPROVAL,
        ReleaseComponentKind.RUN_RESULT,
        ReleaseComponentKind.RECIPE_EVIDENCE,
        ReleaseComponentKind.REPORT,
        ReleaseComponentKind.CRITIC_RESULT,
        ReleaseComponentKind.OPERATIONAL_HISTORY,
    }
    missing = sorted(item.value for item in required - {item.kind for item in components})
    if missing:
        violations.append("missing release components: " + ", ".join(missing))

    violations = list(dict.fromkeys(violations))
    evidence_complete = (
        approval_complete and validation_complete and critic_complete and not missing
    )
    ready = (
        evidence.deterministic_status == "validated_success"
        and evidence_complete
        and not violations
    )
    lifecycle = (
        ReleaseLifecycleState.VALIDATED
        if ready
        else (
            ReleaseLifecycleState.REJECTED
            if evidence.deterministic_status in {"validation_failed", "execution_failed"}
            else ReleaseLifecycleState.CANDIDATE
        )
    )
    return AuthoritativeReleaseCandidate(
        release_id=release_id,
        subject_type="recipe",
        subject_id=recipe.recipe_id,
        deterministic_status=evidence.deterministic_status,
        lifecycle_state=lifecycle,
        components=components,
        approval_complete=approval_complete,
        validation_complete=validation_complete,
        critic_complete=critic_complete,
        evidence_complete=evidence_complete,
        ready_for_release=ready,
        violations=violations,
        assessed_at=assessed_at,
    )
