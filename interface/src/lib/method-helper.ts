import {z} from 'zod';
import {methodDocumentSchema} from './method-memory';
export const helperReceiptSchema=z.object({contract_version:z.literal('1.0'),status:z.string().max(80),evidence_kind:z.literal('validated_plan_only'),model_calls:z.number().int().min(0).max(1),note_id:z.string().optional(),source_plan_sha256:z.string().optional(),setting_revision:z.number().int().optional(),finding:z.string().max(100).nullable().optional(),elapsed_ms:z.number().optional()});
export const helperBundleSchema=z.object({contract_version:z.literal('1.0'),helper_version:z.string(),model:z.string().max(200),conversation_id:z.string(),note_id:z.string(),source_plan_sha256:z.string(),source_conversation_revision:z.number().int(),status:z.literal('machine_generated_unvalidated'),evidence_kind:z.literal('validated_plan_only'),document:methodDocumentSchema});
export const helperStatusSchema=helperReceiptSchema.extend({note:helperBundleSchema.optional()});
export type HelperStatus=z.infer<typeof helperStatusSchema>;
