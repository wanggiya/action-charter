import type { HelperStatus } from "../lib/method-helper";
import type { PlannerConversation } from "../lib/planner-conversation";

type Props = {
  includeHistory: boolean;
  workflowState: "included" | "none" | "unbound";
  usage: PlannerConversation["context_usage"];
  helper?:HelperStatus;
  update?:PlannerConversation["method_helper_update"];
};

export function PlannerContextDisclosure({includeHistory,workflowState,usage,helper,update}:Props){
  return <details className="planner-context-disclosure">
    <summary>Context sent to Planner</summary>
    <p>Other conversations are not included. Project guidance and supported operation contracts remain separate from chat history.</p>
    <h3>Next request</h3>
    <dl>
      <div><dt>Latest message</dt><dd>Included when you send</dd></div>
      <div><dt>Current workflow</dt><dd>{workflowState==="included"?"Included, even when chat messages are OFF":workflowState==="none"?"No workflow yet":"Open or bind this chat’s workflow before sending"}</dd></div>
      {helper&&helper.status!=="disabled"&&<div><dt>Method helper</dt><dd>{helper.status==="ready"?"Unvalidated note available for this exact workflow":`No note included yet · ${helper.status.replaceAll("_"," ")}`}</dd></div>}
      <div><dt>Recent chat messages</dt><dd>{includeHistory?"Bounded excerpts from this chat; its opening message is also included when available":"Excluded; saved history stays intact"}</dd></div>
    </dl>
    <h3>Last completed request</h3>
    {usage?<>
      <dl>
        <div><dt>Chat messages</dt><dd>{usage.history_enabled?"ON":"OFF"} · {usage.included_messages} recent messages included · {usage.omitted_messages} omitted{usage.excerpts_truncated?" · excerpts shortened":""}</dd></div>
        {usage.selected_method_id&&<div><dt>Reviewed method · older request</dt><dd>Included · version {usage.selected_method_revision}</dd></div>}
        {usage.method_helper&&<div><dt>Method helper</dt><dd>{usage.method_helper.status==="included"?"Included · machine-generated, unvalidated":`Not included · ${usage.method_helper.status.replaceAll("_"," ")}`}</dd></div>}
        {usage.successful_methods&&<div><dt>Saved successful methods</dt><dd>{usage.successful_methods.count} included · {usage.successful_methods.status.replaceAll('_',' ')} · this chat only</dd></div>}
        {usage.recipe_discovery&&<div><dt>Recipe discovery</dt><dd>{usage.recipe_discovery.rounds} read-only searches/inspections · {usage.recipe_reuse?.length??0} sources reported used</dd></div>}
        {!!usage.required_gate_bindings?.length&&<div><dt>Required checks</dt><dd>{usage.required_gate_bindings.length} operation requirements applied from the registry · no authorization recorded</dd></div>}
        {usage.effort_budget&&<div><dt>Planner effort</dt><dd>{usage.effort_budget.model_calls}/{usage.effort_budget.model_call_limit} model calls · {usage.effort_budget.tool_calls}/{usage.effort_budget.tool_call_limit} discovery calls · {usage.effort_budget.elapsed_seconds.toFixed(1)} seconds{usage.effort_budget.token_usage_complete?` · ${usage.effort_budget.prompt_tokens} input / ${usage.effort_budget.completion_tokens} output tokens`:" · token usage unavailable or incomplete"}{usage.effort_budget.deadline_seconds!==null?` · ${usage.effort_budget.deadline_seconds}s deadline`:" · per-call timeout; no overall deadline configured"}</dd></div>}
        {usage.model_request&&<div><dt>Model request</dt><dd>{(usage.model_request.prompt_bytes/1024).toFixed(1)} KB · {usage.model_request.elapsed_seconds.toFixed(1)} seconds · {usage.model_request.supplied_schema_count} schemas / {usage.model_request.available_operation_count} available operations{usage.model_request.response_format?` · format: ${usage.model_request.response_format}`:""}{usage.model_request.finish_reason?` · finish: ${usage.model_request.finish_reason}`:""}</dd></div>}
        <div><dt>Opening message</dt><dd>{usage.opening_message_included==null?"Not recorded for this older request":usage.opening_message_included?"Included separately":"Not included"}</dd></div>
        <div><dt>Current workflow</dt><dd>{usage.current_workflow_included==null?"Not recorded for this older request":usage.current_workflow_included?"Included":"Not included"}</dd></div>
      </dl>
      <small>These details describe the completed request. Changing the switch affects your next request.</small>
    </>:<p>No completed-request details available yet.</p>}
    {helper?.note&&<details className="helper-note-details"><summary>Method note · unvalidated</summary><p>{helper.note.document.title}</p><p>{helper.note.document.purpose}</p><small>Source: this chat's validated plan only · revision {helper.note.source_conversation_revision}. No execution or verified outcome evidence. Model: {helper.note.model}.</small>{(['inputs','prerequisites','checks','limitations'] as const).map(key=><div key={key}><h3>{key}</h3><ul>{helper.note!.document[key].map((text,index)=><li key={index}>{text}</li>)}</ul></div>)}<ol>{helper.note.document.operations.map((operation,index)=><li key={index}><strong>{operation.skill}</strong>: {operation.guidance}</li>)}</ol></details>}
    {update&&update.status!=="disabled"&&update.status!=="unchanged"&&<small>Helper after this turn: {update.status.replaceAll("_"," ")} · {update.model_calls} extra model request{update.model_calls===1?'':'s'}{update.finding?` · ${update.finding}`:''}.</small>}
    <small>Viewing history or changing this switch does not authorize or execute anything.</small>
  </details>;
}
