"""Existing workflows HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def post_0_runs(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.workflow_runs import RunRequest, run_action
    response = run_action(RunRequest.model_validate(payload), project_root=project_root)
    return response

def post_1_prepare(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.workflow import WorkflowRequest, prepare_workflow, authorize_workflow, execute_workflow
    workflow_request = WorkflowRequest.model_validate(payload)
    expected_action = {'prepare': 'prepare_workflow', 'authorize': 'authorize_workflow', 'execute': 'execute_workflow'}[self.path.rsplit('/', 1)[-1]]
    if workflow_request.action != expected_action:
        raise route_context.services.InterfaceApiError('workflow action does not match endpoint')
    response = {'prepare_workflow': prepare_workflow, 'authorize_workflow': authorize_workflow, 'execute_workflow': execute_workflow}[expected_action](workflow_request, project_root=project_root)
    return response
