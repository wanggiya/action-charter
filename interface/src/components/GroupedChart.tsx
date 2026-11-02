import {useState} from 'react';
import {ChartPlot} from './ChartPlot';
import {GroupedChart3D} from './GroupedChart3D';

type Group=Record<string,string|number|null>;
export function GroupedChart({fields,groups,matchingRows,basis:controlledBasis,controlPrefix='Outcome',initialMeasure='percentage'}:{fields:string[];groups:Group[];matchingRows:number;basis?:'total'|'primary';controlPrefix?:string;initialMeasure?:'count'|'percentage'}){
 const [kind,setKind]=useState('bar'),[measure,setMeasure]=useState(initialMeasure),[localBasis,setBasis]=useState<'total'|'primary'>('total');
 const [size,setSize]=useState('comfortable');
 const basis=controlledBasis??localBasis,within=basis==='primary'&&fields.length>1;
 const totals=new Map<unknown,number>();
 for(const g of groups)totals.set(g[fields[0]],(totals.get(g[fields[0]])??0)+Number(g.row_count));
 const denominator=within?`Within each ${fields[0]} group`:'All matching rows';
 const values=groups.map((g,index)=>{const rows=Number(g.row_count),d=within?totals.get(g[fields[0]])??0:matchingRows;return {label:fields.map(k=>g[k]===null?'(missing)':g[k]===''?'(empty cell)':String(g[k])).join(' · '),value:measure==='count'?rows:d?100*rows/d:0,x:index,index,members:[],facts:[['Rows',rows],['Percentage',d?`${(100*rows/d).toFixed(2)}%`:'N/A'],['Denominator',d]] as [string,string|number][]};});
 return <section className="grouped-chart" data-chart-size={size} aria-label="Grouped result chart">
  <h4>{fields.join(' × ')} · {measure==='count'?'Row count':`Percentage · ${denominator}`}</h4>
  <div className="analytical-controls"><label>Chart<select aria-label={`${controlPrefix} group chart type`} value={kind} onChange={e=>setKind(e.target.value)}>{['bar','column','pie','donut',...(fields.length===2?['3d-column']:[])].map(k=><option key={k} value={k}>{k==='3d-column'?'3D columns':k}</option>)}</select></label><label>Measure<select aria-label={`${controlPrefix} group chart measure`} value={measure} onChange={e=>setMeasure(e.target.value as 'count'|'percentage')}><option value="percentage">Percentage</option><option value="count">Row count</option></select></label>
   <label>Chart size<select aria-label={`${controlPrefix} group chart size`} value={size} onChange={e=>setSize(e.target.value)}><option value="compact">Compact</option><option value="comfortable">Comfortable</option><option value="large">Large</option></select></label>
   {controlledBasis===undefined&&<label>Percentage of<select aria-label={`${controlPrefix} percentage denominator`} value={basis} onChange={e=>setBasis(e.target.value as 'total'|'primary')}><option value="total">All matching rows</option><option value="primary" disabled={fields.length<2}>Within each {fields[0]} group</option></select></label>}
  </div>
  <p>{measure==='count'?'Counts cover all matching records.':`${denominator}; values and the axis are percentages from 0 to 100%.`} Percentages count records, not distinct patients.</p>
  {groups.length>100?<p>{groups.length} complete groups exceed the 100-group chart limit. Use the table; no groups were silently omitted.</p>:!matchingRows?<p>No matching records; percentages are undefined.</p>:(kind==='pie'||kind==='donut')&&within&&measure==='percentage'?<p>Within-group percentages have separate denominators. Choose bar/column or “All matching rows” for a meaningful pie/donut.</p>:kind==='3d-column'?<GroupedChart3D fields={fields} groups={groups} values={values} percent={measure==='percentage'}/>:<ChartPlot kind={kind} x={fields.join(' / ')} y={measure==='count'?'Row count':`Percentage · ${denominator}`} valueFormat={measure==='percentage'?'percent':'number'} values={values}/>}
 </section>;
}
