import { z } from "zod";

export const recipeCandidateSchema=z.object({definition:z.record(z.unknown()),recipe_sha256:z.string(),source_plan_sha256:z.string().optional(),
  test_report:z.unknown(),critic:z.object({conclusion:z.string(),findings:z.array(z.string()),limitations:z.array(z.string())}),source_kind:z.string().optional()});
export type RecipeCandidate=z.infer<typeof recipeCandidateSchema>;
