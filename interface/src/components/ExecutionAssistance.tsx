import {useState} from 'react';
import {z} from 'zod';
import type {ResultRecord} from './ResultsWorkspace';

const replySchema=z.object({status:z.literal('advisory'),message:z.string(),suggested_action:z.enum(['explain','propose_revision']),
  model:z.string(),model_calls:z.number(),tool_calls:z.number(),workflow_changed:z.literal(false),data_written:z.literal(false)});
export function ExecutionAssistance({record,stepId}:{record:ResultRecord;stepId:string}) {
  const [question,setQuestion]=useState('Explain this operation’s evidence, codebook coverage and any unresolved limitations.');
  const [reply,setReply]=useState<z.infer<typeof replySchema>|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const ask=async()=>{
    setBusy(true);setError('');setReply(null);
    try{
      const response=await fetch('/api/v1/workflow/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'execution_assistance',run_id:record.run_id,conversation_id:record.conversation_id,confirmed_plan_sha256:record.plan_sha256,step_id:stepId,assistant_question:question})});
      const value=await response.json();
      if(!response.ok)throw new Error(typeof value.error==='string'?value.error:'Execution assistance unavailable');
      setReply(replySchema.parse(value));
    }catch(e){setError(e instanceof Error?e.message:'Execution assistance failed');}finally{setBusy(false);}
  };
  return <details className="detail-section"><summary>Execution assistance · optional model reasoning</summary>
    <p>Ask about recorded results or a stopped operation. The assistant may request one verified read-only profile. It cannot change the workflow, approve work or repeat writes.</p>
    <label>Question<textarea value={question} maxLength={2000} onChange={e=>setQuestion(e.target.value)} /></label>
    <button disabled={busy||!question.trim()||!record.conversation_id||!record.plan_sha256} onClick={()=>void ask()}>{busy?'Assessing evidence…':'Ask execution assistant'}</button>
    {error&&<p role="alert">{error}</p>}
    {reply&&<><p>{reply.message}</p><small>{reply.model} · {reply.model_calls} model calls · {reply.tool_calls} read-only tool calls · unvalidated interpretation. {reply.suggested_action==='propose_revision'?'Send a follow-up to Planner to review a revised workflow.':''}</small></>}
  </details>;
}
