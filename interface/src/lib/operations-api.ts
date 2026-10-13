import { z } from "zod";
const operation=z.object({id:z.string(),name:z.string(),version:z.string().nullable(),workflow_supported:z.boolean(),result_schema_available:z.boolean(),parameters_schema:z.record(z.unknown()),output_schema:z.record(z.unknown()),outputs:z.array(z.object({contract:z.string()})),dependencies:z.array(z.string()),runtime_requirements:z.array(z.object({distribution:z.string(),requirement:z.string(),installed_version:z.string().nullable(),available:z.boolean()})),effects:z.object({access:z.string(),reads:z.string(),writes:z.string()}),approval_required:z.boolean(),validation_required:z.boolean(),origin:z.string(),adapter_configuration:z.record(z.unknown()).nullable(),package_sha256:z.string().nullable()});
const parameter=z.object({name:z.string(),kind:z.string(),annotation:z.string().nullable(),default:z.string().nullable(),required:z.boolean()});
const candidate=z.object({candidate_id:z.string(),distribution:z.string(),version:z.string(),qualified_name:z.string(),kind:z.string(),parameters:z.array(parameter),return_annotation:z.string().nullable(),documentation:z.string(),executable:z.literal(false),promotion:z.string()});
export const pageSchema=z.object({scan_sha256:z.string(),candidates:z.array(candidate),match_count:z.number(),next_offset:z.number().nullable(),truncated:z.boolean(),execution_performed:z.literal(false)});
export type CandidatePage=z.infer<typeof pageSchema>;
export const scanSchema=z.object({scan_sha256:z.string(),candidate_count:z.number(),truncated:z.boolean(),coverage:z.array(z.object({distribution:z.string(),files_scanned:z.number(),candidates:z.number(),complete:z.boolean(),reasons:z.array(z.string())})),unscanned_libraries:z.number(),imports_performed:z.literal(false),execution_performed:z.literal(false),page:pageSchema});
export type Scan=z.infer<typeof scanSchema>;
export const testSchema=z.object({package_sha256:z.string(),package_id:z.string(),passed:z.boolean(),cases:z.array(z.object({passed:z.boolean(),row_count:z.number(),columns:z.array(z.string())})),scope:z.literal("temporary_fixtures_only"),execution_performed:z.literal(false)});
export type PackageTest=z.infer<typeof testSchema>;
export async function operationRequest(path:string,body?:unknown):Promise<unknown> {
 const response=await fetch(`/api/v1/operations/${path}`,{cache:"no-store",credentials:"same-origin",...(body?{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}:{})});
 const raw=await response.text();if(raw.length>2000000)throw new Error("Operation metadata exceeds the response budget");
 const value:unknown=JSON.parse(raw);
 if(!response.ok){const error=z.object({error:z.string()}).safeParse(value);throw new Error(error.success?error.data.error:"Operation request blocked");}
 return value;
}
export async function loadOperationCatalog(){return z.object({operations:z.array(operation),execution_performed:z.literal(false)}).parse(await operationRequest('catalog'));}
export async function loadLibraries(){return z.object({libraries:z.array(z.object({name:z.string(),version:z.string()})),total_libraries:z.number(),inventory_truncated:z.boolean()}).parse(await operationRequest('libraries'));}

export const savedScansSchema=z.object({scans:z.array(scanSchema.omit({page:true})),execution_performed:z.literal(false)});
export async function loadSavedScans(){return savedScansSchema.parse(await operationRequest('scans'));}
