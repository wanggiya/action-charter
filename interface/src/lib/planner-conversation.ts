import { z } from "zod";
import { plannerResultSchema, type InterfacePlannerResult } from "./interface-api";

const conversationSchema = z.object({
  conversation_id: z.string().regex(/^[a-f0-9]{32}$/),
  revision: z.number().int().nonnegative(),
  messages: z.array(z.object({ role: z.enum(["user", "assistant"]), content: z.string().min(1).max(8000), selected_skill_ids: z.array(z.string()).max(20).nullable().optional(), plan_skill_ids: z.array(z.string()).max(20).nullable().optional() })).max(100),
  planner_result: plannerResultSchema.nullable(),
  selected_skill_ids: z.array(z.string()).max(20).default([]),
  allowed_skill_ids: z.array(z.string()).max(20).optional(),
  supported_skill_ids: z.array(z.string()).max(20),
  context_usage: z.object({history_enabled:z.boolean(),included_messages:z.number(),omitted_messages:z.number(),excerpts_truncated:z.boolean(),prompt_bytes:z.number(),prompt_limit_bytes:z.number()}).nullable().optional(),
  proposal_changed: z.boolean(),
  approval_performed: z.literal(false), execution_performed: z.literal(false),
});
export type PlannerConversation = z.infer<typeof conversationSchema>;
export function newConversationId() { return crypto.randomUUID().replaceAll("-", ""); }
export async function plannerConversation(action: "read" | "turn", id: string, revision = 0, message = "", base: InterfacePlannerResult | null = null, skills: string[] = [], currentPlanFilename: string | null = null, useHistory = true): Promise<PlannerConversation> {
  const current = base ? { agent_id: base.agent_id, model: base.model, original_request: base.original_request, context_references: base.context_references, plan: base.plan, warnings: base.warnings } : null;
  const response = await fetch("/api/v1/planner/conversation", {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, conversation_id: id, expected_revision: revision, message, current_plan: current, allowed_skill_ids: skills, current_plan_filename: currentPlanFilename, use_history: useHistory }),
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

const inventorySchema = z.object({ conversations: z.array(z.object({ conversation_id: z.string().regex(/^[a-f0-9]{32}$/), revision: z.number().int().nonnegative(), summary: z.string().max(120) })).max(20), approval_performed: z.literal(false), execution_performed: z.literal(false) });
export async function loadPlannerConversations() {
  const response = await fetch("/api/v1/planner/conversation", { method: "POST", cache: "no-store", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "list", conversation_id: "0".repeat(32) }) });
  if (!response.ok) throw new Error("Conversation history unavailable");
  return inventorySchema.parse(await response.json()).conversations;
}
