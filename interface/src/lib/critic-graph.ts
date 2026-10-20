import type {Workflow} from './workflow';
import type {WorkflowRun} from './workflow-tools';
export const CRITIC_NODE_ID='planned_critic';
export function criticState(run:WorkflowRun){
 const status=run.critic_review?.status;
 const label=status==='complete'&&run.critic_review?.assessment?'Reviewed':status==='running'?'Reviewing':status==='queued'?'Waiting':status==='deferred'?'Deferred':status==='not_requested'||!status?'Not requested':'Unavailable';
 const graphStatus:Workflow['nodes'][number]['status']=label==='Reviewed'?'complete':label==='Reviewing'?'running':'pending';
 return {label,graphStatus,requested:Boolean(status&&status!=='not_requested')};
}
/** Advisory presentation only: never appended to plan steps or executable edges. */
export function withCriticReview<T extends {nodes:Workflow['nodes'];edges:Workflow['edges'];readOnly:boolean}>(graph:T,run:WorkflowRun):T{
 const state=criticState(run),outcome=graph.nodes.find(node=>node.id==='planned_outcome');
 if(!graph.readOnly||!outcome||!state.requested||graph.nodes.some(node=>node.id===CRITIC_NODE_ID))return graph;
 return {...graph,nodes:[...graph.nodes,{id:CRITIC_NODE_ID,title:'Critic review · advisory',subtitle:`${state.label} · recorded evidence only`,kind:'agent',category:'planning',group:'assurance',x:outcome.x,y:Math.min(3800,outcome.y+200),status:state.graphStatus,authority:'Advisory interpretation; no validation or execution authority',performedBy:'Critic agent',evidence:run.run_id,details:null}],edges:[...graph.edges,{from:outcome.id,to:CRITIC_NODE_ID,kind:'evidence',label:'advisory review'}]};
}
