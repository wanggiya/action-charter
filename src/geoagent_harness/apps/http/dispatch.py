"""Ordered existing HTTP routes; matching precedes payload dispatch."""
import re
from http import HTTPStatus
from geoagent_harness.apps.http.routers import settings
from geoagent_harness.apps.http.routers import history
from geoagent_harness.apps.http.routers import runs
from geoagent_harness.apps.http.routers import recipes
from geoagent_harness.apps.http.routers import results
from geoagent_harness.apps.http.routers import assurance
from geoagent_harness.apps.http.routers import operations
from geoagent_harness.apps.http.routers import plans
from geoagent_harness.apps.http.routers import workflows
from geoagent_harness.apps.http.routers import conversations

GET_ROUTES = (
    ('exact', '/api/v1/health', settings.get_0_health),
    ('exact', '/api/v1/write-policy', settings.get_1_write_policy),
    ('exact', '/api/v1/model-status', settings.get_2_model_status),
    ('exact', '/api/v1/models', settings.get_3_models),
    ('exact', '/api/v1/tasks', history.get_0_tasks),
    ('regex', '/api/v1/tasks/(task-[a-z0-9][a-z0-9_-]{0,63})/context', history.get_task_match),
    ('regex', '/api/v1/tasks/(task-[a-z0-9][a-z0-9_-]{0,63})/relationships', history.get_relationship_match),
    ('regex', '/api/v1/tasks/(task-[a-z0-9][a-z0-9_-]{0,63})/artifacts', history.get_artifact_match),
    ('exact', '/api/v1/reviewed-context-inventory', history.get_4_reviewed_context_inventory),
    ('regex', '/api/v1/context/reviews/(context-review\\.[a-f0-9]{64}\\.json)', history.get_review_match),
    ('regex', '/api/v1/intent/reviews/(intent-review\\.[a-f0-9]{64}\\.json)', history.get_intent_review_match),
    ('exact', '/api/v1/executions', runs.get_0_executions),
    ('regex', '/api/v1/executions/([a-f0-9]{64})', runs.get_progress_match),
    ('exact', '/api/v1/recipe-templates', recipes.get_0_recipe_templates),
    ('exact', '/api/v1/data-resources', results.get_0_data_resources),
    ('exact', '/api/v1/critic-evidence', assurance.get_0_critic_evidence),
    ('prefix', '/api/v1/operations/', operations.get_metadata),
    ('exact', '/api/v1/planner-skills', plans.get_0_planner_skills),
    ('exact', '/api/v1/plans', plans.get_1_plans),
    ('exact', '/api/v1/inspection-runs', runs.get_2_inspection_runs),
    ('exact', '/api/v1/recipes', recipes.get_1_recipes),
)

POST_ROUTES = {
    '/api/v1/models/select': settings.post_4_select,
    '/api/v1/models/reasoning': settings.post_5_reasoning,
    '/api/v1/models/review-timeout': settings.post_6_review_timeout,
    '/api/v1/write-policy': settings.post_7_write_policy,
    '/api/v1/context/retrieve': history.post_7_retrieve,
    '/api/v1/context/review': history.post_8_review,
    '/api/v1/intent/reason': history.post_9_reason,
    '/api/v1/intent/inspect': history.post_10_inspect,
    '/api/v1/intent/review': history.post_10_inspect,
    '/api/v1/intent/plan': history.post_10_inspect,
    '/api/v1/intent/save-plan': history.post_10_inspect,
    '/api/v1/tasks/events': history.post_11_events,
    '/api/v1/recipe-proposals/compile': recipes.post_2_compile,
    '/api/v1/critic-evidence/save-adapted-trace': assurance.post_1_save_adapted_trace,
    '/api/v1/critic-evidence/run': assurance.post_2_run,
    '/api/v1/critic-evidence/record-result': assurance.post_3_record_result,
    '/api/v1/releases/prepare-recipe': assurance.post_4_prepare_recipe,
    '/api/v1/releases/create-recipe': assurance.post_5_create_recipe,
    '/api/v1/snakemake/preview-export': assurance.post_6_preview_export,
    '/api/v1/snakemake/export': assurance.post_7_export,
    '/api/v1/plans/validate-edit': plans.post_2_validate_edit,
    '/api/v1/workflow/runs': workflows.post_0_runs,
    '/api/v1/reusable-recipes': recipes.post_3_reusable_recipes,
    '/api/v1/workflow/prepare': workflows.post_1_prepare,
    '/api/v1/workflow/authorize': workflows.post_1_prepare,
    '/api/v1/workflow/execute': workflows.post_1_prepare,
    '/api/v1/operations/scan': operations.post_1_scan,
    '/api/v1/operations/test-package': operations.post_1_scan,
    '/api/v1/operations/install-package': operations.post_1_scan,
    '/api/v1/method-memory': conversations.post_0_method_memory,
    '/api/v1/planner/diagnostics': conversations.post_1_diagnostics,
    '/api/v1/planner/submit': conversations.post_2_submit,
    '/api/v1/chat/history': conversations.post_3_history,
    '/api/v1/analysis/view': results.post_1_view,
    '/api/v1/planner/conversation': conversations.post_4_conversation,
    '/api/v1/plans/create': plans.post_3_create,
    '/api/v1/plans/save-generated': plans.post_4_save_generated,
    '/api/v1/plans/save-reviewed': plans.post_5_save_reviewed,
    '/api/v1/plans/prepare-approval': plans.post_6_prepare_approval,
    '/api/v1/plans/record-approval': plans.post_7_record_approval,
    '/api/v1/plans/verify-approval': plans.post_8_verify_approval,
    '/api/v1/plans/preview-execution': plans.post_9_preview_execution,
    '/api/v1/plans/compile-recipe': plans.post_10_compile_recipe,
    '/api/v1/plans/save-reviewed-recipe': plans.post_11_save_reviewed_recipe,
    '/api/v1/recipe-proposals/save-reviewed': recipes.post_4_save_reviewed,
    '/api/v1/recipes/prepare-approval': recipes.post_5_prepare_approval,
    '/api/v1/recipes/record-approval': recipes.post_6_record_approval,
    '/api/v1/recipes/verify-approval': recipes.post_7_verify_approval,
    '/api/v1/recipes/preview-execution': recipes.post_8_preview_execution,
    '/api/v1/recipes/execute': recipes.post_9_execute,
}
POST_PATHS = frozenset(POST_ROUTES)

def dispatch_get(handler, context):
    for kind, path, action in GET_ROUTES:
        match = re.fullmatch(path, handler.path) if kind == 'regex' else None
        if (kind == 'exact' and handler.path == path) or (kind == 'prefix' and handler.path.startswith(path)) or match:
            action(handler, context, match)
            return
    handler._send(HTTPStatus.NOT_FOUND, {"error": "endpoint is not available"})


def dispatch_post(handler, context, payload):
    return POST_ROUTES[handler.path](handler, context, payload)


from geoagent_harness.core.execution.actions import task_entrypoint
_dispatch_get_action = task_entrypoint(dispatch_get, trigger="http", audit=False)
_CONTEXT_POSTS = frozenset({
    '/api/v1/workflow/runs','/api/v1/workflow/prepare','/api/v1/planner/conversation',
    '/api/v1/planner/submit','/api/v1/planner/submissions','/api/v1/reusable-recipes',
    '/api/v1/recipes/prepare-approval','/api/v1/recipes/verify-approval',
    '/api/v1/recipes/preview-execution','/api/v1/plans/prepare-approval',
    '/api/v1/plans/verify-approval','/api/v1/plans/preview-execution',
    '/api/v1/plans/compile-recipe','/api/v1/recipe-proposals/compile',
    '/api/v1/snakemake/preview-export','/api/v1/releases/prepare-recipe',
})
_dispatch_post_action = task_entrypoint(dispatch_post, trigger="http",
    audit=lambda arguments: arguments['handler'].path not in _CONTEXT_POSTS)


def _buffered_action(action, handler, context, *args, **kwargs):
    # A route's early response must wait for audit acknowledgement too. Never
    # send a success and then a second error if terminal persistence fails.
    send=handler._send
    pending=[]
    handler._send=lambda *response:pending.append(response)
    try:
        result=action(handler,context,*args,**kwargs)
    finally:
        handler._send=send
    for response in pending:send(*response)
    return result


def dispatch_get(handler, context, *, actor=None, run_context=None):
    from geoagent_harness.contracts.task_context import ActionContextError
    try:
        return _buffered_action(_dispatch_get_action,handler,context,actor=actor,run_context=run_context)
    except ActionContextError as exc:
        from geoagent_harness.apps.http.errors import send_post_error
        if not send_post_error(handler,context,exc):raise


def dispatch_post(handler, context, payload, *, actor=None, run_context=None):
    # An opaque event key can prevent repetition; it supplies no identity or authority.
    from geoagent_harness.contracts.task_context import RunContext
    from geoagent_harness.platform.action_context import current_action
    if run_context is None and current_action() is None:
        key=handler.headers.get('Idempotency-Key')
        if key is not None:
            run_context=RunContext(str(context.project_root.resolve()),trigger='http',idempotency_key=key)
    return _buffered_action(_dispatch_post_action,handler,context,payload,actor=actor,run_context=run_context)
