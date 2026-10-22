import {useState} from 'react';

type Row=Record<string,unknown>;
export type TableViewState={query:string;sort:{column:string;descending:boolean}|null;page:number;hidden:string[]};
export const emptyTableView=():TableViewState=>({query:'',sort:null,page:0,hidden:[]});
export function ResultTable({data,selectedRow,onSelectRow,state,onState,rowIds,serverPage=false}:{data:Row;selectedRow:number|null;onSelectRow:(index:number)=>void;state?:TableViewState;onState?:(state:TableViewState)=>void;rowIds?:number[];serverPage?:boolean}) {
  const columns=(Array.isArray(data.columns)?data.columns:[]).filter((v):v is string=>typeof v==='string').slice(0,32);
  const rows=(Array.isArray(data.preview)?data.preview:[]).slice(0,1000).flatMap((row,index)=>row&&typeof row==='object'&&!Array.isArray(row)?[{row:row as Row,index:rowIds?.[index]??index}]:[]);
  const [local,setLocal]=useState<TableViewState>(emptyTableView);
  const {query,sort,page,hidden}=state??local;
  const update=(patch:Partial<TableViewState>)=>{const next={...(state??local),...patch};if(onState)onState(next);else setLocal(next);};
  const visible=columns.filter(c=>!hidden.includes(c));
  const ordered=[...rows];
  if(sort)ordered.sort((a,b)=>String(a.row[sort.column]??'').localeCompare(String(b.row[sort.column]??''),undefined,{numeric:true})*(sort.descending?-1:1)||a.index-b.index);
  const filtered=ordered.filter(({row})=>!query||visible.some(c=>String(row[c]??'').toLocaleLowerCase().includes(query.toLocaleLowerCase())));
  const pages=Math.max(1,Math.ceil(filtered.length/25)),current=Math.min(page,pages-1);
  return <div className="result-data-table">
    <div className="result-table-controls"><label>Search loaded rows<input aria-label="Search result rows" value={query} maxLength={160} onChange={e=>{update({query:e.target.value,page:0});}} placeholder="Search this preview…"/></label>
    <details><summary>Columns · {visible.length}/{columns.length}</summary><div className="result-column-list">{columns.map(c=><label key={c}><input type="checkbox" checked={!hidden.includes(c)} onChange={()=>update({hidden:hidden.includes(c)?hidden.filter(v=>v!==c):[...hidden,c]})}/>{c}</label>)}</div></details></div>
    <p>{rows.length} loaded / {String(data.row_count??rows.length)} recorded rows · {filtered.length} matching loaded rows. Search and sorting affect this preview only.</p>
    <div className="result-table-scroll" role="region" aria-label="Result data table" tabIndex={0}><table><thead><tr><th scope="col">Row</th>{visible.map(c=><th key={c} scope="col" aria-sort={sort?.column===c?(sort.descending?'descending':'ascending'):'none'}><button onClick={()=>update({sort:{column:c,descending:sort?.column===c?!sort.descending:false}})}>{c}{sort?.column===c?(sort.descending?' ↓':' ↑'):''}</button></th>)}</tr></thead><tbody>{filtered.slice(serverPage?0:current*25,serverPage?100:current*25+25).map(({row,index})=><tr key={index} aria-selected={selectedRow===index} className={selectedRow===index?'selected':''}><th scope="row"><button aria-label={`Select result row ${index+1}`} onClick={()=>onSelectRow(index)}>{index+1}</button></th>{visible.map(c=><td key={c} title={row[c]==null?'Missing':String(row[c])}>{row[c]==null?<span aria-label="Missing value">—</span>:String(row[c])}</td>)}</tr>)}</tbody></table></div>
    {!filtered.length&&<p>No matching loaded rows.</p>}
    {!serverPage&&<div className="result-pagination"><button disabled={current===0} onClick={()=>update({page:current-1})}>Previous page</button><span>Page {current+1} / {pages}</span><button disabled={current+1>=pages} onClick={()=>update({page:current+1})}>Next page</button><button disabled={selectedRow===null} onClick={()=>{const index=filtered.findIndex(item=>item.index===selectedRow);if(index>=0)update({page:Math.floor(index/25)});else{const original=ordered.findIndex(item=>item.index===selectedRow);if(original>=0)update({query:'',page:Math.floor(original/25)});}}}>Show selected row</button></div>}
    <small>At most 32 displayed columns and {serverPage?'100 rows in a verified page':'25 rows per preview page'}. Preview cell text may be shortened to 160 characters. Missing cells are shown as —. Sorting does not change data or workflow order.</small>
  </div>;
}
