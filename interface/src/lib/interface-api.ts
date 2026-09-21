import { z } from "zod";
import { browserRecipeProposalSchema, recipeTemplateCatalogSchema, type BrowserRecipeProposal, type RecipeTemplate } from "./recipe-templates";

const MAX_INTERFACE_RESPONSE_BYTES = 500_000;

const compilationSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("compiled"),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  result: z.object({
    compilation_performed: z.literal(true),
    recipe_saved: z.literal(false),
    approval_performed: z.literal(false),
    execution_performed: z.literal(false),
    recipe: z.object({
      recipe_id: z.string().min(1).max(120),
      steps: z.array(z.object({
        step_id: z.string().min(1).max(120),
        skill_id: z.string().min(1).max(120),
        depends_on: z.array(z.string().min(1).max(120)).max(100),
      }).passthrough()).min(1).max(100),
    }).passthrough(),
    recipe_validation: z.object({
      valid: z.boolean(),
      topological_step_ids: z.array(z.string().max(120)).max(100),
      approval_required_step_ids: z.array(z.string().max(120)).max(100),
      validation_required_step_ids: z.array(z.string().max(120)).max(100),
    }).passthrough(),
  }).passthrough(),
  files_modified: z.literal(false),
  approval_performed: z.literal(false),
  execution_performed: z.literal(false),
});

export type InterfaceCompilation = z.infer<typeof compilationSchema>;

const savedRecipeSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("stored"),
  recipe_id: z.string().min(1).max(120),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  recipe_filename: z.string().regex(/^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$/),
  recipe_saved: z.literal(true),
  approval_performed: z.literal(false),
  execution_performed: z.literal(false),
});

export type SavedInterfaceRecipe = z.infer<typeof savedRecipeSchema>;

const savedRecipeInventorySchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("inspected"),
  recipes: z.array(z.object({
    recipe_id: z.string().min(1).max(120),
    recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
    recipe_filename: z.string().regex(/^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$/),
    saved_at: z.string().datetime({ offset: true }),
    steps: z.array(z.object({
      step_id: z.string().min(1).max(120),
      skill_id: z.string().min(1).max(120),
    })).min(1).max(100),
    approval_required_step_ids: z.array(z.string().max(120)).max(100),
    validation_required_step_ids: z.array(z.string().max(120)).max(100),
  })).max(200),
  recipe_count: z.number().int().nonnegative().max(200),
  inventory_performed: z.literal(true),
  recipe_modified: z.literal(false),
  approval_performed: z.literal(false),
  execution_performed: z.literal(false),
});

export type SavedRecipeInventory = z.infer<typeof savedRecipeInventorySchema>;

const approvalRequestSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("prepared_not_recorded"),
  recipe_id: z.string().min(1).max(120),
  recipe_filename: z.string().regex(/^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$/),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approval_request_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  steps: z.array(z.object({
    step_id: z.string().min(1).max(120),
    skill_id: z.string().min(1).max(120),
    depends_on: z.array(z.string().min(1).max(120)).max(100).default([]),
  })).min(1).max(100),
  approval_required_step_ids: z.array(z.string().max(120)).min(1).max(100),
  validation_required_step_ids: z.array(z.string().max(120)).max(100),
  approval_recorded: z.literal(false),
  execution_performed: z.literal(false),
});

export type PreparedApprovalRequest = z.infer<typeof approvalRequestSchema>;

const recordedApprovalSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("recorded"),
  approval_id: z.string().min(1).max(120),
  approval_filename: z.string().regex(/^recipe-approval-[a-z0-9-]+\.json$/),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approval_request_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  decision: z.enum(["approved", "denied"]),
  approved_step_ids: z.array(z.string().max(120)).min(1).max(100),
  created_at: z.string().datetime({ offset: true }),
  expires_at: z.string().datetime({ offset: true }).nullable(),
  secrets_redacted: z.literal(true),
  approval_recorded: z.literal(true),
  execution_performed: z.literal(false),
});

export type RecordedRecipeApproval = z.infer<typeof recordedApprovalSchema>;

const verifiedApprovalSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("verified"),
  approval_id: z.string().min(1).max(120),
  approval_filename: z.string().regex(/^recipe-approval-[a-z0-9-]+\.json$/),
  recipe_id: z.string().min(1).max(120),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approval_request_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  decision: z.enum(["approved", "denied"]),
  approved: z.boolean(),
  required_step_ids: z.array(z.string().max(120)).max(100),
  approved_step_ids: z.array(z.string().max(120)).max(100),
  missing_step_ids: z.array(z.string().max(120)).max(100),
  reason: z.string().min(1).max(300),
  independent_verification_performed: z.literal(true),
  approval_modified: z.literal(false),
  execution_performed: z.literal(false),
});

export type VerifiedRecipeApproval = z.infer<typeof verifiedApprovalSchema>;

const executionPreviewSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("previewed_not_executed"),
  execution_preview_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  recipe_id: z.string().min(1).max(120),
  recipe_filename: z.string().regex(/^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$/),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approval_id: z.string().min(1).max(120),
  approval_filename: z.string().regex(/^recipe-approval-[a-z0-9-]+\.json$/),
  approval_request_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  tool_name: z.literal("run_approved_recipe"),
  approved_step_ids: z.array(z.string().max(120)).max(100),
  topological_step_ids: z.array(z.string().max(120)).min(1).max(100),
  steps: z.array(z.object({
    position: z.number().int().positive().max(100),
    step_id: z.string().min(1).max(120),
    skill_id: z.string().min(1).max(120),
    skill_kind: z.string().nullable(),
    access: z.string().nullable(),
    approval_required: z.boolean().nullable(),
    validation_required: z.boolean().nullable(),
    depends_on: z.array(z.string().max(120)).max(100),
    arguments: z.record(z.string(), z.unknown()),
    output_ids: z.array(z.string().max(120)).max(100),
  })).min(1).max(100),
  evidence_destinations: z.array(z.string().max(200)).min(1).max(10),
  approval_reverified: z.literal(true),
  secrets_redacted: z.literal(true),
  execution_available: z.boolean(),
  execution_performed: z.literal(false),
});

export type ExecutionPreview = z.infer<typeof executionPreviewSchema>;

const recipeExecutionSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.enum(["validated_success", "validation_failed"]),
  recipe_id: z.string().min(1).max(120),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approval_id: z.string().min(1).max(120),
  execution_preview_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  step_results: z.array(z.object({
    step_id: z.string().min(1).max(120),
    skill_id: z.string().min(1).max(120),
    status: z.enum(["completed", "validated_success", "validation_failed"]),
    validation_performed: z.boolean(),
    output_ids: z.array(z.string().max(120)).max(100),
    outcome: z.unknown(),
    validation_outcome: z.unknown().nullable(),
  })).min(1).max(100),
  run_result_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  run_result_path: z.string().min(1).max(2000),
  evidence_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  evidence_path: z.string().min(1).max(2000),
  report_path: z.string().min(1).max(2000),
  execution_performed: z.literal(true),
  evidence_recorded: z.literal(true),
  report_written: z.literal(true),
});

export type RecipeExecutionResult = z.infer<typeof recipeExecutionSchema>;

const executionProgressSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.enum(["running", "validated_success", "validation_failed", "failed", "interrupted"]),
  execution_preview_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  recipe_id: z.string().min(1).max(120).nullable().optional(),
  recipe_filename: z.string().max(240).nullable().optional(),
  recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/).nullable().optional(),
  started_at: z.string().datetime({ offset: true }),
  finished_at: z.string().datetime({ offset: true }).nullable(),
  failed_step_id: z.string().max(120).nullable(),
  interruption_detected: z.boolean(),
  recovery_guidance: z.string().max(1000).nullable(),
  steps: z.array(z.object({
    step_id: z.string().min(1).max(120),
    skill_id: z.string().min(1).max(120),
    depends_on: z.array(z.string().min(1).max(120)).max(100).default([]),
    status: z.enum(["queued", "running", "completed", "validated_success", "validation_failed", "failed", "interrupted"]),
  })).min(1).max(100),
  execution_performed: z.boolean(),
});

export type ExecutionProgress = z.infer<typeof executionProgressSchema>;

const executionInventorySchema = z.object({
  schema_version: z.literal("1.0"),
  attempts: z.array(z.object({
    execution_preview_sha256: z.string().regex(/^[a-f0-9]{64}$/),
    status: z.enum(["running", "validated_success", "validation_failed", "failed", "interrupted"]),
    recipe_id: z.string().min(1).max(120).nullable(),
    recipe_filename: z.string().max(240).nullable(),
    recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/).nullable(),
    started_at: z.string().datetime({ offset: true }),
    finished_at: z.string().datetime({ offset: true }).nullable(),
    failed_step_id: z.string().max(120).nullable(),
    interruption_detected: z.boolean(),
    step_count: z.number().int().positive().max(100),
  })).max(200),
  attempt_count: z.number().int().nonnegative().max(200),
  inventory_truncated: z.boolean(),
  execution_performed: z.literal(false),
});

export type ExecutionInventory = z.infer<typeof executionInventorySchema>;

const plannerResultSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("planned_not_saved"),
  agent_id: z.literal("planner"),
  model: z.string().min(1).max(200),
  original_request: z.string().min(1).max(8000),
  allowed_skill_ids: z.array(z.string().regex(/^[a-z][a-z0-9_]*$/)).min(1).max(20),
  context_references: z.array(z.string().min(1).max(500)).max(100),
  plan: z.object({
    schema_version: z.literal("1.0"),
    status: z.literal("planned"),
    summary: z.string().min(1).max(2000),
    steps: z.array(z.object({
      step_id: z.string().regex(/^step_[1-9][0-9]*$/),
      skill: z.string().regex(/^[a-z][a-z0-9_]*$/),
      purpose: z.string().min(1).max(1000),
      arguments: z.record(z.string(), z.unknown()),
      requires_approval: z.boolean(),
      expected_artifacts: z.array(z.string().max(1000)).max(100),
      validation_required: z.boolean(),
    })).min(1).max(20),
    assumptions: z.array(z.string().max(2000)).max(100),
    risks: z.array(z.string().max(2000)).max(100),
    execution_performed: z.literal(false),
    validation_performed: z.literal(false),
  }),
  plan_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  warnings: z.array(z.string().max(2000)).max(100),
  plan_saved: z.literal(false),
  approval_performed: z.literal(false),
  execution_performed: z.literal(false),
});

export type InterfacePlannerResult = z.infer<typeof plannerResultSchema>;

const savedPlannerResultSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.enum(["stored", "already_stored"]),
  plan_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  plan_filename: z.string().regex(/^planner-plan\.[a-f0-9]{64}\.json$/),
  plan_saved: z.literal(true),
  plan_modified: z.boolean(),
  approval_performed: z.literal(false),
  execution_performed: z.literal(false),
});

export type SavedPlannerResult = z.infer<typeof savedPlannerResultSchema>;

const preparedPlanApprovalSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.enum(["prepared_not_recorded", "approval_not_required"]),
  plan_filename: z.string().regex(/^planner-plan\.[a-f0-9]{64}\.json$/),
  plan_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approval_request_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approval_required_step_ids: z.array(z.string().regex(/^step_[1-9][0-9]*$/)).max(20),
  steps: z.array(z.object({
    step_id: z.string().regex(/^step_[1-9][0-9]*$/),
    skill: z.string().regex(/^[a-z][a-z0-9_]*$/),
    purpose: z.string().min(1).max(1000),
    arguments: z.record(z.string(), z.unknown()),
    requires_approval: z.boolean(),
    validation_required: z.boolean(),
  })).min(1).max(20),
  approval_recorded: z.literal(false),
  execution_performed: z.literal(false),
});

export type PreparedPlanApproval = z.infer<typeof preparedPlanApprovalSchema>;

const recordedPlanApprovalSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("recorded"),
  decision: z.enum(["approved", "denied"]),
  approval_id: z.string().regex(/^approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}$/),
  approval_filename: z.string().regex(/^approval-[0-9]{8}t[0-9]{6}z-[a-f0-9]{8}\.json$/),
  plan_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  approved_step_ids: z.array(z.string().regex(/^step_[1-9][0-9]*$/)).max(20),
  expires_at: z.string().datetime({ offset: true }).nullable(),
  secrets_redacted: z.literal(true),
  approval_recorded: z.literal(true),
  execution_performed: z.literal(false),
});

export type RecordedPlanApproval = z.infer<typeof recordedPlanApprovalSchema>;

const verifiedPlanApprovalSchema = z.object({
  schema_version: z.literal("1.0"), status: z.literal("verified"),
  approved: z.boolean(), decision: z.enum(["approved", "denied"]),
  approval_id: z.string(), plan_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  verified_step_ids: z.array(z.string().regex(/^step_[1-9][0-9]*$/)).max(20),
  reason: z.string(), independent_verification_performed: z.literal(true),
  plan_modified: z.literal(false), approval_modified: z.literal(false),
  execution_performed: z.literal(false),
});
export type VerifiedPlanApproval = z.infer<typeof verifiedPlanApprovalSchema>;

const planExecutionPreviewSchema = z.object({
  schema_version: z.literal("1.0"), status: z.literal("previewed_not_executed"),
  execution_preview_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  envelope: z.object({ schema_version: z.literal("1.0"), plan_sha256: z.string(), approval_id: z.string(), approved_step_ids: z.array(z.string()), selected_skills: z.array(z.string()), tool_name: z.literal("run_vector_postgis_workflow"), tool_arguments: z.record(z.string(), z.unknown()), execution_performed: z.literal(false) }),
  execution_available: z.literal(false), execution_performed: z.literal(false),
});
export type PlanExecutionPreview = z.infer<typeof planExecutionPreviewSchema>;
const compiledPlanRecipeSchema = z.object({ schema_version: z.literal("1.0"), status: z.literal("compiled_not_saved"), source_plan_sha256: z.string(), recipe_sha256: z.string(), recipe: z.object({ recipe_id: z.string(), summary: z.string(), steps: z.array(z.object({ step_id: z.string(), skill_id: z.string(), depends_on: z.array(z.string()), arguments: z.record(z.string(), z.unknown()), output_ids: z.array(z.string()) }).passthrough()) }).passthrough(), approval_required_step_ids: z.array(z.string()), validation_required_step_ids: z.array(z.string()), recipe_saved: z.literal(false), recipe_approval_performed: z.literal(false), execution_performed: z.literal(false) });
export type CompiledPlanRecipe = z.infer<typeof compiledPlanRecipeSchema>;

const plannerSkillCatalogSchema = z.object({
  schema_version: z.literal("1.0"),
  skills: z.array(z.object({
    id: z.string().regex(/^[a-z][a-z0-9_]*$/),
    kind: z.string().nullable(),
    access: z.string().nullable(),
    approval_required: z.boolean(),
    validation_required: z.boolean(),
  })).min(1).max(200),
  skill_count: z.number().int().positive().max(200),
  catalog_validated: z.literal(true),
  execution_performed: z.literal(false),
});

export type PlannerSkillCatalog = z.infer<typeof plannerSkillCatalogSchema>;

const savedPlanInventorySchema = z.object({
  schema_version: z.literal("1.0"), status: z.literal("inspected"),
  plans: z.array(z.object({
    plan_filename: z.string(), plan_sha256: z.string().regex(/^[a-f0-9]{64}$/), saved_at: z.string(),
    planner_result: z.object({ agent_id: z.literal("planner"), model: z.string(), original_request: z.string(), context_references: z.array(z.string()), plan: plannerResultSchema.shape.plan, warnings: z.array(z.string()) }),
    approvals: z.array(z.object({ approval_id: z.string(), approval_filename: z.string(), decision: z.enum(["approved", "denied"]), step_ids: z.array(z.string()), created_at: z.string(), expires_at: z.string().nullable() })).max(500),
  })).max(200), plan_count: z.number().int().nonnegative(), files_modified: z.literal(false), execution_performed: z.literal(false),
});
export type SavedPlanInventory = z.infer<typeof savedPlanInventorySchema>;

async function boundedJson(response: Response): Promise<unknown> {
  const declaredLength = Number(response.headers.get("content-length") ?? "0");
  if (declaredLength > MAX_INTERFACE_RESPONSE_BYTES) throw new Error("interface response is too large");
  const text = await response.text();
  if (new TextEncoder().encode(text).byteLength > MAX_INTERFACE_RESPONSE_BYTES) throw new Error("interface response is too large");
  return JSON.parse(text);
}

export async function loadApiRecipeTemplates(): Promise<RecipeTemplate[]> {
  const response = await fetch("/api/v1/recipe-templates", { cache: "no-store", credentials: "same-origin" });
  if (!response.ok) throw new Error("interface template service is unavailable");
  return recipeTemplateCatalogSchema.parse(await boundedJson(response)).templates;
}

export async function compileRecipeProposal(proposal: BrowserRecipeProposal): Promise<InterfaceCompilation> {
  const validated = browserRecipeProposalSchema.parse(proposal);
  const response = await fetch("/api/v1/recipe-proposals/compile", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(validated),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "proposal compilation failed");
  }
  return compilationSchema.parse(payload);
}

export async function saveReviewedRecipe(
  proposal: BrowserRecipeProposal,
  confirmedRecipeSha256: string,
): Promise<SavedInterfaceRecipe> {
  const validated = browserRecipeProposalSchema.parse(proposal);
  const response = await fetch("/api/v1/recipe-proposals/save-reviewed", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "save_reviewed_recipe",
      proposal: validated,
      confirmed_recipe_sha256: z.string().regex(/^[a-f0-9]{64}$/).parse(confirmedRecipeSha256),
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "reviewed recipe save failed");
  }
  return savedRecipeSchema.parse(payload);
}

export async function saveCompiledPlannerRecipe(
  compiled: CompiledPlanRecipe,
  stored: SavedPlannerResult,
  prepared: PreparedPlanApproval,
  recorded: RecordedPlanApproval,
): Promise<SavedInterfaceRecipe> {
  const response = await fetch("/api/v1/plans/save-reviewed-recipe", {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "save_reviewed_plan_recipe",
      plan_filename: stored.plan_filename,
      confirmed_plan_sha256: stored.plan_sha256,
      confirmed_approval_request_sha256: prepared.approval_request_sha256,
      approval_filename: recorded.approval_filename,
      confirmed_recipe_sha256: compiled.recipe_sha256,
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "reviewed Planner recipe save failed");
  }
  return savedRecipeSchema.parse(payload);
}

export async function loadSavedRecipes(): Promise<SavedRecipeInventory> {
  const response = await fetch("/api/v1/recipes", {
    cache: "no-store",
    credentials: "same-origin",
  });
  const payload = await boundedJson(response);
  if (!response.ok) throw new Error("saved recipe inventory is unavailable");
  return savedRecipeInventorySchema.parse(payload);
}

export async function prepareRecipeApproval(
  recipeFilename: string,
  confirmedRecipeSha256: string,
): Promise<PreparedApprovalRequest> {
  const response = await fetch("/api/v1/recipes/prepare-approval", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "prepare_recipe_approval",
      recipe_filename: recipeFilename,
      confirmed_recipe_sha256: confirmedRecipeSha256,
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "approval request preparation failed");
  }
  return approvalRequestSchema.parse(payload);
}

export async function recordRecipeApproval(input: {
  request: PreparedApprovalRequest;
  decision: "approved" | "denied";
  approver: string;
  reason: string;
  validForMinutes: number | null;
}): Promise<RecordedRecipeApproval> {
  const response = await fetch("/api/v1/recipes/record-approval", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "record_recipe_approval",
      recipe_filename: input.request.recipe_filename,
      confirmed_recipe_sha256: input.request.recipe_sha256,
      confirmed_approval_request_sha256: input.request.approval_request_sha256,
      decision: input.decision,
      approver: input.approver,
      reason: input.reason,
      valid_for_minutes: input.validForMinutes,
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "approval decision could not be recorded");
  }
  return recordedApprovalSchema.parse(payload);
}

export async function verifyRecordedRecipeApproval(
  request: PreparedApprovalRequest,
  recorded: RecordedRecipeApproval,
): Promise<VerifiedRecipeApproval> {
  const response = await fetch("/api/v1/recipes/verify-approval", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "verify_recipe_approval",
      recipe_filename: request.recipe_filename,
      confirmed_recipe_sha256: request.recipe_sha256,
      confirmed_approval_request_sha256: request.approval_request_sha256,
      approval_filename: recorded.approval_filename,
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "approval verification failed");
  }
  return verifiedApprovalSchema.parse(payload);
}

export async function prepareExecutionPreview(
  request: PreparedApprovalRequest,
  recorded: RecordedRecipeApproval,
): Promise<ExecutionPreview> {
  const response = await fetch("/api/v1/recipes/preview-execution", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "prepare_execution_preview",
      recipe_filename: request.recipe_filename,
      confirmed_recipe_sha256: request.recipe_sha256,
      confirmed_approval_request_sha256: request.approval_request_sha256,
      approval_filename: recorded.approval_filename,
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "execution preview failed");
  }
  return executionPreviewSchema.parse(payload);
}

export async function executeExactPreview(
  request: PreparedApprovalRequest,
  recorded: RecordedRecipeApproval,
  preview: ExecutionPreview,
): Promise<RecipeExecutionResult> {
  const response = await fetch("/api/v1/recipes/execute", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "execute_exact_preview",
      recipe_filename: request.recipe_filename,
      confirmed_recipe_sha256: request.recipe_sha256,
      confirmed_approval_request_sha256: request.approval_request_sha256,
      approval_filename: recorded.approval_filename,
      confirmed_execution_preview_sha256: preview.execution_preview_sha256,
      confirmation: "execute_exact_preview",
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "approved execution failed");
  }
  return recipeExecutionSchema.parse(payload);
}

export async function loadExecutionProgress(executionPreviewSha256: string): Promise<ExecutionProgress | null> {
  const digest = z.string().regex(/^[a-f0-9]{64}$/).parse(executionPreviewSha256);
  const response = await fetch(`/api/v1/executions/${digest}`, {
    cache: "no-store",
    credentials: "same-origin",
  });
  if (response.status === 404) return null;
  const payload = await boundedJson(response);
  if (!response.ok) throw new Error("execution progress is unavailable");
  return executionProgressSchema.parse(payload);
}

export async function loadExecutionInventory(): Promise<ExecutionInventory> {
  const response = await fetch("/api/v1/executions", {
    cache: "no-store",
    credentials: "same-origin",
  });
  const payload = await boundedJson(response);
  if (!response.ok) throw new Error("execution inventory is unavailable");
  return executionInventorySchema.parse(payload);
}

export async function loadPlannerSkills(): Promise<PlannerSkillCatalog> {
  const response = await fetch("/api/v1/planner-skills", {
    cache: "no-store",
    credentials: "same-origin",
  });
  const payload = await boundedJson(response);
  if (!response.ok) throw new Error("planner skill catalog is unavailable");
  return plannerSkillCatalogSchema.parse(payload);
}

export async function loadSavedPlans(): Promise<SavedPlanInventory> {
  const response = await fetch("/api/v1/plans", { cache: "no-store", credentials: "same-origin" });
  const payload = await boundedJson(response);
  if (!response.ok) throw new Error("saved plan inventory is unavailable");
  return savedPlanInventorySchema.parse(payload);
}

export async function createPlannerPlan(request: string, allowedSkillIds: string[]): Promise<InterfacePlannerResult> {
  const boundedRequest = z.string().trim().min(1).max(8000).parse(request);
  const boundedSkills = z.array(z.string().regex(/^[a-z][a-z0-9_]*$/)).min(1).max(20).parse(allowedSkillIds);
  const response = await fetch("/api/v1/plans/create", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "plan_task", request: boundedRequest, allowed_skill_ids: boundedSkills }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "planner could not produce a validated plan");
  }
  return plannerResultSchema.parse(payload);
}

export async function saveReviewedPlannerPlan(result: InterfacePlannerResult): Promise<SavedPlannerResult> {
  const response = await fetch("/api/v1/plans/save-reviewed", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "save_reviewed_plan",
      confirmed_plan_sha256: result.plan_sha256,
      allowed_skill_ids: result.allowed_skill_ids,
      planner_result: {
        agent_id: result.agent_id,
        model: result.model,
        original_request: result.original_request,
        context_references: result.context_references,
        plan: result.plan,
        warnings: result.warnings,
      },
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "reviewed plan could not be stored");
  }
  return savedPlannerResultSchema.parse(payload);
}

export async function preparePlannerApproval(stored: SavedPlannerResult): Promise<PreparedPlanApproval> {
  const response = await fetch("/api/v1/plans/prepare-approval", {
    method: "POST",
    cache: "no-store",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "prepare_plan_approval",
      plan_filename: stored.plan_filename,
      confirmed_plan_sha256: stored.plan_sha256,
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "plan approval request could not be prepared");
  }
  return preparedPlanApprovalSchema.parse(payload);
}

export async function recordPlannerApproval(input: {
  stored: SavedPlannerResult;
  prepared: PreparedPlanApproval;
  decision: "approved" | "denied";
  approver: string;
  reason: string;
  validForMinutes: number | null;
}): Promise<RecordedPlanApproval> {
  const response = await fetch("/api/v1/plans/record-approval", {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "record_plan_approval",
      plan_filename: input.stored.plan_filename,
      confirmed_plan_sha256: input.stored.plan_sha256,
      confirmed_approval_request_sha256: input.prepared.approval_request_sha256,
      decision: input.decision,
      approver: input.approver,
      reason: input.reason,
      valid_for_minutes: input.validForMinutes,
    }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) {
    const message = z.object({ error: z.string().max(300) }).safeParse(payload);
    throw new Error(message.success ? message.data.error : "plan approval could not be recorded");
  }
  return recordedPlanApprovalSchema.parse(payload);
}

export async function verifyPlannerApproval(stored: SavedPlannerResult, prepared: PreparedPlanApproval, recorded: RecordedPlanApproval): Promise<VerifiedPlanApproval> {
  const response = await fetch("/api/v1/plans/verify-approval", {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "verify_plan_approval", plan_filename: stored.plan_filename, confirmed_plan_sha256: stored.plan_sha256, confirmed_approval_request_sha256: prepared.approval_request_sha256, approval_filename: recorded.approval_filename }),
  });
  const payload = await boundedJson(response);
  if (!response.ok) throw new Error("plan approval verification failed");
  return verifiedPlanApprovalSchema.parse(payload);
}

export async function previewPlannerExecution(stored: SavedPlannerResult, prepared: PreparedPlanApproval, recorded: RecordedPlanApproval): Promise<PlanExecutionPreview> {
  const response = await fetch("/api/v1/plans/preview-execution", { method: "POST", cache: "no-store", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "preview_plan_execution", plan_filename: stored.plan_filename, confirmed_plan_sha256: stored.plan_sha256, confirmed_approval_request_sha256: prepared.approval_request_sha256, approval_filename: recorded.approval_filename }) });
  const payload = await boundedJson(response);
  if (!response.ok) { const message = z.object({ error: z.string().max(500) }).safeParse(payload); throw new Error(message.success ? message.data.error : "execution preview failed"); }
  return planExecutionPreviewSchema.parse(payload);
}
export async function compilePlannerRecipe(stored: SavedPlannerResult, prepared: PreparedPlanApproval, recorded: RecordedPlanApproval): Promise<CompiledPlanRecipe> {
  const response = await fetch("/api/v1/plans/compile-recipe", { method: "POST", cache: "no-store", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "compile_plan_recipe", plan_filename: stored.plan_filename, confirmed_plan_sha256: stored.plan_sha256, confirmed_approval_request_sha256: prepared.approval_request_sha256, approval_filename: recorded.approval_filename }) });
  const payload = await boundedJson(response); if (!response.ok) { const message = z.object({ error: z.string().max(500) }).safeParse(payload); throw new Error(message.success ? message.data.error : "Planner recipe compilation failed"); } return compiledPlanRecipeSchema.parse(payload);
}
