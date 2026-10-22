import {z} from 'zod';
export const capabilityCandidateSchema=z.object({
 schema_version:z.literal('1.0'),status:z.enum(['tested','rejected','use_existing']),operation_id:z.string(),package_sha256:z.string(),
 definition:z.object({source_column:z.string(),output_column:z.string(),steps:z.array(z.object({kind:z.string(),old:z.string().nullable().optional(),new:z.string().nullable().optional()}))}),
 tests:z.object({passed:z.boolean(),cases:z.array(z.unknown()).optional(),negative_cases:z.array(z.unknown()).optional(),finding:z.string().optional()}).passthrough().nullable(),
 critic:z.object({status:z.string(),assessment:z.string().nullable(),reason:z.string()}).passthrough().nullable(),
 candidate_sha256:z.string().nullable(),request:z.string(),installed:z.boolean().default(false),
}).passthrough();
export type CapabilityCandidate=z.infer<typeof capabilityCandidateSchema>;
