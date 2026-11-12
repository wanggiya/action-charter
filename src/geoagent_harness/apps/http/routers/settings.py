"""Existing settings HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_0_health(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.task_actions.conversation import PLANNER_CONTRACT_REVISION
    from geoagent_harness.task_actions.inspection_planning import ANALYTICAL_PLANNING_REVISION
    execution_enabled = route_context.services.effective_write_settings(route_context.services.load_settings(), project_root).enable_write_tools
    self._send(HTTPStatus.OK, {'schema_version': '1.0', 'status': 'ready', 'bound_to_loopback': True, 'planner_contract_revision': PLANNER_CONTRACT_REVISION, 'inspection_on_send_revision': 'inspection-batch-v5', 'result_exploration_revision': 'typed-views-v1', 'analytical_table_revision': 'table-analysis-v1', 'analytical_planning_revision': ANALYTICAL_PLANNING_REVISION, 'analytical_loop_revision': 'bounded-analyst-v1', 'model_selection_revision': 'ollama-selection-v1', 'planner_correction_limit': 1, 'write_authority': 'bounded_recipe_and_approval_evidence', 'execution_authority': execution_enabled, 'execution_mode': 'exact_approved_recipe' if execution_enabled else 'disabled'})
    return RESPONSE_SENT

def get_1_write_policy(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.write_policy_snapshot(project_root) or {'active': False, 'enabled': False, 'locked': True, 'execution_performed': False})
    except (route_context.services.WritePolicyError, OSError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'Write policy unavailable; no permission granted', 'execution_performed': False})
    return RESPONSE_SENT

def get_2_model_status(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.platform.model_gateway.diagnostics import inspect_model_configuration
    from geoagent_harness.platform.model_gateway.catalog import request_selection
    with request_selection(project_root):
        self._send(HTTPStatus.OK, inspect_model_configuration())
    return RESPONSE_SENT

def get_3_models(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.platform.model_gateway.catalog import catalog, CatalogError
    try:
        self._send(HTTPStatus.OK, catalog(project_root))
    except (CatalogError, route_context.services.ModelSettingsError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'Ollama discovery unavailable. Check the configured endpoint and service. No model call or download occurred.'})
    return RESPONSE_SENT

def post_4_select(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.platform.model_gateway.catalog import select, Selection, CatalogError
    try:
        response = select(project_root, Selection.model_validate(payload))
    except CatalogError as error:
        self._send(HTTPStatus.CONFLICT, {'error': str(error), 'execution_performed': False})
        return RESPONSE_SENT
    return response

def post_5_reasoning(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.platform.model_gateway.catalog import select_reasoning, ReasoningSelection, CatalogError
    try:
        response = select_reasoning(project_root, ReasoningSelection.model_validate(payload))
    except CatalogError as error:
        self._send(HTTPStatus.CONFLICT, {'error': str(error), 'execution_performed': False})
        return RESPONSE_SENT
    return response

def post_6_review_timeout(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.platform.model_gateway.catalog import select_review_timeout, ReviewTimeoutSelection, CatalogError
    try:
        response = select_review_timeout(project_root, ReviewTimeoutSelection.model_validate(payload))
    except CatalogError as error:
        self._send(HTTPStatus.CONFLICT, {'error': str(error), 'execution_performed': False})
        return RESPONSE_SENT
    return response

def post_7_write_policy(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.update_write_policy(project_root, route_context.services.PolicyUpdate.model_validate(payload))
    return response
