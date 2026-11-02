import {useState} from 'react';
import {z} from 'zod';
import {Download} from 'lucide-react';
import {StatisticalReport} from './StatisticalReport';
import {downloadBlob} from '../lib/report-document';
import type {TableStatistics} from '../lib/table-statistics';
import {reportFigures} from '../lib/statistical-figures';
import {StatisticalFigure} from './StatisticalFigure';

const schema=z.object({schema_version:z.literal('readiness-assessment-v1'),source:z.string(),source_sha256:z.string(),
 source_rows:z.number(),matching_rows:z.number(),omissions:z.record(z.number().int().nonnegative()).optional(),report_markdown:z.string().max(48000),execution_authority:z.literal(false),data_written:z.literal(false)});

export function ReadinessReport({value,source,sha256,statistics}:{value:unknown;source:string;sha256:string;statistics?:TableStatistics}){
 const [format,setFormat]=useState('md'),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('');
 const parsed=schema.safeParse(value);
 if(!parsed.success||parsed.data.source!==source||parsed.data.source_sha256!==sha256)return <p>No matching readiness report is recorded. A new analytical inspection can produce one; opening this page does not rerun the workflow.</p>;
 const report=parsed.data;
 const omissions=Object.entries(report.omissions??{}).filter(([,count])=>count>0);
 const figures=statistics?.source?.path===source&&statistics?.source?.sha256===sha256?reportFigures(statistics):[];
 const download=async()=>{
  setBusy(true);setMessage('');setError('');
  try{
   const blob=format==='md'?new Blob([report.report_markdown],{type:'text/markdown;charset=utf-8'}):await(await import('../lib/report-pdf')).reportPdf(report.report_markdown,figures);
   downloadBlob(blob,`data-readiness.${format}`);setMessage('Report download prepared.');
  }catch(e){setError(e instanceof Error?e.message:'Report export unavailable');}finally{setBusy(false);}
 };
 return <section className="statistics-panel" aria-label="Data readiness report">
  <div className="statistics-page-header"><div><p className="statistics-eyebrow">Recorded source evidence</p><h3>Data readiness and findings</h3><p>{report.matching_rows.toLocaleString()} matching / {report.source_rows.toLocaleString()} source records</p></div>
   <div className="statistics-export"><label>Report format<select aria-label="Readiness report format" value={format} disabled={busy} onChange={e=>setFormat(e.target.value)}><option value="md">Markdown (.md)</option><option value="pdf">PDF (.pdf)</option></select></label><button type="button" disabled={busy} onClick={()=>void download()}><Download size={16}/>{busy?'Preparing…':'Download readiness report'}</button></div>
  </div>
  {message&&<small className="statistics-download-status" role="status">{message}</small>}{error&&<p role="alert">{error}</p>}
  {omissions.length>0&&<p className="results-notice" role="status">Report display limits: {omissions.map(([name,count])=>`${count} ${name==='statistical_report'?'statistical method appendix':name}`).join(' · ')} omitted. Original results remain available in Columns, Groups and Statistics; calculations were not sampled.</p>}
  <StatisticalReport markdown={report.report_markdown.replace(/^# [^\n]+\n/,'')}/>
  {figures.map(f=><StatisticalFigure key={f.title} figure={f}/>)}
  {figures.length>0&&<p>Figures project recorded statistics; complete available numerical tables and method limits remain in Statistics. Report figures retain their existing field/display caps.</p>}
 </section>;
}
