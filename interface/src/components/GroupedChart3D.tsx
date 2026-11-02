import {useEffect,useState} from 'react';
import type {PlotValue} from './ChartPlot';

type Group=Record<string,string|number|null>;
const label=(v:unknown)=>v===null?'(missing)':v===''?'(empty cell)':String(v);
const colors=['#22d3ee','#60a5fa','#4ade80','#fbbf24','#c084fc'];
export function GroupedChart3D({fields,groups,values,percent}:{fields:string[];groups:Group[];values:PlotValue[];percent:boolean}){
 const [rotation,setRotation]=useState(-30),[elevation,setElevation]=useState(35),[selected,setSelected]=useState<number|null>(null);
 useEffect(()=>setSelected(null),[fields,groups,percent]);
 const rows=[...new Set(groups.map(g=>g[fields[0]]))],columns=[...new Set(groups.map(g=>g[fields[1]]))];
 const maximum=percent?100:Math.max(1,...values.map(v=>v.value)),a=rotation*Math.PI/180,b=elevation*Math.PI/180;
 const project=(x:number,y:number,z:number)=>[450+x*Math.cos(a)-y*Math.sin(a),390+(x*Math.sin(a)+y*Math.cos(a))*Math.sin(b)-z*Math.cos(b)];
 const point=(x:number,y:number,z:number)=>project(x,y,z).join(',');
 const position=(i:number,n:number,span:number)=>n===1?0:-span/2+i*span/(n-1);
 const width=Math.min(38,360/Math.max(1,rows.length)),depth=Math.min(46,220/Math.max(1,columns.length));
 const bars=groups.map((g,i)=>({i,x:position(rows.indexOf(g[fields[0]]),rows.length,430),y:position(columns.indexOf(g[fields[1]]),columns.length,240)})).sort((p,q)=>(p.x*Math.sin(a)+p.y*Math.cos(a))-(q.x*Math.sin(a)+q.y*Math.cos(a)));
 return <div className="chart-inspection grouped-chart-3d" onKeyDown={e=>{if(e.key==='Escape')setSelected(null);}}>
  <div className="analytical-controls"><label>Rotation<input aria-label="3D rotation" type="range" min="-75" max="75" value={rotation} onChange={e=>setRotation(Number(e.target.value))}/></label><label>Elevation<input aria-label="3D elevation" type="range" min="20" max="65" value={elevation} onChange={e=>setElevation(Number(e.target.value))}/></label><button type="button" onClick={()=>{setRotation(-30);setElevation(35);}}>Reset 3D view</button></div>
  <p>{fields[0]} and {fields[1]} form the base; column height is {percent?'percentage (0–100%)':'record count'}. Rotate to reveal hidden columns. Use the cross-table or 2D view for exact comparisons.</p>
  <svg viewBox="0 0 900 560" role="img" aria-label={`3D columns: ${fields.join(' / ')}`} onClick={e=>{if(!(e.target as Element).closest('[data-chart-value]'))setSelected(null);}}>
   <polygon points={[point(-255,-175,0),point(255,-175,0),point(255,175,0),point(-255,175,0)].join(' ')} className="chart-3d-floor"/>
   {[0,.25,.5,.75,1].map(t=><g key={t}><line className="visualization-grid" x1={project(-255,-175,t*270)[0]} y1={project(-255,-175,t*270)[1]} x2={project(255,-175,t*270)[0]} y2={project(255,-175,t*270)[1]}/><text x={project(-255,-175,t*270)[0]-8} y={project(-255,-175,t*270)[1]} textAnchor="end">{Number((maximum*t).toFixed(2))}{percent?'%':''}</text></g>)}
   {bars.map(({i,x,y})=>{const v=values[i],z=270*v.value/maximum,c=columns.indexOf(groups[i][fields[1]]),corners=[[x-width,y-depth],[x+width,y-depth],[x+width,y+depth],[x-width,y+depth]];return <g key={i} data-chart-value={v.value} data-3d-row={label(groups[i][fields[0]])} data-3d-column={label(groups[i][fields[1]])} role="button" tabIndex={0} aria-label={`${v.label}: ${v.value}${percent?'%':''}`} className={`visual-mark${selected===i?' selected':''}`} onClick={()=>setSelected(i)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(i);}}} style={{'--column-color':colors[c%colors.length]} as React.CSSProperties}>
    <title>{v.label}: {v.value}{percent?'%':''}</title>
    <polygon className="chart-3d-side" points={[point(...corners[1] as [number,number],0),point(...corners[2] as [number,number],0),point(...corners[2] as [number,number],z),point(...corners[1] as [number,number],z)].join(' ')}/>
    <polygon className="chart-3d-front" points={[point(...corners[2] as [number,number],0),point(...corners[3] as [number,number],0),point(...corners[3] as [number,number],z),point(...corners[2] as [number,number],z)].join(' ')}/>
    {z>0&&<polygon className="chart-3d-top" points={corners.map(([cx,cy])=>point(cx,cy,z)).join(' ')}/>}
   </g>;})}
   {rows.map((r,i)=><text key={i} x={project(position(i,rows.length,430),185,0)[0]} y={project(position(i,rows.length,430),185,0)[1]+12} textAnchor="middle">{label(r)}</text>)}
   {columns.map((c,i)=><text key={i} x={project(280,position(i,columns.length,240),0)[0]+12} y={project(280,position(i,columns.length,240),0)[1]}>{label(c)}</text>)}
   <text x="450" y="25" textAnchor="middle">{fields[0]} × {fields[1]}</text>
  </svg>
  {selected!==null&&values[selected]&&<section className="chart-value-detail" role="group" aria-label="Chart value details"><strong>{values[selected].label}</strong><dl>{[[percent?'Percentage':'Rows',percent?`${values[selected].value.toFixed(2)}%`:values[selected].value],...values[selected].facts??[]].map(([k,v],i)=><div key={i}><dt>{k}</dt><dd>{v}</dd></div>)}</dl><small>Click the background or press Escape to dismiss.</small></section>}
 </div>;
}
