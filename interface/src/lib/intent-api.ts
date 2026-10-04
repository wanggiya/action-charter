import { z } from "zod";
import { boundedJson, plannerResultSchema } from "./interface-api";
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const item = z.string().min(1).max(1000);
export const retrievedContextSchema = z.object({
  status: z.literal("retrieved_not_reviewed"), context_sha256: digest, query: z.string(), selected_task_ids: z.array(z.string()).max(5),
  excerpts: z.array(z.object({ task_id: z.string(), sequence: z.number().int(), text: z.string().max(1000), source: z.object({ path: z.string(), sha256: digest }) })).max(8),
  review_performed: z.literal(false), approval_inferred: z.literal(false), execution_performed: z.literal(false), model_called: z.literal(false),
}).passthrough();
export type RetrievedContext = z.infer<typeof retrievedContextSchema>;
export const intentSchema = z.object({
  schema_version: z.literal("1.0"), agent_id: z.literal("intent"), model: z.string().max(200), original_request: z.string().max(4000),
  clarification_answers: z.array(item).max(5), review_filename: z.string().regex(/^context-review\.[a-f0-9]{64}\.json$/).nullable(), context_sha256: digest.nullable(),
  proposal: z.object({ status: z.enum(["intent_proposed", "clarification_required"]), objective: z.string().min(1).max(2000), known_inputs: z.array(item).max(20), requested_outputs: z.array(item).max(20), constraints: z.array(item).max(20), clarification_questions: z.array(item).max(5), cited_sequences: z.array(z.number().int()).max(8) }).strict(),
  status: z.literal("proposed_not_saved"), human_review_required: z.literal(true), correction_attempted: z.boolean().default(false), model_called: z.literal(true), plan_created: z.literal(false), approval_inferred: z.literal(false), execution_performed: z.literal(false), tools_called: z.literal(false),
}).strict();
export type Intent = z.infer<typeof intentSchema>;
const storedContextSchema = z.object({ status: z.literal("reviewed_context_stored"), review_filename: z.string().regex(/^context-review\.[a-f0-9]{64}\.json$/), review_sha256: digest, context_sha256: digest, review_performed: z.literal(true), plan_approved: z.literal(false), execution_performed: z.literal(false), model_called: z.literal(false) });
const inspectedIntentSchema = z.object({ status: z.enum(["ready_for_intent_review", "clarification_required"]), intent_sha256: digest, review_allowed: z.boolean(), intent: intentSchema, review_performed: z.literal(false), plan_approved: z.literal(false), execution_performed: z.literal(false), model_called: z.literal(false) });
export type InspectedIntent = z.infer<typeof inspectedIntentSchema>;
const storedIntentSchema = z.object({ status: z.literal("reviewed_intent_stored"), review_filename: z.string().regex(/^intent-review\.[a-f0-9]{64}\.json$/), review_sha256: digest, intent_sha256: digest, review_performed: z.literal(true), plan_approved: z.literal(false), execution_performed: z.literal(false), model_called: z.literal(false) });
export const handoffSchema = z.object({ status: z.literal("planned_not_saved"), plan_sha256: digest, intent_review_filename: z.string(), intent_sha256: digest, context_sha256: digest.nullable(),
  planner_result: z.object({ agent_id: z.literal("planner"), model: z.string(), original_request: z.string(), context_references: z.array(z.string()), plan: plannerResultSchema.shape.plan, warnings: z.array(z.string()) }),
  model_called: z.literal(true), reviewed_intent_rechecked: z.literal(true), plan_saved: z.literal(false), additional_human_approval_required: z.boolean(), warnings: z.array(z.string()), approval_inferred: z.literal(false), execution_performed: z.literal(false), tools_called: z.literal(false),
});
export type Handoff = z.infer<typeof handoffSchema>;
async function post<S extends z.ZodTypeAny>(path: string, body: unknown, schema: S): Promise<z.output<S>> {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin", cache: "no-store", body: JSON.stringify(body) });
  const payload = await boundedJson(response);
  if (!response.ok) { const failure = z.object({ error: z.string().max(5000) }).safeParse(payload); throw new Error(failure.success ? failure.data.error : "Request failed. Restart the updated API and check the model settings."); }
  return schema.parse(payload);
}
export const retrieveContext = (query: string, taskIds: string[]) => post("/api/v1/context/retrieve", { action: "retrieve_task_context", query, task_ids: taskIds }, retrievedContextSchema);
export const reviewContext = (context: RetrievedContext, reviewer: string) => post("/api/v1/context/review", { action: "review_task_context", query: context.query, task_ids: context.selected_task_ids, confirmed_context_sha256: context.context_sha256, reviewer, reason: "Reviewed displayed historical excerpts for reasoning only; no work approved." }, storedContextSchema);
export const reasonIntent = (reviewFilename: string | null, request: string, answers: string[]) => post("/api/v1/intent/reason", { action: "reason_task_intent", review_filename: reviewFilename, request, clarification_answers: answers }, intentSchema);
export const inspectIntent = (intent: Intent) => post("/api/v1/intent/inspect", { action: "inspect_intent_proposal", intent }, inspectedIntentSchema);
export const reviewIntent = (inspected: InspectedIntent, reviewer: string) => post("/api/v1/intent/review", { action: "review_task_intent", intent: inspected.intent, confirmed_intent_sha256: inspected.intent_sha256, reviewer, reason: "Reviewed displayed resolved intent; no plan or execution approved." }, storedIntentSchema);
export const handoffIntent = (reviewFilename: string, skill: "inspect_vector" | "inspect_raster" = "inspect_vector") => post("/api/v1/intent/plan", { action: "plan_reviewed_intent", review_filename: reviewFilename, allowed_skill_ids: [skill] }, handoffSchema);

const savedIntentPlanSchema = z.object({ schema_version: z.literal("1.0"), status: z.enum(["stored", "already_stored"]), plan_filename: z.string(), plan_sha256: digest, plan_saved: z.literal(true), plan_modified: z.boolean(), approval_performed: z.literal(false), execution_performed: z.literal(false), model_called: z.literal(false), approval_inferred: z.literal(false), tools_called: z.literal(false) });
export const saveIntentPlan = (plan: Handoff) => post("/api/v1/intent/save-plan", { action: "save_reviewed_intent_plan", review_filename: plan.intent_review_filename, planner_result: plan.planner_result, confirmed_plan_sha256: plan.plan_sha256 }, savedIntentPlanSchema);

const reviewInventorySchema = z.object({ status: z.literal("inspected"), reviews: z.array(z.object({ kind: z.enum(["context", "intent"]), review_filename: z.string().regex(/^(context|intent)-review\.[a-f0-9]{64}\.json$/), status: z.enum(["available", "blocked"]), summary: z.string().max(500), reviewed_at: z.string().nullable(), reviewer: z.string().nullable(), reason: z.string() })).max(50), review_count: z.number().int(), inventory_truncated: z.boolean(), findings: z.array(z.string()), files_modified: z.literal(false), model_called: z.literal(false), approval_inferred: z.literal(false), execution_performed: z.literal(false) });
export type ReviewInventory = z.infer<typeof reviewInventorySchema>;
const recoveredContextSchema = z.object({ status: z.literal("reviewed_context_only"), context: retrievedContextSchema, context_sha256: digest, reviewer: z.string(), reviewed_at: z.string(), review_performed: z.literal(true), plan_approved: z.literal(false), execution_performed: z.literal(false), model_called: z.literal(false) });
const recoveredIntentSchema = z.object({ status: z.literal("reviewed_intent_only"), intent: intentSchema, intent_sha256: digest, reviewer: z.string(), reviewed_at: z.string(), review_performed: z.literal(true), plan_approved: z.literal(false), execution_performed: z.literal(false), model_called: z.literal(false) });
async function get<S extends z.ZodTypeAny>(path: string, schema: S): Promise<z.output<S>> {
  const response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
  const payload = await boundedJson(response);
  if (!response.ok) { const failure = z.object({ error: z.string().max(5000) }).safeParse(payload); throw new Error(failure.success ? failure.data.error : "Saved review could not be reopened."); }
  return schema.parse(payload);
}
export const loadReviewInventory = () => get("/api/v1/reviewed-context-inventory", reviewInventorySchema);
export const recoverContext = (filename: string) => get(`/api/v1/context/reviews/${encodeURIComponent(filename)}`, recoveredContextSchema);
export const recoverIntent = (filename: string) => get(`/api/v1/intent/reviews/${encodeURIComponent(filename)}`, recoveredIntentSchema);
