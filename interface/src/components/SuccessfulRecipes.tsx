import type { SuccessfulMethod } from "../lib/workflow-tools";

/** Details only: browsing rows and keyword navigation belong to the parent. */
export function SuccessfulRecipes({record,onInspect,onDiscuss}:{record:SuccessfulMethod;onInspect:(id:string)=>void;onDiscuss:(message:string,methodId?:string)=>void}) {
  return <section className="detail-section successful-method" aria-label="Successful workflow details">
    <h3>{record.name}</h3>
    <p>Recorded success with the original inputs. Adaptation requires current validation and fresh authority for writes.</p>
    {record.critic_annotation&&<details className="critic-method-annotation"><summary>Critic method note · advisory</summary><h4>{record.critic_annotation.title}</h4><p>{record.critic_annotation.purpose}</p><ul>{record.critic_annotation.limitations.map((finding,i)=><li key={i}>{finding}</li>)}</ul><small>Model annotation · {record.critic_annotation.model} · source run {record.critic_annotation.run_id.slice(0,12)}. Historical evidence only; no generalized validation or execution authority.</small></details>}
    <details><summary>More actions</summary><button className="context-intent-toggle" disabled={record.contract_status!=="current"} onClick={()=>onDiscuss(`Use the saved workflow “${record.name}”. Adapt it to: `,record.method_id)}>Discuss this method</button></details>
    {record.contract_status!=="current"&&<p>Operation contracts changed or are unavailable. Historical success does not validate a new workflow.</p>}
    <p className="recipe-operation-chain">{record.operations.map(operation=>operation.name).join(' → ')}</p>
    <details><summary>Execution evidence</summary>
      <ol>{record.operations.map(operation=><li key={operation.step_id}>{operation.step_id} · {operation.name} · v{operation.version} → {operation.outputs.join(', ')}</li>)}</ol>
      <details><summary>Successful source runs · {record.sources.length}</summary>{record.sources.map(source=><div key={source.run_id}><p>{new Date(source.finished_at).toLocaleString()} · Plan {source.plan_sha256.slice(0,12)}</p><button className="context-intent-toggle utility-button" onClick={()=>onInspect(source.run_id)}>Inspect recorded outcome</button></div>)}</details>
    </details>
  </section>;
}
