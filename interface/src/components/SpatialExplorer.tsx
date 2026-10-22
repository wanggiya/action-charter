import {useEffect,useRef,useState} from 'react';
import {PointMap,type MapCamera} from './RecordedVisualization';
import {loadSpatial,type SpatialScope,type SpatialResult,type SpatialOptions} from '../lib/spatial-view';

type Props={blocked?:boolean;scope:SpatialScope|null;skill:string;outcome:Record<string,unknown>;value:SpatialResult|null;onValue:(value:SpatialResult|null)=>void;selectedRow:number|null;onSelectRow:(value:number)=>void;camera:MapCamera;onCamera:React.Dispatch<React.SetStateAction<MapCamera>>};
export function SpatialExplorer({blocked=false,scope,skill,outcome,value,onValue,selectedRow,onSelectRow,camera,onCamera}:Props){
 const vector=skill==='inspect_vector';
 const loaded=value?.kind==='vector'||value?.kind==='raster'?value:null;
 const [layer,setLayer]=useState(value?.kind==='vector'?value.layer:''),[visible,setVisible]=useState(true);
 const [render,setRender]=useState<SpatialOptions['render']>(value?.kind==='raster'?value.render:'gray');
 const [bands,setBands]=useState(value?.kind==='raster'?value.bands:[1]),[stretch,setStretch]=useState<SpatialOptions['stretch']>(value?.kind==='raster'?value.stretch:'minmax');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[pixel,setPixel]=useState<Extract<SpatialResult,{kind:'pixel'}>|null>(null),[opacity,setOpacity]=useState(1);
 useEffect(()=>{if(value?.kind==='vector')setLayer(value.layer);if(value?.kind==='raster'){setRender(value.render);setBands(value.bands);setStretch(value.stretch);}},[value]);
 const alive=useRef(true);useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 const load=async(options:SpatialOptions)=>{
  if(!scope||busy||blocked)return;setBusy(true);setError('');
  try{const next=await loadSpatial(scope,options);if(!alive.current)return;
   if(next.kind==='pixel')setPixel(next);else{onValue(next);setPixel(null);onSelectRow(-1);onCamera({zoom:1,x:0,y:0});if(next.kind==='vector')setLayer(next.layer);}
  }catch(e){if(alive.current){setError(e instanceof Error?e.message:'Spatial view unavailable');onValue(null);setPixel(null);}}
  finally{if(alive.current)setBusy(false);}
 };
 const count=Number(outcome.band_count??(value&&'band_count'in value?value.band_count:1));
 const layers=loaded?.kind==='vector'?loaded.layers:Array.isArray(outcome.layers)?outcome.layers.map((item:unknown)=>String((item as {name:string}).name)):[];
 return <div className="spatial-explorer">
  <div className="visualization-controls spatial-controls">
   {vector?<label>Layer<select aria-label="Vector layer" value={layer||layers[0]||''} onChange={e=>setLayer(e.target.value)}>{layers.map(name=><option key={name}>{name}</option>)}</select></label>:<>
    <label>Display<select aria-label="Raster display" value={render} onChange={e=>{const mode=e.target.value as SpatialOptions['render'];setRender(mode);setBands(mode==='rgb'?[1,Math.min(2,count),Math.min(3,count)]:[bands[0]]);}}>{[['gray','Grayscale'],['ramp','Continuous color'],['rgb','RGB bands'],['classes','Categorical colors']].map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
    {bands.map((band,i)=><label key={i}>{render==='rgb'?['Red','Green','Blue'][i]:'Band'}<select aria-label={render==='rgb'?`${['Red','Green','Blue'][i]} band`:'Raster band'} value={band} onChange={e=>setBands(items=>items.map((v,j)=>i===j?Number(e.target.value):v))}>{Array.from({length:Math.min(16,count)},(_,j)=><option key={j} value={j+1}>{j+1}</option>)}</select></label>)}
    <label>Stretch<select aria-label="Raster stretch" value={stretch} disabled={render==='classes'} onChange={e=>setStretch(e.target.value as SpatialOptions['stretch'])}><option value="minmax">Preview min / max</option><option value="percentile">Preview 2–98%</option></select></label>
   </>}
   <button type="button" disabled={!scope||busy||blocked} onClick={()=>void load(vector?{mode:'vector',...(layer?{layer}:{})}:{mode:'raster',bands,render,stretch})}>{busy||blocked?'Checking spatial source…':vector?'Load verified vector':loaded?'Apply raster display':'Load verified raster'}</button>
  </div>
  <p className="spatial-read-note">Explicit source-hash check and bounded read. Display settings do not modify the dataset or execute a workflow.</p>
  {error&&<p role="alert">{error} Verified view cleared; the saved inspection evidence remains available.</p>}
  {vector?<>
   <div className="map-view-controls"><button type="button" aria-pressed={visible} onClick={()=>setVisible(v=>!v)}>{visible?'Hide layer':'Show layer'}</button>{loaded?.kind==='vector'&&<button type="button" onClick={()=>{onValue(null);setLayer('');onSelectRow(-1);onCamera({zoom:1,x:0,y:0});}}>Use recorded geometry</button>}</div>
   {loaded?.kind==='vector'&&<p>Source CRS {loaded.source_crs??'unknown'} → display {loaded.display_crs??'unavailable'}{loaded.reprojected?' · reprojected for display only':''}. Layer {loaded.layer}.</p>}
   {visible?<PointMap value={loaded?.kind==='vector'?loaded.spatial_preview:outcome.spatial_preview} camera={camera} onCamera={onCamera} selectedRow={selectedRow} onSelectRow={onSelectRow}/>:<p>Layer hidden. Its selected attributes remain available in Table.</p>}
  </>:loaded?.kind==='raster'?<>
   <label className="raster-opacity">Opacity<input aria-label="Raster opacity" type="range" min="0" max="1" step="0.05" value={opacity} onChange={e=>setOpacity(Number(e.target.value))}/></label>
   <RasterImage value={loaded} opacity={opacity} camera={camera} onCamera={onCamera} onPixel={(row,column)=>void load({mode:'pixel',row,column,bands:loaded.bands})}/>
   <p>{loaded.source_width} × {loaded.source_height} source pixels · {loaded.width} × {loaded.height} preview · CRS {loaded.crs??'unknown'}</p>
   <p>{loaded.nodata_preview_pixels} NoData/non-finite preview pixels shown transparent. Click the image to read an exact source pixel.</p>
   <div className="raster-legend" aria-label="Raster legend">{loaded.render==='ramp'&&<span className="raster-ramp"/>}{loaded.ranges.map(range=><span key={range.band}>Band {range.band}: {range.minimum??'NoData'} → {range.maximum??'NoData'}</span>)}{loaded.legend.map(item=><span key={item.value}><i style={{background:item.color}}/>{item.value}</span>)}</div>
   {pixel&&<div className="selected-feature" role="status">Source pixel row {pixel.row}, column {pixel.column} · center {pixel.x}, {pixel.y} ({pixel.crs??'CRS unknown'})<p>{pixel.values.map((v,i)=>`Band ${pixel.bands[i]}: ${v??'NoData'}`).join(' · ')}</p></div>}
   <details><summary>Raster bounds and rendering scope</summary><p>West / south / east / north: {loaded.bounds.join(' / ')}. Source affine transform: {loaded.transform.join(', ')}.</p><p>Nearest-neighbor preview, maximum 256 × 256. Ranges and classes describe preview pixels only, not complete-raster statistics. Raster is shown in its pixel grid; source CRS/transform provide spatial context. No basemap or raster reprojection.</p></details>
  </>:<p>Load a verified raster to view its pixels. Inspection metadata remains in Overview. Older results without a source binding require a new inspection.</p>}
 </div>;
}
function RasterImage({value,opacity,camera,onCamera,onPixel}:{value:Extract<SpatialResult,{kind:'raster'}>;opacity:number;camera:MapCamera;onCamera:React.Dispatch<React.SetStateAction<MapCamera>>;onPixel:(row:number,column:number)=>void}){
 const svg=useRef<SVGSVGElement|null>(null),drag=useRef<{x:number;y:number;cx:number;cy:number;moved:boolean}|null>(null);
 const width=value.width,height=value.height;
 const zoom=(factor:number,x=width/2,y=height/2)=>onCamera(c=>{const next=Math.max(.5,Math.min(16,c.zoom*factor)),ratio=next/c.zoom;return{zoom:next,x:x-ratio*(x-c.x),y:y-ratio*(y-c.y)};});
 const point=(x:number,y:number)=>{const matrix=svg.current?.getScreenCTM();return matrix?new DOMPoint(x,y).matrixTransform(matrix.inverse()):null;};
 useEffect(()=>{const node=svg.current;if(!node)return;const wheel=(e:WheelEvent)=>{e.preventDefault();e.stopPropagation();const p=point(e.clientX,e.clientY);if(p)zoom(Math.exp(-Math.max(-200,Math.min(200,e.deltaY))*.002),p.x,p.y);};node.addEventListener('wheel',wheel,{passive:false});return()=>node.removeEventListener('wheel',wheel);},[width,height]);
 return <><div className="map-view-controls"><button type="button" aria-label="Zoom raster in" onClick={()=>zoom(1.3)}>+</button><button type="button" aria-label="Zoom raster out" onClick={()=>zoom(1/1.3)}>−</button><button type="button" onClick={()=>onCamera({zoom:1,x:0,y:0})}>Fit raster</button><span>{camera.zoom.toFixed(1)}× · drag to pan</span></div>
  <svg ref={svg} className="raster-image" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Verified raster preview" onPointerDown={e=>{const p=point(e.clientX,e.clientY);if(!p)return;drag.current={x:p.x,y:p.y,cx:camera.x,cy:camera.y,moved:false};e.currentTarget.setPointerCapture(e.pointerId);}} onPointerMove={e=>{const d=drag.current,p=point(e.clientX,e.clientY);if(!d||!p)return;const dx=p.x-d.x,dy=p.y-d.y;if(Math.hypot(dx,dy)>Math.max(width,height)/100)d.moved=true;if(d.moved)onCamera(c=>({...c,x:d.cx+dx,y:d.cy+dy}));}} onPointerUp={e=>{const d=drag.current,p=point(e.clientX,e.clientY);if(d&&!d.moved&&p){const x=(p.x-camera.x)/camera.zoom,y=(p.y-camera.y)/camera.zoom;if(x>=0&&y>=0&&x<width&&y<height)onPixel(Math.min(value.source_height-1,Math.floor(y/height*value.source_height)),Math.min(value.source_width-1,Math.floor(x/width*value.source_width)));}drag.current=null;if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}} onPointerCancel={()=>{drag.current=null;}}>
   <g transform={`translate(${camera.x} ${camera.y}) scale(${camera.zoom})`}><image href={value.image} width={width} height={height} opacity={opacity} style={{imageRendering:'pixelated'}}/></g>
  </svg></>;
}
