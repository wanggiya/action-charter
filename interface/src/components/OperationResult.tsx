import {useState} from 'react';
import {CheckCircle2, XCircle, CircleHelp} from 'lucide-react';
import {skillLabel} from '../lib/skill-labels';
import type {WorkflowRun} from '../lib/workflow-tools';
import {CalculationSummary} from './CalculationEditor';
import {OperationFlow} from './OperationFlow';
import {TablePreview} from './TablePreview';
import {RecordedVisualization} from './RecordedVisualization';

type Planned={step_id:string;skill:string;purpose:string;arguments:Record<string,unknown>};
const object=(value:unknown):Record<string,unknown>=>value&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,unknown>:{};
const labels:Record<string,string>={calculation_values:'Calculated values verified',output_sha256:'Output file matches recorded digest',source_identity:'Source matches recorded input',row_count:'Row count matches recorded result',columns:'Output columns match recorded result'};

export function ReadableValidation({value}:{value:unknown}) {
  const result=object(value),checks=object(result.checks);
  return <div className="readable-validation"><h4>{result.passed===true?'Validation passed':result.passed===false?'Validation failed':'No separate validation recorded'}</h4>
    {Object.entries(checks).map(([name,passed])=><div className={`validation-check ${passed===true?'passed':passed===false?'failed':'unknown'}`} key={name}>
      {passed===true?<CheckCircle2 size={15}/>:passed===false?<XCircle size={15}/>:<CircleHelp size={15}/>}
      <span>{labels[name]??name.replaceAll('_',' ')}</span><strong>{passed===true?'Passed':passed===false?'Failed':'Not reported'}</strong>
    </div>)}
    {typeof result.reason==='string'&&<p>{result.reason}</p>}
  </div>;
}
function calculationColumns(args:Record<string,unknown>) {
  const names=new Set<string>();
  let remaining=100;
  const visit=(value:unknown)=>{if(--remaining<0)return;const node=object(value);if(node.kind==='column'&&typeof node.name==='string')names.add(node.name);for(const key of ['left','right','condition','then','otherwise'])if(node[key])visit(node[key]);};
  const rows=Array.isArray(args.calculations)?args.calculations:[];
  rows.forEach(row=>visit(object(row).expression));
  rows.forEach(row=>{const name=object(row).output_column;if(typeof name==='string')names.add(name);});
  return [...names];
}
export function OperationResult({planned,run,stepId,notice}:{planned?:Planned;run?:WorkflowRun|null;stepId:string;notice?:string}) {
  const [allColumns,setAllColumns]=useState(false);
  const step=run?.steps.find(item=>item.step_id===stepId&&(!planned||item.skill_id===planned.skill));
  const skill=step?.skill_id??planned?.skill??'operation';
  const args=step?.arguments??planned?.arguments??{};
  const outcome=object(step?.outcome);
  const recorded=Boolean(step);
  const finished=step&&['completed','validated_success','reused_completed'].includes(step.status);
  const focus=skill==='calculate_csv_columns'?calculationColumns(args):[];
  const preview=Array.isArray(outcome.preview)&&Array.isArray(outcome.columns);
  return <section className="detail-section operation-result" aria-label={`Operation result: ${skillLabel(skill)}`}>
    <header><h3>{recorded?'Recorded operation':'Proposed operation'}</h3><strong className={`result-state state-${step?.status??'proposed'}`}>{recorded?step!.status.replaceAll('_',' '):'Not executed · no matching recorded result'}</strong></header>
    {planned?.purpose&&<p className="result-purpose">{planned.purpose}</p>}
    {run&&step&&<p className="recorded-run-label">Run {run.run_id.slice(0,12)} · {run.status.replaceAll('_',' ')} · {new Date(run.started_at).toLocaleString()}{run.finished_at&&<> · finished {new Date(run.finished_at).toLocaleString()}</>}</p>}
    {!recorded&&notice&&<p className="result-notice">{notice}</p>}
    {recorded&&!finished&&<p className="result-notice">{step?.status==='queued'?'This step has not started.':step?.status==='running'?'This step is running; results are not final.':'This step did not complete successfully. Any recorded values may be partial; inspect before recovery.'}</p>}
    {skill==='calculate_csv_columns'&&<CalculationSummary arguments={args}/>}
    <OperationFlow compact stepId={stepId} skill={skill} arguments={args} outcome={step?.outcome} dependsOn={step?.depends_on}/>
    {recorded&&<dl className="result-facts">{['row_count','feature_count','crs'].flatMap(key=>outcome[key]!==undefined&&typeof outcome[key]!=='object'?[<div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{String(outcome[key])}</dd></div>]:[])}</dl>}
    {preview&&<><h4>Recorded data preview</h4>{focus.length>0&&<button type="button" className="result-column-toggle" aria-pressed={allColumns} onClick={()=>setAllColumns(value=>!value)}>{allColumns?'Show calculation columns':'Show all columns'}</button>}<TablePreview value={outcome} columns={!allColumns&&focus.length?focus:undefined}/><small className="result-notice">Saved preview from this run. Current file contents have not been rechecked.</small></>}
    {recorded&&!preview&&<p className="result-notice">{outcome.preview_omitted?'Result preview exceeded the storage budget; inspect durable evidence.':step?.outcome==null?'No result recorded for this step.':'No table preview recorded for this operation.'}</p>}
    {finished&&run&&<RecordedVisualization key={`${run.run_id}:${stepId}`} outcome={step?.outcome} runId={run.run_id} stepId={stepId}/>}
    {recorded&&<ReadableValidation value={step?.validation_outcome}/>}
    {run?.finding&&<p className="result-notice" role="status">{run.finding}</p>}
    <details className="inspector-raw-arguments"><summary>Technical details</summary><p>Recorded evidence is not a recheck of current files or fresh execution authority.</p>{run&&<dl><div><dt>Run ID</dt><dd>{run.run_id}</dd></div><div><dt>Plan digest</dt><dd>{run.plan_sha256}</dd></div></dl>}<h4>{recorded?'Recorded':'Proposed'} arguments</h4><pre>{JSON.stringify(args,null,2)}</pre>{recorded&&<><h4>Recorded outcome</h4><pre>{JSON.stringify(step?.outcome,null,2)}</pre><h4>Validation details</h4><pre>{JSON.stringify(step?.validation_outcome,null,2)}</pre></>}</details>
  </section>;
}
