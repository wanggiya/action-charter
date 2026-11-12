"""Existing history HTTP adapters; shared actions retain execution authority."""
from __future__ import annotations
from http import HTTPStatus
import json
import re
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from geoagent_harness.apps.http.context import RESPONSE_SENT

def get_0_tasks(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    try:
        self._send(HTTPStatus.OK, route_context.services.inspect_task_inventory(root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history')))
    except (route_context.services.TaskHistoryError, OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'task inventory is unavailable'})
    return RESPONSE_SENT

def get_task_match(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    task_match = match
    try:
        self._send(HTTPStatus.OK, route_context.services.inspect_interface_task_context(project_root=project_root, task_id=task_match.group(1), task_root=task_root))
    except route_context.services.TaskHistoryError:
        self._send(HTTPStatus.NOT_FOUND, {'error': 'task context is unavailable'})
    except (OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'task context could not be loaded'})
    return RESPONSE_SENT

def get_relationship_match(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    relationship_match = match
    from geoagent_harness.core.ledger.task_history.relationships import inspect_task_relationships
    try:
        self._send(HTTPStatus.OK, inspect_task_relationships(root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), task_id=relationship_match.group(1), project_root=route_context.services._trusted_root(project_root)))
    except route_context.services.TaskHistoryError:
        self._send(HTTPStatus.NOT_FOUND, {'error': 'task relationship inspection is unavailable'})
    except (OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'task relationships could not be inspected'})
    return RESPONSE_SENT

def get_artifact_match(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    artifact_match = match
    try:
        self._send(HTTPStatus.OK, route_context.services.inspect_task_artifacts(root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), task_id=artifact_match.group(1), project_root=route_context.services._trusted_root(project_root)))
    except route_context.services.TaskHistoryError:
        self._send(HTTPStatus.NOT_FOUND, {'error': 'task artifact inspection is unavailable'})
    except (OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'task evidence could not be inspected'})
    return RESPONSE_SENT

def get_4_reviewed_context_inventory(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.agents.roles.intent.inventory import reviewed_context_inventory
    try:
        self._send(HTTPStatus.OK, reviewed_context_inventory(project_root=route_context.services._trusted_root(project_root)))
    except (OSError, ValueError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'review inventory is unavailable'})
    return RESPONSE_SENT

def get_review_match(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    review_match = match
    from geoagent_harness.agents.memory.context_retrieval import load_reviewed_context, ContextReviewError
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    try:
        self._send(HTTPStatus.OK, load_reviewed_context(review_root=route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'reviewed-contexts'), history_root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), filename=review_match.group(1)))
    except (ContextReviewError, ContextRetrievalError, OSError, ValueError, KeyError):
        self._send(HTTPStatus.CONFLICT, {'error': 'reviewed context is unavailable or stale; retrieve and review again'})
    return RESPONSE_SENT

def get_intent_review_match(self, route_context, match=None):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    intent_review_match = match
    from geoagent_harness.agents.roles.intent.review import load_reviewed_intent
    try:
        self._send(HTTPStatus.OK, load_reviewed_intent(project_root=route_context.services._trusted_root(project_root), filename=intent_review_match.group(1)))
    except (OSError, ValueError, KeyError):
        self._send(HTTPStatus.CONFLICT, {'error': 'reviewed intent is unavailable, invalid or stale; inspect and review again', 'execution_performed': False})
    return RESPONSE_SENT

def post_7_retrieve(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.agents.memory.context_retrieval import retrieve_task_context, ContextRetrievalError
    context_request = route_context.services.InterfaceContextRetrievalRequest.model_validate(payload)
    try:
        response = retrieve_task_context(root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), query=context_request.query, task_ids=context_request.task_ids)
    except ContextRetrievalError as exc:
        self._send(HTTPStatus.BAD_REQUEST, {'error': str(exc)})
        return RESPONSE_SENT
    return response

def post_8_review(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.agents.memory.context_retrieval import save_reviewed_context, ContextReviewError
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    review_request = route_context.services.InterfaceContextReviewRequest.model_validate(payload)
    try:
        response = save_reviewed_context(history_root=task_root if task_root is not None else route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'task-history'), review_root=route_context.services.runtime_store_path(route_context.services._trusted_root(project_root), 'reviewed-contexts'), query=review_request.query, task_ids=review_request.task_ids, confirmed_context_sha256=review_request.confirmed_context_sha256, reviewer=review_request.reviewer, reason=review_request.reason)
    except (ContextReviewError, ContextRetrievalError) as exc:
        self._send(HTTPStatus.CONFLICT, {'error': str(exc)})
        return RESPONSE_SENT
    return response

def post_9_reason(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.agents.roles.intent.service import reason_task_intent
    from geoagent_harness.contracts.intent import IntentError
    from geoagent_harness.agents.memory.context_retrieval import ContextReviewError
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    intent_request = route_context.services.InterfaceIntentRequest.model_validate(payload)
    try:
        response = reason_task_intent(project_root=route_context.services._trusted_root(project_root), history_root=task_root, review_filename=intent_request.review_filename, request=intent_request.request, clarification_answers=intent_request.clarification_answers, selected_input_path=intent_request.selected_input_path)
    except (ContextReviewError, ContextRetrievalError, OSError, KeyError) as exc:
        self._send(HTTPStatus.CONFLICT, {'error': 'reviewed context is unavailable or stale; retrieve and review again', 'execution_performed': False})
        return RESPONSE_SENT
    except IntentError as exc:
        self._send(HTTPStatus.BAD_REQUEST, {'error': str(exc), 'execution_performed': False})
        return RESPONSE_SENT
    except (route_context.services.ModelClientError, route_context.services.ModelSettingsError) as exc:
        from geoagent_harness.platform.model_gateway.diagnostics import model_failure
        self._send(HTTPStatus.BAD_GATEWAY, model_failure(exc))
        return RESPONSE_SENT
    return response

def post_10_inspect(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    from geoagent_harness.agents.roles.intent.review import inspect_intent_for_review, save_reviewed_intent
    from geoagent_harness.agents.roles.intent.handoff import plan_reviewed_intent, save_reviewed_intent_plan
    from geoagent_harness.contracts.intent import IntentError
    from geoagent_harness.agents.memory.context_retrieval import ContextReviewError
    from geoagent_harness.agents.memory.context_retrieval import ContextRetrievalError
    try:
        if self.path == '/api/v1/intent/inspect':
            inspected = route_context.services.InterfaceIntentInspectionRequest.model_validate(payload)
            response = inspect_intent_for_review(payload=inspected.intent, project_root=route_context.services._trusted_root(project_root))
        elif self.path == '/api/v1/intent/review':
            confirmed = route_context.services.InterfaceIntentReviewRequest.model_validate(payload)
            response = save_reviewed_intent(payload=confirmed.intent, project_root=route_context.services._trusted_root(project_root), confirmed_intent_sha256=confirmed.confirmed_intent_sha256, reviewer=confirmed.reviewer, reason=confirmed.reason)
        elif self.path == '/api/v1/intent/save-plan':
            saving = route_context.services.InterfaceIntentPlanSaveRequest.model_validate(payload)
            response = save_reviewed_intent_plan(project_root=route_context.services._trusted_root(project_root), filename=saving.review_filename, planner_result=saving.planner_result, confirmed_plan_sha256=saving.confirmed_plan_sha256, save_plan=route_context.services.save_interface_reviewed_plan)
        else:
            handoff = route_context.services.InterfaceIntentHandoffRequest.model_validate(payload)
            response = plan_reviewed_intent(project_root=route_context.services._trusted_root(project_root), filename=handoff.review_filename, allowed_skill_ids=handoff.allowed_skill_ids)
    except (ContextReviewError, ContextRetrievalError, OSError, KeyError):
        self._send(HTTPStatus.CONFLICT, {'error': 'reviewed intent/context is unavailable or stale; inspect and review again', 'execution_performed': False})
        return RESPONSE_SENT
    except IntentError as exc:
        status = HTTPStatus.CONFLICT if 'already exists' in str(exc) or 'changed' in str(exc) else HTTPStatus.BAD_REQUEST
        self._send(status, {'error': route_context.services.redact_text(str(exc)), 'execution_performed': False})
        return RESPONSE_SENT
    except (route_context.services.ModelClientError, route_context.services.ModelSettingsError) as exc:
        from geoagent_harness.platform.model_gateway.diagnostics import model_failure
        self._send(HTTPStatus.BAD_GATEWAY, model_failure(exc))
        return RESPONSE_SENT
    return response

def post_11_events(self, route_context, payload):
    project_root = route_context.project_root
    recipe_root = route_context.recipe_root
    approval_root = route_context.approval_root
    task_root = route_context.task_root
    response = route_context.services.record_interface_task_event(route_context.services.InterfaceTaskEventRequest.model_validate(payload), project_root=project_root, task_root=task_root)
    return response
