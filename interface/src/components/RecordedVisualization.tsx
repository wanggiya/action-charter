import {ChartPlot,chartTypes,type PlotValue} from './ChartPlot';
import {geometryFeatures,geometryCoordinates,geometryPath} from '../lib/geometry-view';
import {useEffect,useRef,useState} from 'react';

const record=(value:unknown):Record<string,unknown>=>value&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,unknown>:{};
const numeric=(value:unknown):number|null=>{
  if(typeof value!=='number'&&(typeof value!=='string'||!/^[-]?(?:0|[1-9][0-9]*)(?:[.][0-9]+)?(?:[eE][+-]?[0-9]+)?$/.test(value)||value.length>60))return null;
  const number=Number(value);return Number.isFinite(number)&&Math.abs(number)<=1e15?number:null;
};
const label=(value:unknown)=>value==null?'Missing':String(value).slice(0,160);
const tick=(value:number)=>Number(value.toPrecision(4)).toString();

export type ChartViewState={kind:string;selectedX:string;selectedY:string;aggregation?:'rows'|'count'|'sum'|'mean'|'min'|'max'};
export type MapCamera={zoom:number;x:number;y:number};
export function DataChart({data,selectedRow,onSelectRow,options,onOptions,analysis,onAnalyze,busy}:{data:Record<string,unknown>;selectedRow?:number|null;onSelectRow?:(index:number)=>void;options?:ChartViewState;onOptions?:(value:ChartViewState)=>void;analysis?:Record<string,unknown>|null;onAnalyze?:(spec:{group_by:string;value:string|null;aggregation:string})=>void;busy?:boolean}) {
  const columns=(data.columns as unknown[]).filter((v):v is string=>typeof v==='string').slice(0,32);
  const rows=(data.preview as unknown[]).slice(0,20).map(record);
  const profiles=Array.isArray(data.column_profiles)?data.column_profiles.map(record):[];
  const numbers=columns.filter(column=>profiles.some(profile=>profile.name===column&&profile.observed_type==='numeric-compatible text')||(rows.some(row=>numeric(row[column])!==null)&&rows.every(row=>row[column]==null||numeric(row[column])!==null)));
  const [local,setLocal]=useState<ChartViewState>({kind:'bar',selectedX:columns[0]??'',selectedY:numbers[0]??'',aggregation:'rows'});
  const state=options??local,{kind,selectedX,selectedY}=state,aggregation=state.aggregation??'rows';
  const update=(patch:Partial<ChartViewState>)=>{const next={...state,...patch};if(onOptions)onOptions(next);else setLocal(next);};
  const xOptions=kind==='scatter'?numbers:columns;
  const x=xOptions.includes(selectedX)?selectedX:xOptions[0]??'';
  const y=numbers.includes(selectedY)?selectedY:numbers[0]??'';
  const full=['complete_verified_artifact','complete_filtered_artifact'].includes(String(analysis?.scope))&&analysis?.group_by===x&&(aggregation==='count'||analysis.value===(y||null))&&analysis.aggregation===aggregation;
  const raw:PlotValue[]=rows.flatMap((row,index)=>{const value=aggregation==='count'?1:numeric(row[y]),abscissa=numeric(row[x]);return value===null||kind==='scatter'&&abscissa===null?[]:[{value,x:abscissa??index,label:label(row[x]),index,members:[index]}];});
  let values=raw;
  if(aggregation!=='rows'){
    const groups=new Map<string,PlotValue[]>();
    raw.forEach(v=>{const key=JSON.stringify(rows[v.index][x]??null);groups.set(key,[...(groups.get(key)??[]),v]);});
    values=[...groups.values()].map(group=>({...group[0],members:group.map(v=>v.index),value:aggregation==='count'?group.length:aggregation==='sum'?group.reduce((a,v)=>a+v.value,0):aggregation==='mean'?group.reduce((a,v)=>a+v.value,0)/group.length:aggregation==='min'?Math.min(...group.map(v=>v.value)):Math.max(...group.map(v=>v.value))}));
  }
  if(full&&Array.isArray(analysis.preview))values=analysis.preview.slice(0,100).flatMap((item,i)=>{const row=record(item),v=numeric(row.value);return v===null?[]:[{value:v,x:i,label:label(row.category),index:i,members:[]}];});
  if(!numbers.length&&aggregation!=='count')return <div><p>No chartable numeric column in this saved preview. Text identifiers and mixed/non-finite values are not converted.</p><button type="button" onClick={()=>update({aggregation:'count'})}>Count categories</button></div>;
  return <div className="recorded-chart">
    <div className="visualization-controls"><label>Chart<select aria-label="Chart" value={kind} onChange={e=>update({kind:e.target.value})}>{chartTypes.map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label>
      <label>{kind==='scatter'?'X axis':'Category'}<select aria-label={kind==='scatter'?'X axis':'Category'} value={x} onChange={e=>update({selectedX:e.target.value})}>{xOptions.map(column=><option key={column}>{column}</option>)}</select></label>
      <label>{kind==='scatter'?'Y axis':'Value'}<select aria-label={kind==='scatter'?'Y axis':'Value'} value={y} disabled={aggregation==='count'} onChange={e=>update({selectedY:e.target.value})}>{numbers.map(column=><option key={column}>{column}</option>)}</select></label>
      <label>Aggregation<select aria-label="Chart aggregation" value={aggregation} onChange={e=>update({aggregation:e.target.value as ChartViewState['aggregation']})}>{['rows','count','sum','mean','min','max'].map(value=><option key={value}>{value}</option>)}</select></label>
    </div>
    {aggregation!=='rows'&&onAnalyze&&<div className="verified-preview-controls"><button type="button" disabled={busy} onClick={()=>onAnalyze({group_by:x,value:y||null,aggregation})}>{busy?'Checking artifact…':'Analyze verified CSV'}</button><small>Explicit hash-verified read and aggregation of the complete bounded CSV artifact. No workflow execution.</small></div>}
    <p>{aggregation==='rows'?y:`${aggregation}(${aggregation==='count'?'rows':y})`} by {x} · {full?`${values.length} plotted groups / ${analysis.source_row_count} source rows`:`${values.length} plotted / ${rows.length} preview rows · ${rows.length-raw.length} omitted for missing/invalid values`}.</p>
    {['histogram','box','summary'].includes(kind)&&<p>Statistics describe the plotted values after aggregation; group statistics are unweighted.</p>}
    <ChartPlot kind={kind} values={values} x={x} y={aggregation==='rows'?y:`${aggregation}(${aggregation==='count'?'rows':y})`} selectedRow={full?null:selectedRow} onSelectRow={full?undefined:onSelectRow}/>
    <small>{full?`Complete hash-verified ${analysis.scope==='complete_filtered_artifact'?'matching rows':'artifact'}: ${analysis.source_row_count} source rows, ${analysis.row_count} groups. Grouped marks do not identify individual table rows.`:`Saved sample: first ${rows.length} preview rows of ${label(data.row_count??'?')} recorded rows; limits 20 rows / 32 columns. ${aggregation==='rows'?'One mark per row, no grouping or totals.':'Aggregation covers only these sampled rows, not the complete file. Selecting a group highlights its first included row.'}`} Approximate display; table values are exact. Line/area follow displayed row order. Null numeric values are omitted.</small>
  </div>;
}

export function PointMap({value,selectedRow,onSelectRow,camera:controlledCamera,onCamera}:{value:unknown;selectedRow?:number|null;onSelectRow?:(index:number)=>void;camera?:MapCamera;onCamera?:React.Dispatch<React.SetStateAction<MapCamera>>}) {
  const [localCamera,setLocalCamera]=useState<MapCamera>({zoom:1,x:0,y:0});
  const camera=controlledCamera??localCamera,setCamera=onCamera??setLocalCamera;
  const svgRef=useRef<SVGSVGElement|null>(null);
  const drag=useRef<{x:number;y:number;startX:number;startY:number;moved:boolean}|null>(null);
  const dataAvailable=record(value).status==='available';
  useEffect(()=>{
    const svg=svgRef.current;if(!svg)return;
    const wheel=(event:WheelEvent)=>{event.preventDefault();event.stopPropagation();const matrix=svg.getScreenCTM();const p=matrix?new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse()):{x:220,y:135};setCamera(c=>{const zoom=Math.max(.5,Math.min(16,c.zoom*Math.exp(-Math.max(-200,Math.min(200,event.deltaY))*.002))),ratio=zoom/c.zoom;return{zoom,x:p.x-220-ratio*(p.x-220-c.x),y:p.y-135-ratio*(p.y-135-c.y)};});};
    svg.addEventListener('wheel',wheel,{passive:false});return()=>svg.removeEventListener('wheel',wheel);
  },[dataAvailable,setCamera]);
  const data=record(value);
  const features=geometryFeatures(data);
  const points=features.flatMap(feature=>geometryCoordinates(feature.geometry.coordinates));
  if(!features.length)return <p>{label(data.finding??'No supported WGS84 geometry snapshot recorded. Older runs must not inherit geometry from current files.')}</p>;
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const span=Math.max(maxX-minX,(maxY-minY)*1.6,.001);
  const cx=(minX+maxX)/2,cy=(minY+maxY)/2;
  return <div className="recorded-point-map"><div className="map-view-controls"><button type="button" aria-label="Zoom map in" onClick={()=>setCamera(c=>({...c,zoom:Math.min(16,c.zoom*1.3)}))}>+</button><button type="button" aria-label="Zoom map out" onClick={()=>setCamera(c=>({...c,zoom:Math.max(.5,c.zoom/1.3)}))}>−</button><button type="button" onClick={()=>setCamera({zoom:1,x:0,y:0})}>Fit extent</button><span>{camera.zoom.toFixed(1)}× · drag to pan</span></div><p>Layer {label(data.layer)} · CRS {label(data.crs)} · longitude / latitude</p>
    {selectedRow!=null&&features[selectedRow]&&<div className="map-view-controls"><button type="button" onClick={()=>{const coords=geometryCoordinates(features[selectedRow].geometry.coordinates),fx=coords.map(p=>p[0]),fy=coords.map(p=>p[1]),middleX=(Math.min(...fx)+Math.max(...fx))/2,middleY=(Math.min(...fy)+Math.max(...fy))/2;const zoom=Math.max(1,Math.min(16,span/Math.max(Math.max(...fx)-Math.min(...fx),(Math.max(...fy)-Math.min(...fy))*1.6,span/8)*.8));setCamera({zoom,x:-(middleX-cx)/span*360*zoom,y:(middleY-cy)/span*360*zoom});}}>Fit selected feature</button><button type="button" onClick={()=>onSelectRow?.(-1)}>Clear feature selection</button></div>}
    <details className="map-extent-summary"><summary>Displayed geometry extent and types</summary><dl>{[['West',minX],['East',maxX],['South',minY],['North',maxY]].map(([name,value])=><div key={String(name)}><dt>{name}</dt><dd>{Number(Number(value).toPrecision(8))}</dd></div>)}</dl><p>{[...new Set(features.map(feature=>feature.geometry.type))].map(type=>`${type}: ${features.filter(feature=>feature.geometry.type===type).length}`).join(' · ')}</p><small>Extent covers displayed WGS84 geometry, not necessarily the full dataset. Sample and omitted-feature limits remain visible below.</small></details>
    <svg ref={svgRef} viewBox="0 0 430 285" role="img" aria-label={features.every(f=>f.geometry.type==='Point')?'Recorded WGS84 point map':'Recorded WGS84 geometry map'} style={{touchAction:'none'}} onPointerDown={e=>{drag.current={x:e.clientX,y:e.clientY,startX:camera.x,startY:camera.y,moved:false};e.currentTarget.setPointerCapture(e.pointerId);}} onPointerMove={e=>{const d=drag.current;if(!d)return;const dx=e.clientX-d.x,dy=e.clientY-d.y;if(Math.abs(dx)+Math.abs(dy)>3)d.moved=true;const scale=1/(e.currentTarget.getScreenCTM()?.a??(e.currentTarget.getBoundingClientRect().width/430));setCamera(c=>({...c,x:d.startX+dx*scale,y:d.startY+dy*scale}));}} onPointerUp={e=>{const d=drag.current;if(d&&!d.moved){const matrix=e.currentTarget.getScreenCTM();if(!matrix)return;const point=new DOMPoint(e.clientX,e.clientY).matrixTransform(matrix.inverse());const px=point.x,py=point.y;const hit=document.elementFromPoint(e.clientX,e.clientY)?.closest('[data-map-feature]');const nearest=features.flatMap((f,i)=>f.geometry.type==='Point'?geometryCoordinates(f.geometry.coordinates).map(p=>({index:i,distance:Math.hypot(220+camera.x+(p[0]-cx)/span*360*camera.zoom-px,135+camera.y-(p[1]-cy)/span*360*camera.zoom-py)})):[]).filter(p=>p.distance<12).sort((a,b)=>a.distance-b.distance)[0];const index=nearest?.index??(hit?Number(hit.getAttribute('data-map-feature')):-1);onSelectRow?.(index);}drag.current=null;if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}} onPointerCancel={()=>{drag.current=null;}}>
      <g transform={`translate(${camera.x+220} ${camera.y+135}) scale(${camera.zoom}) translate(-220 -135)`}>
      {[0,1,2,3,4].map(i=><path key={i} className="visualization-grid" d={`M30 ${25+i*55}H410 M${30+i*95} 25V245`}/>)}
      {features.map((feature,i)=>({feature,i})).sort((a,b)=>{const rank=(type:string)=>type.includes('Polygon')?0:type.includes('Line')?1:2;return rank(a.feature.geometry.type)-rank(b.feature.geometry.type);}).map(({feature,i})=>{
        const project=([x,y]:[number,number]):[number,number]=>[220+(x-cx)/span*360,135-(y-cy)/span*360];
        const coordinates=geometryCoordinates(feature.geometry.coordinates),first=coordinates[0];
        const choose=()=>onSelectRow?.(i);
        return <g key={feature.id} data-map-feature={i} className={selectedRow===i?'visual-mark selected':'visual-mark'} role={onSelectRow?'button':undefined} tabIndex={onSelectRow?0:undefined} aria-label={`Feature ${feature.id}: ${feature.geometry.type==='Point'?`${first[0]}, ${first[1]}`:feature.geometry.type}`} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}}}><title>Feature {feature.id} · {feature.geometry.type}{feature.geometry.type==='Point'?` · ${first[0]}, ${first[1]}`:''}</title>{['Point','MultiPoint'].includes(feature.geometry.type)?coordinates.map((p,j)=><circle key={j} cx={project(p)[0]} cy={project(p)[1]} r={(selectedRow===i?8:5)/camera.zoom}/>):<path className={`map-geometry ${feature.geometry.type.includes('Polygon')?'polygon':'line'}`} d={geometryPath(feature.geometry,project)} fillRule="evenodd"/>}</g>;
      })}
      </g><text x="25" y="275">{Number(minX.toPrecision(7))} → {Number(maxX.toPrecision(7))} source longitude</text><text x="405" y="18" textAnchor="end">N ↑</text>
    </svg>
    {selectedRow!=null&&features[selectedRow]&&<div className="selected-feature"><p>Selected feature {features[selectedRow].id} · {features[selectedRow].geometry.type}{features[selectedRow].geometry.type==='Point'?` · longitude ${geometryCoordinates(features[selectedRow].geometry.coordinates)[0][0]} · latitude ${geometryCoordinates(features[selectedRow].geometry.coordinates)[0][1]}`:''}</p><dl>{Object.entries(features[selectedRow].properties).map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value??'Missing'}</dd></div>)}</dl></div>}
    <p>{features.length} features shown · {label(data.examined_features)} examined / {label(data.total_features)} features · {label(data.skipped_features)} skipped{data.truncated===true?' · truncated sample':''}</p>
    <small>Selected snapshot layer, first {label(data.feature_limit??32)} features; WGS84 points, lines and polygon boundaries. Longitude/latitude diagram distorts distances. No basemap or additional file read in this map component. Geometry is limited to {label(data.vertex_limit??2048)} vertices, attributes to 12 columns / 160 characters.</small>
    <details><summary>Geometry snapshot identity</summary><code>{label(data.snapshot_sha256??'Not recorded')}</code><p>This digest identifies the saved geometry snapshot, not the whole source file.</p></details>
  </div>;
}

export function RecordedVisualization({outcome,runId,stepId}:{outcome:unknown;runId:string;stepId:string}) {
  const data=record(outcome);
  const table=Array.isArray(data.preview)&&Array.isArray(data.columns);
  const spatial=data.spatial_preview!==undefined||Array.isArray(data.layers);
  if(!table&&!spatial)return null;
  const output=record(data.output);
  return <details className="recorded-visualization"><summary>{table?'Chart recorded data':'Map recorded geometry'}</summary>
    <p className="visualization-provenance">Recorded snapshot · run {runId.slice(0,12)} · {stepId}<br/>Artifact: {label(output.path??data.source??'Not recorded')}</p>
    {table?<DataChart data={data}/>:<PointMap value={data.spatial_preview}/>}
    <small>Saved snapshot; current files are not rechecked. Viewing makes no model call or execution.</small>
  </details>;
}
