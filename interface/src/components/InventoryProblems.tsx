import type {InventoryProblem} from '../lib/interface-api';

export function InventoryProblems({label,items=[],count=items.length,truncated=false}:{
 label:string;items?:InventoryProblem[];count?:number;truncated?:boolean;
}){
 if(!count)return null;
 return <details className="inventory-problems" open aria-label={`${label} unavailable records`}>
  <summary>{label} · Unavailable records · {count}</summary>
  <p>These saved records could not be validated. Valid records remain available. Original files are preserved.</p>
  {items.map((item,index)=><article className="execution-attempt" key={`${item.kind}-${item.filename}-${index}`}>
   <strong>{item.filename}</strong><small>{item.kind.replaceAll('_',' ')}</small>
   <p>{item.reason}</p><span>Blocked · approval and execution unavailable</span>
  </article>)}
  {truncated&&<p>Only the first {items.length} findings are shown. No omitted record is approved or executable.</p>}
 </details>;
}
