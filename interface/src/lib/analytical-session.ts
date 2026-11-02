import {z} from 'zod';
export const analyticalSessionSchema=z.object({directory:z.string(),conversation_revision:z.number().int().positive().optional(),status:z.enum(['completed','partial','needs_input']),message:z.string(),
  inventory:z.object({files:z.array(z.object({path:z.string(),bytes:z.number(),format:z.string(),possible_sample:z.boolean(),sample_provenance:z.string(),columns:z.array(z.string()).optional(),possible_codebook:z.boolean().optional()}))}),
  observations:z.array(z.object({tool:z.string(),result:z.record(z.unknown())})),
  journal:z.array(z.object({tool:z.string(),status:z.string(),path:z.string().optional()})),
  model_calls:z.number(),tool_calls:z.number(),elapsed_seconds:z.number(),data_written:z.literal(false),workflow_changed:z.literal(false)});
export type AnalyticalSession=z.infer<typeof analyticalSessionSchema>;
