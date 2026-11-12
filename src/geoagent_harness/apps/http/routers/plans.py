"""Existing plans HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_0_planner_skills(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.interface_planner_skill_catalog(project_root))
    except (route_context.services.InterfaceApiError, route_context.services.SkillRegistryError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'planner skill catalog is unavailable'})
    return RESPONSE_SENT

def get_1_plans(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.interface_saved_plan_inventory(project_root))
    except (route_context.services.InterfaceApiError, route_context.services.ApprovalError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'saved plan inventory is unavailable'})
    return RESPONSE_SENT

def post_2_validate_edit(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.contracts.actions import EditRequest
    from geoagent_harness.capabilities.workflow import validate_edit
    response = validate_edit(EditRequest.model_validate(payload), project_root=project_root)
    return response

def post_3_create(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.plan_interface_task(route_context.services.InterfacePlanRequest.model_validate(payload), project_root=project_root)
    return response

def post_4_save_generated(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    generated = route_context.services.InterfaceGeneratedPlanSaveRequest.model_validate(payload)
    response = route_context.services.save_interface_reviewed_plan(generated, project_root=project_root)
    response['human_review_performed'] = False
    response['storage_kind'] = 'generated_proposal'
    return response

def post_5_save_reviewed(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.save_interface_reviewed_plan(route_context.services.InterfaceReviewedPlanSaveRequest.model_validate(payload), project_root=project_root)
    response['task_reference'] = route_context.services.attach_task_artifact(root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), task_id=payload.get('task_id'), project_root=route_context.services._trusted_root(project_root), artifact_path='plans/' + response['plan_filename'])
    return response

def post_6_prepare_approval(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.prepare_interface_plan_approval(route_context.services.InterfacePlanApprovalPreparationRequest.model_validate(payload), project_root=project_root)
    return response

def post_7_record_approval(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.record_interface_plan_approval(route_context.services.InterfacePlanApprovalDecisionRequest.model_validate(payload), project_root=project_root, approval_root=approval_root)
    response['task_reference'] = route_context.services.attach_task_artifact(root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), task_id=payload.get('task_id'), project_root=route_context.services._trusted_root(project_root), artifact_path='approvals/' + response['approval_filename'])
    return response

def post_8_verify_approval(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.verify_interface_plan_approval(route_context.services.InterfacePlanApprovalVerificationRequest.model_validate(payload), project_root=project_root, approval_root=approval_root)
    return response

def post_9_preview_execution(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.preview_interface_plan_execution(route_context.services.InterfacePlanExecutionPreviewRequest.model_validate(payload), project_root=project_root, approval_root=approval_root)
    return response

def post_10_compile_recipe(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.compile_interface_plan_recipe(route_context.services.InterfacePlanRecipeCompilationRequest.model_validate(payload), project_root=project_root, approval_root=approval_root)
    return response

def post_11_save_reviewed_recipe(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.save_interface_plan_recipe(route_context.services.InterfacePlanRecipeSaveRequest.model_validate(payload), project_root=project_root, approval_root=approval_root, recipe_root=recipe_root)
    response['task_reference'] = route_context.services.attach_task_artifact(root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), task_id=payload.get('task_id'), project_root=route_context.services._trusted_root(project_root), artifact_path='workflow-recipes/' + response['recipe_filename'])
    return response
