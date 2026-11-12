"""Existing runs HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_0_executions(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.interface_execution_inventory(project_root))
    except (route_context.services.InterfaceApiError, OSError, ValueError, json.JSONDecodeError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'execution inventory is unavailable'})
    return RESPONSE_SENT

def get_progress_match(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    progress_match = match
    digest = progress_match.group(1)
    try:
        payload = route_context.services.interface_execution_progress(project_root, digest)
    except route_context.services.InterfaceProgressUnavailable:
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'execution progress is unavailable'})
        return RESPONSE_SENT
    if payload is None:
        self._send(HTTPStatus.NOT_FOUND, {'error': 'execution progress is not available'})
    else:
        self._send(HTTPStatus.OK, payload)
    return RESPONSE_SENT

def get_2_inspection_runs(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.workflow import inspection_inventory
    try:
        self._send(HTTPStatus.OK, inspection_inventory(project_root=project_root))
    except (route_context.services.InterfaceApiError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'inspection history unavailable'})
    return RESPONSE_SENT
