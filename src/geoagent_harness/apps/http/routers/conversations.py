"""Existing conversations HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def post_0_method_memory(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.method_memory import MethodRequest, method_action
    response = method_action(MethodRequest.model_validate(payload), project_root=project_root)
    return response

def post_1_diagnostics(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.platform.model_gateway.telemetry import read as read_diagnostics

    class DiagnosticRequest(BaseModel):
        model_config = ConfigDict(extra='forbid')
        conversation_id: str = Field(pattern='^[a-f0-9]{32}$')
    diagnostic_request = DiagnosticRequest.model_validate(payload)
    response = read_diagnostics(project_root, diagnostic_request.conversation_id)
    return response

def post_2_submit(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.planner_submission import SubmissionRequest, submission_action
    response = submission_action(SubmissionRequest.model_validate(payload), project_root=project_root)
    return response

def post_3_history(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.chat_history import HistoryRequest, history_action
    response = history_action(HistoryRequest.model_validate(payload), project_root=project_root)
    return response

def post_4_conversation(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.conversation import TurnRequest, conversation_turn
    response = conversation_turn(TurnRequest.model_validate(payload), project_root=project_root)
    return response
