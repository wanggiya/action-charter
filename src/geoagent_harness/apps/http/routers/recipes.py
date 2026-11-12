"""Existing recipes HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_0_recipe_templates(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.interface_recipe_template_catalog(project_root))
    except (route_context.services.InterfaceApiError, route_context.services.RecipeTemplateCatalogError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'trusted template catalog is unavailable'})
    return RESPONSE_SENT

def get_1_recipes(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.interface_saved_recipe_inventory(project_root=project_root, recipe_root=recipe_root))
    except (route_context.services.InterfaceApiError, route_context.services.RecipePolicyError, route_context.services.RecipeStorageError, route_context.services.SkillRegistryError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'trusted recipe inventory is unavailable'})
    return RESPONSE_SENT

def post_2_compile(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.compile_interface_recipe_proposal(payload, project_root=project_root)
    return response

def post_3_reusable_recipes(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.capabilities.recipes.catalog.composition import RecipeRequest
    from geoagent_harness.task_actions.recipe_catalog import recipe_action
    response = recipe_action(RecipeRequest.model_validate(payload), project_root=project_root)
    return response

def post_4_save_reviewed(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    if not isinstance(payload, dict) or set(payload) != {'proposal', 'confirmed_recipe_sha256', 'action'} or payload.get('action') != 'save_reviewed_recipe':
        raise route_context.services.InterfaceApiError('reviewed save request is invalid')
    response = route_context.services.save_interface_reviewed_recipe(payload['proposal'], confirmed_recipe_sha256=payload['confirmed_recipe_sha256'], project_root=project_root, recipe_root=recipe_root)
    return response

def post_5_prepare_approval(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    if not isinstance(payload, dict) or set(payload) != {'recipe_filename', 'confirmed_recipe_sha256', 'action'} or payload.get('action') != 'prepare_recipe_approval':
        raise route_context.services.InterfaceApiError('approval preparation request is invalid')
    response = route_context.services.prepare_interface_recipe_approval(recipe_filename=payload['recipe_filename'], confirmed_recipe_sha256=payload['confirmed_recipe_sha256'], project_root=project_root, recipe_root=recipe_root)
    return response

def post_6_record_approval(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    decision = route_context.services.InterfaceApprovalDecision.model_validate(payload)
    response = route_context.services.record_interface_recipe_approval(decision, project_root=project_root, recipe_root=recipe_root, approval_root=approval_root)
    return response

def post_7_verify_approval(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    verification_request = route_context.services.InterfaceApprovalVerificationRequest.model_validate(payload)
    response = route_context.services.verify_interface_recipe_approval(verification_request, project_root=project_root, recipe_root=recipe_root, approval_root=approval_root)
    return response

def post_8_preview_execution(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    preview_request = route_context.services.InterfaceExecutionPreviewRequest.model_validate(payload)
    response = route_context.services.prepare_interface_execution_preview(preview_request, project_root=project_root, recipe_root=recipe_root, approval_root=approval_root)
    return response

def post_9_execute(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    execution_request = route_context.services.InterfaceRecipeExecutionRequest.model_validate(payload)
    response = route_context.services.execute_interface_recipe_with_task_references(execution_request, project_root=project_root, recipe_root=recipe_root, approval_root=approval_root, task_root=task_root, execute_recipe=route_context.services.execute_interface_recipe)
    return response
