import {z} from 'zod';
const sourceOptions=z.object({sheet:z.string().nullable().optional(),header_row:z.number().optional(),cell_range:z.string().nullable().optional(),records_key:z.string().nullable().optional()});
export const fieldGuidanceSchema=z.object({schema_version:z.literal('field-guidance-v1'),source:z.string(),source_sha256:z.string(),source_rows:z.number(),matching_rows:z.number(),field_count:z.number(),omitted_fields:z.number(),basis:z.string(),advisory_only:z.literal(true),
 source_options:sourceOptions.optional(),
 analysis_starters:z.array(z.object({column:z.string(),analysis:z.object({source_options:sourceOptions.optional(),statistics:z.object({methods:z.array(z.literal('describe')),columns:z.array(z.string()),missing_policy:z.literal('error')})})})).optional().default([]),
 analysis_opportunities:z.array(z.object({id:z.string(),title:z.string(),fields:z.array(z.string()),operation:z.string(),contract:z.string(),reason:z.string(),requirements:z.array(z.string())})).optional().default([]),
 candidates:z.object({measurement:z.array(z.string()),grouping:z.array(z.string()),identifier:z.array(z.string()),review:z.array(z.string())}),
 fields:z.array(z.object({name:z.string(),role:z.string(),kind:z.string(),basis:z.array(z.string()),confidence:z.string(),numeric_count:z.number().nullable(),missing_count:z.number(),distinct_count:z.number().nullable(),suggestion:z.string(),cautions:z.array(z.string())})),limitations:z.array(z.string())});
export type FieldGuidance=z.infer<typeof fieldGuidanceSchema>;
export function parseFieldGuidance(value:unknown){const result=fieldGuidanceSchema.safeParse(value);return result.success?result.data:null;}
