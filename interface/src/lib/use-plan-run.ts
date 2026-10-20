import {useEffect, useState} from 'react';
import {z} from 'zod';
import {runs, runSchema, type WorkflowRun} from './workflow-tools';

export function currentChatId(): string | null {
  try { return localStorage.getItem('actioncharter:planner-conversation:v1'); } catch { return null; }
}
export function matchesPlanRun(run:WorkflowRun|null, plan:string|undefined, chat:string|null) {
  return Boolean(run && plan && chat && run.plan_sha256===plan && run.conversation_id===chat);
}

/** Read recorded evidence only. Never start, authorize, recover or retry work. */
export function usePlanRun(plan:string|undefined, draft:boolean, live:WorkflowRun|null) {
  const chat=currentChatId();
  const scope=`${chat??''}:${plan??''}`;
  const [state,setState]=useState<{scope:string;run:WorkflowRun|null;status:string}>({scope:'',run:null,status:''});
  const [selection,setSelection]=useState<WorkflowRun|null>(null);
  const [revision,setRevision]=useState(0);
  useEffect(()=>{
    let active=true;
    setSelection(null);
    if(!plan||!chat||draft){setState({scope,run:null,status:draft?'Draft edits have no execution evidence.':'No chat-linked execution evidence.'});return;}
    setState({scope,run:null,status:'Loading recorded execution…'});
    void (async()=>{
      const inventory=z.object({records:z.array(runSchema)}).parse(await runs({action:'list'}));
      const latest=inventory.records.filter(run=>matchesPlanRun(run,plan,chat)).sort((a,b)=>b.started_at.localeCompare(a.started_at))[0];
      const record=latest?runSchema.parse(await runs({action:'read',run_id:latest.run_id})):null;
      if(active)setState({scope,run:matchesPlanRun(record,plan,chat)?record:null,status:record?'':'No recorded run found in the recent history for this chat and plan.'});
    })().catch(()=>{if(active)setState({scope,run:null,status:'Recorded results unavailable. Refresh evidence or inspect Execution History; nothing was retried.'});});
    return()=>{active=false;};
  },[plan,chat,draft,revision]);
  const loaded=state.scope===scope?state.run:null;
  const current=matchesPlanRun(live,plan,chat)?live:null;
  const pinned=matchesPlanRun(selection,plan,chat)?selection:null;
  const run=draft?null:pinned??(current&&(!loaded||current.started_at>=loaded.started_at)?current:loaded);
  useEffect(()=>{
    if(!run||draft||(!pinned&&live?.run_id===run.run_id)||!['queued','running'].includes(run.critic_review?.status??''))return;
    let active=true;
    const timer=window.setTimeout(()=>{
      void runs({action:'read',run_id:run.run_id}).then(value=>{
        const next=runSchema.parse(value);
        if(!active||!matchesPlanRun(next,plan,chat)||next.run_id!==run.run_id)return;
        if(pinned)setSelection(previous=>previous?.run_id===next.run_id?next:previous);
        else setState(previous=>previous.scope===scope?{scope,run:next,status:''}:previous);
      }).catch(()=>{if(active)setState(previous=>previous.scope===scope?{...previous,status:'Assessment status unavailable. The graph shows the last recorded state; refresh results to reconnect.'}:previous);});
    },700);
    return()=>{active=false;window.clearTimeout(timer);};
  },[run,scope,draft,live?.run_id,Boolean(pinned)]);
  return {run,status:state.scope===scope?state.status:'Loading recorded execution…',
    refresh:()=>setRevision(value=>value+1),
    select:(value:WorkflowRun|null)=>setSelection(value&&matchesPlanRun(value,plan,chat)?value:null)};
}
