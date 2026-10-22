import {resultViewSpecSchema} from "./result-exploration";
import {runSchema} from "./workflow-tools";
import {capabilityCandidateSchema} from "./capability-candidate";
import { recipeCandidateSchema } from "./recipe-candidate";
import { helperReceiptSchema, helperStatusSchema } from "./method-helper";
import { z } from "zod";
import { plannerResultSchema, type InterfacePlannerResult } from "./interface-api";

export const submissionReceiptSchema = z.object({submission_id:z.string().regex(/^[a-f0-9]{32}$/),conversation_id:z.string().regex(/^[a-f0-9]{32}$/),status:z.string(),finding:z.string(),run_id:z.string().nullable()});

export const conversationSchema = z.object({
  submission:submissionReceiptSchema.optional(),
  submitted_run:runSchema.nullable().optional(),
  conversation_id: z.string().regex(/^[a-f0-9]{32}$/),
  revision: z.number().int().nonnegative(),
  messages: z.array(z.object({ role: z.enum(["user", "assistant"]), content: z.string().min(1).max(8000), task_id:z.string().regex(/^[a-f0-9]{32}$/).nullable().optional(), conversation_id:z.string().regex(/^[a-f0-9]{32}$/).nullable().optional(), selected_skill_ids: z.array(z.string()).max(64).nullable().optional(), plan_skill_ids: z.array(z.string()).max(64).nullable().optional() })).max(100),
  planner_result: plannerResultSchema.nullable(),
  recipe_candidate:recipeCandidateSchema.nullable().optional(),
  recommendations_enabled:z.boolean().default(false),
  acquisition_enabled:z.boolean().default(false),
  capability_candidate:capabilityCandidateSchema.nullable().optional(),
  selected_skill_ids: z.array(z.string()).max(64).default([]),
  allowed_skill_ids: z.array(z.string()).max(64).optional(),
  supported_skill_ids: z.array(z.string()).max(64),
  context_usage: z.object({result_view:resultViewSpecSchema.nullable().optional(),outcome_recommendations:z.object({status:z.string(),scope:z.literal("this_chat"),policy_version:z.string().optional(),recipe_order_changed:z.boolean().optional(),baseline_recipe_ids:z.array(z.string()).max(5).optional(),supplied_recipe_ids:z.array(z.string()).max(5).optional(),model_adoption:z.literal("not_measured").optional(),authority_granted:z.literal(false).optional(),items:z.array(z.object({operation_id:z.string(),verified_passes:z.number(),check_failures:z.number(),score:z.number(),contract_sha256:z.string().optional(),basis:z.string().optional()})).max(5)}).optional(),required_gate_bindings:z.array(z.string()).optional(),effort_budget:z.object({model_calls:z.number(),model_call_limit:z.number(),tool_calls:z.number(),tool_call_limit:z.number(),prompt_bytes_total:z.number(),prompt_tokens:z.number().nullable(),completion_tokens:z.number().nullable(),token_usage_complete:z.boolean(),elapsed_seconds:z.number(),deadline_seconds:z.number().nullable(),stopping_reason:z.string().nullable(),scope:z.string()}).optional(),history_enabled:z.boolean(),included_messages:z.number(),omitted_messages:z.number(),excerpts_truncated:z.boolean(),prompt_bytes:z.number(),prompt_limit_bytes:z.number(),opening_message_included:z.boolean().optional(),current_workflow_included:z.boolean().optional(),selected_method_id:z.string().nullable().optional(),selected_method_revision:z.number().nullable().optional(),method_helper:helperReceiptSchema.optional(),successful_methods:z.object({status:z.string(),count:z.number(),method_ids:z.array(z.string()),bytes:z.number(),explicit_selection:z.boolean()}).optional(),recipe_discovery:z.object({rounds:z.number(),actions:z.array(z.string()),sources:z.array(z.object({id:z.string().nullable(),name:z.string().nullable()}))}).optional(),recipe_reuse:z.array(z.object({id:z.string(),name:z.string(),basis:z.string()})).optional(),model_request:z.object({planner_contract:z.string().optional(),stage:z.string(),prompt_bytes:z.number(),supplied_schema_count:z.number(),available_operation_count:z.number(),retrieved_method_count:z.number(),elapsed_seconds:z.number(),model_calls:z.number().int().nonnegative().optional(),response_schema_bytes:z.number().optional(),response_shape:z.string().optional(),finish_reason:z.string().nullable().optional(),response_format:z.string().nullable().optional(),completion_tokens:z.number().nullable().optional()}).optional()}).nullable().optional(),
  proposal_changed: z.boolean(),
  method_helper:helperStatusSchema.optional(),
  method_helper_update:helperReceiptSchema.optional(),
  active_task_id:z.string().regex(/^[a-f0-9]{32}$/).nullable().optional(),
  task_title:z.string().max(160).nullable().optional(),
  task_revision:z.number().int().nonnegative().nullable().optional(),
  task_history_preview:z.array(z.object({role:z.enum(["user","assistant"]),content:z.string().max(1000),conversation_id:z.string().nullable().optional(),content_truncated:z.boolean().optional()})).max(12).default([]),
  task_message_count:z.number().int().min(0).max(100).default(0),
  conversation_memory:z.object({scope:z.literal("conversation"),message_count:z.number(),cross_conversation_memory:z.literal(false),semantic_summary_available:z.literal(false)}).optional(),
  linked_task_ids:z.array(z.string().regex(/^[a-f0-9]{32}$/)).max(128).default([]),
  approval_performed: z.literal(false), execution_performed: z.literal(false),
});
export type PlannerConversation = z.infer<typeof conversationSchema>;
export function newConversationId() { return crypto.randomUUID().replaceAll("-", ""); }
export async function plannerConversation(action: "read" | "turn" | "bind_task_plan" | "configure_acquisition" | "configure_recommendations" | "install_capability", id: string, revision = 0, message = "", base: InterfacePlannerResult | null = null, skills: string[] = [], currentPlanFilename: string | null = null, useHistory = true, taskId:string|null=null, taskRevision:number|null=null, taskTitle="",methodId:string|null=null,successfulMethodId:string|null=null, acquisition?:{recommendations_enabled?:boolean;acquisition_enabled?:boolean;confirmed_candidate_sha256?:string}, submission?:{id:string;enabled:boolean}): Promise<PlannerConversation> {
  if (action === "turn" || action === "configure_acquisition" || action === "install_capability") {
    const health = await fetch("/api/v1/health", {cache:"no-store", credentials:"same-origin"});
    if (!health.ok) throw new Error("Cannot check the running API version. Check the ActionCharter launcher terminal. No planner request was sent.");
    const runtime = z.object({planner_contract_revision:z.string().optional(),inspection_on_send_revision:z.string().optional()}).safeParse(await health.json());
    if (!runtime.success || runtime.data.planner_contract_revision !== "inspection-source-v2") {
      throw new Error("The running API has an older or incompatible Planner version. Stop the terminal running ActionCharter with Ctrl+C, then run bash scripts/start_actioncharter.sh from this checkout. Startup must show Planner contract revision: inspection-source-v2. Refresh this page afterward. No model request was sent; your saved workflow is preserved.");
    }
    if(submission&&runtime.data.inspection_on_send_revision!=='inspection-batch-v5')throw new Error('Restart the ActionCharter launcher and refresh this page before submitting. No submission was sent.');
  }
  const current = base ? { agent_id: base.agent_id, model: base.model, original_request: base.original_request, context_references: base.context_references, plan: base.plan, warnings: base.warnings } : null;
  const turn = { action, conversation_id: id, expected_revision: revision, message, current_plan: current, allowed_skill_ids: skills, current_plan_filename: currentPlanFilename, use_history: useHistory, task_id:taskId, expected_task_revision:taskRevision, task_title:taskTitle,method_id:methodId,successful_method_id:successfulMethodId, ...acquisition };
  const response = await fetch(submission ? "/api/v1/planner/submit" : "/api/v1/planner/conversation", {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(submission ? {action:"submit",submission_id:submission.id,conversation_id:id,inspect_on_send:submission.enabled,turn} : turn),
  });
  const raw = await response.text();
  if (raw.length > 2_000_000) throw new Error("Planner response exceeds the bounded conversation limit");
  const payload: unknown = JSON.parse(raw);
  if (!response.ok) {
    const failure = z.object({ error: z.string().max(1000), retry_guidance:z.string().max(1000).optional(), finding:z.string().max(1000).optional(), schema_findings:z.array(z.string().max(1000)).max(6).optional(),planner_diagnostics:z.object({planner_contract:z.string().optional(),stage:z.string(),prompt_bytes:z.number(),elapsed_seconds:z.number(),supplied_schema_count:z.number(),response_shape:z.string().optional(),finish_reason:z.string().nullable().optional(),response_format:z.string().nullable().optional(),completion_tokens:z.number().nullable().optional()}).nullable().optional() }).safeParse(payload);
    throw new Error(failure.success ? [failure.data.error,...(failure.data.schema_findings?.length ? failure.data.schema_findings : [failure.data.finding]),failure.data.retry_guidance,failure.data.planner_diagnostics?`Planner request: ${(failure.data.planner_diagnostics.prompt_bytes/1024).toFixed(1)} KB · ${failure.data.planner_diagnostics.elapsed_seconds.toFixed(1)} seconds · ${failure.data.planner_diagnostics.supplied_schema_count} operation schemas${failure.data.planner_diagnostics.planner_contract?` · contract: ${failure.data.planner_diagnostics.planner_contract}`:" · contract: legacy API — restart launcher"} · ${failure.data.planner_diagnostics.stage.replaceAll('_',' ')}${failure.data.planner_diagnostics.response_shape?` · response: ${failure.data.planner_diagnostics.response_shape}`:''}${failure.data.planner_diagnostics.finish_reason?` · finish: ${failure.data.planner_diagnostics.finish_reason}`:''}${failure.data.planner_diagnostics.response_format?` · format: ${failure.data.planner_diagnostics.response_format}`:''}`:null].filter(Boolean).join("\n\n") : "Planner conversation is unavailable. Your current plan is preserved.");
  }
  if (submission) {
    const envelope = submissionEnvelopeSchema.parse(payload);
    if (!envelope.conversation) throw new Error(envelope.submission.finding);
    return {...envelope.conversation,submission:envelope.submission,submitted_run:envelope.run};
  }
  return conversationSchema.parse(payload);
}

const inventorySchema = z.object({ conversations: z.array(z.object({ conversation_id: z.string().regex(/^[a-f0-9]{32}$/), revision: z.number().int().nonnegative(), summary: z.string().max(120) })).max(64), approval_performed: z.literal(false), execution_performed: z.literal(false) });
export async function loadPlannerConversations() {
  const response = await fetch("/api/v1/planner/conversation", { method: "POST", cache: "no-store", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "list", conversation_id: "0".repeat(32) }) });
  if (!response.ok) throw new Error("Conversation history unavailable");
  return inventorySchema.parse(await response.json()).conversations;
}

export const capabilityControl=(action:"configure_acquisition"|"configure_recommendations"|"install_capability",id:string,revision:number,fields:{recommendations_enabled?:boolean;acquisition_enabled?:boolean;confirmed_candidate_sha256?:string})=>plannerConversation(action,id,revision,"",null,[],null,true,null,null,"",null,null,fields);

const submissionEnvelopeSchema = z.object({submission:submissionReceiptSchema,conversation:conversationSchema.nullable(),run:runSchema.nullable()});
export async function readPlannerSubmission(submissionId:string, conversationId:string) {
  const response = await fetch('/api/v1/planner/submit',{method:'POST',cache:'no-store',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'read',submission_id:submissionId,conversation_id:conversationId})});
  if (!response.ok) throw new Error('Submission receipt unavailable. Inspect saved chat and Execution History before sending again.');
  return submissionEnvelopeSchema.parse(await response.json());
}
