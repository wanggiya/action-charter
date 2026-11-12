import {useEffect,useState} from 'react';
import {z} from 'zod';
import type {ResultRecord} from './ResultsWorkspace';
import {StatisticalReport} from './StatisticalReport';
import {downloadBlob} from '../lib/report-document';
const schema=z.object({schema_version:z.literal('workflow-handoff-v1'),run_id:z.string(),plan_sha256:z.string().nullable(),
 analytical_markdown:z.string().max(300000),technical_markdown:z.string().max(300000),status:z.string(),
 execution_performed:z.literal(false),authority_granted:z.literal(false)});
export function WorkflowHandoff({record,technicalOnly=false}:{record:ResultRecord;technicalOnly?:boolean}){
 const [report,setReport]=useState<z.infer<typeof schema>|null>(null),[error,setError]=useState(''),[section,setSection]=useState(technicalOnly?'Technical':'Analytical'),[format,setFormat]=useState('md'),[busy,setBusy]=useState(false);
 useEffect(()=>{
  let alive=true;setReport(null);setError('');
  void(async()=>{try{
   const response=await fetch('/api/v1/workflow/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'report',run_id:record.run_id})});
   const text=await response.text();if(text.length>1048576)throw new Error('Handoff exceeds response budget');
   const payload=JSON.parse(text);if(!response.ok)throw new Error(payload.error??'Handoff unavailable');
   const result=schema.parse(payload.handoff);
   if(result.run_id!==record.run_id||result.plan_sha256!==record.plan_sha256)throw new Error('Handoff scope mismatch');
   if(alive)setReport(result);
  }catch(e){if(alive)setError(e instanceof Error?e.message:'Handoff unavailable');}})();
  return()=>{alive=false;};
 },[record.run_id,record.plan_sha256,record.status]);
 const markdown=report?(section==='Technical'?report.technical_markdown:report.analytical_markdown):'';
 const download=async()=>{setBusy(true);try{
  const blob=format==='md'?new Blob([markdown],{type:'text/markdown;charset=utf-8'}):await(await import('../lib/report-pdf')).reportPdf(markdown);
  downloadBlob(blob,`workflow-${section.toLowerCase()}.${format}`);
 }catch(e){setError(e instanceof Error?e.message:'Export unavailable');}finally{setBusy(false);}};
 return <section className="statistics-panel" aria-label="Workflow handoff">
  <h3>Workflow reports</h3><p>Recorded run evidence only. Opening or downloading this report does not rerun the workflow.</p>
  {error&&<p role="alert">{error}</p>}
  {!technicalOnly&&<nav className="results-tabs" role="tablist" aria-label="Workflow report pages">{['Analytical','Technical'].map(name=><button type="button" role="tab" aria-selected={section===name} key={name} onClick={()=>setSection(name)}>{name}</button>)}</nav>}
  {report?<><div className="statistics-export"><label>Format<select aria-label="Workflow report format" value={format} onChange={e=>setFormat(e.target.value)}><option value="md">Markdown (.md)</option><option value="pdf">PDF (.pdf)</option></select></label><button disabled={busy} onClick={()=>void download()}>Download workflow report</button></div><StatisticalReport markdown={markdown}/></>:!error&&<p role="status">Preparing recorded handoff…</p>}
 </section>;
}
