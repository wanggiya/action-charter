import { z } from "zod";
const list = z.array(z.string().min(1).max(600)).min(1).max(8);
export const methodDocumentSchema = z.object({title:z.string().min(1).max(120),purpose:z.string().min(1).max(800),inputs:list,prerequisites:list,operations:z.array(z.object({skill:z.string().min(1).max(100),guidance:z.string().min(1).max(600)})).min(1).max(12),checks:list,limitations:list});
export type MethodDocument = z.infer<typeof methodDocumentSchema>;
const sourceSchema=z.object({conversation_id:z.string(),conversation_revision:z.number().int(),message_indices:z.array(z.number().int()),include_workflow:z.boolean(),source_sha256:z.string()});
export type MethodSource=z.infer<typeof sourceSchema>;
const versionSchema=z.object({document:methodDocumentSchema,source:sourceSchema,saved_at:z.string()});
const recordSchema=versionSchema.extend({method_id:z.string(),conversation_id:z.string(),revision:z.number().int(),status:z.literal('operator_reviewed_unvalidated'),versions:z.array(versionSchema).max(8)});
export type MethodRecord=z.infer<typeof recordSchema>;
export const methodStateSchema=z.object({enabled:z.boolean(),revision:z.number().int(),approval_performed:z.literal(false),execution_performed:z.literal(false)});
export type MethodState=z.infer<typeof methodStateSchema>;
export const methodListSchema=methodStateSchema.extend({methods:z.array(recordSchema).max(128)});
export const methodProposalSchema=z.object({document:methodDocumentSchema,source:sourceSchema,model:z.string(),status:z.literal('unvalidated_proposal'),prompt_bytes:z.number(),model_calls:z.literal(1),approval_performed:z.literal(false),execution_performed:z.literal(false)});
export async function methodMemory<T>(fields:Record<string,unknown>,schema:z.ZodType<T>):Promise<T>{
 const response=await fetch('/api/v1/method-memory',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',cache:'no-store',body:JSON.stringify(fields)});
 const raw=await response.text();if(raw.length>2_000_000)throw new Error('Method response exceeds its size limit');
 let data:unknown;try{data=JSON.parse(raw);}catch{throw new Error('Method service returned an unreadable response');}
 if(!response.ok){const failure=z.object({error:z.string(),retry_guidance:z.string().optional()}).safeParse(data);throw new Error(failure.success?[failure.data.error,failure.data.retry_guidance].filter(Boolean).join(' '):'Method service unavailable');}
 return schema.parse(data);
}
export const methodSavedSchema=z.object({method:recordSchema,approval_performed:z.literal(false),execution_performed:z.literal(false)});
export const methodDeletedSchema=z.object({deleted:z.literal(true),approval_performed:z.literal(false),execution_performed:z.literal(false)});
