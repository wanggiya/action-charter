"""Existing legacy planning coordination, independent of HTTP."""
from __future__ import annotations
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
from geoagent_harness.platform.storage import repositories
from pathlib import Path
import re
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from geoagent_harness.capabilities.recipes.catalog import RecipeTemplateCatalogError, load_recipe_template_catalog
from geoagent_harness.capabilities.recipes.proposals.compiler import RecipeCompilationError, compile_recipe_proposal
from geoagent_harness.capabilities.recipes.proposals.schemas import RecipeProposal
from geoagent_harness.platform.skill_registry import SkillRegistryError, load_skill_registry
from geoagent_harness.core.policy.approvals import ApprovalError, create_approval, load_approval, load_planner_result, plan_sha256, verify_approval
from geoagent_harness.core.policy.approvals.schemas import ApprovalRecord
from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError, create_recipe_approval, load_recipe_approval, verify_recipe_approval
from geoagent_harness.capabilities.recipes.execution import RecipePolicyError, validate_recipe_policy
from geoagent_harness.capabilities.recipes.execution import RecipeStorageError, load_recipe, recipe_path, save_recipe
from geoagent_harness.capabilities.recipes.execution import recipe_sha256
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.contracts.redaction import redact_text
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan, prepare_interface_plan_approval, record_interface_plan_approval, verify_interface_plan_approval, preview_interface_plan_execution, compile_interface_plan_recipe, _planner_recipe_definition, save_interface_plan_recipe, prepare_interface_recipe_approval, record_interface_recipe_approval, verify_interface_recipe_approval
from geoagent_harness.contracts.interface_requests import (
    InterfacePlanRequest,
)
from geoagent_harness.contracts.interface_limits import (
    MAX_INTERFACE_PLANS,
    MAX_INTERFACE_PLAN_APPROVALS,
    MAX_INTERFACE_RECIPES,
)


class _InventoryProblems:
    """Display-only, bounded diagnostics; never reusable execution/authority data."""

    def __init__(self):
        self.records = []
        self.count = 0
        self.seen = set()

    def add(self, path, kind, error):
        key = (str(path), kind)
        if key in self.seen:
            return
        self.seen.add(key)
        self.count += 1
        if len(self.records) >= MAX_INTERFACE_RECIPES:
            return
        if isinstance(error, RecipePolicyError):
            code, reason = 'policy_rejected', str(error)
        elif isinstance(error, ValidationError):
            code, reason = 'invalid_record', 'Stored record failed schema validation'
        elif isinstance(error, OSError):
            code, reason = 'unavailable_record', 'Stored record could not be read safely'
        elif isinstance(error, RecursionError):
            code, reason = 'invalid_record', 'Stored record exceeds the nesting limit'
        else:
            code = 'invalid_record'
            reason = str(error) if isinstance(error, (RecipeStorageError, RecipeApprovalError, ApprovalError, InterfaceApiError)) else 'Stored record failed validation'
        reason = ''.join(c if c.isprintable() else ' ' for c in redact_text(reason))[:300]
        name = path.name if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,249}\.json', path.name) else 'Unrecognized record name'
        self.records.append({'filename': name, 'kind': kind, 'status': 'unavailable',
            'code': code, 'reason': reason, 'approval_allowed': False, 'execution_allowed': False})

    def read(self, path, kind, loader):
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
                raise InterfaceApiError('Stored record is not a single regular file')
            return loader()
        except (InterfaceApiError, RecipeStorageError, RecipeApprovalError, ApprovalError, OSError, ValueError, RecursionError) as error:
            self.add(path, kind, error)
            return None

    def projection(self):
        # Keep the normal/empty response contract, including historical snapshots.
        return {} if not self.count else {'invalid_records': self.records,
            'invalid_record_count': self.count,
            'invalid_records_truncated': self.count > len(self.records)}


def interface_recipe_template_catalog(project_root: Path) -> dict[str, Any]:
    """Return the same validated non-executing catalog projection as the CLI."""

    catalog = load_recipe_template_catalog(_trusted_root(project_root))
    optional_by_profile = {
        "vector_inspection": ["source_layer"],
        "raster_inspection": [],
        "raster_conversion": ["resampling"],
        "vector_conversion": ["source_layer", "target_layer", "target_format"],
        "vector_postgis": ["source_layer"],
    }
    return {
        "schema_version": catalog.schema_version,
        "templates": [
            {
                **template.model_dump(mode="json"),
                "optional_parameters": optional_by_profile[template.parameter_profile],
                "parameter_roots": {
                    name: root
                    for name, root in (
                        ("path", "data/input"),
                        ("target_path", "data/output"),
                    )
                    if name in template.required_parameters
                },
            }
            for template in catalog.templates
        ],
        "catalog_validated": True,
        "files_modified": False,
        "execution_performed": False,
    }


def _normalize_interface_recipe_paths(payload: object) -> object:
    """Expand filename-only interface parameters into governed data roots.

    Explicit relative and absolute paths remain unchanged so the existing
    compiler and execution policies retain final authority over them.
    """

    if not isinstance(payload, dict):
        return payload
    selection = payload.get("selection")
    if not isinstance(selection, dict):
        return payload
    parameters = selection.get("parameters")
    if not isinstance(parameters, dict):
        return payload

    normalized_parameters = dict(parameters)
    for name, root in (("path", "data/input"), ("target_path", "data/output")):
        value = normalized_parameters.get(name)
        if (
            isinstance(value, str)
            and value
            and "/" not in value
            and "\\" not in value
            and value not in {".", ".."}
        ):
            normalized_parameters[name] = f"{root}/{value}"

    return {
        **payload,
        "selection": {
            **selection,
            "parameters": normalized_parameters,
        },
    }


def plan_interface_task(
    request: InterfacePlanRequest,
    *,
    project_root: Path,
    agents_root: Path | None = None,
) -> dict[str, Any]:
    """Call the existing planner without persistence, approval, or execution."""

    from geoagent_harness.agents.roles.planner import plan_task

    root = _trusted_root(project_root)
    trusted_agents = agents_root if agents_root is not None else root / "agents"
    selected_context = "\n\nFile input convention: resolve a bare input filename under data/input. Keep explicit normalized data/input paths. This convention does not grant file access or execution authority."
    if request.input_paths:
        selected_context += "\n\nOperator-selected governed input references:\n" + "\n".join(
            f"- {path}" for path in request.input_paths
        )
    result = plan_task(
        original_request=request.request + selected_context,
        project_root=root,
        agents_root=trusted_agents,
        allowed_skill_ids=request.allowed_skill_ids,
    )
    return {
        "schema_version": "1.0",
        "status": "planned_not_saved",
        "agent_id": result.agent_id,
        "model": result.model,
        "original_request": request.request,
        "allowed_skill_ids": request.allowed_skill_ids,
        "context_references": [*result.context_references, *request.input_paths],
        "plan": result.plan.model_dump(mode="json"),
        "plan_sha256": plan_sha256(result.plan),
        "warnings": result.warnings,
        "plan_saved": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def interface_planner_skill_catalog(project_root: Path) -> dict[str, Any]:
    """Return safe implemented skills for explicit planner selection."""

    from geoagent_harness.capabilities.registry.registry import operation_catalog
    contracts = operation_catalog(_trusted_root(project_root))['operations']
    skills = [{key:operation[key] for key in ['id','name','workflow_supported','default_arguments','package_sha256','parameters_schema','outputs','kind','approval_required','validation_required']} | {'access':operation['effects']['access']} for operation in contracts]
    return {
        "schema_version": "1.0",
        "skills": skills,
        "skill_count": len(skills),
        "catalog_validated": True,
        "execution_performed": False,
    }


def interface_saved_plan_inventory(
    project_root: Path,
    *, plan_root: Path | None = None,
    approval_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return bounded validated plans and matching approval summaries."""

    root = _trusted_root(project_root)
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
    if plans.is_symlink() or (plans.exists() and not plans.is_dir()):
        raise InterfaceApiError("plan root is unsafe")
    if approvals.is_symlink() or (approvals.exists() and not approvals.is_dir()):
        raise InterfaceApiError("approval root is unsafe")
    problems = _InventoryProblems()
    approval_by_plan: dict[str, list[tuple[dict[str, Any], ApprovalRecord]]] = {}
    if approvals.exists():
        approval_paths = sorted(approvals.glob("approval-*.json"))
        if len(approval_paths) > MAX_INTERFACE_PLAN_APPROVALS:
            raise InterfaceApiError("plan approval inventory exceeds its limit")
        for path in approval_paths:
            record = problems.read(path, 'plan_approval', lambda: load_approval(path=path, approval_root=approvals))
            if record is None:
                continue
            approval_by_plan.setdefault(record.plan_sha256, []).append(({
                "approval_id": record.approval_id,
                "approval_filename": path.name,
                "decision": record.decision,
                "step_ids": record.step_ids,
                "created_at": record.created_at.isoformat(),
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            }, record))
    items = []
    if plans.exists():
        paths = [plans / name for name in repositories(root).documents('plans',directory=plans).names(order='recent') if name.startswith('planner-plan.')]
        if len(paths) > MAX_INTERFACE_PLANS:
            raise InterfaceApiError("saved plan inventory exceeds its limit")
        for path in paths:
            result = problems.read(path, 'plan', lambda: repositories(root).documents('plans',directory=plans).load(path.name))
            if result is None:
                continue
            digest = plan_sha256(result.plan)
            if path.name != f"planner-plan.{digest}.json":
                problems.add(path, 'plan', InterfaceApiError("saved plan filename does not match its digest"))
                continue
            required_steps = [step.step_id for step in result.plan.steps if step.requires_approval]
            linked_approvals = []
            for summary, record in approval_by_plan.get(digest, []):
                verification = verify_approval(
                    approval=record,
                    plan=result.plan,
                    required_step_ids=required_steps,
                    now=now,
                )
                linked_approvals.append({
                    **summary,
                    "authority_link": "verified" if verification.approved else "blocked",
                    "authority_reason": verification.reason,
                })
            items.append({
                "plan_filename": path.name, "plan_sha256": digest,
                "saved_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "planner_result": result.model_dump(mode="json"),
                "approvals": linked_approvals,
            })
    return {"schema_version": "1.0", "status": "inspected", "plans": items, "plan_count": len(items), "files_modified": False, "execution_performed": False, **problems.projection()}


def compile_interface_recipe_proposal(
    payload: object,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Validate and compile one proposal without persistence or execution."""

    proposal = RecipeProposal.model_validate(_normalize_interface_recipe_paths(payload))
    root = _trusted_root(project_root)
    result = compile_recipe_proposal(
        proposal,
        registry=load_skill_registry(root),
    )
    if result.recipe_saved or result.approval_performed or result.execution_performed:
        raise InterfaceApiError("compiler crossed the non-mutating interface boundary")
    return {
        "schema_version": "1.0",
        "status": "compiled",
        "result": result.model_dump(mode="json"),
        "recipe_sha256": recipe_sha256(result.recipe),
        "files_modified": False,
        "approval_performed": False,
        "execution_performed": False,
    }


def save_interface_reviewed_recipe(
    payload: object,
    *,
    confirmed_recipe_sha256: str,
    project_root: Path,
    recipe_root: Path | None = None,
) -> dict[str, Any]:
    """Recompile, verify the reviewed digest, and immutably save one recipe."""

    if not isinstance(confirmed_recipe_sha256, str) or len(confirmed_recipe_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in confirmed_recipe_sha256
    ):
        raise InterfaceApiError("confirmed recipe digest is invalid")
    proposal = RecipeProposal.model_validate(_normalize_interface_recipe_paths(payload))
    root = _trusted_root(project_root)
    compiled = compile_recipe_proposal(
        proposal,
        registry=load_skill_registry(root),
    )
    digest = recipe_sha256(compiled.recipe)
    if digest != confirmed_recipe_sha256:
        raise InterfaceApiError("reviewed recipe digest no longer matches")
    destination = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    if destination.is_symlink():
        raise InterfaceApiError("recipe root cannot be a symlink")
    saved, path = save_recipe(compiled.recipe, recipe_root=destination)
    return {
        "schema_version": "1.0",
        "status": "stored",
        "recipe_id": saved.recipe_id,
        "recipe_sha256": recipe_sha256(saved),
        "recipe_filename": path.name,
        "recipe_saved": True,
        "approval_performed": False,
        "execution_performed": False,
    }


def interface_saved_recipe_inventory(
    *,
    project_root: Path,
    recipe_root: Path | None = None,
    approval_root: Path | None = None,
    plan_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return bounded safe summaries of immutable stored recipes."""

    root = _trusted_root(project_root)
    destination = recipe_root if recipe_root is not None else runtime_store_path(root, "workflow-recipes")
    approvals = approval_root if approval_root is not None else runtime_store_path(root, "approvals")
    plans = plan_root if plan_root is not None else runtime_store_path(root, 'plans')
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise InterfaceApiError("recipe root is unsafe")
    if approvals.is_symlink() or (approvals.exists() and not approvals.is_dir()):
        raise InterfaceApiError("approval root is unsafe")
    if plans.is_symlink() or (plans.exists() and not plans.is_dir()):
        raise InterfaceApiError("plan root is unsafe")
    problems = _InventoryProblems()
    approval_by_recipe: dict[str, list[tuple[Path, Any]]] = {}
    if approvals.exists():
        approval_paths = sorted(approvals.glob("recipe-approval-*.json"))
        if len(approval_paths) > MAX_INTERFACE_PLAN_APPROVALS:
            raise InterfaceApiError("recipe approval inventory exceeds its limit")
        for approval_path in approval_paths:
            record = problems.read(approval_path, 'recipe_approval', lambda: load_recipe_approval(approval_path, approval_root=approvals))
            if record is None:
                continue
            approval_by_recipe.setdefault(record.recipe_sha256, []).append((approval_path, record))
    if not destination.exists():
        recipes: list[dict[str, Any]] = []
    else:
        paths = sorted(destination.glob("*.json"), key=lambda path: path.name)
        if len(paths) > MAX_INTERFACE_RECIPES:
            raise InterfaceApiError("recipe inventory exceeds its limit")
        registry = load_skill_registry(root)
        recipes = []
        for path in paths:
            recipe = problems.read(path, 'recipe', lambda: load_recipe(path, recipe_root=destination))
            if recipe is None:
                continue
            policy = problems.read(path, 'recipe', lambda: validate_recipe_policy(recipe, registry=registry))
            if policy is None:
                continue
            digest = recipe_sha256(recipe)
            plan_match = "unavailable"
            matched_plan_digest: str | None = None
            plan_match_reason = "No exact saved Planner definition found"
            planner_id = re.fullmatch(r"planner-([a-f0-9]{16})", recipe.recipe_id)
            if planner_id and plans.is_dir():
                plan_paths = list(plans.glob(f"planner-plan.{planner_id.group(1)}*.json"))
                if len(plan_paths) > MAX_INTERFACE_PLANS:
                    raise InterfaceApiError("matching Planner inventory exceeds its limit")
                matches = []
                invalid_plan = False
                for plan_path in plan_paths:
                    planner_result = problems.read(plan_path, 'plan', lambda: load_planner_result(path=plan_path, plan_root=plans))
                    if planner_result is None:
                        invalid_plan = True
                        continue
                    plan_digest = plan_sha256(planner_result.plan)
                    if plan_path.name != f"planner-plan.{plan_digest}.json":
                        problems.add(plan_path, 'plan', InterfaceApiError("matching Planner filename is invalid"))
                        invalid_plan = True
                        continue
                    try:
                        reconstructed = _planner_recipe_definition(planner_result, plan_digest)
                    except (InterfaceApiError, ValidationError):
                        continue
                    if recipe_sha256(reconstructed) == digest:
                        matches.append(plan_digest)
                if invalid_plan:
                    plan_match, plan_match_reason = 'blocked', 'Matching Planner evidence contains an invalid record'
                elif len(matches) == 1:
                    plan_match, matched_plan_digest = "verified", matches[0]
                    plan_match_reason = "Canonical recipe definition matches the saved Planner result"
                elif plan_paths:
                    plan_match = "blocked"
                    plan_match_reason = "No unique exact Planner definition matches this recipe"
            linked_approvals = []
            for approval_path, record in approval_by_recipe.get(digest, []):
                verification = verify_recipe_approval(
                    approval=record, recipe=recipe, registry=registry, now=now,
                )
                linked_approvals.append({
                    "approval_id": record.approval_id,
                    "approval_filename": approval_path.name,
                    "decision": record.decision,
                    "step_ids": record.step_ids,
                    "created_at": record.created_at.isoformat(),
                    "expires_at": record.expires_at.isoformat() if record.expires_at else None,
                    "authority_link": "verified" if verification.approved else "blocked",
                    "authority_reason": verification.reason,
                })
            recipes.append({
                "recipe_id": recipe.recipe_id,
                "recipe_sha256": digest,
                "recipe_filename": path.name,
                "matching_plan_sha256": matched_plan_digest,
                "plan_definition_link": plan_match,
                "plan_definition_reason": plan_match_reason,
                "saved_at": datetime.fromtimestamp(
                    path.stat().st_mtime,
                    timezone.utc,
                ).isoformat(),
                "steps": [
                    {"step_id": step.step_id, "skill_id": step.skill_id, "depends_on": step.depends_on}
                    for step in recipe.steps
                ],
                "approval_required_step_ids": policy.approval_required_step_ids,
                "validation_required_step_ids": policy.validation_required_step_ids,
                "approvals": linked_approvals,
            })
    return {
        "schema_version": "1.0",
        "status": "inspected",
        "recipes": recipes,
        "recipe_count": len(recipes),
        "inventory_performed": True,
        "recipe_modified": False,
        "approval_performed": False,
        "execution_performed": False,
        **problems.projection(),
    }


# Trusted context kwargs stay outside transport/model request schemas.
from geoagent_harness.core.execution.actions import task_entrypoint as _task_entrypoint
interface_recipe_template_catalog = _task_entrypoint(interface_recipe_template_catalog, audit=False)
plan_interface_task = _task_entrypoint(plan_interface_task)
interface_planner_skill_catalog = _task_entrypoint(interface_planner_skill_catalog, audit=False)
interface_saved_plan_inventory = _task_entrypoint(interface_saved_plan_inventory, audit=False)
compile_interface_recipe_proposal = _task_entrypoint(compile_interface_recipe_proposal, audit=False)
save_interface_reviewed_recipe = _task_entrypoint(save_interface_reviewed_recipe)
interface_saved_recipe_inventory = _task_entrypoint(interface_saved_recipe_inventory, audit=False)
