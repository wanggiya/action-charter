import {useEffect,useRef,useState} from 'react';
import {parseAnalysis,type TableAnalysis} from './AnalyticalProfile';
import {ResultTable,emptyTableView} from './ResultTable';
import {DataChart} from './RecordedVisualization';
import {DatasetCrossTab} from './DatasetCrossTab';
import {GroupedChart} from './GroupedChart';
import type {ResultRecord} from './ResultsWorkspace';
import './TableExplorer.css';

type Options=Record<string,unknown>;
export function useTableAnalysis(record:ResultRecord,stepId:string,onResult:(value:TableAnalysis)=>void) {
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const active=useRef<AbortController|null>(null);
  const sequence=useRef(0);
  const stop=()=>{sequence.current++;active.current?.abort();active.current=null;setBusy(false);};
  useEffect(()=>()=>{sequence.current++;active.current?.abort();},[]);
  const read=async(options:Options)=>{
    if(!record.conversation_id||!record.plan_sha256){setError('Choose a run bound to this chat and plan.');return;}
    active.current?.abort();const controller=new AbortController();active.current=controller;
    const id=++sequence.current;setBusy(true);setError('');
    try{
      const response=await fetch('/api/v1/workflow/runs',{signal:controller.signal,method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'table_analysis',run_id:record.run_id,conversation_id:record.conversation_id,confirmed_plan_sha256:record.plan_sha256,step_id:stepId,table_options:options})});
      const value=await response.json();
      if(!response.ok)throw new Error(typeof value.error==='string'?value.error:'Analysis unavailable');
      if(value.run_id!==record.run_id||value.plan_sha256!==record.plan_sha256||value.step_id!==stepId||value.verified_at_read!==true)throw new Error('Analysis response scope mismatch');
      const analysis=parseAnalysis(value.table_analysis);if(!analysis)throw new Error('Invalid analytical result');
      if(id===sequence.current)onResult(analysis);
    }catch(e){if(id===sequence.current&&!controller.signal.aborted)setError(e instanceof Error?e.message:'Analysis failed');}
    finally{if(id===sequence.current){setBusy(false);active.current=null;}}
  };
  return {read,busy,error,stop};
}

type Reader=ReturnType<typeof useTableAnalysis>;
export function AnalysisRequestStatus({reader}:{reader:Reader}) {
  return <>{reader.busy&&<div role="status"><p>Verifying the complete source and calculating the requested view… Previous results remain below.</p><button onClick={reader.stop}>Stop waiting</button><small>Stops this browser request. The bounded backend read may continue until its worker finishes.</small></div>}{reader.error&&<p role="alert">{reader.error} Previous results are preserved.</p>}</>;
}

export function ColumnExplorer({analysis,columns,reader}:{analysis:TableAnalysis|null;columns:string[];reader:Reader}) {
  const [search,setSearch]=useState(''),[selected,setSelected]=useState(columns[0]??'');
  const [missing,setMissing]=useState((analysis?.request.missing_values as Record<string,string[]>|undefined)?.[columns[0]??'']?.join(', ')??''),[rows,setRows]=useState(false),[key,setKey]=useState('');
  const p=analysis?.profiles.find(p=>p.name===selected);
  const matches=columns.filter(c=>c.toLowerCase().includes(search.toLowerCase()));
  const exact=()=>void reader.read({...analysis?.request,offset:0,limit:20,profile_columns:[selected],
    quality_columns:[selected],duplicate_rows:rows,duplicate_key:key?[key]:[],group_by:[],distinct_columns:[],numeric_columns:[],count_columns:[],
    missing_values:{...(analysis?.request.missing_values as Options??{}),[selected]:missing?missing.split(',').map(v=>v.trim()).filter(Boolean):[]}});
  return <section className="table-explorer" aria-label="Column quality explorer">
    <p>Inspect field quality across all matching rows. Distinct values and values occurring once are different measures.</p>
    <label>Search fields<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Find a column"/></label>
    <div className="analytical-field-list" role="group" aria-label="Available fields">{matches.map(name=><button key={name} aria-pressed={selected===name} onClick={()=>{setSelected(name);const tokens=analysis?.request.missing_values as Record<string,string[]>|undefined;setMissing(tokens?.[name]?.join(', ')??'');}}>{name}</button>)}{!matches.length&&<p>No matching fields.</p>}</div>
    <h4>{selected||'Select a field'}</h4>
    <div className="analytical-controls">
      <label>Declared missing tokens · comma separated<input aria-label="Declared missing tokens" value={missing} onChange={e=>setMissing(e.target.value)} placeholder="For example: ?"/></label>
      <label>Check duplicate key<select aria-label="Check duplicate key" value={key} onChange={e=>setKey(e.target.value)}><option value="">Not requested</option>{columns.map(c=><option key={c}>{c}</option>)}</select></label>
      <div className="planner-history-control"><span>Duplicate entire rows</span><button className="planner-history-switch" type="button" role="switch" aria-label="Duplicate entire rows" aria-checked={rows} onClick={()=>setRows(v=>!v)}><span className="history-switch-track" aria-hidden="true"/><span className="history-switch-thumb" aria-hidden="true"/><span className="history-switch-label history-switch-off" aria-hidden="true">Off</span><span className="history-switch-label history-switch-on" aria-hidden="true">On</span></button></div>
      <button disabled={reader.busy||!selected} onClick={exact}>Run quality checks</button>
    </div>
    <small>Checks use the current recorded filters. Blank cells are always missing; declared tokens are additional. Literal None/Unknown remain values unless explicitly declared. Exact checks have memory/entry limits.</small>
    <AnalysisRequestStatus reader={reader}/>
    {p?<><dl className="result-summary-facts"><div><dt>Missing</dt><dd>{p.missing_count.toLocaleString()}</dd></div><div><dt>Empty cells</dt><dd>{p.empty_count?.toLocaleString()??'Not recorded'}</dd></div><div><dt>Declared missing</dt><dd>{p.declared_missing_count?.toLocaleString()??'Not recorded'}</dd></div><div><dt>Distinct non-missing</dt><dd>{p.distinct_count?.toLocaleString()??'Not calculated'}</dd></div>
      {p.frequency&&Object.entries(p.frequency).filter(([name])=>!['status','distinct_count'].includes(name)).map(([name,value])=><div key={name}><dt>{name.replaceAll('_',' ')}</dt><dd>{typeof value==='number'?value.toLocaleString():String(value)}</dd></div>)}
    </dl>{!p.frequency&&<p>Exact repetition metrics are unavailable for this field. Run quality checks explicitly.</p>}
    {p.categories.length>0&&<div className="result-table-scroll"><table><thead><tr><th>Value</th><th>Definition</th><th>Frequency</th></tr></thead><tbody>{p.categories.map((c,i)=><tr key={i}><td>{c.value}</td><td>{c.description??'—'}</td><td>{c.count.toLocaleString()}</td></tr>)}</tbody></table></div>}
    <p>Once-only values occur exactly once; repeated values occur more than once. Excess occurrences count repeats beyond the first. Missing values are excluded from these field metrics.</p></>:<p>Run quality checks to load this column’s profile.</p>}
    {analysis?.quality&&<details open><summary>Duplicate checks · current calculation</summary>{analysis.quality.duplicate_rows&&<p>Duplicate entire rows: <strong>{analysis.quality.duplicate_rows.excess_occurrences.toLocaleString()}</strong> excess occurrences.</p>}{analysis.quality.duplicate_key&&<><p>Key: {analysis.quality.duplicate_key.columns.join(', ')} · Missing-key rows: {analysis.quality.duplicate_key.missing_key_rows.toLocaleString()} · Excess occurrences: {analysis.quality.duplicate_key.excess_occurrences.toLocaleString()}</p><p>Candidate key: {analysis.quality.duplicate_key.candidate_key?'Yes':'No'} · Rows with missing key fields are excluded from duplicate-key counts.</p></>}{!analysis.quality.duplicate_rows&&!analysis.quality.duplicate_key&&<p>Duplicate row/key checks not requested.</p>}</details>}
  </section>;
}

export function GroupExplorer({analysis,columns,reader}:{analysis:TableAnalysis|null;columns:string[];reader:Reader}) {
  const [group,setGroup]=useState(analysis?.group_by[0]??columns[0]??''),[split,setSplit]=useState(analysis?.group_by[1]??'');
  const [distinct,setDistinct]=useState((analysis?.request.distinct_columns as string[]|undefined)?.[0]??''),[numeric,setNumeric]=useState((analysis?.request.numeric_columns as string[]|undefined)?.[0]??''),[filterColumn,setFilterColumn]=useState(analysis?.request.filters?.[0]?.column??''),[filterValue,setFilterValue]=useState(analysis?.request.filters?.[0]?.value??'');
  const [presentation,setPresentation]=useState<'table'|'details'|'chart'>('table'),[measure,setMeasure]=useState('row_count');
  const [state,setState]=useState(emptyTableView),[selected,setSelected]=useState<number|null>(null);
  const [missingGroup,setMissingGroup]=useState('');
  const run=()=>{
    const names=[group,...(split?[split]:[])];
    void reader.read({...analysis?.request,offset:0,limit:20,profile_columns:[],quality_columns:[],duplicate_key:[],duplicate_rows:false,
      group_by:names,numeric_columns:numeric?[numeric]:[],distinct_columns:distinct?[distinct]:[],count_columns:[],
      missing_values:{...(analysis?.request.missing_values as Options??{}),[group]:missingGroup?missingGroup.split(',').map(v=>v.trim()).filter(Boolean):[]},
      filters:filterColumn?[{column:filterColumn,value:filterValue}]:[]});
    setState(emptyTableView());setSelected(null);
  };
  const metrics=analysis?.groups.length?Object.keys(analysis.groups[0]).filter(c=>!analysis.group_by.includes(c)):[];
  const effectiveMeasure=metrics.includes(measure)?measure:'row_count';
  const chartCategory=analysis?.group_by.join(' / ')||'Group';
  const chartRows=analysis?.groups.map(g=>({[chartCategory]:JSON.stringify(analysis.group_by.map(n=>{const value=String(g[n]??'');const definition=analysis.codebook?.sections[n]?.[value];return definition?`${value}: ${definition}`:value;})),[effectiveMeasure]:g[effectiveMeasure]}))??[];
  return <section className="table-explorer" aria-label="Grouped data explorer">
    <p>Choose fields and measures, then run an explicit complete-file calculation. No model call or workflow regeneration is required.</p>
    <div className="analytical-controls">
      <label>Rows (vertical)<select aria-label="Explore group by" value={group} onChange={e=>{setGroup(e.target.value);if(split===e.target.value)setSplit('');}}>{columns.map(c=><option key={c}>{c}</option>)}</select></label>
      <label>Columns (horizontal)<select aria-label="Explore split by" value={split} onChange={e=>setSplit(e.target.value)}><option value="">None</option>{columns.filter(c=>c!==group).map(c=><option key={c}>{c}</option>)}</select></label>
    </div>
    <details><summary>Additional measures and filters</summary><div className="analytical-controls">
      <label>Distinct count field<select aria-label="Explore distinct field" value={distinct} onChange={e=>setDistinct(e.target.value)}><option value="">None</option>{columns.map(c=><option key={c}>{c}</option>)}</select></label>
      <label>Numeric summary field<select aria-label="Explore numeric field" value={numeric} onChange={e=>setNumeric(e.target.value)}><option value="">None</option>{columns.map(c=><option key={c}>{c}</option>)}</select></label>
      <label>Filter field<select aria-label="Explore filter field" value={filterColumn} onChange={e=>setFilterColumn(e.target.value)}><option value="">No filter</option>{columns.map(c=><option key={c}>{c}</option>)}</select></label>
      <label>Exact filter value<input aria-label="Explore filter value" disabled={!filterColumn} value={filterValue} onChange={e=>setFilterValue(e.target.value)}/></label>
    </div>
    </details>
    <button disabled={reader.busy||!group||split===group} onClick={run}>Run analysis</button>
    <AnalysisRequestStatus reader={reader}/>
    {analysis&&JSON.stringify(analysis.group_by)!==JSON.stringify([group,...(split?[split]:[])])&&<p className="result-notice">Selection changed. Run analysis to apply it; the displayed result still shows {analysis.group_by.join(' × ')||'the previous calculation'}.</p>}
    <p>Controls are a draft. Results below use the recorded query: {analysis?.group_by.join(' / ')||'No grouping yet'}. Coverage: {analysis?.matched_row_count.toLocaleString()??'—'} matching / {analysis?.source_row_count.toLocaleString()??'—'} source rows.</p>
    {analysis&&<details><summary>Result scope and definitions</summary><p>Exact row/encounter counts and proportions use all matching rows. Distinct counts exclude declared missing values and may overlap across groups. Numeric summaries require explicitly selected numerical meaning.</p><p>Missing group tokens remain separate raw groups; no category is silently removed. Numeric invalid values are excluded from numeric measures and reported in column profiles.</p><pre>{JSON.stringify(analysis.request,null,2)}</pre></details>}
    {analysis?.profiles.some(p=>p.numeric)&&<details><summary>Numeric field coverage</summary>{analysis?.profiles.filter(p=>p.numeric).map(p=><p key={p.name}>Numeric field {p.name}: {p.numeric!.count.toLocaleString()} valid values · {p.numeric!.invalid_count.toLocaleString()} invalid · {p.missing_count.toLocaleString()} missing. Counts and means exclude invalid/missing values.</p>)}</details>}
    {analysis?.groups.length?<>
      <div className="verified-preview-controls"><button aria-pressed={presentation==='table'} onClick={()=>setPresentation('table')}>Result table</button><button aria-pressed={presentation==='chart'} onClick={()=>setPresentation('chart')}>Result chart</button>{analysis.group_by.length===2&&<button aria-pressed={presentation==='details'} onClick={()=>setPresentation('details')}>Detailed measures</button>}</div>
      {presentation==='table'&&analysis.group_by.length===2?<DatasetCrossTab key={JSON.stringify(analysis.group_by)} fields={analysis.group_by} groups={analysis.groups} matchingRows={analysis.matched_row_count}/>:presentation!=='chart'?<ResultTable data={{columns:Object.keys(analysis.groups[0]),preview:analysis.groups,row_count:analysis.groups.length}} state={state} onState={setState} selectedRow={selected} onSelectRow={setSelected}/>:<>
        <label>Plot measure<select aria-label="Explore plot measure" value={effectiveMeasure} onChange={e=>setMeasure(e.target.value)}>{metrics.map(c=><option key={c}>{c}</option>)}</select></label>
        {effectiveMeasure==='row_count'?<GroupedChart key={JSON.stringify(analysis.group_by)} fields={analysis.group_by} groups={analysis.groups} matchingRows={analysis.matched_row_count} controlPrefix="Explore" initialMeasure="count"/>:chartRows.length<=100?<DataChart key={effectiveMeasure+JSON.stringify(analysis.group_by)} data={{columns:[chartCategory,effectiveMeasure],preview:chartRows,row_count:chartRows.length}} completeGroups/>:<p>{chartRows.length} complete groups exceed the 100-group chart display limit. Use the result table or refine your grouping; no groups have been silently omitted.</p>}
      </>}
    </>:<p>No grouped result yet. Choose a low-cardinality field and run analysis.</p>}
    <details><summary>Missing-value policy for grouping field</summary><label>Declared missing group tokens<input value={missingGroup} onChange={e=>setMissingGroup(e.target.value)} placeholder="Comma separated; optional"/></label><small>Changes take effect on Run analysis. Missing declarations affect summaries; raw group labels remain visible.</small></details>
  </section>;
}
