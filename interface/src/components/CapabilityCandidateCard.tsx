import type {CapabilityCandidate} from '../lib/capability-candidate';
export function CapabilityCandidateCard({candidate,enabled,busy,onInstall,onContinue}:{candidate:CapabilityCandidate;enabled:boolean;busy:boolean;onInstall:()=>void;onContinue:()=>void}){
 const installed=candidate.installed||candidate.status==='use_existing';
 return <section className="detail-section capability-candidate" aria-label="Capability candidate">
  <h3>{installed?'Available text capability':candidate.status==='tested'?'Tested capability candidate':'Capability preparation stopped'}</h3>
  <p><strong>{candidate.definition.source_column}</strong> → <strong>{candidate.definition.output_column}</strong></p>
  <p>{candidate.definition.steps.map(step=>step.kind==='replace_literal'?`Replace ${JSON.stringify(step.old)} with ${JSON.stringify(step.new)}`:step.kind.replaceAll('_',' ')).join(' → ')}</p>
  {candidate.tests&&<p>{candidate.tests.passed?'Synthetic and held-out checks passed':'Checks failed'} · {candidate.tests.negative_cases?.length??0} negative/effect checks</p>}
  {candidate.tests?.finding&&<p>{candidate.tests.finding}</p>}
  {candidate.critic&&<p>Critic · advisory: {candidate.critic.assessment?.replaceAll('_',' ')??candidate.critic.status}. {candidate.critic.reason}</p>}
  <small>One bounded CSV text adapter. Original columns stay. Installation grants no write or execution authority.</small>
  <small>Project-wide definition; installation does not copy your chat or user rows into the package.</small>
  <details><summary>Definition, limits and test evidence</summary><pre>{JSON.stringify(candidate,null,2)}</pre></details>
  {installed?<button type="button" className="context-intent-toggle" disabled={busy} onClick={onContinue}>Continue with installed capability</button>:<button type="button" className="context-intent-toggle" disabled={busy||!enabled||candidate.status!=='tested'||!candidate.candidate_sha256} onClick={onInstall}>{busy?'Working…':'Install and update workflow'}</button>}
 </section>;
}
