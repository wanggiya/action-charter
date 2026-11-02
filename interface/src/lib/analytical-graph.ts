import type {AnalyticalSession} from './analytical-session';
import {workflowSchema,type Workflow} from './workflow';
export type AnalyticalRecord={session:AnalyticalSession;conversationId:string;revision:number;chatRevision?:number};
const object=(v:unknown):Record<string,unknown>=>v&&typeof v==='object'&&!Array.isArray(v)?v as Record<string,unknown>:{};
export const analyticalFileId=(index:number)=>`analytical_input_${index}`;
export const analyticalActionId=(index:number)=>`analytical_action_${index}`;
export function analyticalGraph({session:s,conversationId,revision}:AnalyticalRecord):Workflow {
  const nodes:Workflow['nodes']=[];const edges:Workflow['edges']=[];
  const details=(summary:string,facts:[string,string][]=[]):NonNullable<Workflow['nodes'][number]['details']>=>({summary:summary.slice(0,240),observedFacts:facts.map(([label,value])=>({label:label.slice(0,50),value:value.slice(0,120)})),findings:[],evidencePreviews:[]});
  nodes.push({id:'analytical_request',title:'Explore input data',subtitle:s.directory.slice(0,120),kind:'input',category:'input',group:'intake',x:80,y:70,status:'complete',authority:'Explicit read-only exploration request',performedBy:'User',evidence:`Chat ${conversationId} · revision ${revision}`,details:details('The selected conversation requested read-only exploration. No write or workflow-run authority was granted.')});
  nodes.push({id:'analytical_reasoning',title:'Analytical reasoning',subtitle:`${s.model_calls} model calls · ${s.status.replaceAll('_',' ')}`,kind:'agent',category:'planning',group:'planning',x:390,y:70,status:s.status==='completed'?'complete':'interrupted',authority:'Choose from bounded read-only analytical actions',performedBy:'Analytical role',evidence:'Recorded model/tool session',details:details('The model selected analytical actions and generated an advisory explanation. This is not an approval or a separately validated Critic assessment.',[['Model calls',String(s.model_calls)],['Tool calls',String(s.tool_calls)],['Session duration',`${s.elapsed_seconds.toFixed(1)} seconds`]])});
  edges.push({from:'analytical_request',to:'analytical_reasoning',kind:'control',label:'question'});
  const used=new Set(s.journal.map(j=>j.path));
  s.observations.forEach(o=>{const b=object(o.result.codebook);if(typeof b.path==='string')used.add(b.path);});
  const represented=s.inventory.files.map((f,index)=>({f,index})).sort((a,b)=>Number(used.has(b.f.path))-Number(used.has(a.f.path))).slice(0,8);
  represented.forEach(({f,index},position)=>{
    const profile=s.observations.find(o=>o.tool==='profile_table'&&o.result.path===f.path&&typeof o.result.source_sha256==='string');
    nodes.push({id:analyticalFileId(index),title:f.path.split('/').pop()!.slice(0,80),subtitle:(profile?'Profiled source':f.possible_sample?'Candidate sample · unverified':f.possible_codebook?'Possible codebook':'Discovered input').slice(0,120),kind:'data',category:'input',group:'intake',x:1040,y:570+position*180,status:'complete',authority:'Recorded local input evidence; no write authority',performedBy:profile?'Bounded profile service':'Input discovery',evidence:profile?String(profile.result.source_sha256):'Listing/header evidence; not a full-source hash',details:details('Discovery alone does not prove complete-file analysis or sample provenance.',[['Path',f.path],['Bytes',f.bytes.toLocaleString()],['Scope',profile?'Complete parsed selected source':'Directory metadata / bounded header'],['Sample provenance',f.sample_provenance]])});
  });
  s.journal.forEach((j,index)=>{
    const result=s.observations[index]?.result??{};
    const title=j.tool==='discover_inputs'?'Discover input files':j.tool==='assess_table'?'Assess processing strategy':j.tool==='profile_table'?'Profile selected table':j.tool.replaceAll('_',' ');
    nodes.push({id:analyticalActionId(index),title,subtitle:`${index+1}. ${j.status}${j.tool==='profile_table'&&typeof result.source_rows==='number'?` · ${result.source_rows.toLocaleString()} rows`:''}`,kind:'tool',category:'tool',group:'execution',x:700+index*660,y:310,status:j.status==='completed'?'complete':'failed',authority:'Read-only tool invocation; no workflow dispatch',performedBy:'Shared analytical service',evidence:typeof result.source_sha256==='string'?result.source_sha256:`Recorded ${j.tool} observation`,details:details(String(result.reason??result.error??'Recorded tool observation. Select this block to inspect its facts and coverage.'),[['Tool',j.tool],['Path',j.path??s.directory],['Status',j.status]])});
    edges.push({from:'analytical_reasoning',to:analyticalActionId(index),kind:'tool',label:'read-only call'});
    if(index)edges.push({from:analyticalActionId(index-1),to:analyticalActionId(index),kind:'control',label:'recorded order'});
    represented.forEach(({f,index:fi})=>{
      if(j.path===f.path||object(result.codebook).path===f.path)edges.push({from:analyticalFileId(fi),to:analyticalActionId(index),kind:'data',label:j.path===f.path?'source':'codebook'});
      else if(j.tool==='discover_inputs')edges.push({from:analyticalActionId(index),to:analyticalFileId(fi),kind:'data',label:'discovered'});
    });
  });
  nodes.push({id:'analytical_summary',title:s.status==='completed'?'Analytical outcome':'Partial analytical outcome',subtitle:'Recorded facts + advisory explanation',kind:'evidence',category:'evidence',group:'assurance',x:700+Math.max(1,s.journal.length)*660,y:310,status:s.status==='completed'?'complete':'interrupted',authority:'Evidence display only; no execution approval',performedBy:'Tools + analytical role',evidence:`Chat ${conversationId} · revision ${revision}`,details:details('Computed observations support this explanation. Model interpretation is advisory; no Critic assessment or write authorization is implied.',[['Status',s.status],['Data writes','None'],['Workflow changed','No']])});
  s.journal.forEach((_,index)=>edges.push({from:analyticalActionId(index),to:'analytical_summary',kind:'evidence',label:'recorded facts'}));
  return workflowSchema.parse({schemaVersion:'1.0',id:`analysis-${conversationId}-${revision}`,title:'Analytical session · '+s.directory,correlationId:`${conversationId}:${revision}`,readOnly:true,source:'analytical_session',nodes,edges});
}
