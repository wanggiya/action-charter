"""Read-only exact plan/approval relationships in explicitly recorded task evidence."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from .service import TaskHistoryError, _artifact_bytes, _digest, load_task_events


def inspect_task_relationships(*, root: Path, task_id: str, project_root: Path,
                               now: datetime | None = None, registry: Any = None) -> dict[str, Any]:
    # Reuse authoritative artifact schemas and the existing approval verifier.
    from geoagent_harness.planner.schemas import PlannerResult
    from geoagent_harness.approvals.schemas import ApprovalRecord
    from geoagent_harness.approvals.service import plan_sha256, verify_approval
    from pydantic import ValidationError
    from geoagent_harness.recipes.schemas import WorkflowRecipe, RecipeRunResult, RecipeApprovalRecord
    from geoagent_harness.recipes.evidence_schemas import RecipeRunEvidence
    from geoagent_harness.recipes.digest import recipe_sha256
    from geoagent_harness.planner.recipe_definition import planner_recipe_definition, PlannerRecipeDefinitionError
    events = load_task_events(root=root, task_id=task_id)
    if not events:
        raise TaskHistoryError("task history does not exist")
    plans, approvals, recipes, results, evidence, recipe_approvals, findings = {}, {}, {}, {}, {}, {}, []
    for event in events:
        payload = event["payload"]
        path, expected = payload["artifact_path"], payload["artifact_sha256"]
        if path is None and expected is None:
            continue
        if not isinstance(path, str) or not isinstance(expected, str):
            findings.append({"sequence": event["sequence"], "reason": "Invalid artifact reference"})
            continue
        try:
            raw = _artifact_bytes(project_root, path)
            if _digest(raw) != expected:
                raise TaskHistoryError("artifact bytes changed")
            data = json.loads(raw)
            if path.startswith("plans/planner-plan."):
                result = PlannerResult.model_validate(data)
                digest = plan_sha256(result.plan)
                if path != f"plans/planner-plan.{digest}.json":
                    raise TaskHistoryError("plan filename does not match canonical plan")
                plans[path] = (result, digest)
            elif path.startswith("approvals/approval-"):
                approval = ApprovalRecord.model_validate(data)
                if path != f"approvals/{approval.approval_id}.json":
                    raise TaskHistoryError("approval filename does not match identity")
                approvals[path] = approval
            elif path.startswith("approvals/recipe-approval-"):
                approval = RecipeApprovalRecord.model_validate(data)
                if path != f"approvals/{approval.approval_id}.json":
                    raise TaskHistoryError("recipe approval filename conflicts with identity")
                recipe_approvals[path] = approval
            elif path.startswith("workflow-recipes/"):
                recipe = WorkflowRecipe.model_validate(data)
                if path != f"workflow-recipes/{recipe.recipe_id}.{recipe_sha256(recipe)}.json":
                    raise TaskHistoryError("recipe filename does not match exact definition")
                recipes[path] = recipe
            elif path.startswith("recipe-runs/"):
                results[path] = RecipeRunResult.model_validate(data)
            elif path.startswith("recipe-evidence/"):
                evidence[path] = RecipeRunEvidence.model_validate(data)
        except (OSError, ValueError, ValidationError, TaskHistoryError):
            findings.append({"sequence": event["sequence"], "reason": "Evidence unavailable, altered or schema-invalid"})
    relationships = []
    for approval_path, approval in approvals.items():
        matching = [(path, result.plan) for path, (result, digest) in plans.items() if digest == approval.plan_sha256]
        if len(matching) != 1:
            relationships.append({"approval_path": approval_path, "plan_path": None,
                                  "relationship": "unlinked", "decision_verified": False,
                                  "reason": "No unique exact plan recorded in this task"})
            continue
        plan_path, plan = matching[0]
        required = [step.step_id for step in plan.steps if step.requires_approval]
        verification = verify_approval(approval=approval, plan=plan, required_step_ids=required, now=now)
        exact_scope = set(approval.step_ids) == set(required) and len(approval.step_ids) == len(set(approval.step_ids)) and bool(required)
        relationships.append({"approval_path": approval_path, "plan_path": plan_path,
                              "relationship": "exact_plan", "decision": approval.decision,
                              "decision_verified": verification.approved and exact_scope,
                              "reason": verification.reason if exact_scope else "Recorded step scope differs from this plan's required scope"})
    recipe_relationships = []
    for recipe_path, recipe in recipes.items():
        matching = []
        for plan_path, (result, digest) in plans.items():
            try:
                expected_recipe = planner_recipe_definition(result, digest)
            except PlannerRecipeDefinitionError:
                continue
            if recipe.model_dump(mode="json") == expected_recipe.model_dump(mode="json"):
                matching.append(plan_path)
        exact = len(matching) == 1
        recipe_relationships.append({"recipe_path": recipe_path,
            "plan_path": matching[0] if exact else None,
            "relationship": "exact_definition" if exact else "unlinked",
            "reason": "Recipe matches the complete deterministic source-plan definition" if exact else "No unique exact source-plan definition recorded in this task",
            "execution_authorized": False})
    execution_approval_relationships = []
    for approval_path, approval in recipe_approvals.items():
        matching = [(path, recipe) for path, recipe in recipes.items() if recipe_sha256(recipe) == approval.recipe_sha256]
        verified, reason = False, "No unique exact recipe recorded in this task"
        if len(matching) == 1:
            from geoagent_harness.recipes.approval import verify_recipe_approval, RecipeApprovalError
            from geoagent_harness.skill_registry import load_skill_registry, SkillRegistryError
            try:
                checked = verify_recipe_approval(approval=approval, recipe=matching[0][1],
                    registry=registry if registry is not None else load_skill_registry(project_root), now=now)
                verified, reason = checked.approved, checked.reason
            except (RecipeApprovalError, SkillRegistryError, OSError, ValueError):
                reason = "Current recipe policy or registry could not be verified"
        execution_approval_relationships.append({"approval_path": approval_path,
            "recipe_path": matching[0][0] if len(matching) == 1 else None,
            "relationship": "exact_recipe" if len(matching) == 1 else "unlinked",
            "decision": approval.decision, "decision_verified_now": verified,
            "reason": reason, "execution_authorized": False})
    outcome_relationships = []
    for result_path, result in results.items():
        matching_recipes = [(path, recipe) for path, recipe in recipes.items()
                            if recipe.recipe_id == result.recipe_id and recipe_sha256(recipe) == result.recipe_sha256]
        matching_evidence = [path for path, item in evidence.items()
                             if item.run_result.model_dump(mode="json") == result.model_dump(mode="json")]
        step_match = False
        if len(matching_recipes) == 1:
            recipe = matching_recipes[0][1]
            actual = [(step.step_id, step.skill_id) for step in result.step_results]
            expected = [(step.step_id, step.skill_id) for step in recipe.steps]
            step_match = actual == expected if result.final_status == "validated_success" else actual == expected[:len(actual)]
            step_match = step_match and all(
                step.execution.step_id == step.step_id and step.execution.skill_id == step.skill_id
                and step.execution.output_ids == recipe.steps[index].output_ids
                for index, step in enumerate(result.step_results)
            )
        if result.final_status == "validated_success":
            status_match = result.failed_step_id is None and all(step.status != "validation_failed" for step in result.step_results)
        else:
            status_match = result.step_results[-1].status == "validation_failed" and result.failed_step_id == result.step_results[-1].step_id
        exact = len(matching_recipes) == 1 and len(matching_evidence) == 1 and step_match and status_match
        matching_approvals = [path for path, approval in recipe_approvals.items()
                              if approval.approval_id == result.approval_id and approval.recipe_sha256 == result.recipe_sha256]
        outcome_relationships.append({"result_path": result_path,
            "execution_approval_path": matching_approvals[0] if len(matching_approvals) == 1 else None,
            "execution_approval_link": "exact_identity" if len(matching_approvals) == 1 else "unlinked",
            "recipe_path": matching_recipes[0][0] if len(matching_recipes) == 1 else None,
            "evidence_path": matching_evidence[0] if len(matching_evidence) == 1 else None,
            "relationship": "exact_recorded_outcome" if exact else "unlinked",
            "final_status": result.final_status,
            "reason": "Exact recipe identity, step sequence and embedded evidence result match" if exact else "Missing, ambiguous or inconsistent recorded recipe/result/evidence relationship",
            "execution_authorized": False, "live_outputs_reverified": False})
    return {"schema_version": "1.0", "task_id": task_id, "relationships": relationships,
            "execution_approval_relationships": execution_approval_relationships,
            "recipe_relationships": recipe_relationships, "outcome_relationships": outcome_relationships,
            "findings": findings, "verification_scope": "recorded_plan_approval_recipe_and_outcome",
            "execution_authorized": False, "approval_recorded": False,
            "execution_performed": False, "model_called": False}
