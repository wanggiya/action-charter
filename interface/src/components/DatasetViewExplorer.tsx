import {useEffect,useRef,useState} from 'react';
import {z} from 'zod';
import type {AnalyticalRecord} from '../lib/analytical-graph';
import type {DatasetResult} from '../lib/dataset-result';
import {ResultTable} from './ResultTable';
import {DatasetCrossTab} from './DatasetCrossTab';
import {ChartPlot} from './ChartPlot';
const scalar=z.union([z.string(),z.number().finite(),z.null()]);
const viewSchema=z.object({conversation_id:z.string(),revision:z.number(),source_sha256:z.string(),profile_sha256:z.string(),view:z.enum(['table','groups']),columns:z.array(z.string()),group_by:z.array(z.string()),source_rows:z.number(),matching_rows:z.number(),groups:z.array(z.record(scalar)),table:z.object({columns:z.array(z.string()),preview:z.array(z.record(scalar)),row_count:z.number(),offset:z.number().optional(),limit:z.number().optional()}),verified_at_read:z.boolean().optional()});
type SavedView=z.infer<typeof viewSchema>;
const percent=(v:unknown)=>typeof v==='number'?`${v.toFixed(2)}%`:'Not available';
function initialGroups(r:DatasetResult,id:string,revision:number):SavedView|null{
 const keys=Array.isArray(r.query.group_by)?r.query.group_by.filter((k):k is string=>typeof k==='string'):[];
 if(!keys.length||keys.length>2||!r.groups.length)return null;
 const totals=new Map<string,number>();r.groups.forEach(g=>{const k=String(g[keys[0]]);totals.set(k,(totals.get(k)??0)+Number(g.row_count));});
 return {conversation_id:id,revision,source_sha256:r.source_sha256,profile_sha256:String(r.artifact.sha256),view:'groups',columns:keys,group_by:keys,source_rows:r.source_rows,matching_rows:r.matching_rows,table:{columns:[],preview:[],row_count:r.matching_rows},groups:r.groups.map(g=>({...Object.fromEntries(keys.map(k=>[k,String(g[k])])),row_count:Number(g.row_count),total_denominator:r.matching_rows,primary_denominator:totals.get(String(g[keys[0]]))??0,percentage_total:r.matching_rows?100*Number(g.row_count)/r.matching_rows:null,percentage_within_primary:totals.get(String(g[keys[0]]))?100*Number(g.row_count)/totals.get(String(g[keys[0]]))!:null}))};
}
export function DatasetViewExplorer({record,dataset:r,mode,readOnly=false,archivedView}:{readOnly?:boolean;archivedView?:unknown;record:AnalyticalRecord;dataset:DatasetResult;mode:'table'|'groups'}){
 const archived=viewSchema.safeParse(archivedView);
 const originalTable:SavedView={conversation_id:record.conversationId,revision:record.revision,source_sha256:r.source_sha256,profile_sha256:String(r.artifact.sha256),view:'table',columns:Array.isArray(r.table.columns)?r.table.columns as string[]:[],group_by:[],source_rows:r.source_rows,matching_rows:r.matching_rows,table:{columns:r.table.columns as string[],preview:r.table.preview as Record<string,string|number|null>[],row_count:r.matching_rows},groups:[]};
 const initial=archived.success&&archived.data.view===mode?archived.data:mode==='groups'?initialGroups(r,record.conversationId,record.chatRevision??record.revision):readOnly?originalTable:null;
 const candidates=r.profiles.filter(p=>mode==='table'||p.analytical_role!=='identifier').map(p=>p.name);
 const [primary,setPrimary]=useState(initial?.columns[0]??(candidates.includes('age')?'age':candidates[0]??'')),[split,setSplit]=useState(initial?.columns[1]??'');
 const [result,setResult]=useState<SavedView|null>(initial),[busy,setBusy]=useState(false),[loading,setLoading]=useState(!readOnly),[error,setError]=useState(''),[basis,setBasis]=useState('total'),[presentation,setPresentation]=useState('table'),[kind,setKind]=useState('bar'),[measure,setMeasure]=useState('percentage');
 const [page,setPage]=useState(0),[selected,setSelected]=useState<number|null>(null);
 const active=useRef<AbortController|null>(null),sequence=useRef(0);
 const body={conversation_id:record.conversationId,expected_revision:record.chatRevision??record.revision,source_sha256:r.source_sha256,profile_sha256:String(r.artifact.sha256),view:mode};
 const read=async(action:'read'|'calculate',offset=0)=>{
  active.current?.abort();const controller=new AbortController();active.current=controller;const seq=++sequence.current;
  if(action==='calculate')setBusy(true);setError('');
  try{
   const response=await fetch('/api/v1/analysis/view',{signal:controller.signal,method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,action,columns:action==='calculate'?[primary,...(split?[split]:[])]:[],offset,limit:20})});
   const value=await response.json();if(!response.ok)throw new Error(typeof value.error==='string'?value.error:'Dataset view unavailable');
   if(value.result){const v=viewSchema.parse(value.result);if(v.conversation_id!==body.conversation_id||v.source_sha256!==body.source_sha256||v.profile_sha256!==body.profile_sha256||v.view!==mode)throw new Error('Dataset view scope mismatch');
    if(seq===sequence.current){setResult(v);setPage(0);setSelected(null);if(action==='read'){setPrimary(v.columns[0]??primary);setSplit(v.columns[1]??'');}}
   }
  }catch(e){if(seq===sequence.current&&!controller.signal.aborted)setError(e instanceof Error?e.message:'Dataset view failed');}
  finally{if(seq===sequence.current){setBusy(false);setLoading(false);}}
 };
 useEffect(()=>{if(readOnly)return;void read('read');return()=>{sequence.current++;active.current?.abort();};},[record.conversationId,record.chatRevision,r.source_sha256,r.artifact.sha256,mode]);
 const keys=result?.columns??[],within=basis==='primary'&&keys.length>1;
 const rows=result?.groups??[];
 const denominator=within?`Within each ${keys[0]} group`:'All matching rows';
 const visibleRows=rows.slice(page*100,page*100+100);
 const displayRows=visibleRows.map(g=>({...Object.fromEntries(keys.map(k=>[k,g[k]===''?'(empty cell)':g[k]])),Rows:g.row_count,Percentage:percent(g[within?'percentage_within_primary':'percentage_total']),Denominator:g[within?'primary_denominator':'total_denominator']}));
 const pending=result&&JSON.stringify(result.columns)!==JSON.stringify([primary,...(split?[split]:[])]);
 const stop=()=>{sequence.current++;active.current?.abort();setBusy(false);setLoading(false);};
 return <section className="table-explorer dataset-view-explorer" aria-label={mode==='groups'?'Interactive dataset groups':'Selected dataset columns'}>
  <div className="analytical-controls">
   <label>{mode==='groups'?'Group by':'Column'}<select aria-label={mode==='groups'?'Outcome group by':'Outcome table column'} disabled={readOnly||busy||loading} value={primary} onChange={e=>{setPrimary(e.target.value);if(split===e.target.value)setSplit('');}}>{candidates.map(c=><option key={c}>{c}</option>)}</select></label>
   <label>{mode==='groups'?'Split by':'Additional column'}<select aria-label={mode==='groups'?'Outcome split by':'Outcome additional column'} disabled={readOnly||busy||loading} value={split} onChange={e=>setSplit(e.target.value)}><option value="">None</option>{candidates.filter(c=>c!==primary).map(c=><option key={c}>{c}</option>)}</select></label>
  </div>
  <button type="button" disabled={readOnly||busy||loading||!primary} onClick={()=>void read('calculate')}>{busy?'Calculating…':mode==='groups'?'Apply grouping':'Load selected columns'}</button>
  {loading&&<p role="status">Loading saved selection; no calculation requested…</p>}
  {busy&&<div role="status"><p>Verifying the full source and calculating your selection. Previous results remain below.</p><button type="button" onClick={stop}>Stop waiting</button><small>Stops this browser request. The bounded backend job may continue until its deadline.</small></div>}
  {error&&<p role="alert">{error} Previous results are preserved.</p>}
  {readOnly&&<p className="result-notice">Historical snapshot. No new reads or calculations are available here.</p>}
  {!readOnly&&pending&&<p className="result-notice">Selection changed. Apply it to calculate new results; the table/chart below still shows {keys.join(' / ')}.</p>}
  {result?<>
   <p>Recorded selection: <strong>{keys.join(' / ')}</strong> · {result.matching_rows.toLocaleString()} matching / {result.source_rows.toLocaleString()} source rows.</p>
   {mode==='table'?<>
    <p>Only the selected columns are shown. This is a verified page of source rows, not a group summary.</p>
    <ResultTable key={JSON.stringify(result.columns)+String(result.table.offset)} data={result.table} rowIds={result.table.preview.map((_,i)=>(result.table.offset??0)+i)} serverPage selectedRow={selected} onSelectRow={setSelected}/>
    <div className="result-pagination"><button disabled={readOnly||busy||loading||Boolean(pending)||(result.table.offset??0)===0} onClick={()=>void read('calculate',Math.max(0,(result.table.offset??0)-20))}>Previous source page</button><span>Matching-row offset {result.table.offset??0}</span><button disabled={readOnly||busy||loading||Boolean(pending)||(result.table.offset??0)+result.table.preview.length>=result.matching_rows} onClick={()=>void read('calculate',(result.table.offset??0)+20)}>Next source page</button></div>
   </>:<>
    {!(presentation==='table'&&keys.length===2)&&<><div className="analytical-controls"><label>Percentage of<select aria-label="Outcome percentage denominator" value={within?'primary':'total'} onChange={e=>setBasis(e.target.value)}><option value="total">All matching rows</option><option value="primary" disabled={keys.length<2}>{keys[0]?`Within each ${keys[0]} group`:'Within first group'}</option></select></label></div>
    <p>{denominator}. Percentages use row counts, not distinct patients. Empty cells and declared missing-marker groups remain included. Changing the denominator does not rescan data.</p></>}
    <div className="verified-preview-controls"><button type="button" aria-pressed={presentation==='table'} onClick={()=>setPresentation('table')}>Group table</button><button type="button" aria-pressed={presentation==='chart'} onClick={()=>setPresentation('chart')}>Group chart</button></div>
    {presentation==='table'&&keys.length===2?<DatasetCrossTab key={JSON.stringify(keys)} fields={keys} groups={rows} matchingRows={result.matching_rows}/>:presentation==='table'?<><ResultTable key={String(within)+JSON.stringify(keys)+page} data={{columns:[...keys,'Rows','Percentage','Denominator'],preview:displayRows,row_count:rows.length}} rowIds={displayRows.map((_,i)=>page*100+i)} serverPage selectedRow={selected} onSelectRow={setSelected}/><div className="result-pagination"><button disabled={page===0} onClick={()=>setPage(p=>p-1)}>Previous groups</button><span>Groups {rows.length?page*100+1:0}–{Math.min((page+1)*100,rows.length)} / {rows.length}</span><button disabled={(page+1)*100>=rows.length} onClick={()=>setPage(p=>p+1)}>Next groups</button></div></>:<>
     <div className="analytical-controls"><label>Chart<select aria-label="Outcome group chart type" value={kind} onChange={e=>setKind(e.target.value)}>{['bar','column','pie','donut'].map(k=><option key={k}>{k}</option>)}</select></label><label>Measure<select aria-label="Outcome group chart measure" value={measure} onChange={e=>setMeasure(e.target.value)}><option value="percentage">Percentage</option><option value="count">Row count</option></select></label></div>
     {rows.length<=100?((kind==='pie'||kind==='donut')&&within?<p>Within-group percentages have separate denominators. Choose bar/column or “All matching rows” for a meaningful pie/donut.</p>:<ChartPlot kind={kind} x={keys.join(' / ')} y={measure==='percentage'?`Percentage · ${denominator}`:'Row count'} values={rows.map((g,i)=>({label:keys.map(k=>g[k]===''?'(empty cell)':String(g[k])).join(' · '),value:Number(g[measure==='count'?'row_count':within?'percentage_within_primary':'percentage_total']),x:i,index:i,members:[],facts:[['Rows',Number(g.row_count)],['Percentage',percent(g[within?'percentage_within_primary':'percentage_total'])],['Denominator',Number(g[within?'primary_denominator':'total_denominator'])]]}))}/>):<p>{rows.length} complete groups exceed the 100-group chart limit. Use the paginated table; groups have not been silently omitted.</p>}
    </>}
    {!rows.length&&<p>No groups match this saved query.</p>}
   </>}
  </>:<p>{mode==='groups'?'Choose age alone, or age with readmitted, then Apply grouping.':'Choose age alone, or add readmitted, then Load selected columns.'} New calculations are explicit read-only actions; no model call or write authorization is needed.</p>}
 </section>;
}
