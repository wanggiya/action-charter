import { z } from "zod";

const safeIdentifier = z.string().regex(/^[a-z][a-z0-9_]*$/).max(100);
const recipeTemplateStepSchema = z.object({
  step_id: z.string().regex(/^step_[1-9][0-9]*$/),
  skill_id: safeIdentifier,
  depends_on: z.array(z.string().regex(/^step_[1-9][0-9]*$/)).max(20),
  output_ids: z.array(safeIdentifier).min(1).max(20),
});

export const recipeTemplateSchema = z.object({
  template_id: safeIdentifier,
  parameter_profile: z.enum(["vector_inspection", "raster_inspection", "raster_conversion", "vector_conversion", "vector_postgis"]),
  assessment_policy: z.enum(["none", "vector_conversion", "raster_conversion"]),
  skill_ids: z.array(safeIdentifier).min(1).max(20),
  required_parameters: z.array(safeIdentifier).min(1).max(20),
  steps: z.array(recipeTemplateStepSchema).min(1).max(20),
});

export const recipeTemplateCatalogSchema = z.object({
  schema_version: z.literal("1.0"),
  templates: z.array(recipeTemplateSchema).min(1).max(50),
  catalog_validated: z.literal(true),
  files_modified: z.literal(false),
  execution_performed: z.literal(false),
});

export const browserRecipeProposalSchema = z.object({
  schema_version: z.literal("1.0"),
  status: z.literal("proposed_not_compiled"),
  original_request: z.string().min(1).max(8000),
  summary: z.string().min(1).max(2000),
  recipe_id_hint: z.string().regex(/^[a-z0-9][a-z0-9_-]{0,100}$/).nullable(),
  selection: z.object({ template_id: safeIdentifier, parameters: z.record(z.string(), z.string().min(1).max(2000)) }),
  assumptions: z.array(z.string().max(2000)).max(20),
  missing_information: z.array(z.string().max(2000)).max(20),
  warnings: z.array(z.string().max(2000)).max(20),
  compilation_performed: z.literal(false),
  execution_requested: z.literal(false),
  approval_performed: z.literal(false),
  execution_performed: z.literal(false),
});

export type RecipeTemplate = z.infer<typeof recipeTemplateSchema>;
export type BrowserRecipeProposal = z.infer<typeof browserRecipeProposalSchema>;
