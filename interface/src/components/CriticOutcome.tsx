import type { WorkflowRun } from "../lib/workflow-tools";
import {criticState} from '../lib/critic-graph';

export function CriticOutcome({run}:{run:WorkflowRun|null}){
 if(!run)return null;
 const review=run.critic_review,state=criticState(run);
 return <section className="detail-section critic-outcome" aria-label="Critic outcome assessment">
   <h3>Critic review · advisory</h3><p className="critic-review-state" role="status">{state.label}</p>
   <p>Recorded execution: <strong>{run.status.replaceAll('_',' ')}</strong>. Independent validation is reported with each operation.</p>
   <p className="critic-run-identity">Run <code>{run.run_id}</code> · {new Date(run.started_at).toLocaleString()}</p>
   <small>Model interpretation of recorded observations. It does not change execution status, certify current targets or grant authorization.</small>
   {state.label==='Reviewed'&&review?.assessment?<><p className="critic-summary">{review.assessment.summary}</p>
    <details><summary>Findings · {review.assessment.findings.length}</summary>{review.assessment.findings.length?review.assessment.findings.map((item,i)=><p key={i}>{item}</p>):<p>No additional findings reported.</p>}</details>
    <details><summary>Limitations · {review.assessment.limitations.length}</summary>{review.assessment.limitations.map((item,i)=><p key={i}>{item}</p>)}</details>
    {review.assessment.reusable_method&&<details><summary>Procedure suggestion · unvalidated</summary><strong>{review.assessment.reusable_method.title}</strong><p>{review.assessment.reusable_method.purpose}</p><p>{review.assessment.reusable_method.operations.join(' → ')}</p>{review.assessment.reusable_method.limitations.map((item,i)=><p key={i}>{item}</p>)}<small>Advisory only. Successful-workflow retention and tested capability promotion have separate requirements.</small></details>}
   </>:<p>{state.label==='Reviewing'?'Critic is reviewing recorded evidence. Execution has already finished.':state.label==='Waiting'?'Assessment requested; waiting for recorded execution evidence.':review?.finding??'No model assessment recorded. Execution facts remain available.'}</p>}
   {review?.annotation_status==='unavailable'&&<p role="status">The assessment is preserved, but its recipe note could not be indexed. Baseline recipes and execution results are unaffected.</p>}
   <details className="critic-provenance"><summary>Assessment provenance</summary><dl><div><dt>Run ID</dt><dd>{run.run_id}</dd></div><div><dt>Plan digest</dt><dd>{run.plan_sha256}</dd></div><div><dt>Model</dt><dd>{review?.model??'Not recorded'}</dd></div><div><dt>Evidence digest</dt><dd>{review?.source_sha256??'Not recorded'}</dd></div></dl><small>Opening or refreshing this view does not request another assessment or execute operations.</small></details>
 </section>;
}
