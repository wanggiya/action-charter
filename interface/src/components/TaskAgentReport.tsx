import type {WorkflowRun} from '../lib/workflow-tools';
export function TaskAgentReport({run}:{run:WorkflowRun|null}){
 if(!run?.agent_mode)return null;
 const r=run.agent_report,c=run.agent_coordination;
 const download=(json=false)=>{if(!r)return;const blob=new Blob([json?JSON.stringify(r,null,2):r.text??JSON.stringify(r,null,2)],{type:json?'application/json':'text/plain'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`task-report-${run.run_id}.${json?"json":"txt"}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 return <details className="task-agent-report"><summary>Task report · {run.agent_mode==='single'?'Single agent · self-review':'Planner / Executor / Critic'}</summary>
  {!r?<p>Execution facts are recorded. Model review/report may still be pending or unavailable; reopening does not rerun operations.</p>:<>
   <p>{r.assessment.assessment?.summary??r.assessment.finding}</p><p>Recorded execution: {r.evidence.status}. {r.review_kind==='self_review'?'Self-review is not an independent Critic assessment.':'Critic uses a separate context and the recorded evidence.'}</p>
   <dl className="result-facts"><div><dt>Model calls · planning / outcome</dt><dd>{r.planning_metrics?.model_calls??'Unknown'} / {r.metrics.model_calls}</dd></div><div><dt>Operation attempts</dt><dd>{r.tool_calls}</dd></div><div><dt>Tokens · planning / outcome</dt><dd>{r.planning_metrics?.token_usage_complete?`${r.planning_metrics.prompt_tokens} + ${r.planning_metrics.completion_tokens}`:'Not fully reported'} / {r.metrics.token_usage_complete?`${r.metrics.prompt_tokens} + ${r.metrics.completion_tokens}`:'Not fully reported'}</dd></div><div><dt>Model elapsed · planning / outcome</dt><dd>{r.planning_metrics?.elapsed_seconds??'?'}s / {r.metrics.elapsed_seconds}s</dd></div></dl>
   {r.evidence.steps.map(s=><details key={s.step_id}><summary>{s.step_id} · {s.skill} · {s.status}</summary><pre>{JSON.stringify({facts:s.facts,validation:s.validation},null,2)}</pre></details>)}
   {r.assessment.assessment?.findings.map((f,i)=><p key={i}>{f}</p>)}{[...(r.assessment.assessment?.limitations??[]),...r.limitations].map((f,i)=><small key={i}>{f}</small>)}
   <button type="button" onClick={()=>download()}>Download recorded report</button><button type="button" onClick={()=>download(true)}>Download evidence JSON</button>
  </>}{c&&<small>Mode is frozen for this run. Contexts and reports grant no execution authority.</small>}
 </details>;
}
