"""Existing ordered HTTP exception responses, without changing policy decisions."""
from __future__ import annotations
from http import HTTPStatus
import json
from pydantic import ValidationError
from geoagent_harness.contracts.redaction import redact_text

def send_post_error(self, route_context, exc):
    from geoagent_harness.contracts.task_context import DuplicateAction, ActionStorageError
    if isinstance(exc, DuplicateAction):
        self._send(HTTPStatus.CONFLICT, {'error':str(exc),'code':'action_already_claimed',
            'action_run_id':exc.run_id,'action_id':exc.identity,'previous_action_status':exc.status,
            'dispatch_performed':False})
        return True
    if isinstance(exc, ActionStorageError):
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error':str(exc),'code':'action_storage_uncertain',
            'execution_status':'unconfirmed','retry_automatically':False})
        return True
    if isinstance(exc, (json.JSONDecodeError, ValidationError)):
        self._send(HTTPStatus.BAD_REQUEST, {'error': 'request payload is invalid', **({'approval_performed': False, 'execution_performed': False} if self.path == '/api/v1/method-memory' else {})})
        return True
    if isinstance(exc, route_context.services.RecipeCompilationError):
        self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': 'recipe proposal could not be compiled'})
        return True
    if isinstance(exc, route_context.services.InterfaceApiError):
        status = HTTPStatus.CONFLICT if 'digest no longer matches' in str(exc) or 'already exists' in str(exc) else HTTPStatus.BAD_REQUEST
        self._send(status, {'error': str(exc), **({'approval_performed': False, 'execution_performed': False} if self.path == '/api/v1/method-memory' else {})})
        return True
    if isinstance(exc, route_context.services.TaskHistoryError):
        self._send(HTTPStatus.CONFLICT, {'error': str(exc)})
        return True
    if isinstance(exc, route_context.services.RecipeStorageError):
        self._send(HTTPStatus.CONFLICT, {'error': 'reviewed recipe could not be stored immutably'})
        return True
    if isinstance(exc, route_context.services.RecipeApprovalError):
        self._send(HTTPStatus.CONFLICT, {'error': 'recipe approval could not be recorded'})
        return True
    if isinstance(exc, route_context.services.ApprovedRecipeError):
        from geoagent_harness.task_actions.workflow import execution_failure_payload
        self._send(HTTPStatus.CONFLICT, execution_failure_payload(exc))
        return True
    if isinstance(exc, route_context.services.CriticAgentError):
        self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': 'Critic model did not produce a policy-valid assessment', 'finding': route_context.services.redact_text(str(exc))[:500], 'critic_result_recorded': False, 'release_created': False, 'execution_performed': False})
        return True
    if isinstance(exc, route_context.services.CriticEvidenceError):
        self._send(HTTPStatus.CONFLICT, {'error': 'stored Critic evidence failed deterministic verification', 'critic_result_recorded': False, 'release_created': False, 'execution_performed': False})
        return True
    if isinstance(exc, (route_context.services.CriticResultRecordError, route_context.services.CriticResultStorageError)):
        self._send(HTTPStatus.CONFLICT, {'error': 'Critic result could not be recorded immutably', 'critic_result_recorded': False, 'release_created': False, 'execution_performed': False})
        return True
    if isinstance(exc, (route_context.services.ReleaseAssessmentError, route_context.services.AuthoritativeReleaseStorageError, route_context.services.OperationalHistoryError, route_context.services.SnakemakeExportContractError, route_context.services.SnakemakeExportGenerationError, route_context.services.SnakemakeExportPolicyError)):
        self._send(HTTPStatus.CONFLICT, {'error': str(exc), 'release_created': False, 'execution_performed': False})
        return True
    if isinstance(exc, route_context.services.PlannerAgentError):
        from geoagent_harness.platform.model_gateway.telemetry import error_code as diagnostic_error_code
        message = str(exc)
        if getattr(exc, 'reason', None) == 'unverified_reuse_claim':
            error = 'planner claimed unverified recipe reuse'
            code = 'planner_reuse_unverified'
            finding = '; '.join(exc.findings)
        elif getattr(exc, 'reason', None) == 'request_coverage_incomplete':
            error = 'planner omitted a requested operation'
            code = 'planner_scope_incomplete'
            finding = '; '.join(exc.findings)
        elif getattr(exc, 'reason', None) == 'schema_repair_deferred':
            error = 'planner did not return the requested workflow'
            code = 'planner_repair_deferred'
            finding = '; '.join(exc.findings) or 'The model repeated a schema-repair promise after one correction.'
        elif getattr(exc, 'reason', None) == 'output_truncated':
            error = 'planner response hit the model output limit'
            code = 'planner_output_truncated'
            finding = '; '.join(exc.findings)
        elif getattr(exc, 'reason', None) == 'capability_gap_unresolved':
            error = 'planner could not resolve the text-capability request'
            code = 'planner_capability_gap'
            finding = '; '.join(exc.findings)
        elif 'invalid JSON' in message:
            error = 'planner model returned invalid JSON'
            code = 'planner_invalid_json'
            finding = 'The model response was not one complete JSON object.'
        elif 'invalid plan schema' in message:
            error = 'planner model returned an invalid plan schema'
            code = 'planner_invalid_schema'
            finding = '; '.join(exc.findings) or 'The model response did not satisfy the required workflow-plan schema.'
        elif diagnostic_error_code(exc) == 'planner_review_needs_revision':
            error = 'planner role review requested revision'
            code = 'planner_review_needs_revision'
            finding = 'An advisory role requested changes after the bounded correction. This is separate from deterministic operation validation.'
        elif 'deterministic policy' in message:
            error = 'planner plan was rejected by deterministic policy'
            code = 'planner_policy_rejected'
            finding = '; '.join(exc.findings) or message.partition('deterministic policy:')[2].strip() or 'The candidate plan violated deterministic policy.'
        else:
            error = 'planner could not produce a validated plan'
            code = 'planner_generation_failed'
            finding = 'The configured model did not produce a validated plan.'
        self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': error, 'code': code, 'finding': finding[:1000], 'retryable': True, 'schema_findings': exc.findings, 'correction_attempted': exc.correction_attempted, 'planner_diagnostics': getattr(exc, 'planner_diagnostics', None), 'retry_guidance': 'The Planner must follow the declared text-capability contract: propose a bounded missing candidate when ON, or use the supplied compatible installed operation. Do not substitute numeric arithmetic. Your workflow is preserved; do not add approval flags or edit stored files.' if code == 'planner_capability_gap' else 'The model cited a reuse source that was unavailable, uninspected or unrelated. The saved workflow is preserved. Retry the same task; ordinary planning needs no recipe selection or extra authorization instructions.' if code == 'planner_reuse_unverified' else 'The model omitted a requested operation after one correction. Your saved workflow is preserved. Inspect the listed missing method or operation and retry with a compatible selected model. No execution happened. Do not edit stored plans or add authorization instructions.' if code == 'planner_scope_incomplete' else 'The endpoint reported finish_reason=length. Increase MODEL_MAX_TOKENS in the launcher environment and restart, or reduce the requested workflow scope. The saved workflow is preserved; no partial plan was accepted.' if code == 'planner_output_truncated' else 'This is a model-output failure, not missing user authorization or technical details. Your saved workflow is preserved. Retry the same task after checking the running backend and selected skills; do not add approval or validation rules to your request.' if code == 'planner_repair_deferred' else 'The model did not follow the plan structure after a bounded correction. Inspect the listed fields and retry generation with the same reviewed scope; do not modify stored review files.' if code in {'planner_invalid_json', 'planner_invalid_schema'} else 'The role review requested changes after one correction. Inspect the supplied finding and current workflow. No authorization instruction can repair this review disagreement; no extra retry or execution happened.' if code == 'planner_review_needs_revision' else 'The proposed workflow did not satisfy registered operation contracts. Review the listed finding and current workflow. Internal task IDs and approval flags are not user authorization instructions; changing permissions cannot repair an invalid plan.', 'plan_returned': False, 'plan_saved': False, 'approval_performed': False, 'execution_performed': False})
        return True
    if isinstance(exc, route_context.services.PlannerPolicyError):
        message = 'Edited workflow failed policy: ' + str(exc)[:240] if self.path == '/api/v1/plans/validate-edit' else 'reviewed plan was rejected by deterministic policy'
        self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': message})
        return True
    if isinstance(exc, (route_context.services.ContextPackError, route_context.services.ModelClientError, route_context.services.ModelSettingsError)):
        if self.path in {'/api/v1/planner/conversation', '/api/v1/planner/submit', '/api/v1/method-memory', '/api/v1/reusable-recipes'}:
            if isinstance(exc, route_context.services.ModelClientError):
                message, code = (str(exc), exc.code)
                guidance = 'The model did not finish before MODEL_TIMEOUT_SECONDS. The saved workflow is preserved; nothing executed and the timed-out call is not retried automatically. Request diagnostics show the stage, bytes and elapsed time when available. In Settings → Model service, try Reasoning effort None for a compatible model, fewer selected skills, or a smaller installed model. Saved project reasoning settings apply to new requests without a launcher restart. Inspect Ollama logs if it still times out; timeout alone does not prove context overflow.' if code == 'model_timeout' else 'The configured endpoint rejected JSON-schema output. Check its structured-output support. For a compatible endpoint that only supports JSON mode, explicitly set MODEL_RESPONSE_FORMAT=json_object in the launcher environment and restart. No automatic fallback or retry occurred.' if code == 'model_response_format_rejected' else 'Planner reached its call or configured time limit. Review request diagnostics; reduce the scope or adjust trusted launcher settings. Nothing executed.' if code == 'planner_budget_exhausted' else 'Check the exact installed model name and endpoint in Settings. HTTP 404 can indicate a missing model or unsupported route.'
            elif isinstance(exc, route_context.services.ModelSettingsError):
                message, code = ('Planner model configuration is invalid or missing', 'model_configuration_failed')
                guidance = 'Check MODEL_NAME and MODEL_BASE_URL in the launcher environment, then restart the launcher.'
            else:
                message, code = ('Planner context could not be prepared', 'planner_context_failed')
                guidance = 'Check trusted context files and the current workflow. Disable previous messages or reduce selected skills if the prompt exceeds its budget.'
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': message, 'code': code, 'planner_diagnostics': getattr(exc, 'planner_diagnostics', None), 'retry_guidance': guidance, 'approval_performed': False, 'execution_performed': False})
            return True
        if self.path == '/api/v1/critic-evidence/run':
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'Critic model service is unavailable'})
            return True
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'planner could not produce a validated plan'})
        return True
    if isinstance(exc, route_context.services.WritePolicyError):
        self._send(HTTPStatus.CONFLICT, {'error': str(exc), 'code': 'write_policy_blocked', 'execution_performed': False})
        return True
    if isinstance(exc, (route_context.services.SkillRegistryError, OSError, ValueError)):
        if self.path in {'/api/v1/analysis/view', '/api/v1/chat/history'}:
            self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': route_context.services.redact_text(str(exc))[:600], 'approval_performed': False, 'execution_performed': False})
            return True
        if self.path in {'/api/v1/reusable-recipes', '/api/v1/workflow/runs'}:
            from geoagent_harness.capabilities.recipes.catalog.composition import RecipePreparationError
            message = str(exc) if isinstance(exc, RecipePreparationError) else 'Request failed recipe contracts, isolated fixture checks or safe run storage requirements. The saved workflow is preserved; inspect its parameters and retry.'
            self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': message, 'approval_performed': False, 'execution_performed': False})
            return True
        if self.path == '/api/v1/method-memory':
            self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': 'Method proposal failed its schema or safe storage checks. Edit the proposal or select fewer sources; nothing saved or executed.', 'approval_performed': False, 'execution_performed': False})
            return True
        if self.path.startswith('/api/v1/operations/'):
            from geoagent_harness.contracts.operation_packages import PackageError
            message = str(exc)[:600] if isinstance(exc, PackageError) else 'Operation package or discovery request failed its typed bounds, source/fixture checks or safe storage requirements'
            self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {'error': message, 'approval_performed': False, 'execution_performed': False})
            return True
        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {'error': 'trusted compilation service is unavailable'})
        return True
    return False
