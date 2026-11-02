import {useId,useState} from 'react';
import {Download} from 'lucide-react';
import type {TableStatistics} from '../lib/table-statistics';
import {downloadBlob} from '../lib/report-document';
import {StatisticalFigure} from './StatisticalFigure';
import {groupedMeanFigure,correlationFigure,reportFigures} from '../lib/statistical-figures';
import {StatisticalReport} from './StatisticalReport';
const show=(v:unknown)=>v===null?'Unavailable':typeof v==='number'?Number(v.toPrecision(8)).toString():String(v);
const label=(v:string)=>v.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
function Facts({values}:{values:Record<string,unknown>}){
 return <dl className="statistics-facts">{Object.entries(values).map(([name,value])=><div key={name}><dt>{label(name)}</dt><dd>{show(value)}</dd></div>)}</dl>;
}
function Matrix({title,columns,values}:{title:string;columns:string[];values:(number|null)[][]}){
 return <div className="result-table-scroll"><table><caption>{title}</caption><thead><tr><th>Field</th>{columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{values.map((row,i)=><tr key={i}><th scope="row">{columns[i]}</th>{row.map((v,j)=><td key={j}>{show(v)}</td>)}</tr>)}</tbody></table></div>;
}
function Descriptive({rows}:{rows:TableStatistics['descriptive']}){
 return <div className="result-table-scroll"><table><thead><tr>{['Field','Count','Mean','Minimum','Maximum','Variance','Standard deviation','Percentiles'].map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map(d=><tr key={d.column}><th scope="row">{d.column}</th>{[d.count,d.mean,d.minimum,d.maximum,d.variance,d.standard_deviation].map((v,i)=><td key={i}>{show(v)}</td>)}<td>{Object.entries(d.percentiles).map(([p,v])=>`${p}%: ${show(v)}`).join(' · ')}</td></tr>)}</tbody></table></div>;
}
export function StatisticsPanel({result:r}:{result:TableStatistics}){
 const id=useId(),[chosen,setChosen]=useState('Summary'),[format,setFormat]=useState('md'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState(''),[figureField,setFigureField]=useState('');
 const selectedField=r.descriptive.some(d=>d.column===figureField)?figureField:r.descriptive[0]?.column;
 const meanFigure=selectedField?groupedMeanFigure(r,selectedField):null;
 const sections=['Summary',...(r.descriptive.length?['Descriptive']:[]),...(r.correlations.length||r.covariance_matrix?['Matrices']:[]),...(r.regression?['Regression']:[]),'Report'];
 const section=sections.includes(chosen)?chosen:'Summary';
 const download=async()=>{
  setBusy(true);setError('');setStatus('');
  try{
   const blob=format==='md'?new Blob([r.report_markdown],{type:'text/markdown;charset=utf-8'}):await (await import('../lib/report-pdf')).reportPdf(r.report_markdown,reportFigures(r));
   downloadBlob(blob,`statistical-analysis.${format}`);setStatus(`${format==='md'?'Markdown':'PDF'} download prepared.`);
  }catch(e){setError(e instanceof Error?e.message:'Report download could not be prepared.');}finally{setBusy(false);}
 };
 return <section className="statistics-panel" aria-label="Statistical analysis">
  <div className="statistics-page-header"><div><p className="statistics-eyebrow">Recorded statistical analysis</p><h3>Statistical results</h3><p>{r.methods.map(name=>name==='describe'?'Descriptive statistics':name==='covariance'?'Covariance matrix':label(name)).join(' · ')}</p><p>{r.analysis_rows.toLocaleString()} analyzed / {r.matching_rows.toLocaleString()} matching records · {r.excluded_rows.toLocaleString()} excluded</p></div>
   <div className="statistics-export"><label>Report format<select aria-label="Statistical report format" value={format} disabled={busy} onChange={e=>{setFormat(e.target.value);setStatus('');}}><option value="md">Markdown (.md)</option><option value="pdf">PDF (.pdf)</option></select></label><button type="button" disabled={busy} onClick={()=>void download()} aria-label="Download statistical report"><Download size={16}/>{busy?'Preparing PDF…':'Download report'}</button>{status&&<small className="statistics-download-status" role="status">{status}</small>}</div>
  </div>
  {error&&<p role="alert">{error}</p>}
  <nav className="results-tabs statistics-page-tabs" role="tablist" aria-label="Statistical pages" onKeyDown={e=>{
   const index=sections.indexOf(section),next=e.key==='ArrowRight'?(index+1)%sections.length:e.key==='ArrowLeft'?(index+sections.length-1)%sections.length:e.key==='Home'?0:e.key==='End'?sections.length-1:null;
   if(next===null)return;e.preventDefault();setChosen(sections[next]);e.currentTarget.querySelectorAll<HTMLButtonElement>('[role=tab]')[next]?.focus();
  }}>{sections.map(name=><button type="button" key={name} role="tab" id={`${id}-${name}`} aria-controls={`${id}-page`} aria-selected={section===name} tabIndex={section===name?0:-1} onClick={()=>setChosen(name)}>{name}</button>)}</nav>
  <div className="statistics-page" role="tabpanel" id={`${id}-page`} aria-labelledby={`${id}-${section}`} tabIndex={0}>
   {section==='Summary'&&<><h4>Analysis summary</h4>{r.specification?.question&&<p><strong>Analysis question:</strong> {r.specification.question}</p>}<p>Calculated from the whole matching source, not preview rows. Missing policy: {r.missing_policy}.</p><Facts values={{'Variance / SD / covariance denominator':`n − ${r.ddof}`,'Percentile method':r.quantile_method,...(r.source?{Source:r.source.path,'Source SHA-256':r.source.sha256}:{})}}/>
    <details><summary>Missing and invalid values</summary><div className="result-table-scroll"><table><thead><tr><th>Field</th><th>Missing</th><th>Invalid</th></tr></thead><tbody>{Object.keys(r.missing_counts).map(c=><tr key={c}><th scope="row">{c}</th><td>{r.missing_counts[c]}</td><td>{r.invalid_counts[c]}</td></tr>)}</tbody></table></div></details>
    <details><summary>Methods and limitations</summary><ul>{r.limitations.map(v=><li key={v}>{v}</li>)}</ul><Facts values={r.runtime_versions}/></details></>}
   {section==='Descriptive'&&<><h4>Descriptive statistics</h4><p>The selected complete-case population is shared by these methods. No values are imputed. Variance and standard deviation use n − {r.ddof}.</p>{meanFigure&&<><label>Chart measurement<select aria-label="Statistical chart measurement" value={selectedField} onChange={e=>setFigureField(e.target.value)}>{r.descriptive.map(d=><option key={d.column} value={d.column}>{d.column}</option>)}</select></label><StatisticalFigure figure={meanFigure}/></>}<Descriptive rows={r.descriptive}/>{r.grouped_descriptive.map((g,i)=><details key={i}><summary>{Object.entries(g.group).map(([k,v])=>`${k}: ${v||'(empty cell)'}`).join(' · ')} · {g.analysis_rows} analyzed / {g.matching_rows} matching</summary><Descriptive rows={g.descriptive}/></details>)}</>}
   {section==='Matrices'&&<><h4>Statistical matrices</h4>{r.correlations.map(c=><section key={c.method}><h5>{label(c.method)} correlation · {c.rows.toLocaleString()} rows</h5><p>{c.inference}</p>{correlationFigure(r,r.correlations.indexOf(c))&&<StatisticalFigure figure={correlationFigure(r,r.correlations.indexOf(c))!}/>}<Matrix title={`${c.method} · Coefficient`} columns={c.columns} values={c.coefficients}/><Matrix title={`${c.method} · Unadjusted P-value`} columns={c.columns} values={c.p_values}/></section>)}{r.covariance_matrix&&<section><h5>Covariance · {r.covariance_matrix.rows.toLocaleString()} rows</h5><p>Denominator: n − {r.covariance_matrix.ddof}. Values retain the products of the original variable units; they are not standardized correlations.</p><Matrix title="Covariance matrix" columns={r.covariance_matrix.columns} values={r.covariance_matrix.values}/></section>}</>}
   {section==='Regression'&&r.regression&&<><h4>Linear regression · {r.regression.outcome}</h4><p>Predictors: {r.regression.predictors.join(', ')}. {r.regression.intercept?'An intercept is included.':'No intercept is included.'}</p><Facts values={{Rows:r.regression.rows,Covariance:r.regression.covariance,Clusters:r.regression.clusters,'R-squared':r.regression.r_squared,'Adjusted R-squared':r.regression.adjusted_r_squared,'R-squared type':r.regression.r_squared_kind,'Confidence level':r.regression.confidence_level,'Residual standard error':r.regression.residual_standard_error,'Inference status':r.regression.inference_status.replaceAll('_',' ')}}/>
    <div className="result-table-scroll"><table><caption>OLS coefficients and conditional inference</caption><thead><tr>{['Term','Coefficient','Standard error','t statistic','P-value','Confidence lower','Confidence upper'].map(v=><th key={v}>{v}</th>)}</tr></thead><tbody>{r.regression.coefficients.map((c,i)=><tr key={i}><th scope="row">{c.term}</th>{[c.coefficient,c.standard_error,c.t_statistic,c.p_value,c.confidence_lower,c.confidence_upper].map((v,j)=><td key={j}>{show(v)}</td>)}</tr>)}</tbody></table></div>
    <p>In-sample associations conditional on the declared model and covariance assumptions. Neither statistical significance nor R-squared establishes causality.</p><details><summary>Regression diagnostics</summary><Facts values={{'Residual degrees of freedom':r.regression.degrees_of_freedom_residual,'Inference degrees of freedom':r.regression.degrees_of_freedom_inference,'Condition number':r.regression.condition_number,...r.regression.diagnostics}}/></details></>}
   {section==='Report'&&<><StatisticalReport markdown={r.report_markdown}/>{reportFigures(r).map(f=><StatisticalFigure key={f.title} figure={f}/>)}{r.grouped_descriptive.length>0&&r.descriptive.length>4&&<p>Report figures show the first four selected measurement fields. Complete results remain in the report tables.</p>}</>}
  </div>
 </section>;
}
