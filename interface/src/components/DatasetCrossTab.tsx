import {useState} from 'react';
type Group=Record<string,string|number|null>;
const label=(v:unknown)=>v===null?'(missing)':v===''?'(empty cell)':String(v);
export function DatasetCrossTab({fields,groups,matchingRows}:{fields:string[];groups:Group[];matchingRows:number}){
 const [swapped,setSwapped]=useState(false),[measure,setMeasure]=useState('count'),[rowPage,setRowPage]=useState(0),[columnPage,setColumnPage]=useState(0);
 const [rowField,columnField]=swapped?[fields[1],fields[0]]:fields;
 const rowValues=[...new Set(groups.map(g=>g[rowField]))],columnValues=[...new Set(groups.map(g=>g[columnField]))];
 const counts=new Map<unknown,Map<unknown,number>>(),rowTotals=new Map<unknown,number>(),columnTotals=new Map<unknown,number>();
 for(const g of groups){const a=g[rowField],b=g[columnField],n=Number(g.row_count);if(!counts.has(a))counts.set(a,new Map());counts.get(a)!.set(b,(counts.get(a)!.get(b)??0)+n);rowTotals.set(a,(rowTotals.get(a)??0)+n);columnTotals.set(b,(columnTotals.get(b)??0)+n);}
 const total=[...rowTotals.values()].reduce((a,b)=>a+b,0),complete=total===matchingRows;
 const show=(n:number,row:number,column:number)=>{const d=measure==='row'?row:measure==='column'?column:matchingRows;return measure==='count'?n.toLocaleString():d?`${(100*n/d).toFixed(2)}%`:'N/A';};
 const rp=Math.min(rowPage,Math.max(0,Math.ceil(rowValues.length/25)-1)),cp=Math.min(columnPage,Math.max(0,Math.ceil(columnValues.length/12)-1));
 const visibleRows=rowValues.slice(rp*25,rp*25+25),visibleColumns=columnValues.slice(cp*12,cp*12+12);
 return <section className="dataset-cross-tab" aria-label="Two-variable cross-tab">
  <div className="analytical-controls"><label>Cell values<select aria-label="Cross-tab cell values" value={measure} onChange={e=>setMeasure(e.target.value)}><option value="count">Row count</option><option value="row">Row percentage</option><option value="column">Column percentage</option><option value="total">Overall percentage</option></select></label><button type="button" onClick={()=>{setSwapped(v=>!v);setRowPage(0);setColumnPage(0);}}>Swap rows and columns</button></div>
  <p>Rows: <strong>{rowField}</strong> · Columns: <strong>{columnField}</strong>. {measure==='count'?'Cells count records.':measure==='row'?`Each cell ÷ all records in its ${rowField} row.`:measure==='column'?`Each cell ÷ all records in its ${columnField} column.`:'Each cell ÷ all matching records.'} Missing/marker groups are retained. Percentages count records, not distinct patients.</p>
  {!complete&&<p role="alert">Recorded groups do not reconcile with matching rows. Totals below cover only recorded groups.</p>}
  <div className="result-table-scroll" role="region" aria-label="Cross-tab table" tabIndex={0}><table><caption>{rowField} × {columnField} · {measure==='count'?'Row count':measure==='row'?'Row percentage':measure==='column'?'Column percentage':'Overall percentage'}</caption><thead><tr><th scope="col">{rowField} / {columnField}</th>{visibleColumns.map((v,i)=><th scope="col" key={i}>{label(v)}</th>)}<th scope="col">Total</th></tr></thead><tbody>{visibleRows.map((a,i)=><tr key={i}><th scope="row">{label(a)}</th>{visibleColumns.map((b,j)=><td key={j}>{show(counts.get(a)?.get(b)??0,rowTotals.get(a)??0,columnTotals.get(b)??0)}</td>)}<td>{show(rowTotals.get(a)??0,rowTotals.get(a)??0,total)}</td></tr>)}</tbody><tfoot><tr><th scope="row">Total</th>{visibleColumns.map((b,j)=><td key={j}>{show(columnTotals.get(b)??0,total,columnTotals.get(b)??0)}</td>)}<td>{show(total,total,total)}</td></tr></tfoot></table></div>
  <p>{total.toLocaleString()} grouped / {matchingRows.toLocaleString()} matching records. Totals and denominators include all recorded categories, including those outside this page. An unobserved combination is 0; a zero denominator is N/A.</p>
  {rowValues.length>25&&<div className="result-pagination"><button disabled={!rp} onClick={()=>setRowPage(rp-1)}>Previous row categories</button><span>Row categories {rowValues.length?rp*25+1:0}–{Math.min(rp*25+25,rowValues.length)} / {rowValues.length}</span><button disabled={(rp+1)*25>=rowValues.length} onClick={()=>setRowPage(rp+1)}>Next row categories</button></div>}
  {columnValues.length>12&&<div className="result-pagination"><button disabled={!cp} onClick={()=>setColumnPage(cp-1)}>Previous column categories</button><span>Column categories {columnValues.length?cp*12+1:0}–{Math.min(cp*12+12,columnValues.length)} / {columnValues.length}</span><button disabled={(cp+1)*12>=columnValues.length} onClick={()=>setColumnPage(cp+1)}>Next column categories</button></div>}
 </section>;
}
