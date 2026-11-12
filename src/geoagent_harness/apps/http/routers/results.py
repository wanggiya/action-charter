"""Existing results HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_0_data_resources(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.interface_data_resource_inventory(project_root))
    except (route_context.services.InterfaceApiError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'data resource inventory is unavailable'})
    return RESPONSE_SENT

def post_1_view(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.data.tabular.dataset_views import DatasetViewRequest, dataset_view
    response = dataset_view(DatasetViewRequest.model_validate(payload), project_root=project_root)
    return response
