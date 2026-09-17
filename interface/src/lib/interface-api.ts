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
