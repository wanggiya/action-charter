import type {AnalyticalSession} from '../lib/analytical-session';
const object=(v:unknown):Record<string,unknown>=>v&&typeof v==='object'&&!Array.isArray(v)?v as Record<string,unknown>:{};
const number=(v:unknown)=>typeof v==='number'?v.toLocaleString():'Not recorded';
export function AnalyticalEvidence({session}:{session:AnalyticalSession}) {
  return <details className="planner-chat-context analytical-evidence"><summary>Analytical evidence · {session.status.replaceAll('_',' ')} · {session.tool_calls} read-only actions</summary>
    <p>Folder: {session.directory}. The explanation above is model interpretation; the facts below are recorded tool results. No data files were written and the workflow is unchanged.</p>
    <details><summary>Discovered files · {session.inventory.files.length}</summary>{session.inventory.files.map(f=><div key={f.path}><strong>{f.path}</strong><p>{number(f.bytes)} bytes · {f.columns?.length??'?'} columns{f.possible_codebook?' · possible codebook':''}{f.possible_sample?' · possible sample; provenance unverified':''}</p></div>)}</details>
    {session.observations.map((o,i)=>{const r=o.result;
      if(o.tool==='assess_table')return <section key={i}><h4>Strategy · {String(r.path??'')}</h4><p>{String(r.reason??'Assessment unavailable')}</p><small>{String(r.operation??'')} · {String(r.strategy??'')} · {number(r.source_bytes)} source bytes. Runtime limits still apply.</small></section>;
      if(o.tool==='profile_table'&&r.source_sha256){const profiles=Array.isArray(r.profiles)?r.profiles.map(object):[];return <section key={i}><h4>Computed profile · {String(r.path)}</h4><p>{number(r.source_rows)} source rows · {number(r.matching_rows)} matching rows · {r.possible_sample?'Possible sample; provenance unverified':'Selected-source scope'}</p><small>Source SHA-256: {String(r.source_sha256).slice(0,16)}…</small>
        {Object.entries(object(r.distinct_counts)).map(([name,count])=><p key={name}>Distinct {name}: {number(count)}</p>)}
        <div className="result-table-scroll"><table><thead><tr><th>Field</th><th>Missing</th><th>Distinct</th><th>Numeric mean</th></tr></thead><tbody>{profiles.map((p,j)=><tr key={j}><td>{String(p.name)}</td><td>{number(p.missing_count)}</td><td>{number(p.distinct_count)}</td><td>{number(object(p.numeric).mean)}</td></tr>)}</tbody></table></div>
        <p>{number(r.group_count)} recorded groups{r.groups_truncated?' · only the first 20 groups supplied to the model':''}. Aggregates cover matching source rows, not preview rows.</p>
        <details><summary>Analysis specification and checks</summary><pre>{JSON.stringify({request:r.request,checks:r.checks,codebook:r.codebook},null,2)}</pre></details></section>;}
      if(r.error)return <p role="status" key={i}>Read stopped · {String(r.path??'')}: {String(r.error)}</p>;
      return null;})}
    <details><summary>Action history and budget</summary>{session.journal.map((j,i)=><p key={i}>{i+1}. {j.tool.replaceAll('_',' ')} · {j.path??session.directory} · {j.status}</p>)}<p>{session.model_calls} model calls · {session.tool_calls} tool calls · {session.elapsed_seconds.toFixed(1)} seconds. Tool calls can include bounded header probes. Saved evidence restores without repeating these calls.</p></details>
  </details>;
}
