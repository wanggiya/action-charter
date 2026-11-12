"""HTTP application composition and historical public service exports."""
from __future__ import annotations
from geoagent_harness.platform.paths import runtime_store_path, ensure_state_root
from geoagent_harness.platform.workspace import WorkspaceLayout, runtime_reference, runtime_reference_path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
from geoagent_harness.platform.storage import repositories
import json
import os
from pathlib import Path
import re
import tempfile
from threading import Lock
from typing import Any, Callable, Literal
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from geoagent_harness.capabilities.recipes.catalog import RecipeTemplateCatalogError, load_recipe_template_catalog
from geoagent_harness.capabilities.recipes.proposals.compiler import RecipeCompilationError, compile_recipe_proposal
from geoagent_harness.capabilities.recipes.proposals.schemas import RecipeProposal
from geoagent_harness.platform.skill_registry import SkillRegistryError, load_skill_registry
from geoagent_harness.contracts.redaction import redact_text, redact_value
from geoagent_harness.agents.memory.context_pack import ContextPackError
from geoagent_harness.core.ledger.task_history import TaskHistoryError, append_task_event, build_task_context, load_task_events, inspect_task_inventory, inspect_task_artifacts, attach_task_artifact, record_task_attempt_state
from geoagent_harness.platform.evidence import CriticEvidenceError, MAX_TRACE_BYTES, MAX_REPORT_BYTES, build_critic_evidence
from geoagent_harness.agents.roles.critic.recipe_trace import RecipeTraceAdapterError, build_recipe_trace_candidate, persist_recipe_trace_candidate, recipe_trace_sha256, render_recipe_trace_report
from geoagent_harness.agents.roles.critic import CriticAgentError
from geoagent_harness.agents.roles.critic import critique_task
from geoagent_harness.contracts.critic import CriticResult
from geoagent_harness.platform.storage.critic_records import CriticResultRecordError, build_critic_result_record, critic_result_sha256
from geoagent_harness.platform.storage.critic_record_storage import CriticResultStorageError, load_critic_result_record, persist_critic_result_record
from geoagent_harness.core.ledger.trace import WorkflowTrace
from geoagent_harness.platform.model_gateway import ModelClientError
from geoagent_harness.platform.model_gateway import ModelSettingsError
from geoagent_harness.agents.roles.planner import PlannerAgentError
from geoagent_harness.agents.roles.planner import PlannerPolicyError, validate_plan_policy
from geoagent_harness.agents.roles.planner import PlannerResult
from geoagent_harness.agents.roles.executor import ExecutorPolicyError, build_execution_envelope
from geoagent_harness.core.policy.approvals import ApprovalError, create_approval, load_approval, load_planner_result, plan_sha256, verify_approval
from geoagent_harness.core.policy.approvals.schemas import ApprovalRecord
from geoagent_harness.task_actions.approved_recipe import ApprovedRecipeError, run_approved_recipe as execute_approved_recipe
from geoagent_harness.platform.settings import load_settings
from geoagent_harness.core.policy.write_policy import effective as effective_write_settings, snapshot as write_policy_snapshot, session as write_policy_session, update as update_write_policy, PolicyUpdate, WritePolicyError
from geoagent_harness.capabilities.recipes.execution import RecipeApprovalError, create_recipe_approval, load_recipe_approval, verify_recipe_approval
from geoagent_harness.capabilities.recipes.execution import RecipeEvidenceStorageError, load_recipe_evidence, load_recipe_run_result, recipe_evidence_sha256, recipe_run_result_sha256
from geoagent_harness.capabilities.recipes.execution import RecipePolicyError, validate_recipe_policy
from geoagent_harness.capabilities.recipes.execution import RecipeStorageError, load_recipe, recipe_path, save_recipe
from geoagent_harness.capabilities.recipes.execution import recipe_sha256
from geoagent_harness.capabilities.recipes.execution import build_recipe_execution_envelope
from geoagent_harness.contracts.recipes import RecipeStep, WorkflowRecipe
from geoagent_harness.core.ledger.releases import AuthoritativeReleaseStorageError, load_authoritative_release, persist_authoritative_release
from geoagent_harness.core.ledger.releases import ReleaseAssessmentError, assess_recipe_release_candidate, authoritative_release_candidate_sha256
from geoagent_harness.core.ledger.operational_history import AgentRole, OperationalIdentity
from geoagent_harness.core.ledger.operational_history import OperationalHistoryError, operational_event_log_path
from geoagent_harness.core.ledger.operational_history import record_gis_workflow_history
from geoagent_harness.capabilities.recipes.execution import recipe_run_result_path
from geoagent_harness.data.export.snakemake.contracts import SnakemakeExportContractError, validate_snakemake_export_contract
from geoagent_harness.data.export.snakemake.generator import SnakemakeExportGenerationError, generate_snakemake_recipe_export
from geoagent_harness.data.export.snakemake.planner import SnakemakeExportPolicyError, plan_snakemake_recipe_export
from geoagent_harness.contracts.errors import InterfaceApiError
from geoagent_harness.platform.project import _trusted_root
from geoagent_harness.platform.outcomes import _bounded_outcome
from geoagent_harness.contracts.actions import InterfaceApprovalDecision, InterfaceApprovalVerificationRequest, InterfaceExecutionPreviewRequest, InterfaceRecipeExecutionRequest, InterfaceReviewedPlanSaveRequest, InterfaceGeneratedPlanSaveRequest, InterfacePlanApprovalPreparationRequest, InterfacePlanApprovalDecisionRequest, InterfacePlanApprovalVerificationRequest, InterfacePlanExecutionPreviewRequest, InterfacePlanRecipeCompilationRequest, InterfacePlanRecipeSaveRequest
from geoagent_harness.task_actions.artifacts import save_interface_reviewed_plan, prepare_interface_plan_approval, record_interface_plan_approval, verify_interface_plan_approval, preview_interface_plan_execution, compile_interface_plan_recipe, _planner_recipe_definition, save_interface_plan_recipe, prepare_interface_recipe_approval, record_interface_recipe_approval, verify_interface_recipe_approval
from geoagent_harness.task_actions.execution import _progress_path, _persist_execution_progress, _load_execution_progress, interface_execution_inventory, prepare_interface_execution_preview, execute_interface_recipe, _EXECUTION_LOCK, _ACTIVE_EXECUTIONS, _ACTIVE_PROGRESS, _EXECUTION_PROGRESS

import sys
from geoagent_harness.apps.http.context import RequestContext
from geoagent_harness.apps.http.transport import make_handler
from geoagent_harness.contracts.interface_requests import (
    InterfaceContextRetrievalRequest,
    InterfaceContextReviewRequest,
    InterfaceIntentRequest,
    InterfaceIntentInspectionRequest,
    InterfaceIntentReviewRequest,
    InterfaceIntentHandoffRequest,
    InterfaceIntentPlanSaveRequest,
    InterfaceTaskEventRequest,
    InterfacePlanRequest,
    InterfaceRecipeTraceSaveRequest,
    InterfaceCriticRunRequest,
    InterfaceCriticRecordRequest,
    InterfaceRecipeReleaseRequest,
    InterfaceRecipeReleaseCreationRequest,
    InterfaceSnakemakeExportPreviewRequest,
    InterfaceSnakemakeExportRequest,
)
from geoagent_harness.contracts.interface_limits import (
    MAX_INTERFACE_REQUEST_BYTES,
    MAX_INTERFACE_RECIPES,
    MAX_INTERFACE_PLANS,
    MAX_INTERFACE_PLAN_APPROVALS,
    MAX_INTERFACE_EXECUTION_ATTEMPTS,
    SAFE_RECIPE_FILENAME,
    LOOPBACK_HOST,
    MAX_INTERFACE_OUTCOME_BYTES,
    MAX_INTERFACE_DATA_RESOURCES,
    MAX_INTERFACE_CRITIC_EVIDENCE,
    INTERFACE_DATA_EXTENSIONS,
)
from geoagent_harness.task_actions.resource_catalogs import (
    interface_data_resource_inventory,
)
from geoagent_harness.task_actions.critic_review import (
    interface_critic_evidence_inventory,
    _exact_recipe_progress,
    _stored_trace_pair_exact,
    _interface_recipe_trace_candidates,
    save_interface_recipe_trace,
    run_interface_critic,
    record_interface_critic_result,
)
from geoagent_harness.task_actions.release_review import (
    _recipe_release_candidate,
    prepare_interface_recipe_release,
    create_interface_recipe_release,
)
from geoagent_harness.task_actions.legacy_planning import (
    interface_recipe_template_catalog,
    _normalize_interface_recipe_paths,
    plan_interface_task,
    interface_planner_skill_catalog,
    interface_saved_plan_inventory,
    compile_interface_recipe_proposal,
    save_interface_reviewed_recipe,
    interface_saved_recipe_inventory,
)
from geoagent_harness.task_actions.legacy_export import (
    _snakemake_export_plan,
    preview_interface_snakemake_export,
    export_interface_snakemake_recipe,
)
from geoagent_harness.task_actions.task_context import (
    record_interface_task_event,
    inspect_interface_task_context,
)
from geoagent_harness.task_actions.execution import (
    InterfaceProgressUnavailable,
    interface_execution_progress,
    execute_interface_recipe_with_task_references,
)


def _handler(project_root: Path, recipe_root: Path | None = None,
             approval_root: Path | None = None, task_root: Path | None = None) -> type[BaseHTTPRequestHandler]:
    return make_handler(RequestContext(project_root, recipe_root, approval_root,
                                       task_root, sys.modules[__name__]))


def serve_interface_api(
    *,
    project_root: Path,
    host: str = LOOPBACK_HOST,
    port: int = 8765,
    server_factory: Callable[..., ThreadingHTTPServer] = ThreadingHTTPServer,
) -> None:
    """Serve the non-mutating API and refuse non-loopback binding."""

    if host != LOOPBACK_HOST:
        raise InterfaceApiError("interface API must bind to 127.0.0.1")
    if port < 1 or port > 65_535:
        raise InterfaceApiError("interface API port is invalid")
    root = _trusted_root(project_root)
    from geoagent_harness.platform.settings import parse_flag
    with write_policy_session(root, enabled=load_settings().enable_write_tools,
            locked=parse_flag(os.environ.get('ACTIONCHARTER_READ_ONLY_LOCK'))):
        server = server_factory((host, port), _handler(root))
        try:
            server.serve_forever()
        finally:
            server.server_close()
