import {CapabilityCandidateCard} from "./CapabilityCandidateCard";
import { RecipeCandidateCard } from "./RecipeCandidateCard";
import { CHAT_MEMORY_KEY, loadChatMemory, loadSwitchPreference, saveSwitchPreference } from "../lib/switch-preferences";
import { PlannerContextDisclosure } from "./PlannerContextDisclosure";
import { canRestorePlan } from "../lib/saved-plan-recovery";
import { PanelResize } from "./PanelResize";
import { useEffect, useRef, useState } from "react";
import { Bot, Settings, X, Send, Plus, ChevronDown, Search, Check } from "lucide-react";
import { loadPlannerSkills, saveGeneratedPlannerPlan, type SavedPlanInventory, type InterfacePlannerResult, type SavedPlannerResult, type PlannerSkillCatalog } from "../lib/interface-api";
import { skillLabel } from "../lib/skill-labels";
import { loadPlannerConversations, newConversationId, plannerConversation, capabilityControl, readPlannerSubmission, type PlannerConversation } from "../lib/planner-conversation";

import type {ResultViewSpec} from "../lib/result-exploration";
import type {WorkflowRun} from "../lib/workflow-tools";

type Props = { onResultView:(spec:ResultViewSpec)=>Promise<void>;onSubmittedRun:(run:WorkflowRun)=>Promise<void>; currentPlan: InterfacePlannerResult | null; currentSaved: SavedPlannerResult | null; visible: boolean; editsPending: boolean; onClose: () => void; onPlan: (plan: InterfacePlannerResult) => void; onSaved: (saved: SavedPlannerResult) => void; onRestore: (plan: SavedPlanInventory["plans"][number]) => Promise<void>; onScopeChange:()=>void; onTaskBusyChange:(busy:boolean)=>void };
const storageKey = "actioncharter:planner-conversation:v1";
function initialId() {
  try { const id = localStorage.getItem(storageKey); if (id && /^[a-f0-9]{32}$/.test(id)) return id; } catch { /* Storage is optional. */ }
  return newConversationId();
}
export function TextPlanner({ currentPlan: plan, currentSaved: saved, visible, editsPending, onClose, onPlan, onSaved, onRestore, onScopeChange, onTaskBusyChange, onSubmittedRun, onResultView }: Props) {
  const [id, setId] = useState(initialId);
  const [sessions, setSessions] = useState<Awaited<ReturnType<typeof loadPlannerConversations>>>([]);
  const [conversation, setConversation] = useState<PlannerConversation | null>(null);
  const [useHistory, setUseHistory] = useState(()=>loadChatMemory(id));
  const [settingsOpen,setSettingsOpen]=useState(false);
  const settingsRef=useRef<HTMLElement>(null);
  useEffect(()=>{
    if(!settingsOpen)return;
    const dismiss=(event:PointerEvent)=>{if(!settingsRef.current?.contains(event.target as Node)&&!(event.target as Element).closest?.('[aria-label="Conversation settings"]'))setSettingsOpen(false);};
    const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')setSettingsOpen(false);};
    document.addEventListener('pointerdown',dismiss);document.addEventListener('keydown',escape);
    return()=>{document.removeEventListener('pointerdown',dismiss);document.removeEventListener('keydown',escape);};
  },[settingsOpen]);
  useEffect(()=>setSettingsOpen(false),[id]);
  const [inspectOnSend,setInspectOnSend]=useState(()=>loadSwitchPreference('actioncharter:inspect-on-send:v1',false));
  const sendInFlight=useRef(false);
  const [submissionNotice,setSubmissionNotice]=useState('');
  const [pendingSubmission,setPendingSubmission]=useState<string|null>(null);
  useEffect(()=>{try{setPendingSubmission(sessionStorage.getItem(`actioncharter:pending-inspection:${id}`));}catch{setPendingSubmission(null);}setSubmissionNotice('');},[id]);
  const rememberSubmission=(value:string|null)=>{setPendingSubmission(value);try{if(value)sessionStorage.setItem(`actioncharter:pending-inspection:${id}`,value);else sessionStorage.removeItem(`actioncharter:pending-inspection:${id}`);}catch{/* Receipt remains in backend history. */}};
  const [draft, setDraft] = useState("");
  const [successfulSelection,setSuccessfulSelection]=useState<string|null>(null);
  useEffect(()=>setSuccessfulSelection(null),[id]);
  useEffect(()=>{const compose=(event:Event)=>{const detail=(event as CustomEvent<{message:string;successfulMethodId?:string}>).detail;const message=detail?.message;if(typeof message==="string"){setSuccessfulSelection(detail.successfulMethodId&&/^[a-f0-9]{64}$/.test(detail.successfulMethodId)?detail.successfulMethodId:null);setDraft(message);requestAnimationFrame(()=>document.querySelector<HTMLTextAreaElement>('[aria-label="Message Planner"]')?.focus());}};window.addEventListener("actioncharter:planner-compose-message",compose);return()=>window.removeEventListener("actioncharter:planner-compose-message",compose);},[]);
  const [composerHeight,setComposerHeight]=useState(112);
  const composerDrag=useRef<{y:number;height:number}|null>(null);
  const resizeComposer=(height:number,panel:HTMLElement|null)=>setComposerHeight(Math.max(72,Math.min(height,320,(panel?.clientHeight??700)*0.45)));
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [skillsOpen, setSkillsOpen] = useState(false);
  const [skillSearch, setSkillSearch] = useState("");
  const [catalog, setCatalog] = useState<PlannerSkillCatalog | null>(null);
  const [catalogError, setCatalogError] = useState("");
  useEffect(() => {
    let active = true;
    void loadPlannerSkills().then((value) => { if (active) setCatalog(value); }).catch(() => { if (active) setCatalogError("Skill catalog unavailable; automatic planning remains available."); });
    return () => { active = false; };
  }, []);
  useEffect(()=>{let active=true;const refresh=()=>{void loadPlannerSkills().then(value=>{if(active)setCatalog(value);}).catch(()=>setCatalogError("Registry refresh unavailable"));void plannerConversation("read",id).then(value=>{if(active&&!currentRef.current.editsPending&&!currentRef.current.busy)setConversation(value);}).catch(()=>{});};window.addEventListener("actioncharter:operations-changed",refresh);return()=>{active=false;window.removeEventListener("actioncharter:operations-changed",refresh);};},[id]);
  useEffect(()=>{let active=true;const refresh=()=>{void plannerConversation('read',id).then(value=>{if(active)setConversation(current=>current?.conversation_id===id?{...current,method_helper:value.method_helper}:current);}).catch(()=>{});};window.addEventListener('actioncharter:method-helper-changed',refresh);return()=>{active=false;window.removeEventListener('actioncharter:method-helper-changed',refresh);};},[id]);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [pendingMessage, setPendingMessage] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const conversationRef = useRef(conversation);
  conversationRef.current = conversation;
  const currentRef = useRef({ plan, editsPending, id, busy });
  currentRef.current = { plan, editsPending, id, busy };
  const callbacks = useRef({ onPlan, onSaved, onRestore });
  callbacks.current = { onPlan, onSaved, onRestore };
  useEffect(() => {
    let active = true;
    setLoaded(false);
    try { localStorage.setItem(storageKey, id); } catch { /* Conversation remains usable. */ }
    void plannerConversation("read", id).then(async (state) => {
      if (!active) return;
      setConversation(state); setSelectedSkills(state.selected_skill_ids);
      void loadPlannerConversations().then((items) => { if (active) setSessions(items); }).catch(() => { /* Current conversation still works. */ });
      // The conversation owns its latest validated proposal. Recover it directly;
      // artifact inventory order/global browser bookmarks cannot substitute another chat.
      if (state.planner_result && canRestorePlan(active, currentRef.current.id === id, Boolean(currentRef.current.plan), currentRef.current.editsPending)) {
        const expected = currentRef.current.plan?.plan_sha256;
        const stored = await saveGeneratedPlannerPlan(state.planner_result);
        if (active && currentRef.current.id === id && !currentRef.current.editsPending && currentRef.current.plan?.plan_sha256 === expected) {
          callbacks.current.onPlan(state.planner_result);
          callbacks.current.onSaved(stored);
        }
      }
      if (active) setLoaded(true);
    }).catch((e: unknown) => { if (active) { setError(e instanceof Error ? e.message : "Conversation recovery failed"); setLoaded(true); } });
    return () => { active = false; };
  }, [id]);
  useEffect(() => { if (visible) scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [conversation, pendingMessage, visible]);
  const publish = async (result: InterfacePlannerResult) => {
    // Saving must succeed before replacing the current workflow.
    const base = currentRef.current.plan?.plan_sha256;
    const identity = currentRef.current.id;
    const stored = await saveGeneratedPlannerPlan(result);
    if (currentRef.current.editsPending || currentRef.current.id !== identity || currentRef.current.plan?.plan_sha256 !== base) throw new Error("The workspace changed while opening this proposal. Your current workflow is preserved.");
    callbacks.current.onPlan(result); callbacks.current.onSaved(stored);
  };
  const send = async (override?:string,scope?:string[],resumeState?:PlannerConversation,continuation=false) => {
    const text = (override??draft).trim();
    const activeConversation=resumeState??conversation;
    if (((busy||sendInFlight.current)&&!continuation) || !loaded || !text || editsPending) return;
    if(activeConversation?.active_task_id&&plan?.plan_sha256!==activeConversation.planner_result?.plan_sha256){setError('Open this conversation’s plan or explicitly use the current workflow before sending.');return;}
    const base = plan; const submittedId = id;
    sendInFlight.current=true;
    const submission=!continuation?{id:newConversationId(),enabled:inspectOnSend}:undefined;
    if(submission)rememberSubmission(submission.id);
    setSubmissionNotice('');setBusy(true);onTaskBusyChange(true); setError(""); setPendingMessage(text);
    try {
      const state = await plannerConversation("turn", id, activeConversation?.revision ?? 0, text, base, scope??selectedSkills, saved?.plan_sha256 === base?.plan_sha256 ? saved?.plan_filename ?? null : null, useHistory,activeConversation?.active_task_id??null,activeConversation?.task_revision??null,"",null,successfulSelection,undefined,submission);
      if(currentRef.current.id!==submittedId)return;
      setConversation(state); setDraft(""); setSuccessfulSelection(null);
      void loadPlannerConversations().then(setSessions).catch(() => { /* Current transcript is saved. */ });
      if (state.proposal_changed && state.planner_result) {
        if (currentRef.current.id !== submittedId || currentRef.current.editsPending || currentRef.current.plan?.plan_sha256 !== base?.plan_sha256) {
          setError("The workspace changed while the planner was responding. Its proposal is saved in this conversation; reopen it when you are ready.");
        } else {
          const stored = await saveGeneratedPlannerPlan(state.planner_result);
          // Recheck after storage: manual graph edits can happen while saving.
          if (currentRef.current.id === submittedId && !currentRef.current.editsPending && currentRef.current.plan?.plan_sha256 === base?.plan_sha256) {
            callbacks.current.onPlan(state.planner_result); callbacks.current.onSaved(stored);
          } else setError("The workspace changed while saving. Your current graph is preserved; use Open conversation plan to review the response.");
        }
      }
      if(state.context_usage?.result_view && currentRef.current.id===submittedId && !currentRef.current.editsPending){
        await onResultView(state.context_usage.result_view);
      }
      if(state.submission){
        setSubmissionNotice(state.submission.finding);
        if(state.submitted_run && currentRef.current.id===submittedId && !currentRef.current.editsPending)await onSubmittedRun(state.submitted_run);
        rememberSubmission(null);
      }
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Planning failed; current plan preserved"); }
    finally { sendInFlight.current=false;setBusy(false);onTaskBusyChange(false);setPendingMessage(""); }
  };
  const checkSubmission=async()=>{
    if(!pendingSubmission||busy)return;
    const identity=id;setBusy(true);setError('');
    try{
      const receipt=await readPlannerSubmission(pendingSubmission,id);
      if(currentRef.current.id!==identity||currentRef.current.editsPending)return;
      setSubmissionNotice(receipt.submission.finding);
      if(receipt.conversation && receipt.conversation.revision>=(conversationRef.current?.revision??0)){
        setConversation(receipt.conversation);
        if(receipt.conversation.planner_result)await publish(receipt.conversation.planner_result);
        if(receipt.run)await onSubmittedRun(receipt.run);
      }
      if(!['processing','starting'].includes(receipt.submission.status))rememberSubmission(null);
    }catch(e){setError(e instanceof Error?e.message:'Submission receipt unavailable');}
    finally{setBusy(false);}
  };
  const toggleRecommendations=async()=>{
    if(busy||!loaded||editsPending)return;
    const originalId=id;setBusy(true);setError('');
    try{const state=await capabilityControl('configure_recommendations',id,conversation?.revision??0,{recommendations_enabled:!conversation?.recommendations_enabled});if(currentRef.current.id===originalId)setConversation(state);}
    catch(e){setError(e instanceof Error?e.message:'Recommendation setting unavailable');}
    finally{setBusy(false);}
  };
  const toggleAcquisition=async()=>{
    if(busy||!loaded||editsPending)return;
    const originalId=id;setBusy(true);setError('');
    try{const state=await capabilityControl('configure_acquisition',id,conversation?.revision??0,{acquisition_enabled:!conversation?.acquisition_enabled});if(currentRef.current.id===originalId)setConversation(state);}
    catch(e){setError(e instanceof Error?e.message:'Capability setting unavailable');}
    finally{setBusy(false);}
  };
  const continueCapability=async(install:boolean)=>{
    const candidate=conversation?.capability_candidate;
    if(!candidate||busy||editsPending)return;
    const originalId=id;setBusy(true);setError('');
    try{
      const state=install?await capabilityControl('install_capability',id,conversation?.revision??0,{confirmed_candidate_sha256:candidate.candidate_sha256??undefined}):conversation!;
      if(currentRef.current.id!==originalId||currentRef.current.editsPending)throw new Error('Workspace changed. The installed capability is available; resume its original chat when ready.');
      setConversation(state);setSelectedSkills([]);
      window.dispatchEvent(new Event('actioncharter:operations-changed'));
      await send(`Continue the requested workflow using registered operation ${candidate.operation_id}. Return the complete workflow; do not request acquisition or execute it. Original request: ${candidate.request}`,[],state,true);
    }catch(e){setError(e instanceof Error?e.message:'Installation failed; workflow preserved');}
    finally{setBusy(false);}
  };
  useEffect(()=>{
    let active=true;
    const edited=(event:Event)=>{
      const detail=(event as CustomEvent<{previousPlanSha?:string;result:InterfacePlannerResult;bindToCurrentConversation?:boolean}>).detail;
      const stateBefore=conversationRef.current;
      if(!detail?.result||(!detail.previousPlanSha&&!detail.bindToCurrentConversation)||!stateBefore||currentRef.current.busy||stateBefore.planner_result?.plan_sha256!==detail.previousPlanSha)return;
      const identity=id;
      setBusy(true);onTaskBusyChange(true);
      void plannerConversation('bind_task_plan',identity,stateBefore.revision,'',detail.result,[],null,true,identity,stateBefore.task_revision??null).then(state=>{
        if(active&&currentRef.current.id===identity&&currentRef.current.plan?.plan_sha256===detail.result.plan_sha256)setConversation(state);
      }).catch(value=>{if(active)setError(value instanceof Error?value.message:'Saved workflow context could not be updated; use the explicit workflow binding button.');}).finally(()=>{if(active)setBusy(false);onTaskBusyChange(false);});
    };
    window.addEventListener('actioncharter:conversation-workflow-edited',edited);
    return()=>{active=false;window.removeEventListener('actioncharter:conversation-workflow-edited',edited);};
  },[id,onTaskBusyChange]);
  const bindWorkflow=async()=>{
    if(busy||!loaded||editsPending)return;
    const originalPlan=plan?.plan_sha256;const originalId=id;
    setBusy(true);setError('');onTaskBusyChange(true);
    try{
      const state=await plannerConversation('bind_task_plan',id,conversation?.revision??0,'',plan,[],null,useHistory,id,conversation?.task_revision??null);
      if(currentRef.current.id!==originalId||currentRef.current.editsPending||currentRef.current.plan?.plan_sha256!==originalPlan)throw new Error('Workspace changed while binding this conversation. Reload the conversation when ready; your graph is preserved.');
      setConversation(state);setSelectedSkills(state.selected_skill_ids);setDraft('');
      onScopeChange();
      if(state.planner_result){const stored=await saveGeneratedPlannerPlan(state.planner_result);callbacks.current.onPlan(state.planner_result);callbacks.current.onSaved(stored);}
      setSessions(await loadPlannerConversations());
    }catch(value){setError(value instanceof Error?value.message:'Workflow binding failed; reload conversation');}
    finally{setBusy(false);onTaskBusyChange(false);}
  };
  return <aside hidden={!visible} className="intent-workbench text-planner planner-dialogue" aria-label="Planner agent">
    <PanelResize side="planner"/>
    <header><h2><Bot size={20}/> Planner agent</h2><div><button aria-label="Conversation settings" aria-expanded={settingsOpen} onClick={()=>setSettingsOpen(value=>!value)}><Settings size={18}/></button><button disabled={busy||editsPending} title="Start a separate conversation with its own saved history" onClick={() => { onScopeChange();setId(newConversationId()); setConversation(null); setSelectedSkills([]); setDraft(""); setError(""); }}><Plus size={15}/> New chat</button><button onClick={onClose} aria-label="Close planner"><X size={18}/></button></div></header>
    {sessions.length > 0 && <select className="planner-session-picker" aria-label="Saved planning conversation" disabled={busy||editsPending} value={sessions.some((session) => session.conversation_id === id) ? id : ""} onChange={(event) => { if (event.target.value) { onScopeChange();setConversation(null);setSelectedSkills([]);setId(event.target.value); setError(""); setDraft(""); } }}><option value="" disabled>Current new conversation</option>{sessions.map((session) => <option key={session.conversation_id} value={session.conversation_id}>{session.summary?.trim() || "Untitled chat"}</option>)}</select>}
    {settingsOpen&&<section ref={settingsRef} className="planner-settings-popover" aria-label="Conversation settings" onKeyDown={event=>{if(event.key==='Escape')setSettingsOpen(false);}}>
      <header><strong>Conversation settings</strong><button aria-label="Close conversation settings" onClick={()=>setSettingsOpen(false)}><X size={16}/></button></header>
    <div className="planner-history-control"><span id="planner-history-label">Chat memory</span><button className="planner-history-switch" type="button" role="switch" aria-labelledby="planner-history-label" aria-checked={useHistory} disabled={busy||!loaded} onClick={() => setUseHistory(value => {const next=!value;saveSwitchPreference(CHAT_MEMORY_KEY,next);return next;})}><span className="history-switch-track" aria-hidden="true"/><span className="history-switch-thumb" aria-hidden="true"/><span className="history-switch-label history-switch-off" aria-hidden="true">Off</span><span className="history-switch-label history-switch-on" aria-hidden="true">On</span></button></div>
    <small>ON includes recent messages and relevant successful methods from this chat. Your latest workflow is always restored. Retrieval adds no model call.</small>
    <div className="planner-history-control"><span id="planner-acquisition-label">Acquire capabilities · optional</span><button className="planner-history-switch" type="button" role="switch" aria-labelledby="planner-acquisition-label" aria-checked={conversation?.acquisition_enabled??false} disabled={busy||!loaded||editsPending} onClick={()=>void toggleAcquisition()}><span className="history-switch-track" aria-hidden="true"/><span className="history-switch-thumb" aria-hidden="true"/><span className="history-switch-label history-switch-off" aria-hidden="true">Off</span><span className="history-switch-label history-switch-on" aria-hidden="true">On</span></button></div>
    <small>Only this chat. Existing tools first; ON permits synthetic testing of a missing bounded text adapter. Installation and execution stay separate.</small>
      <div className="planner-history-control"><span id="planner-inspection-label">Inspect on send</span><button className="planner-history-switch" type="button" role="switch" aria-labelledby="planner-inspection-label" aria-checked={inspectOnSend} disabled={busy||!loaded||editsPending} onClick={()=>{const next=!inspectOnSend;setInspectOnSend(next);saveSwitchPreference('actioncharter:inspect-on-send:v1',next);}}><span className="history-switch-track" aria-hidden="true"/><span className="history-switch-thumb" aria-hidden="true"/><span className="history-switch-label history-switch-off" aria-hidden="true">Off</span><span className="history-switch-label history-switch-on" aria-hidden="true">On</span></button></div>
      <small>When ON, sending an explicit single-dataset CSV, vector or raster inspection can run it within fixed limits. Other workflows keep Execute and write authorization. Remembered across chats in this browser.</small>
      <div className="planner-history-control"><span id="planner-recommendations-label">Use outcome recommendations</span><button className="planner-history-switch" type="button" role="switch" aria-labelledby="planner-recommendations-label" aria-checked={conversation?.recommendations_enabled??false} disabled={busy||!loaded||editsPending} onClick={()=>void toggleRecommendations()}><span className="history-switch-track" aria-hidden="true"/><span className="history-switch-thumb" aria-hidden="true"/><span className="history-switch-label history-switch-off" aria-hidden="true">Off</span><span className="history-switch-label history-switch-on" aria-hidden="true">On</span></button></div>
      <small>This chat only; default OFF. Rank current operations from verified checks, without sharing chats or granting authority. Chat memory preference applies across chats in this browser.</small>
    </section>}
    {conversation?.context_usage?.model_request?.stage==='recorded_evidence'&&<small role="status">Recorded evidence answer · no model call or source read</small>}
    {conversation?.context_usage?.model_request?.stage==='deterministic_inspection'&&<small role="status">Exact inspection workflow · no model call</small>}
    <small className="planner-submit-mode" role="status">{inspectOnSend?'Send and inspect eligible local datasets · other proposals require Execute':'Send creates a proposal · Execute runs it'}</small>
    {pendingSubmission&&!busy&&<button type="button" onClick={()=>void checkSubmission()}>Check last submission · no retry</button>}
    {submissionNotice&&<p className="planner-submission-notice" role="status">{submissionNotice}</p>}
    <details className="planner-chat-context"><summary>Chat history &amp; context</summary><div className="planner-chat-context-body">
    <details className="planner-task-history"><summary>Saved chat history · {conversation?.messages.length??0} messages</summary><small>This chat only. Saved without Authorize or Execute. The full transcript appears below; these are recent excerpts.</small><div className="planner-history-bubbles" aria-label="Saved chat excerpts">{conversation?.task_history_preview.map((entry,index)=><article className={`planner-message role-${entry.role}`} key={index}><small>{entry.role==='user'?'You':'Planner'}</small><p>{entry.content}</p>{entry.content_truncated&&<small>Excerpt shortened</small>}</article>)}{!conversation?.messages.length&&<p>No saved messages yet.</p>}</div></details>
    <PlannerContextDisclosure helper={conversation?.method_helper} update={conversation?.method_helper_update} includeHistory={useHistory} workflowState={plan?.plan_sha256!==conversation?.planner_result?.plan_sha256?"unbound":plan?"included":"none"} usage={conversation?.context_usage}/>
    </div></details>
    {(conversation?.recommendations_enabled||conversation?.context_usage?.outcome_recommendations?.items.length)?<details className="planner-chat-context" aria-label="Outcome recommendations"><summary>Recommendations from verified checks · this chat</summary>
      {!conversation.recommendations_enabled&&<p>Recommendations are OFF. The evidence below was supplied to the last completed planning request.</p>}
      {conversation.context_usage?.outcome_recommendations?.status==='unavailable'?<p>Recommendation evidence was unavailable for the last request. Your workflow is preserved.</p>:conversation.context_usage?.outcome_recommendations?.items.length?conversation.context_usage.outcome_recommendations.items.map(item=><div key={item.operation_id}><p>{skillLabel(item.operation_id)} · {item.verified_passes} passed / {item.check_failures} failed checks</p>{item.basis&&<small>{item.basis}</small>}</div>):<p>No verified checks were supplied to the last planning request. A read-only inspection can complete without a separate validation check, so inspection alone may not produce recommendations. Run a supported transformation with output validation, then send a related request in this chat.</p>}
      {conversation.context_usage?.outcome_recommendations?.policy_version&&<p>Supplied to Planner · recipe order {conversation.context_usage.outcome_recommendations.recipe_order_changed?'changed by check evidence':'unchanged'}. Model use is not established by this receipt.</p>}
      <small>This shows evidence supplied to the last completed planning request, not a live run inventory. Historical evidence grants no authority; current contracts and authorization still apply.</small>
    </details>:null}

    <div className="planner-messages" ref={scrollRef} role="log" aria-label="Planning conversation" aria-live="polite">
      {!conversation?.messages.length && <p className="planner-welcome">Describe your task and files. Then ask me to add, remove or change workflow steps. Bare filenames resolve under data/input.</p>}
      {conversation?.messages.map((entry, index) => {
        const ids = entry.role === "user" ? entry.selected_skill_ids : entry.plan_skill_ids;
        const previous = conversation.messages.slice(0, index).reverse().find((item) => item.role === "assistant" && item.plan_skill_ids != null)?.plan_skill_ids ?? [];
        const added = entry.role === "assistant" && ids ? ids.filter((skill) => !previous.includes(skill)) : [];
        const removed = entry.role === "assistant" && ids ? previous.filter((skill) => !ids.includes(skill)) : [];
        return <article className={`planner-message role-${entry.role}`} key={`${id}-${index}`}><small>{entry.role === "user" ? "You" : "Planner"}</small><p>{entry.content}</p><div className="conversation-skill-tags" aria-label={entry.role === "user" ? "Submitted skill selection" : "Workflow skills at this reply"}><small>{entry.role === "user" ? "Selected skills" : "Workflow skills"}</small>{ids == null ? <span className="conversation-skill-tag">Not recorded for this older message</span> : ids.length ? ids.map((skill) => <span className="conversation-skill-tag" title={skill} key={skill}>{skillLabel(skill)}</span>) : <span className="conversation-skill-tag">{entry.role === "user" ? "Automatic" : "No proposal yet"}</span>}{added.map((skill) => <span className="conversation-skill-tag skill-added" key={`added-${skill}`} title={skill}>+ {skillLabel(skill)}</span>)}{removed.map((skill) => <span className="conversation-skill-tag skill-removed" key={`removed-${skill}`} title={skill}>− {skillLabel(skill)}</span>)}</div></article>;
      })}
      {conversation?.capability_candidate&&<CapabilityCandidateCard candidate={conversation.capability_candidate} enabled={conversation.acquisition_enabled} busy={busy||editsPending} onInstall={()=>void continueCapability(true)} onContinue={()=>void continueCapability(false)}/>}
      {conversation?.recipe_candidate&&<RecipeCandidateCard candidate={conversation.recipe_candidate} disabled={busy||editsPending}/>}
      {pendingMessage && <article className="planner-message role-user"><small>You · sending</small><p>{pendingMessage}</p><div className="conversation-skill-tags"><small>Selected skills</small>{selectedSkills.length ? selectedSkills.map((skill) => <span className="conversation-skill-tag" key={skill}>{skillLabel(skill)}</span>) : <span className="conversation-skill-tag">Automatic</span>}</div></article>}
      {busy && <p className="intent-notice">{pendingMessage?(inspectOnSend?'Planning, checking scope and inspecting eligible data…':'Thinking and validating…'):'Saving conversation context…'}</p>}
    </div>
    {conversation?.active_task_id&&plan&&conversation.planner_result?.plan_sha256!==plan.plan_sha256&&<button type="button" disabled={busy||editsPending} onClick={()=>void bindWorkflow()}>Use current workflow in this conversation</button>}
    {conversation?.planner_result && conversation.planner_result.plan_sha256 !== plan?.plan_sha256 && <button disabled={busy || editsPending} onClick={() => { setBusy(true); setError(""); void publish(conversation.planner_result!).catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not open conversation plan")).finally(() => setBusy(false)); }}>Open conversation plan</button>}
    {error && <div className="intent-error" role="alert"><p>{error}</p><small>{pendingSubmission?'Check the last submission and recorded run before sending again. Dispatch may already have occurred.':'Current workflow preserved. Nothing approved or executed.'}</small><button disabled={busy} onClick={() => { setBusy(true); void plannerConversation("read", id).then((state) => { setConversation(state); setSelectedSkills(state.selected_skill_ids); setError(""); }).catch((e: unknown) => setError(e instanceof Error ? e.message : "Recovery failed")).finally(() => setBusy(false)); }}>Reload conversation</button></div>}
    {editsPending && <p className="intent-notice">Validate and save, or discard your graph edits before sending a planner message.</p>}
    {successfulSelection&&<div className="planner-saved-method-choice"><span>Saved workflow selected · this chat</span><button type="button" aria-label="Clear saved workflow selection" disabled={busy} onClick={()=>setSuccessfulSelection(null)}><X size={13}/></button></div>}
    <form className="planner-composer" onSubmit={(event) => { event.preventDefault(); void send(); }}><div className="composer-resize-handle" role="separator" aria-label="Resize message area" aria-orientation="horizontal" aria-valuemin={72} aria-valuemax={320} aria-valuenow={Math.round(composerHeight)} tabIndex={0}
      onPointerDown={event=>{event.preventDefault();composerDrag.current={y:event.clientY,height:composerHeight};event.currentTarget.setPointerCapture(event.pointerId);}}
      onPointerMove={event=>{if(composerDrag.current)resizeComposer(composerDrag.current.height+composerDrag.current.y-event.clientY,event.currentTarget.closest('aside'));}}
      onPointerUp={()=>{composerDrag.current=null;}} onPointerCancel={()=>{composerDrag.current=null;}} onLostPointerCapture={()=>{composerDrag.current=null;}}
      onKeyDown={event=>{if(event.key==='ArrowUp'||event.key==='ArrowDown'){event.preventDefault();resizeComposer(composerHeight+(event.key==='ArrowUp'?16:-16),event.currentTarget.closest('aside'));}}}/><label className="planning-writing-surface"><span className="sr-only">Message Planner</span><textarea style={{height:composerHeight}} rows={4} maxLength={8000} value={draft} placeholder={plan ? "Ask for a change to this workflow…" : "Inspect sample_points.geojson. Return feature count, fields and CRS."} disabled={busy} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void send(); } }}/></label><button type="submit" disabled={busy || !loaded || !draft.trim() || editsPending}><Send size={15}/>{busy ? "Thinking…" : "Send"}</button>
      <div className="conversation-skill-picker" onKeyDown={(event) => { if (event.key === "Escape") setSkillsOpen(false); }}>
        <button type="button" disabled={busy || !loaded} aria-expanded={skillsOpen} aria-controls="conversation-skill-options" onClick={() => setSkillsOpen((open) => !open)}><ChevronDown size={14}/> Skills · optional{selectedSkills.length ? ` · ${selectedSkills.length} selected` : " · automatic"}</button>
        <div className="conversation-selected-skills">{selectedSkills.map((skill) => <button type="button" key={skill} disabled={busy} title={skill} aria-label={`Remove ${skillLabel(skill)} selection`} onClick={() => setSelectedSkills((items) => items.filter((id) => id !== skill))}>{skillLabel(skill)}<X size={12}/></button>)}</div>
        {skillsOpen && <div id="conversation-skill-options"><label className="conversation-skill-search"><Search size={14}/><input aria-label="Search planning skills" value={skillSearch} placeholder="Search skills…" onChange={(event) => setSkillSearch(event.target.value)}/></label><div className="conversation-skill-options">{catalog?.skills.filter((skill) => conversation?.supported_skill_ids.includes(skill.id) && `${skill.id} ${skillLabel(skill.id)}`.toLowerCase().includes(skillSearch.trim().toLowerCase())).map((skill) => <button type="button" disabled={busy} aria-pressed={selectedSkills.includes(skill.id)} key={skill.id} title={skill.id} onClick={() => setSelectedSkills((items) => items.includes(skill.id) ? items.filter((id) => id !== skill.id) : [...items, skill.id])}>{selectedSkills.includes(skill.id) && <Check size={12}/>}<span>{skillLabel(skill.id)}</span><small>{skill.approval_required ? "Authorization required" : "Read-only"}</small></button>)}</div><button type="button" disabled={busy || !selectedSkills.length} onClick={() => setSelectedSkills([])}>Clear selection · use automatic</button>{catalogError && <small role="status">{catalogError}</small>}<small>Empty selection lets Planner choose. Selected skills permit additions; existing workflow skills and required load dependencies stay available. Selection grants no execution authority.</small></div>}
      </div>
    </form>
    <footer>Enter to send · Shift+Enter for a new line. {inspectOnSend?"Sending can run one supported bounded inspection; writes still need authorization and Execute.":"Messages propose changes; Authorize and Execute remain separate."}</footer>
  </aside>;
}
