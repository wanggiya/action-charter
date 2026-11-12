"""Existing assurance HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_0_critic_evidence(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.interface_critic_evidence_inventory(project_root))
    except (route_context.services.InterfaceApiError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'Critic evidence inventory is unavailable'})
    return RESPONSE_SENT

def post_1_save_adapted_trace(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.save_interface_recipe_trace(route_context.services.InterfaceRecipeTraceSaveRequest.model_validate(payload), project_root=project_root)
    return response

def post_2_run(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.run_interface_critic(route_context.services.InterfaceCriticRunRequest.model_validate(payload), project_root=project_root)
    return response

def post_3_record_result(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.record_interface_critic_result(route_context.services.InterfaceCriticRecordRequest.model_validate(payload), project_root=project_root)
    return response

def post_4_prepare_recipe(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.prepare_interface_recipe_release(route_context.services.InterfaceRecipeReleaseRequest.model_validate(payload), project_root=project_root)
    return response

def post_5_create_recipe(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.create_interface_recipe_release(route_context.services.InterfaceRecipeReleaseCreationRequest.model_validate(payload), project_root=project_root)
    return response

def post_6_preview_export(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.preview_interface_snakemake_export(route_context.services.InterfaceSnakemakeExportPreviewRequest.model_validate(payload), project_root=project_root)
    return response

def post_7_export(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.export_interface_snakemake_recipe(route_context.services.InterfaceSnakemakeExportRequest.model_validate(payload), project_root=project_root)
    return response
