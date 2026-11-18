import {useState} from 'react';
import {z} from 'zod';

const counts=z.object({
 recorded_calls:z.number(),not_sent_calls:z.number(),calls_with_both_counts:z.number(),
 calls_expected_usage:z.number(),
 calls_with_unknown_usage:z.number(),missing_call_records:z.number(),collection_incomplete:z.boolean(),
 calls_with_reported_input:z.number(),calls_with_reported_output:z.number(),
 reported_input_tokens:z.number().nullable(),reported_output_tokens:z.number().nullable(),
 model_call_seconds:z.number().nullable(),timed_calls:z.number(),
 end_to_end_output_tokens_per_second:z.number().nullable(),rate_measured_calls:z.number(),
 model_call_failures:z.number(),timeout_calls:z.number(),correction_calls:z.number(),
 coverage:z.enum(['partial','reported_for_visible_calls','not_sent','no_recorded_calls']),
}).passthrough();
const group=counts.extend({role:z.string(),provider_profile_id:z.string(),model:z.string()});
const scope=counts.extend({id:z.string(),label:z.string(),kind:z.enum(['chat','submission','workflow']),
 workflow_status:z.string().nullable(),by_role_model:z.array(group).max(100)});
export const reportedModelUsageSchema=z.object({schema_version:z.literal('reported-model-tokens-v1'),
 record_limit:z.number(),returned_records:z.number(),retained_records:z.number().nullable(),
 records_truncated:z.boolean(),lifetime_usage:z.literal(false),scopes:z.array(scope).min(1).max(201)}).passthrough();
type Usage=z.infer<typeof reportedModelUsageSchema>;
const number=(value:number|null)=>value==null?'Unknown':value.toLocaleString();

export function ReportedModelUsage({usage}:{usage:Usage}){
 const [selection,setSelection]=useState('chat');
 const selected=usage.scopes.find(s=>s.id===selection)??usage.scopes[0];
 const eligible=selected.calls_expected_usage;
 const tokens=(value:number|null)=>selected.coverage==='not_sent'?'Not sent':number(value);
 return <section className="reported-model-usage" aria-label="Reported model tokens">
  <h4>Reported model tokens</h4>
  <label className="usage-scope">Usage scope<select value={selected.id} onChange={e=>setSelection(e.target.value)}>
   {(['chat','submission','workflow'] as const).map(kind=><optgroup key={kind} label={kind==='chat'?'Chat records':kind==='submission'?'Submissions':'Recorded workflows'}>
    {usage.scopes.filter(s=>s.kind===kind).map(s=><option key={s.id} value={s.id}>{s.label}</option>)}
   </optgroup>)}
  </select></label>
  <p className="usage-caption">Provider-reported context and output, not network bytes. Repeated context is counted per call.</p>
  <div className="usage-token-grid">
   <div><span>Input / context</span><strong>{tokens(selected.reported_input_tokens)}</strong><small>{selected.calls_with_reported_input} calls reporting</small></div>
   <div><span>Generated output</span><strong>{tokens(selected.reported_output_tokens)}</strong><small>{selected.calls_with_reported_output} calls reporting</small></div>
  </div>
  <p className="usage-coverage" role="status">{selected.coverage==='no_recorded_calls'?'No model calls recorded for this scope.':selected.coverage==='not_sent'?'These recorded calls were stopped before model dispatch.':`${selected.calls_with_both_counts} of ${eligible} calls reported both counts${selected.calls_with_unknown_usage?' · Partial usage; unknown counts are excluded.':'.'}`}</p>
  {selected.collection_incomplete&&<p className="usage-caution">Some diagnostic records were not collected or are outside this window. These figures cannot establish complete usage for this scope.</p>}
  {usage.records_truncated&&<p className="usage-caution">Showing {usage.returned_records} of {usage.retained_records} retained chat records. Earlier calls may be outside this window.</p>}
  <p>{selected.recorded_calls} recorded calls · {selected.model_call_seconds==null?'Model-call time unknown':`${selected.model_call_seconds.toFixed(2)} s of measured model-call time`}</p>
  <details><summary>Timing and call outcomes</summary><dl className="usage-metrics">
   <dt>Recorded model calls</dt><dd>{selected.recorded_calls}</dd>
   <dt>Stopped before dispatch</dt><dd>{selected.not_sent_calls}</dd>
   <dt>Model-call time</dt><dd>{selected.model_call_seconds==null?'Unknown':`${selected.model_call_seconds.toFixed(2)} s · ${selected.timed_calls} timed calls`}</dd>
   <dt>Corrections / timeouts</dt><dd>{selected.correction_calls} / {selected.timeout_calls}</dd>
   <dt>Model-call failures</dt><dd>{selected.model_call_failures}</dd>
   <dt>Output rate including waiting</dt><dd>{selected.end_to_end_output_tokens_per_second==null?'Unknown':`${selected.end_to_end_output_tokens_per_second.toFixed(2)} tokens/s · ${selected.rate_measured_calls} measured calls`}</dd>
   {selected.workflow_status&&<><dt>Recorded workflow status</dt><dd>{selected.workflow_status}</dd></>}
  </dl><p className="usage-caption">Model-call time sums call intervals and excludes parent submission durations. The rate uses only calls with reported output and positive measured time; it includes loading, context processing and waiting, not decoding speed alone. A finished model call does not establish a valid plan or successful workflow.</p></details>
  {selected.by_role_model.length>0&&<details><summary>By role and model</summary>
   <div className="usage-breakdown">{selected.by_role_model.map(g=><article className="usage-role" key={`${g.role}:${g.provider_profile_id}:${g.model}`}>
    <header><strong>{g.role}</strong><small>{g.model} · {g.provider_profile_id}</small></header>
    <dl><dt>Input / context</dt><dd>{number(g.reported_input_tokens)}</dd><dt>Generated output</dt><dd>{number(g.reported_output_tokens)}</dd><dt>Recorded calls</dt><dd>{g.recorded_calls}</dd></dl>
   </article>)}</div></details>}
  <p className="usage-caption">Read-only summary of up to {usage.record_limit} recent retained records, not lifetime billing.</p>
 </section>;
}
