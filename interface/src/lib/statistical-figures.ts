import type {TableStatistics} from './table-statistics';
export type StatisticalFigure={title:string;caption:string;svg:string;marks:{label:string;value:number|null;detail:string}[]};
const xml=(v:string)=>v.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]!));
const stable=(svg:string)=>svg.replace(/fill="([^"]+)"/g,(_,color:string)=>`fill="${color}" style="fill:${color};opacity:1"`);
const number=(v:number|null)=>v===null?'Unavailable':Number(v.toPrecision(7)).toString();
const start=(height:number,title:string)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 ${height}" width="760" height="${height}" role="img" aria-label="${xml(title)}"><rect width="760" height="${height}" fill="#101d29"/><text x="18" y="26" fill="#eaf4ff" font-family="sans-serif" font-size="16">${xml(title)}</text>`;
/** Pure projections of recorded aggregates; no source reads, fits or external SVG. */
export function groupedMeanFigure(r:TableStatistics,column:string):StatisticalFigure|null{
 const groups=r.grouped_descriptive.filter(g=>g.descriptive.some(d=>d.column===column));if(!groups.length)return null;
 const shown=groups.slice(0,24),title=`Mean ${column} by recorded group`;
 const marks=shown.map(g=>{const d=g.descriptive.find(d=>d.column===column)!;const label=Object.entries(g.group).map(([k,v])=>`${k}: ${v||'(empty)'}`).join(' · ');return {label,value:d.mean,detail:`${label}; mean ${number(d.mean)}; ${g.analysis_rows} analyzed / ${g.matching_rows} matching rows`};});
 const values=marks.map(m=>m.value??0),lo=Math.min(0,...values),hi=Math.max(0,...values),span=hi-lo||1,x=(v:number)=>275+455*(v-lo)/span,height=90+marks.length*34;
 let svg=start(height,title)+`<line x1="${x(0)}" y1="43" x2="${x(0)}" y2="${height-35}" stroke="#8ba7b5"/>`;
 marks.forEach((m,i)=>{const y=49+i*34,v=m.value??0;svg+=`<text x="18" y="${y+17}" fill="#d4e6ef" font-family="sans-serif" font-size="12">${xml(m.label.length>34?m.label.slice(0,31)+'…':m.label)}</text><rect data-mark="${i}" tabindex="0" role="button" aria-label="${xml(m.detail)}" x="${Math.min(x(0),x(v))}" y="${y}" width="${Math.max(2,Math.abs(x(v)-x(0)))}" height="23" fill="${m.value===null?'#607382':'#36b7d5'}"><title>${xml(m.detail)}</title></rect><text x="${Math.min(700,Math.max(x(v)+5,280))}" y="${y+17}" fill="#ffffff" font-family="sans-serif" font-size="11">${xml(number(m.value))}</text>`;});
 svg+=`<text x="275" y="${height-12}" fill="#c3d5df" font-family="sans-serif" font-size="12">${number(lo)} to ${number(hi)} · original variable units · zero baseline</text></svg>`;
 return {title,svg:stable(svg),marks,caption:`Recorded means; no confidence intervals or uncertainty bars. Group sizes differ; inspect analyzed/matching counts. ${shown.length} of ${groups.length} groups shown; all groups remain in the tables.`};
}
export function correlationFigure(r:TableStatistics,index:number):StatisticalFigure|null{
 const c=r.correlations[index];if(!c)return null;const cols=c.columns.slice(0,12),size=Math.min(48,540/cols.length),height=170+cols.length*size,title=`${c.method} correlation · ${c.rows} complete rows`,marks:StatisticalFigure['marks']=[];
 let svg=start(height,title);
 cols.forEach((a,i)=>{svg+=`<text x="18" y="${151+i*size}" fill="#eaf4ff" font-family="sans-serif" font-size="11">${xml(a.slice(0,22))}</text><text transform="translate(${198+i*size},130) rotate(-50)" fill="#eaf4ff" font-family="sans-serif" font-size="11">${xml(a.slice(0,22))}</text>`;
  cols.forEach((b,j)=>{const v=c.coefficients[i][j],p=c.p_values[i][j],label=`${a} × ${b}`,detail=`${label}: ${number(v)}; unadjusted P-value ${number(p)}; ${c.rows} complete rows`;marks.push({label,value:v,detail});const shade=v===null?'#43515f':v>=0?`rgb(${Math.round(50+130*(1-v))},${Math.round(100+100*v)},210)`:`rgb(210,${Math.round(100+80*(1+v))},${Math.round(70+100*(1+v))})`;
   svg+=`<rect data-mark="${marks.length-1}" tabindex="0" role="button" aria-label="${xml(detail)}" x="${180+j*size}" y="${135+i*size}" width="${size-1}" height="${size-1}" fill="${shade}"><title>${xml(detail)}</title></rect><text pointer-events="none" x="${180+j*size+size/2}" y="${135+i*size+size*.6}" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-size="10">${v===null?'N/A':v.toFixed(2)}</text>`;
  });});
 svg+='</svg>';return {title,svg:stable(svg),marks,caption:`Scale −1 to +1; gray means unavailable. ${cols.length} of ${c.columns.length} fields shown; complete matrices remain in the tables. Association is not causation. ${c.inference}`};
}
export function reportFigures(r:TableStatistics):StatisticalFigure[]{
 const figures=r.descriptive.slice(0,4).map(d=>groupedMeanFigure(r,d.column)).filter((f):f is StatisticalFigure=>f!==null).map(f=>({...f,caption:f.caption+(r.descriptive.length>4?` Grouped report figures cover the first four of ${r.descriptive.length} selected measurements; all fields remain in the numerical tables.`:'')}));
 return [...figures,...r.correlations.map((_,i)=>correlationFigure(r,i)).filter((f):f is StatisticalFigure=>f!==null)];
}
