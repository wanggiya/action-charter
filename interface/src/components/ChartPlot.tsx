import {useEffect,useRef,useState,type KeyboardEvent} from 'react';
export type PlotValue={value:number;x:number;label:string;index:number;members:number[]};
export const chartTypes=[['bar','Horizontal bar'],['column','Column'],['line','Line'],['area','Area'],['pie','Pie'],['donut','Donut'],['scatter','Scatter'],['histogram','Histogram'],['box','Box plot'],['summary','Summary']] as const;
const colors=['#60a5fa','#22d3ee','#4ade80','#fbbf24','#fb923c','#c084fc','#f472b6','#a3e635'];
const tick=(v:number)=>Number(v.toPrecision(4)).toString();
type ChartProps={kind:string;values:PlotValue[];x:string;y:string;selectedRow?:number|null;onSelectRow?:(i:number)=>void};
type ChartDetail={title:string;fields:[string,string|number][]};
export function ChartPlot(props:ChartProps){
 const frame=useRef<HTMLDivElement>(null),[detail,setDetail]=useState<ChartDetail|null>(null);
 const scope=JSON.stringify([props.kind,props.x,props.y,props.values]);
 useEffect(()=>setDetail(null),[scope]);
 useEffect(()=>{
  if(!detail)return;
  const outside=(event:PointerEvent)=>{if(event.target instanceof Node&&!frame.current?.contains(event.target))setDetail(null);};
  const escape=(event:globalThis.KeyboardEvent)=>{if(event.key==='Escape')setDetail(null);};
  document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);
  return ()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);};
 },[detail]);
 return <div ref={frame} className="chart-inspection" onClick={event=>{if(!(event.target as Element).closest('[data-chart-value],[data-chart-series],.chart-value-detail'))setDetail(null);}}>
  <PlotMarks {...props} onInspect={setDetail}/>
  {detail&&<section className="chart-value-detail" role="group" aria-label="Chart value details" aria-live="polite"><strong>{detail.title}</strong><dl>{detail.fields.map(([label,value],i)=><div key={i}><dt>{label}</dt><dd>{value}</dd></div>)}</dl><small>Plotted data · click elsewhere or press Escape to dismiss</small></section>}
 </div>;
}
function PlotMarks({kind,values,x,y,selectedRow,onSelectRow,onInspect}:ChartProps&{onInspect:(detail:ChartDetail)=>void}){
 const min=Math.min(0,...values.map(v=>v.value)),max=Math.max(0,...values.map(v=>v.value));
 const px=(i:number)=>55+(i+.5)/values.length*345,py=(v:number)=>230-(v-min)/(max-min||1)*200;
 const choose=(row:PlotValue)=>{
  const fields:[string,string|number][]=[[x||'Category',kind==='scatter'?row.x:row.label],[y||'Value',row.value]];
  if(kind==='pie'||kind==='donut')fields.push(['Share of plotted total',`${(row.value/values.reduce((sum,v)=>sum+v.value,0)*100).toFixed(1)}%`]);
  if(row.members.length>1)fields.push(['Contributing preview rows',row.members.length]);
  onInspect({title:row.label,fields});onSelectRow?.(row.index);
 };
 const key=(e:KeyboardEvent,row:PlotValue)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(row);}};
 const props=(row:PlotValue)=>({'data-chart-value':row.value,className:selectedRow!=null&&row.members.includes(selectedRow)?'visual-mark selected':'visual-mark',role:'button' as const,tabIndex:0,'aria-label':`${row.label}: ${row.value}`,onClick:()=>choose(row),onKeyDown:(e:KeyboardEvent)=>key(e,row)});
 if(!values.length)return <p>No plottable rows for these axes.</p>;
 if(kind==='summary')return <dl className="chart-summary">{[['Values',values.length],['Sum',values.reduce((a,v)=>a+v.value,0)],['Mean',values.reduce((a,v)=>a+v.value,0)/values.length],['Minimum',Math.min(...values.map(v=>v.value))],['Maximum',Math.max(...values.map(v=>v.value))]].map(([name,value])=><div key={name}><dt>{name}</dt><dd><button type="button" data-chart-value={value} onClick={()=>onInspect({title:String(name),fields:[['Statistic',String(name)],['Value',Number(value)],['Plotted values',values.length]]})}>{tick(Number(value))}</button></dd></div>)}</dl>;
 if(kind==='pie'||kind==='donut'){
  const total=values.reduce((a,v)=>a+v.value,0);
  if(values.some(v=>v.value<0)||total<=0)return <p role="status">Pie and donut require non-negative values and a positive total. Choose a bar chart for signed values.</p>;
  let angle=-Math.PI/2;
  return <><svg viewBox="0 0 430 300" role="img" aria-label={`${kind==='pie'?'Pie':'Donut'} chart: ${y} by ${x}`}>{values.map((row,i)=>{
   const next=angle+row.value/total*Math.PI*2,polar=(a:number,r:number)=>[215+Math.cos(a)*r,145+Math.sin(a)*r];
   const [sx,sy]=polar(angle,115),[ex,ey]=polar(next,115),[ix,iy]=polar(next,65),[jx,jy]=polar(angle,65);
   const d=kind==='pie'?`M215 145 L${sx} ${sy} A115 115 0 ${next-angle>Math.PI?1:0} 1 ${ex} ${ey} Z`:`M${sx} ${sy} A115 115 0 ${next-angle>Math.PI?1:0} 1 ${ex} ${ey} L${ix} ${iy} A65 65 0 ${next-angle>Math.PI?1:0} 0 ${jx} ${jy} Z`;
   angle=next;
   return <g key={i} {...props(row)}><title>{row.label}: {row.value} ({(row.value/total*100).toFixed(1)}%)</title>{row.value===total?<path d={`M215 30 A115 115 0 1 1 215 260 A115 115 0 1 1 215 30 Z${kind==='donut'?' M215 80 A65 65 0 1 0 215 210 A65 65 0 1 0 215 80 Z':''}`} fillRule="evenodd" style={{fill:colors[i%colors.length]}}/>:<path d={d} style={{fill:colors[i%colors.length]}}/>}</g>;
  })}</svg><div className="chart-legend">{values.map((row,i)=><button key={i} type="button" {...props(row)} style={{'--chart-color':colors[i%colors.length]} as React.CSSProperties}><i/>{row.label}: {tick(row.value)} · {(row.value/total*100).toFixed(1)}%</button>)}</div></>;
 }
 if(kind==='histogram'){
  const low=Math.min(...values.map(v=>v.value)),high=Math.max(...values.map(v=>v.value));
  const bins=Array.from({length:Math.min(10,Math.max(1,Math.ceil(Math.sqrt(values.length))))},()=>[] as PlotValue[]),span=(high-low||1)/bins.length;
  values.forEach(v=>bins[Math.min(bins.length-1,Math.floor((v.value-low)/span))].push(v));
  const count=Math.max(...bins.map(b=>b.length));
  return <svg viewBox="0 0 430 285" role="img" aria-label={`Histogram: ${y}`}><path className="visualization-axis" d="M45 15V235H410"/>{bins.map((b,i)=><g key={i} role="button" tabIndex={0} className="visual-mark" data-chart-value={b.length} aria-label={`${tick(low+i*span)} to ${tick(low+(i+1)*span)}: ${b.length}`} onClick={()=>onInspect({title:'Histogram bin',fields:[['From (inclusive)',low+i*span],['To'+(i===bins.length-1?' (inclusive)':' (exclusive)'),low+(i+1)*span],['Plotted values',b.length]]})} onKeyDown={event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.currentTarget.dispatchEvent(new MouseEvent('click',{bubbles:true}));}}}><title>{tick(low+i*span)} to {tick(low+(i+1)*span)}: {b.length} values</title><rect x={50+i*350/bins.length} y={230-b.length/count*200} width={350/bins.length-3} height={b.length/count*200}/><text x={50+(i+.5)*350/bins.length} y={220-b.length/count*200} textAnchor="middle">{b.length}</text></g>)}<text x="50" y="260">{tick(low)}</text><text x="400" y="260" textAnchor="end">{tick(high)}</text></svg>;
 }
 if(kind==='box'){
  const sorted=values.map(v=>v.value).sort((a,b)=>a-b),quantile=(p:number)=>{const index=(sorted.length-1)*p,lo=Math.floor(index),hi=Math.ceil(index);return sorted[lo]+(sorted[hi]-sorted[lo])*(index-lo);};
  const five=[sorted[0],quantile(.25),quantile(.5),quantile(.75),sorted.at(-1)!],scale=(v:number)=>50+(v-five[0])/(five[4]-five[0]||1)*350;
  return <><svg viewBox="0 0 430 190" role="button" tabIndex={0} className="visual-mark" data-chart-value={five[2]} aria-label={`Box plot: ${y}`} onClick={()=>onInspect({title:`Box plot: ${y}`,fields:[['Minimum',five[0]],['Q1',five[1]],['Median',five[2]],['Q3',five[3]],['Maximum',five[4]],['Plotted values',values.length]]})} onKeyDown={event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.currentTarget.dispatchEvent(new MouseEvent('click',{bubbles:true}));}}}><title>Min, Q1, median, Q3, max: {five.map(tick).join(', ')}</title><path className="visualization-axis" d={`M${scale(five[0])} 85H${scale(five[4])} M${scale(five[0])} 65V105 M${scale(five[4])} 65V105`}/><rect x={scale(five[1])} y="55" width={Math.max(1,scale(five[3])-scale(five[1]))} height="60"/><path className="visualization-axis" d={`M${scale(five[2])} 55V115`}/>{five.map((v,i)=><text key={i} x="20" y={135+i*11}>{['Min','Q1','Median','Q3','Max'][i]}: {tick(v)}</text>)}</svg><small>Linear-interpolated quartiles; whiskers show min/max, with no outlier classification.</small></>;
 }
 const scale=(v:number)=>145+(v-min)/(max-min||1)*255;
 const minX=Math.min(...values.map(v=>v.x)),maxX=Math.max(...values.map(v=>v.x)),minY=Math.min(...values.map(v=>v.value)),maxY=Math.max(...values.map(v=>v.value));
 return <svg viewBox={`0 0 430 ${kind==='bar'?values.length*28+45:285}`} role="img" aria-label={`${chartTypes.find(([id])=>id===kind)?.[1]??kind} chart: ${y} by ${x}`}>
 {kind==='bar'?<><line className="visualization-axis" x1={scale(0)} x2={scale(0)} y1="10" y2={values.length*28+15}/>{values.map((row,i)=><g key={i} {...props(row)}><title>{row.label}: {row.value}</title><text x="4" y={i*28+26}>{row.label.slice(0,12)}</text><rect x={Math.min(scale(0),scale(row.value))} y={i*28+12} width={Math.max(1,Math.abs(scale(row.value)-scale(0)))} height="18" rx="3"/><text x="405" y={i*28+26} textAnchor="end">{tick(row.value)}</text></g>)}<text x="145" y={values.length*28+35}>{tick(min)}</text><text x="400" y={values.length*28+35} textAnchor="end">{tick(max)}</text></>:<><path className="visualization-axis" d="M45 15V235H410"/>
 {(kind==='line'||kind==='area')&&<path className={`chart-series ${kind==='area'?'area':''}`} data-chart-series="true" role="button" tabIndex={0} aria-label={`Inspect ${kind} series`} onClick={event=>{const bounds=event.currentTarget.ownerSVGElement!.getBoundingClientRect();const coordinate=(event.clientX-bounds.left)/bounds.width*430;choose(values[Math.max(0,Math.min(values.length-1,Math.round((coordinate-55)/345*values.length-.5)))]);}} onKeyDown={event=>key(event,values[0])} d={`${values.map((v,i)=>`${i?'L':'M'}${px(i)} ${py(v.value)}`).join(' ')}${kind==='area'?` L${px(values.length-1)} ${py(0)} L${px(0)} ${py(0)} Z`:''}`}/>}
 {values.map((row,i)=><g key={i} {...props(row)}><title>{row.label}: {row.value}</title>{kind==='column'?<rect x={px(i)-Math.min(15,150/values.length)} y={Math.min(py(0),py(row.value))} width={Math.min(30,300/values.length)} height={Math.max(1,Math.abs(py(row.value)-py(0)))}/>:<circle cx={kind==='scatter'?55+(row.x-minX)/(maxX-minX||1)*350:px(i)} cy={kind==='scatter'?230-(row.value-minY)/(maxY-minY||1)*210:py(row.value)} r="5"/>}</g>)}
 <text x="50" y="255">{kind==='scatter'?tick(minX):values[0].label.slice(0,16)}</text><text x="405" y="255" textAnchor="end">{kind==='scatter'?tick(maxX):values.at(-1)!.label.slice(0,16)}</text><text x="40" y="25" textAnchor="end">{tick(kind==='scatter'?maxY:max)}</text><text x="40" y="230" textAnchor="end">{tick(kind==='scatter'?minY:min)}</text><text x="230" y="278" textAnchor="middle">{x}</text></>}
 </svg>;
}
