import {DiscoveryStatus} from './DiscoveryStatus';
import {SpatialExplorer} from './SpatialExplorer';
import {loadSpatial,type SpatialResult,type SpatialOptions} from '../lib/spatial-view';
import {geometryFeatures,geometryCoordinates} from '../lib/geometry-view';
import {useEffect,useRef,useState} from 'react';
import {Maximize2,Minimize2,X} from 'lucide-react';
import {z} from 'zod';
import type {WorkflowRun} from '../lib/workflow-tools';
import {runs} from '../lib/workflow-tools';
import {skillLabel} from '../lib/skill-labels';
import {PanelResize} from './PanelResize';
import {DataChart,PointMap,type ChartViewState,type MapCamera} from './RecordedVisualization';
import {ReadableValidation} from './OperationResult';
import {OperationFlow} from './OperationFlow';
import {CalculationSummary} from './CalculationEditor';
import {CriticOutcome} from './CriticOutcome';
import {ResultTable,emptyTableView} from './ResultTable';
import {VerifiedResultExplorer} from './VerifiedResultExplorer';
import {exploreResult,defaultExplorationQuery,type ExplorationResult,type ExplorationQuery,type ChartAnalysisSpec,type ResultViewSpec} from '../lib/result-exploration';

export type ResultView='Overview'|'Table'|'Map'|'Chart'|'Checks';
const resultViews:ResultView[]=['Overview','Table','Map','Chart','Checks'];
const object=(v:unknown):Record<string,unknown>=>v&&typeof v==='object'&&!Array.isArray(v)?v as Record<string,unknown>:{};
const verifiedSchema=z.object({run_id:z.string(),plan_sha256:z.string(),step_id:z.string(),source:z.string(),source_sha256:z.string(),verified_at_read:z.literal(true),row_count:z.number(),column_count:z.number(),columns:z.array(z.string()).max(32),preview:z.array(z.record(z.unknown())).max(1000),preview_truncated:z.boolean(),columns_truncated:z.boolean(),cells_truncated:z.boolean(),chart_analysis:z.object({columns:z.array(z.string()).max(2),preview:z.array(z.object({category:z.string().nullable(),value:z.number().finite().nullable()})).max(100),row_count:z.number(),source_row_count:z.number(),scope:z.literal('complete_verified_artifact'),group_by:z.string(),value:z.string().nullable(),aggregation:z.string(),missing_values:z.string()}).optional(),execution_performed:z.literal(false),approval_performed:z.literal(false)});
export type ResultRecord={run_id:string;plan_sha256?:string;conversation_id?:string|null;status:string;started_at?:string;steps:WorkflowRun['steps'];finding?:string|null;durable?:WorkflowRun};

function ResultViews({record,stepId,view,setView,initialSpec,onViewApplied}:{record:ResultRecord;stepId:string;view:ResultView;setView:(view:ResultView)=>void;initialSpec?:ResultViewSpec;onViewApplied?:()=>void}) {
  const [spatialView,setSpatialView]=useState<SpatialResult|null>(null);
  const [selectedRow,setSelectedRow]=useState<number|null>(null);
  const [explored,setExplored]=useState<ExplorationResult|null>(null),[explorationOpen,setExplorationOpen]=useState(false);
  const [verified,setVerified]=useState<Record<string,unknown>|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [tableState,setTableState]=useState(emptyTableView),[chartState,setChartState]=useState<ChartViewState>({kind:'bar',selectedX:'',selectedY:'',aggregation:'rows'}),[mapCamera,setMapCamera]=useState<MapCamera>({zoom:1,x:0,y:0});
  const preferenceKey=`actioncharter:chart-view:v1:${record.conversation_id??'legacy'}:${record.run_id}:${stepId}`;
  const restored=useRef(false);
  useEffect(()=>{
    if(restored.current)return;restored.current=true;
    try{const value=z.object({kind:z.enum(['bar','column','line','area','pie','donut','scatter','histogram','box','summary']),selectedX:z.string().max(120),selectedY:z.string().max(120),aggregation:z.enum(['rows','count','sum','mean','min','max']).optional()}).parse(JSON.parse(localStorage.getItem(preferenceKey)??'null'));setChartState(value);}catch{/* Default presentation. */}
  },[preferenceKey]);
  useEffect(()=>{if(!restored.current)return;try{localStorage.setItem(preferenceKey,JSON.stringify(chartState));}catch{/* Optional presentation storage. */}},[chartState,preferenceKey]);
  const alive=useRef(true);
  const bodyRef=useRef<HTMLDivElement|null>(null);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
  useEffect(()=>{bodyRef.current?.scrollTo(0,0);},[view]);
  const step=record.steps.find(s=>s.step_id===stepId)!;
  const outcome=object(step.outcome),spatial=object(spatialView?.kind==='vector'?spatialView.spatial_preview:outcome.spatial_preview);
  const table=Array.isArray(outcome.columns)&&Array.isArray(outcome.preview);
  const discovery=object(outcome.discovery);
  const preliminary=discovery.phase==='verifying';
  const verificationStopped=preliminary&&!['queued','running','cancelling'].includes(record.status);
  const completeExplorationAvailable=!(Number(discovery.file_bytes)>8*1024*1024||Number(outcome.row_count)>10000);
  const spatialDisplayAvailable=!(discovery.schema_version==='spatial-discovery-v1'&&(
    Number(discovery.file_bytes)>8*1024*1024||Number(outcome.band_count)>16||
    Number(outcome.width)*Number(outcome.height)*Number(outcome.band_count)>100000000||
    (Array.isArray(outcome.layers)&&outcome.layers.some(value=>{const layer=object(value);return Number(layer.feature_count)>10000||Number(layer.field_count)>100;}))));
  const features=geometryFeatures(spatial),points=features;
  const attributeColumns=[...new Set(features.flatMap(f=>Object.keys(f.properties)))].slice(0,12);
  const coordinateTable={columns:['Feature','Geometry','Longitude','Latitude',...attributeColumns.map(key=>`Attribute: ${key}`)],preview:features.map(f=>{const coordinate=geometryCoordinates(f.geometry.coordinates)[0];return {Feature:f.id,Geometry:f.geometry.type,Longitude:f.geometry.type==='Point'?coordinate[0]:null,Latitude:f.geometry.type==='Point'?coordinate[1]:null,...Object.fromEntries(attributeColumns.map(key=>[`Attribute: ${key}`,f.properties[key]??null]))};}),row_count:spatial.total_features};
  const data=explored??verified??outcome;
  const completed=['completed','validated_success','reused_completed'].includes(step.status);
  const path=String(object(outcome.output).path??outcome.source??step.arguments.path??'No file reference recorded');
  const load=async(analysis?:{group_by:string;value:string|null;aggregation:string})=>{
    if(!record.durable||!record.plan_sha256||busy)return;
    setBusy(true);setError('');
    try{
      const next=verifiedSchema.parse(await runs({action:'preview',run_id:record.run_id,confirmed_plan_sha256:record.plan_sha256,conversation_id:record.conversation_id??undefined,step_id:stepId,...(analysis?{analysis}:{})}));
      if(next.run_id!==record.run_id||next.plan_sha256!==record.plan_sha256||next.step_id!==stepId)throw new Error('Preview scope does not match this recorded operation.');
      if(alive.current){setVerified(next);setSelectedRow(null);setTableState(emptyTableView());}
    }catch(e){if(alive.current){setVerified(null);setSelectedRow(null);setError(e instanceof Error?e.message:'Verified preview unavailable.');}}
    finally{if(alive.current)setBusy(false);}
  };
  const loadExploration=async(query:ExplorationQuery,analysis?:ChartAnalysisSpec)=>{
    if(!record.durable||!record.plan_sha256||!record.conversation_id||busy)return;
    setBusy(true);setError('');setExplorationOpen(true);
    try{
      const next=await exploreResult({run_id:record.run_id,plan_sha256:record.plan_sha256,conversation_id:record.conversation_id,step_id:stepId},query,analysis);
      if(alive.current){setExplored(next);setVerified(null);setSelectedRow(null);setTableState(emptyTableView());}
    }catch(e){if(alive.current){setExplored(null);setVerified(null);setSelectedRow(null);setError(e instanceof Error?e.message:'Complete CSV exploration unavailable.');}}
    finally{if(alive.current)setBusy(false);}
  };
  const appliedInitialView=useRef<ResultViewSpec|null>(null);
  useEffect(()=>{
    if(!initialSpec||appliedInitialView.current===initialSpec)return;
    if(initialSpec.run_id!==record.run_id||initialSpec.step_id!==stepId||initialSpec.plan_sha256!==record.plan_sha256)return;
    appliedInitialView.current=initialSpec;
    onViewApplied?.();
    if(initialSpec.explanation_fields.length)return;
    if(initialSpec.view==='Map'){
      if(initialSpec.spatial&&record.conversation_id){
        setBusy(true);setError('');
        void loadSpatial({run_id:record.run_id,plan_sha256:initialSpec.plan_sha256,conversation_id:record.conversation_id,step_id:stepId},initialSpec.spatial as SpatialOptions).then(next=>{if(alive.current){setSpatialView(next);setSelectedRow(null);setMapCamera({zoom:1,x:0,y:0});}}).catch(e=>{if(alive.current){setSpatialView(null);setError(e instanceof Error?e.message:'Spatial view failed');}}).finally(()=>{if(alive.current)setBusy(false);});
      }
      return;
    }
    if(initialSpec.chart)setChartState({kind:initialSpec.chart_kind,selectedX:initialSpec.chart.group_by,selectedY:initialSpec.chart.value??'',aggregation:initialSpec.chart.aggregation});
    void loadExploration(initialSpec.query,initialSpec.chart??undefined);
  },[initialSpec]);
  return <>
    <nav className="results-tabs" aria-label="Result views" role="tablist" onKeyDown={event=>{
      const index=resultViews.indexOf(view);
      const next=event.key==='ArrowRight'?(index+1)%resultViews.length:event.key==='ArrowLeft'?(index+resultViews.length-1)%resultViews.length:event.key==='Home'?0:event.key==='End'?resultViews.length-1:null;
      if(next===null)return;
      event.preventDefault();setView(resultViews[next]);
      event.currentTarget.querySelectorAll<HTMLButtonElement>('[role=tab]')[next]?.focus();
    }}>{resultViews.map(tab=><button type="button" key={tab} role="tab" tabIndex={view===tab?0:-1} aria-selected={view===tab} aria-controls={`result-view-${tab}`} id={`result-tab-${tab}`} onClick={()=>setView(tab)}>{tab}</button>)}</nav>
    <div ref={bodyRef} className="results-body" role="tabpanel" tabIndex={0} id={`result-view-${view}`} aria-labelledby={`result-tab-${view}`}>
      <article className="outcome-step result-active-operation">
        <header className="result-operation-heading"><div><h3>{view}</h3><span>{skillLabel(step.skill_id)} · {stepId} · {step.status.replaceAll('_',' ')}</span></div>{completed&&<span className="result-source-badge">{preliminary?(verificationStopped?'Verification incomplete':'Verification pending'):spatialView?'Spatial hash verified at read':verified||explored?'CSV hash verified at read':'Recorded snapshot'}</span>}</header>
        <DiscoveryStatus outcome={outcome} runStatus={record.status} detailed={view==='Overview'}/>
        {!completed&&<p role="status">This operation has no completed result. Any recorded values may be partial; inspect its status and recovery evidence.</p>}
        {record.finding&&<p className="result-notice">{record.finding}</p>}
        {view==='Overview'&&<><OperationFlow compact stepId={stepId} skill={step.skill_id} arguments={step.arguments} outcome={step.outcome} dependsOn={step.depends_on}/>{step.skill_id==='calculate_csv_columns'&&<CalculationSummary arguments={step.arguments}/>}
          <dl className="result-summary-facts">{['row_count','column_count'].map(key=>outcome[key]!==undefined?<div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{outcome[key]===null?'Pending':String(outcome[key])}</dd></div>:null)}{Array.isArray(outcome.layers)&&outcome.layers.map((layer,i)=>{const item=object(layer);return <div key={i}><dt>{String(item.name??'Layer')}</dt><dd>{String(item.feature_count??'?')} features · {String(item.crs??'CRS unknown')}</dd></div>;})}</dl>
          <p>Choose Table, Map or Chart to inspect this operation. Each view identifies its sample limits. Checks contains deterministic validation and separate advisory assessment.</p>
          <details><summary>Recorded metadata</summary><pre>{JSON.stringify(step.outcome,null,2)}</pre></details></>}
        {view==='Table'&&((completed||preliminary)?(table||points.length?<>{!table&&<p>{spatialView?.kind==='vector'?'Verified display geometry':'Saved geometry'} and bounded attributes only. Longitude/latitude columns apply to points; unsupported/skipped features are not included.</p>}
          {table&&completed&&completeExplorationAvailable&&record.durable&&record.conversation_id&&<div className="verified-preview-controls"><button type="button" disabled={busy} onClick={()=>void loadExploration(defaultExplorationQuery())}>Explore complete CSV</button>{explored&&<button type="button" onClick={()=>{setExplored(null);setExplorationOpen(false);setError('');setSelectedRow(null);}}>Use saved snapshot</button>}</div>}
          {table&&explorationOpen&&<VerifiedResultExplorer data={explored} busy={busy} error={error} onLoad={query=>void loadExploration(query)}/>}
          {table&&completed&&completeExplorationAvailable&&record.durable&&!explorationOpen&&<details className="result-preview-options"><summary>Preview options</summary><div className="verified-preview-controls"><button type="button" disabled={busy} onClick={()=>void load()}>{busy?'Checking artifact…':verified?'Recheck CSV artifact':'Load verified CSV'}</button>{verified&&<button onClick={()=>{setVerified(null);setSelectedRow(null);setTableState(emptyTableView());setError('');}}>Use saved snapshot</button>}<small>Legacy larger preview only. Search and sorting still affect loaded rows. No workflow execution.</small></div></details>}
          {error&&<p role="alert">{error} The saved snapshot is preserved.</p>}
          {verified&&<p>Hash verified when loaded · {String(verified.source_sha256).slice(0,12)} · limited to 1,000 rows, 32 columns, 160 characters/cell and 128 KB.{verified.cells_truncated?' Some cell text is shortened.':''}{verified.columns_truncated?' Some columns are omitted.':''}</p>}
          <ResultTable key={explored?'explored':verified?'verified':'snapshot'} data={table?data:coordinateTable} rowIds={explored?.row_ids} serverPage={Boolean(explored)} state={tableState} onState={setTableState} selectedRow={selectedRow} onSelectRow={setSelectedRow}/></>:<p>No table snapshot recorded for this operation. Raster, database and other metadata may be available in Overview.</p>):null)}
        {view==='Map'&&error&&<p role="alert">{error} Saved inspection evidence is preserved.</p>}
        {view==='Map'&&!spatialDisplayAvailable?<p>Metadata and package identity are available in Overview. This source exceeds the bounded viewer's file, feature, field or band limits; full geometry/pixel display is unavailable.</p>:view==='Map'&&(completed?(['inspect_vector','inspect_raster'].includes(step.skill_id)?<SpatialExplorer blocked={busy} scope={record.durable&&record.plan_sha256&&record.conversation_id?{run_id:record.run_id,plan_sha256:record.plan_sha256,conversation_id:record.conversation_id,step_id:stepId}:null} skill={step.skill_id} outcome={outcome} value={spatialView} onValue={setSpatialView} selectedRow={selectedRow} onSelectRow={index=>setSelectedRow(index<0?null:index)} camera={mapCamera} onCamera={setMapCamera} />:Array.isArray(outcome.layers)||outcome.spatial_preview?<PointMap value={spatial} camera={mapCamera} onCamera={setMapCamera} selectedRow={selectedRow} onSelectRow={setSelectedRow}/>:<p>No spatial snapshot recorded for this operation. Select a completed vector or raster inspection. CSV and database validation metadata are not map geometries.</p>):null)}
        {view==='Chart'&&(completed?(table||points.length?<><p>Configure the chart below. The plotted data identifies its sample or complete verified scope.</p><DataChart data={table?data:coordinateTable} analysis={object(explored?.chart_analysis??verified?.chart_analysis)} busy={busy} onAnalyze={table&&record.durable?(spec)=>{if(explored)void loadExploration(explored.query,{...spec,aggregation:spec.aggregation as ChartAnalysisSpec['aggregation']});else void load(spec);}:undefined} options={chartState} onOptions={setChartState} selectedRow={explored?explored.row_ids.indexOf(selectedRow??-1):selectedRow} onSelectRow={index=>setSelectedRow(explored?.row_ids[index]??index)}/>{explored&&<p>Filters apply to {explored.matched_row_count} of {explored.row_count} verified source rows. Aggregates cover all matching rows; unaggregated marks show only the current page sample.</p>}{error&&<p role="alert">{error}</p>}{selectedRow!==null&&(explored?explored.row_ids.indexOf(selectedRow):selectedRow)>=20&&<p>The selected table row lies outside the first 20 chart rows.</p>}</>:<p>No chartable table or geometry-attribute snapshot recorded. Choose an executed CSV or vector operation.</p>):null)}
        {view==='Checks'&&<><ReadableValidation value={step.validation_outcome}/><details><summary>Validation details</summary><pre>{JSON.stringify(step.validation_outcome,null,2)}</pre></details>{record.durable&&<CriticOutcome run={record.durable}/>}</>}
      </article>
      <details className="results-provenance"><summary>Source and run identity</summary><dl><div><dt>File reference</dt><dd>{path}</dd></div><div><dt>Run ID</dt><dd>{record.run_id}</dd></div><div><dt>Plan digest</dt><dd>{record.plan_sha256??'Not recorded'}</dd></div><div><dt>Recorded execution</dt><dd>{record.status}</dd></div></dl><p>Saved snapshots do not establish current file freshness. Viewing/filtering/selecting data does not modify it or grant execution authority.</p></details>
    </div>
  </>;
}

export function ResultsWorkspace({record,notice,initialStep,initialView='Overview',initialSpec,onViewApplied,onClose}:{record:ResultRecord|null;notice:string;initialStep?:string;initialView?:ResultView;initialSpec?:ResultViewSpec;onViewApplied?:()=>void;onClose:()=>void}) {
  const [expanded,setExpanded]=useState(false),[chosenStep,setChosenStep]=useState(initialStep??''),[view,setView]=useState<ResultView>(initialView);
  const step=record?.steps.some(s=>s.step_id===chosenStep)?chosenStep:record?.steps[record.steps.length-1]?.step_id??'';
  return <aside className={`record-workspace workspace-right-panel workflow-outcome-panel results-workspace ${expanded?'is-expanded':''}`} aria-labelledby="outcome-title">
    {!expanded&&<PanelResize side="results"/>}
    <header className="results-workspace-header"><div><small>Recorded data explorer</small><h2 id="outcome-title">Current outcome</h2></div><div><button type="button" aria-label={expanded?'Restore graph beside results':'Expand results'} title={expanded?'Restore graph beside results':'Expand results'} onClick={()=>setExpanded(v=>!v)}>{expanded?<Minimize2 size={17}/>:<Maximize2 size={17}/>}</button><button type="button" aria-label="Close outcome" onClick={onClose}><X size={18}/></button></div></header>
    {record&&record.steps.length?<><div className="results-operation-picker"><label>Operation result<select aria-label="Operation result" value={step} onChange={e=>setChosenStep(e.target.value)}>{record.steps.map(s=><option key={s.step_id} value={s.step_id}>{s.step_id} · {skillLabel(s.skill_id)} · {s.status}</option>)}</select></label><small>Run {record.run_id.slice(0,12)} · {record.status.replaceAll('_',' ')}</small><small className="results-narrow-note">Close Results to return to the graph.</small></div><ResultViews key={`${record.run_id}:${step}`} record={record} stepId={step} view={view} setView={setView} initialSpec={initialSpec} onViewApplied={onViewApplied}/></>:<p className="results-empty">{notice||'No matching recorded outcome. Execute a reviewed workflow or select an existing run in Execution History.'}</p>}
  </aside>;
}
