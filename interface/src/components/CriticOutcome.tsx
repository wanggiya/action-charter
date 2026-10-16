import type { WorkflowRun } from "../lib/workflow-tools";

export function CriticOutcome({run}:{run:WorkflowRun|null}){
  if(!run)return null;
  const review=run.critic_review;
  return <section className="detail-section critic-outcome" aria-label="Critic outcome assessment"><h3>Critic assessment</h3><p>Recorded execution: <strong>{run.status.replaceAll("_"," ")}</strong>. Assessment text does not grant authority.</p>
    {review?.status==="complete"&&review.assessment?<><p>{review.assessment.summary}</p><details><summary>Findings and limitations</summary>{[...review.assessment.findings,...review.assessment.limitations].map((item,i)=><p key={i}>{item}</p>)}</details>{review.assessment.reusable_method&&<details><summary>Reusable method suggestion · unvalidated</summary><strong>{review.assessment.reusable_method.title}</strong><p>{review.assessment.reusable_method.purpose}</p><p>{review.assessment.reusable_method.operations.join(" → ")}</p><small>Ask Planner to make this workflow reusable. Fixture testing and registration remain separate.</small></details>}</>:<p role="status">{["queued","running"].includes(review?.status??"")?"Critic is reviewing recorded evidence. Processing is already finished.":review?.finding??"No model assessment recorded. Execution facts remain available above."}</p>}
  </section>;
}
