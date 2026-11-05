import {useEffect,useState} from 'react';
import {z} from 'zod';
import {downloadBlob} from '../lib/report-document';
const resources=z.object({elapsed_seconds:z.number(),process_cpu_seconds:z.number(),api_rss_sampled_peak_bytes:z.number().nullable(),system_available_min_bytes:z.number().nullable()}).passthrough();
const row=z.object({id:z.string(),kind:z.string(),status:z.string(),started_at:z.string(),error_code:z.string().nullable(),role:z.string().optional(),phase:z.string().optional(),model:z.string().optional(),timeout_seconds:z.number().optional(),output_token_limit:z.number().optional(),reasoning_effort:z.string().nullable().optional(),prompt_bytes:z.number().optional(),schema_bytes:z.number().optional(),prompt_tokens:z.number().nullable().optional(),completion_tokens:z.number().nullable().optional(),submission_status:z.string().optional(),workflow_run_id:z.string().nullable().optional(),workflow_status:z.string().optional(),outcome_review:z.object({status:z.string().optional(),error_code:z.string().optional(),timeout_seconds:z.number().nullable().optional()}).optional(),storage_available:z.boolean().optional(),resources:resources.optional()}).passthrough();
const schema=z.object({schema_version:z.literal('request-diagnostics-v1'),conversation_id:z.string(),records:z.array(row).max(100),limitations:z.array(z.string()),execution_performed:z.literal(false),authority_granted:z.literal(false)}).passthrough();
const recovery=(code:string|null)=>code==='model_timeout'?'The response did not finish before its configured timeout. This alone does not establish context overflow or RAM exhaustion. Check phase, request size and resource observations before retrying.':code==='model_unavailable'?'The configured model endpoint could not be reached. Check that its service is running.':code==='planner_invalid_schema'||code==='model_invalid_response'?'The response did not satisfy the required structure. No malformed plan becomes executable.':code==='planner_policy_rejected'?'The proposed operations failed deterministic validation. Review the current proposal and original error; extra authorization cannot repair an invalid plan.':code==='process_interrupted'?'The recording process stopped before completion. Inspect the submission and history before a deliberate retry. No retry is performed here.':code?'Inspect the original error, current workflow and submission receipt before retrying. No RAM or context-overflow diagnosis is inferred.':null;
const mb=(value:number|null|undefined)=>value==null?'Unknown':`${(value/1048576).toFixed(1)} MiB`;
export function RequestDiagnostics({conversationId,version,reveal=0}:{conversationId:string;version:string;reveal?:number}){
 const [open,setOpen]=useState(false),[data,setData]=useState<z.infer<typeof schema>|null>(null),[error,setError]=useState(''),[refresh,setRefresh]=useState(0);
 useEffect(()=>{setData(null);setError('');setOpen(false);},[conversationId]);
 useEffect(()=>{if(reveal>0)setOpen(true);},[reveal]);
 useEffect(()=>{
  if(!open)return;let alive=true;setError('');
  void(async()=>{try{
   const response=await fetch('/api/v1/planner/diagnostics',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({conversation_id:conversationId}),cache:'no-store'});
   const raw=await response.text();if(raw.length>2000000)throw new Error('Diagnostics exceed display budget');
   if(!response.ok)throw new Error('Request diagnostics unavailable; restart the updated API if necessary.');
   const value=schema.parse(JSON.parse(raw));if(value.conversation_id!==conversationId)throw new Error('Diagnostics scope mismatch');
   if(alive)setData(value);
  }catch(e){if(alive){setData(null);setError(e instanceof Error?e.message:'Diagnostics unavailable');}}})();
  return()=>{alive=false;};
 },[conversationId,open,version,refresh]);
 return <details className="request-diagnostics" id={`request-diagnostics-${conversationId}`} open={open} onToggle={e=>setOpen(e.currentTarget.open)}>
  <summary>Request diagnostics</summary>
  {open&&<><p>Recent submissions and model calls in this chat. Opening this panel never retries or executes work.</p>
   <div className="request-diagnostics-actions"><button type="button" onClick={()=>setRefresh(v=>v+1)}>Refresh diagnostics</button><button type="button" disabled={!data} onClick={()=>data&&downloadBlob(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),'request-diagnostics.json')}>Export diagnostics JSON</button></div>
   {error&&<p role="alert">{error}</p>}{!data&&!error&&<p role="status">Loading diagnostics…</p>}
   {data&&<>{data.records.length===0&&<p>No diagnostics were recorded for this chat. Earlier failures cannot be reconstructed.</p>}
    {data.records.map(record=><details key={record.id}><summary>{record.kind==='call'?`${record.role} · ${record.phase}`:record.workflow_run_id?'Workflow processing':'Submission'} · {record.status}{record.error_code?` · ${record.error_code}`:''}</summary>
     {record.storage_available===false&&<p role="status">Telemetry storage was incomplete; some usage records may be missing.</p>}{record.error_code&&<p>{recovery(record.error_code)}</p>}{record.role==='critic'&&record.phase==='outcome_review'&&record.error_code==='model_timeout'&&<p>Critic review timed out after {record.timeout_seconds} seconds. Check the linked workflow status; this review does not retry execution.</p>}
     {record.role==='executor'&&record.phase==='workflow'&&<p>Legacy phase label: older records can include post-run review under executor/workflow. Check the recorded workflow outcome.</p>}
     <dl><dt>Started</dt><dd>{record.started_at}</dd><dt>Elapsed</dt><dd>{record.resources?`${record.resources.elapsed_seconds.toFixed(2)} s`:'Not finished'}</dd>
      {record.model&&<><dt>Model</dt><dd>{record.model}</dd><dt>Reasoning</dt><dd>{record.reasoning_effort??'Provider default (not set)'}</dd><dt>Timeout / output limit</dt><dd>{record.timeout_seconds} s / {record.output_token_limit} tokens</dd><dt>Prompt / schema</dt><dd>{record.prompt_bytes?.toLocaleString()} / {record.schema_bytes?.toLocaleString()} bytes</dd><dt>Reported input / output tokens</dt><dd>{record.prompt_tokens??'Unknown'} / {record.completion_tokens??'Unknown'}</dd></>}
      <dt>API sampled peak RSS</dt><dd>{mb(record.resources?.api_rss_sampled_peak_bytes)}</dd><dt>Minimum system available RAM</dt><dd>{mb(record.resources?.system_available_min_bytes)}</dd><dt>Process CPU</dt><dd>{record.resources?`${record.resources.process_cpu_seconds.toFixed(2)} s`:'Unknown'}</dd>
      {record.kind==='turn'&&<>{record.workflow_status&&<><dt>Workflow status</dt><dd>{record.workflow_status}</dd></>}{record.outcome_review&&<><dt>Critic review</dt><dd>{record.outcome_review.status==='unavailable'&&record.outcome_review.error_code==='model_timeout'?'Unavailable — model timed out':record.outcome_review.status??'Unknown'}</dd></>}<dt>Dispatch</dt><dd>{record.workflow_run_id?`Recorded run ${record.workflow_run_id}`:record.submission_status??'No dispatch recorded here; check the submission receipt'}</dd></>}
     </dl></details>)}
    <details><summary>Measurement limits and privacy</summary><ul>{data.limitations.map(text=><li key={text}>{text}</li>)}</ul><p>These usage records exclude prompts, data rows, raw model responses and credentials. Export contains technical identifiers and model names.</p></details>
   </>}
  </>}
 </details>;
}
