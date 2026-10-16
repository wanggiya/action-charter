import { recipeCandidateSchema } from "./recipe-candidate";
import { helperReceiptSchema, helperStatusSchema } from "./method-helper";
import { z } from "zod";
import { plannerResultSchema, type InterfacePlannerResult } from "./interface-api";

export const conversationSchema = z.object({
  conversation_id: z.string().regex(/^[a-f0-9]{32}$/),
  revision: z.number().int().nonnegative(),
  messages: z.array(z.object({ role: z.enum(["user", "assistant"]), content: z.string().min(1).max(8000), task_id:z.string().regex(/^[a-f0-9]{32}$/).nullable().optional(), conversation_id:z.string().regex(/^[a-f0-9]{32}$/).nullable().optional(), selected_skill_ids: z.array(z.string()).max(64).nullable().optional(), plan_skill_ids: z.array(z.string()).max(64).nullable().optional() })).max(100),
  planner_result: plannerResultSchema.nullable(),
  recipe_candidate:recipeCandidateSchema.nullable().optional(),
  selected_skill_ids: z.array(z.string()).max(64).default([]),
  allowed_skill_ids: z.array(z.string()).max(64).optional(),
  supported_skill_ids: z.array(z.string()).max(64),
  context_usage: z.object({history_enabled:z.boolean(),included_messages:z.number(),omitted_messages:z.number(),excerpts_truncated:z.boolean(),prompt_bytes:z.number(),prompt_limit_bytes:z.number(),opening_message_included:z.boolean().optional(),current_workflow_included:z.boolean().optional(),selected_method_id:z.string().nullable().optional(),selected_method_revision:z.number().nullable().optional(),method_helper:helperReceiptSchema.optional()}).nullable().optional(),
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
export async function plannerConversation(action: "read" | "turn" | "bind_task_plan", id: string, revision = 0, message = "", base: InterfacePlannerResult | null = null, skills: string[] = [], currentPlanFilename: string | null = null, useHistory = true, taskId:string|null=null, taskRevision:number|null=null, taskTitle="",methodId:string|null=null): Promise<PlannerConversation> {
  const current = base ? { agent_id: base.agent_id, model: base.model, original_request: base.original_request, context_references: base.context_references, plan: base.plan, warnings: base.warnings } : null;
  const response = await fetch("/api/v1/planner/conversation", {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, conversation_id: id, expected_revision: revision, message, current_plan: current, allowed_skill_ids: skills, current_plan_filename: currentPlanFilename, use_history: useHistory, task_id:taskId, expected_task_revision:taskRevision, task_title:taskTitle,method_id:methodId }),
  });
  const raw = await response.text();
  if (raw.length > 2_000_000) throw new Error("Planner response exceeds the bounded conversation limit");
  const payload: unknown = JSON.parse(raw);
  if (!response.ok) {
    const failure = z.object({ error: z.string().max(1000), retry_guidance:z.string().max(1000).optional(), finding:z.string().max(1000).optional(), schema_findings:z.array(z.string().max(1000)).max(6).optional() }).safeParse(payload);
    throw new Error(failure.success ? [failure.data.error,...(failure.data.schema_findings?.length ? failure.data.schema_findings : [failure.data.finding]),failure.data.retry_guidance].filter(Boolean).join("\n\n") : "Planner conversation is unavailable. Your current plan is preserved.");
  }
  return conversationSchema.parse(payload);
}

const inventorySchema = z.object({ conversations: z.array(z.object({ conversation_id: z.string().regex(/^[a-f0-9]{32}$/), revision: z.number().int().nonnegative(), summary: z.string().max(120) })).max(64), approval_performed: z.literal(false), execution_performed: z.literal(false) });
export async function loadPlannerConversations() {
  const response = await fetch("/api/v1/planner/conversation", { method: "POST", cache: "no-store", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "list", conversation_id: "0".repeat(32) }) });
  if (!response.ok) throw new Error("Conversation history unavailable");
  return inventorySchema.parse(await response.json()).conversations;
}
