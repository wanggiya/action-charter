import {reportDocument} from '../lib/report-document';
export function StatisticalReport({markdown}:{markdown:string}){
 return <article className="statistical-report" aria-label="Statistical report document">{reportDocument(markdown).map((block,i)=>{
  if(block.kind==='heading')return block.level===1?<h3 key={i}>{block.text}</h3>:block.level===2?<h4 key={i}>{block.text}</h4>:<h5 key={i}>{block.text}</h5>;
  if(block.kind==='paragraph')return <p key={i}>{block.text}</p>;
  if(block.kind==='list')return <ul key={i}>{block.items.map((text,j)=><li key={j}>{text}</li>)}</ul>;
  return <div className="result-table-scroll" key={i}><table><thead><tr>{block.headers.map((text,j)=><th key={j}>{text}</th>)}</tr></thead><tbody>{block.rows.map((row,j)=><tr key={j}>{row.map((text,k)=>k===0?<th scope="row" key={k}>{text}</th>:<td key={k}>{text}</td>)}</tr>)}</tbody></table></div>;
 })}</article>;
}
