import type {AnalyticalRecord} from '../lib/analytical-graph';
import {analyticalActionId,analyticalFileId,analyticalGraph} from '../lib/analytical-graph';
const object=(v:unknown):Record<string,unknown>=>v&&typeof v==='object'&&!Array.isArray(v)?v as Record<string,unknown>:{};
const numeric=(v:unknown)=>typeof v==='number'?v.toLocaleString(undefined,{maximumFractionDigits:6}):'Not recorded';
function ProfileFacts({value:r}:{value:Record<string,unknown>}) {
  const profiles=Array.isArray(r.profiles)?r.profiles.map(object):[];
  return <section className="detail-section" aria-label="Recorded analytical profile"><h3>Computed profile</h3><dl><div><dt>Source</dt><dd>{String(r.path)}</dd></div><div><dt>Source rows</dt><dd>{numeric(r.source_rows)}</dd></div><div><dt>Matching rows</dt><dd>{numeric(r.matching_rows)}</dd></div><div><dt>Coverage</dt><dd>{r.scope==='complete_parsed_file'?'Complete parsed file':String(r.scope)}</dd></div><div><dt>Sample status</dt><dd>{r.possible_sample?'Candidate sample; provenance unverified':'Selected-source results'}</dd></div></dl>
    {Object.entries(object(r.distinct_counts)).map(([name,count])=><p key={name}>Distinct {name}: <strong>{numeric(count)}</strong></p>)}
    <div className="result-table-scroll"><table><thead><tr><th>Field</th><th>Missing</th><th>Mean</th><th>Min</th><th>Max</th></tr></thead><tbody>{profiles.map((p,i)=>{const n=object(p.numeric);return <tr key={i}><td>{String(p.name)}</td><td>{numeric(p.missing_count)}</td><td>{numeric(n.mean)}</td><td>{numeric(n.minimum)}</td><td>{numeric(n.maximum)}</td></tr>;})}</tbody></table></div>
    <p>Numerical/count candidates include full-file statistics when recorded. Coded categories and identifiers are not measurements. Missing counts follow the recorded token policy.</p>
    <details><summary>Source verification and analysis specification</summary><p className="analytical-source-hash">SHA-256: {String(r.source_sha256)}</p><pre>{JSON.stringify({query:r.request,codebook:r.codebook,checks:r.checks},null,2)}</pre></details>
    <details><summary>Grouped summaries · {numeric(r.group_count)}</summary><p>{r.groups_truncated?'Only the first 20 recorded groups were retained for this analytical explanation.':'All recorded groups are shown.'} Aggregates were calculated across matching source rows.</p><pre>{JSON.stringify(r.groups,null,2)}</pre></details>
  </section>;
}
export function AnalyticalInspector({record,nodeId,onSelect,onOutcome}:{record:AnalyticalRecord;nodeId:string;onSelect:(id:string)=>void;onOutcome:()=>void}) {
  const s=record.session;
  const displayedInputs=new Set(analyticalGraph(record).nodes.map(n=>n.id));
  const fileIndex=s.inventory.files.findIndex((_,i)=>analyticalFileId(i)===nodeId);
  const actionIndex=s.journal.findIndex((_,i)=>analyticalActionId(i)===nodeId);
  const file=s.inventory.files[fileIndex];const action=s.journal[actionIndex];const r=s.observations[actionIndex]?.result;
  return <div className="analytical-inspector" aria-label="Analytical session information">
    <button type="button" className="context-intent-toggle" onClick={onOutcome}>View analytical outcome</button><p className="result-notice">Read-only tools already ran. Viewing does not rerun them or authorize writes.</p>
    <dl><div><dt>Conversation</dt><dd>{record.conversationId}</dd></div><div><dt>{s.conversation_revision?'Session revision':'Loaded chat revision'}</dt><dd>{record.revision}</dd></div><div><dt>Folder</dt><dd>{s.directory}</dd></div></dl>
    {file&&<section className="detail-section"><h3>Input evidence</h3><dl><div><dt>Path</dt><dd>{file.path}</dd></div><div><dt>Size</dt><dd>{file.bytes.toLocaleString()} bytes</dd></div><div><dt>Discovery</dt><dd>{file.columns?'Bounded header available':'Directory metadata only'}</dd></div><div><dt>Sample provenance</dt><dd>{file.sample_provenance}</dd></div></dl><details><summary>Recorded columns · {file.columns?.length??0}</summary><p>{file.columns?.join(', ')??'No column metadata recorded'}</p></details><p>Discovery does not prove that this file was selected for analysis.</p>{s.observations.filter(o=>o.tool==='profile_table'&&o.result.path===file.path&&o.result.source_sha256).map((o,i)=><ProfileFacts key={i} value={o.result}/>)}</section>}
    {action&&<section className="detail-section"><h3>Recorded action {actionIndex+1}</h3><dl><div><dt>Tool</dt><dd>{action.tool}</dd></div><div><dt>Status</dt><dd>{action.status}</dd></div><div><dt>Input</dt><dd>{action.path??s.directory}</dd></div></dl>{Boolean(r?.error)&&<p role="alert">{String(r?.error)} No partial tool result is represented as success.</p>}
      {action.tool==='assess_table'&&r&&<><h3>Processing decision</h3><dl>{['operation','strategy','source_bytes','byte_limit','row_limit','runtime_state_checks_required'].map(key=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{r[key]===null?'Not established':String(r[key]??'Not recorded')}</dd></div>)}</dl><p>{String(r.reason??'')}</p><p>A byte check does not certify row count, cardinality, memory or eventual execution success.</p></>}
      {action.tool==='profile_table'&&r&&typeof r.source_sha256==='string'&&<ProfileFacts value={r}/>}
    </section>}
    {(nodeId==='analytical_summary'||nodeId==='analytical_reasoning')&&<><section className="detail-section"><h3>Advisory explanation</h3><p>{s.message}</p><p>{s.model_calls} model calls · {s.tool_calls} recorded tool actions · {s.elapsed_seconds.toFixed(1)} seconds. This session contains no separate Critic assessment.</p></section>{s.observations.filter(o=>o.tool==='profile_table'&&o.result.source_sha256).map((o,i)=><ProfileFacts key={i} value={o.result}/>)}</>}
    {(nodeId==='analytical_action_0'||nodeId==='analytical_request')&&<section className="detail-section"><h3>Discovered inputs · {s.inventory.files.length}</h3>{s.inventory.files.map((f,i)=><p key={f.path}><button className="context-intent-toggle" disabled={!displayedInputs.has(analyticalFileId(i))} onClick={()=>onSelect(analyticalFileId(i))}>{f.path}</button><small>{f.bytes.toLocaleString()} bytes{f.possible_sample?' · possible sample, unverified':''}{f.possible_codebook?' · possible codebook':''}</small></p>)}<p>The graph displays up to eight input blocks; this list retains all discovered files.</p></section>}
    <details className="detail-section"><summary>Recorded action sequence</summary>{s.journal.map((j,i)=><p key={i}><button className="context-intent-toggle" onClick={()=>onSelect(analyticalActionId(i))}>{i+1}. {j.tool.replaceAll('_',' ')} · {j.status}</button></p>)}</details>
  </div>;
}
