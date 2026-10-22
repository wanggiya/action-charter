import {useEffect,useRef,useState} from 'react';
import {z} from 'zod';
import {runs,runSchema,type WorkflowRun} from '../lib/workflow-tools';
import {skillLabel} from '../lib/skill-labels';

export function ExecutionRunHistory({onOutcome,onManage}:{onOutcome:(run:WorkflowRun)=>void;onManage:()=>void}) {
  const [records,setRecords]=useState<WorkflowRun[]>([]);
  const [notice,setNotice]=useState('Loading saved workflow runs…');
  const [busy,setBusy]=useState<string|null>(null);
  const alive=useRef(true);
  useEffect(()=>{alive.current=true;void runs({action:'list'}).then(value=>{
    if(!alive.current)return;
    setRecords(z.object({records:z.array(runSchema).max(200)}).parse(value).records);
    setNotice('');
  }).catch(()=>{if(alive.current)setNotice('Saved workflow runs could not be loaded. Reopen Execution History to retry.');});return()=>{alive.current=false;};},[]);
  const open=async(id:string)=>{
    setBusy(id);
    try {
      const record=runSchema.parse(await runs({action:'read',run_id:id}));
      if(alive.current)onOutcome(record);
    } catch {if(alive.current)setNotice('This saved outcome is unavailable. Nothing was executed.');}
    finally {if(alive.current)setBusy(null);}
  };
  return <section className="saved-workflow-runs" aria-label="Saved workflow runs">
    <div className="history-run-heading"><h3>Saved workflow runs</h3><button type="button" className="context-intent-toggle" onClick={onManage}>Workflow runs · cancellation and recovery</button></div>
    <p>Inspections sent from chat and workflows started with Execute. Opening an outcome reads its saved record.</p>
    {notice&&<p role="status">{notice}</p>}
    {!notice&&!records.length&&<p>No saved workflow runs yet.</p>}
    {records.map(run=>{
      const sources=run.source_paths??[...new Set(run.steps.map(step=>step.arguments.path).filter((path):path is string=>typeof path==='string'))];
      return <article className="execution-attempt" key={run.run_id} data-history-run={run.run_id}>
        <header><strong>{sources.map(path=>path.split('/').pop()).join(', ')||'Workflow run'}</strong><span>{run.status.replaceAll('_',' ')}</span></header>
        <p>{[...new Set(run.steps.map(step=>skillLabel(step.skill_id)))].join(' → ')}</p>
        <small>{new Date(run.started_at).toLocaleString()} · Run {run.run_id.slice(0,12)}</small>
        <details><summary>Source and run identity</summary>{sources.map(path=><p key={path}>{path}</p>)}<code>{run.run_id}</code></details>
        <button type="button" className="context-intent-toggle" disabled={busy!==null} onClick={()=>void open(run.run_id)}>{busy===run.run_id?'Opening…':'View outcome'}</button>
      </article>;
    })}
  </section>;
}
