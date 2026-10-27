import { useState } from 'react';
import { z } from 'zod';
import { ResultTable, emptyTableView } from './ResultTable';
import type { ResultRecord } from './ResultsWorkspace';
import { DataChart } from './RecordedVisualization';

const row = z.record(z.union([z.string(), z.number(), z.null()]));
const optionsSchema = z.object({codebook_path:z.string().nullable().optional(),profile_columns:z.array(z.string()).optional(),
  filters:z.array(z.object({column:z.string(),value:z.string()})).optional(),offset:z.number(),limit:z.number()}).passthrough();
const frequency=z.object({status:z.literal('exact'),distinct_count:z.number(),once_only_values:z.number(),repeated_values:z.number(),rows_in_repeated_groups:z.number(),excess_occurrences:z.number()});
const analysisSchema = z.object({schema_version:z.literal('table-analysis-v1'),source_row_count:z.number(),matched_row_count:z.number(),
  available_columns:z.array(z.string()).optional(),quality:z.object({columns:z.record(frequency),duplicate_rows:frequency.nullable(),duplicate_key:frequency.extend({columns:z.array(z.string()),missing_key_rows:z.number(),candidate_key:z.boolean()}).passthrough().nullable()}).passthrough().optional(),
  columns:z.array(z.string()),distinct_counts:z.record(z.number()),
  profiles:z.array(z.object({name:z.string(),missing_count:z.number(),empty_count:z.number().optional(),declared_missing_count:z.number().optional(),frequency:frequency.nullable().optional(),distinct_count:z.number().nullable(),categories_status:z.string(),
    categories:z.array(z.object({value:z.string(),count:z.number(),proportion:z.number().nullable(),description:z.string().nullable()})),
    numeric:z.object({count:z.number(),mean:z.number().nullable(),minimum:z.number().nullable(),maximum:z.number().nullable(),invalid_count:z.number()}).passthrough().nullable()})),
  groups:z.array(row),group_by:z.array(z.string()),request:optionsSchema,
  table:z.object({columns:z.array(z.string()),preview:z.array(row),row_count:z.number(),offset:z.number(),limit:z.number(),columns_omitted:z.array(z.string())}),
  codebook:z.object({path:z.string(),sha256:z.string(),sections:z.record(z.record(z.string())),coverage:z.record(z.object({matched_rows:z.number(),unmatched_rows:z.number(),unknown_codes:z.record(z.number())})),unbound_sections:z.array(z.string())}).passthrough().nullable(),
  limitations:z.array(z.string()),checks:z.record(z.boolean()),
});
export type TableAnalysis = z.infer<typeof analysisSchema>;
export function parseAnalysis(value: unknown): TableAnalysis | null { const parsed=analysisSchema.safeParse(value);return parsed.success?parsed.data:null; }

export function AnalyticalChart({analysis}:{analysis:TableAnalysis}) {
  if(!analysis.groups.length)return <p>No group summary requested. Ask Planner to profile the file with “Group by” columns, or inspect exact category distributions in Overview.</p>;
  if(analysis.groups.length>100)return <p>The full profile has {analysis.groups.length} groups. Use a narrower grouping/filter before charting; the complete group table remains in Overview.</p>;
  const preview=analysis.groups.map(g=>({group:analysis.group_by.map(n=>String(g[n])).join(' · '),encounters:g.row_count}));
  return <><p>Recorded counts from all {analysis.matched_row_count.toLocaleString()} matching encounters. Group labels: {analysis.group_by.join(' / ')}. This chart uses every recorded group, not the first source rows.</p>
    <DataChart key={JSON.stringify(analysis.group_by)} data={{columns:['group','encounters'],preview,row_count:preview.length}} completeGroups/>
  </>;
}

export function AnalyticalProfile({analysis,onTable}:{analysis:TableAnalysis;onTable:()=>void}) {
  const [column,setColumn]=useState(analysis.profiles[0]?.name??'');
  const [groupsView,setGroupsView]=useState(emptyTableView);
  const [selectedGroup,setSelectedGroup]=useState<number|null>(null);
  const p=analysis.profiles.find(p=>p.name===column);
  return <section className="detail-section" aria-label="Full-file analytical profile">
    <h3>Full-file analytical profile</h3>
    <p>{analysis.source_row_count.toLocaleString()} source rows · {analysis.matched_row_count.toLocaleString()} matching rows. Summaries cover all matching records, not the preview page.</p>
    {Object.entries(analysis.distinct_counts).map(([name,count])=><p key={name}>Distinct {name}: <strong>{count.toLocaleString()}</strong></p>)}
    <button onClick={onTable}>Analytical table</button>
    <details open><summary>Columns and distributions</summary>
      <label>Profile column<select value={column} onChange={e=>setColumn(e.target.value)}>{analysis.profiles.map(p=><option key={p.name}>{p.name}</option>)}</select></label>
      {p&&<><p>Missing: {p.missing_count.toLocaleString()} · Distinct: {p.distinct_count===null?'Not calculated above the category budget':p.distinct_count.toLocaleString()}</p>
        {p.numeric&&<p>Numeric values: {p.numeric.count.toLocaleString()} · Mean: {p.numeric.mean!==null?p.numeric.mean.toFixed(4):'Unavailable'} · Min: {p.numeric.minimum??'—'} · Max: {p.numeric.maximum??'—'} · Invalid: {p.numeric.invalid_count}</p>}
        {p.categories.length?<div className="result-table-scroll"><table><thead><tr><th>Value</th><th>Definition</th><th>Count</th><th>% of matching rows</th></tr></thead><tbody>{p.categories.map((c,i)=><tr key={i}><td>{c.value}</td><td>{c.description??'—'}</td><td>{c.count.toLocaleString()}</td><td>{c.proportion===null?'—':(100*c.proportion).toFixed(2)}</td></tr>)}</tbody></table></div>:<p>{p.categories_status==='unavailable_above_128_distinct'?'Category distribution unavailable above 128 distinct values. No sampled counts substituted.':'No non-missing categories.'}</p>}
        <small>At most 12 categories displayed. Missing tokens follow the declared request; numeric syntax does not establish clinical meaning.</small></>}
    </details>
    {analysis.groups.length>0&&<details><summary>Full-file groups · {analysis.groups.length}</summary>
      <ResultTable data={{columns:Object.keys(analysis.groups[0]),preview:analysis.groups,row_count:analysis.groups.length}} state={groupsView} onState={setGroupsView} selectedRow={selectedGroup} onSelectRow={setSelectedGroup}/>
      <p>Group counts reconcile: {analysis.checks.group_count_reconciles?'Yes':'No'}. Denominator: {analysis.matched_row_count.toLocaleString()} matching encounters, not distinct patients.</p>
    </details>}
    {analysis.codebook&&<details><summary>Codes &amp; definitions</summary><p>{analysis.codebook.path} · supplied definitions</p>
      {Object.entries(analysis.codebook.sections).map(([name,codes])=>{const coverage=analysis.codebook!.coverage[name];return <details key={name}><summary>{name} · {Object.keys(codes).length} codes</summary>
        <p>{coverage?`${coverage.matched_rows.toLocaleString()} matched rows · ${coverage.unmatched_rows.toLocaleString()} unmapped rows`:'Section has no matching source field.'}</p>
        <div className="result-table-scroll"><table><thead><tr><th>Code</th><th>Description</th></tr></thead><tbody>{Object.entries(codes).map(([code,description])=><tr key={code}><td>{code}</td><td>{description}</td></tr>)}</tbody></table></div>
      </details>;})}<small>Labels do not join, duplicate or remove source rows.</small>
    </details>}
    <details><summary>Coverage and limitations</summary>{analysis.limitations.map((item,i)=><p key={i}>{item}</p>)}</details>
  </section>;
}

export function AnalyticalTable({initial,record,stepId}:{initial:TableAnalysis;record:ResultRecord;stepId:string}) {
  const [analysis,setAnalysis]=useState(initial),[state,setState]=useState(emptyTableView);
  const [selected,setSelected]=useState<number|null>(null);
  const [column,setColumn]=useState(initial.columns[0]??''),[value,setValue]=useState('');
  const [columns,setColumns]=useState(initial.table.columns.join(', '));
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const read=async(offset:number,apply=false)=>{
    if(!record.conversation_id||!record.plan_sha256)return;
    setBusy(true);setError('');
    try{
      const table_options={...analysis.request,offset,profile_columns:columns.split(',').map(s=>s.trim()).filter(Boolean),
        filters:apply?(value?[{column,value}]:[]):analysis.request.filters??[]};
      const response=await fetch('/api/v1/workflow/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'table_analysis',run_id:record.run_id,conversation_id:record.conversation_id,confirmed_plan_sha256:record.plan_sha256,step_id:stepId,table_options})});
      const payload=await response.json();
      if(!response.ok)throw new Error(typeof payload.error==='string'?payload.error:'Verified table read failed');
      if(payload.run_id!==record.run_id||payload.step_id!==stepId||payload.plan_sha256!==record.plan_sha256)throw new Error('Table response scope mismatch');
      setAnalysis(analysisSchema.parse(payload.table_analysis));setState(emptyTableView());setSelected(null);
    }catch(e){setError(e instanceof Error?e.message:'Table read unavailable');}finally{setBusy(false);}
  };
  const start=analysis.table.offset+1,end=Math.min(analysis.table.offset+analysis.table.preview.length,analysis.matched_row_count);
  return <section className="detail-section" aria-label="Verified analytical table">
    <h3>Verified analytical table</h3>
    <p>{analysis.matched_row_count?`Rows ${start}–${end}`:'No matching rows'} of {analysis.matched_row_count.toLocaleString()} matching records · {analysis.source_row_count.toLocaleString()} source records.</p>
    <label>Columns to show · up to 16<input value={columns} onChange={e=>setColumns(e.target.value)} /></label>
    <label>Filter column<select aria-label="Filter column" value={column} onChange={e=>setColumn(e.target.value)}>{initial.columns.map(c=><option key={c}>{c}</option>)}</select></label>
    <label>Exact value · empty clears filter<input value={value} onChange={e=>setValue(e.target.value)} /></label>
    <button disabled={busy||!record.conversation_id} onClick={()=>void read(0,true)}>Apply full-file filter</button>
    <button disabled={busy||analysis.table.offset===0} onClick={()=>void read(Math.max(0,analysis.table.offset-analysis.table.limit))}>Previous page</button>
    <button disabled={busy||end>=analysis.matched_row_count} onClick={()=>void read(analysis.table.offset+analysis.table.limit)}>Next page</button>
    {busy&&<p role="status">Reading and verifying the complete source. Display remains paged.</p>}{error&&<p role="alert">{error} Previous recorded view is preserved.</p>}
    <ResultTable data={analysis.table} state={state} onState={setState} selectedRow={selected} onSelectRow={setSelected} serverPage/>
    <small>Apply and paging perform an explicit read of the hash-bound source and codebook. Local table search/sort covers this page only. Cells display up to 160 characters.</small>
  </section>;
}
