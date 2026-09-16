import { z } from "zod";
import { browserRecipeProposalSchema, recipeTemplateCatalogSchema, type BrowserRecipeProposal, type RecipeTemplate } from "./recipe-templates";

const MAX_INTERFACE_RESPONSE_BYTES = 500_000;

const compilationSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("compiled"),
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
