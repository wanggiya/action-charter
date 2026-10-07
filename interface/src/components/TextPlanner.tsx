import { useEffect, useRef, useState } from "react";
import { Bot, X, Send, Plus, ChevronDown, Search, Check } from "lucide-react";
import { loadPlannerSkills, saveGeneratedPlannerPlan, type InterfacePlannerResult, type SavedPlannerResult, type PlannerSkillCatalog } from "../lib/interface-api";
import { skillLabel } from "../lib/skill-labels";
import { loadPlannerConversations, newConversationId, plannerConversation, type PlannerConversation } from "../lib/planner-conversation";

type Props = { currentPlan: InterfacePlannerResult | null; currentSaved: SavedPlannerResult | null; visible: boolean; editsPending: boolean; onClose: () => void; onPlan: (plan: InterfacePlannerResult) => void; onSaved: (saved: SavedPlannerResult) => void };
const storageKey = "actioncharter:planner-conversation:v1";
function initialId() {
  try { const id = localStorage.getItem(storageKey); if (id && /^[a-f0-9]{32}$/.test(id)) return id; } catch { /* Storage is optional. */ }
  return newConversationId();
}
export function TextPlanner({ currentPlan: plan, currentSaved: saved, visible, editsPending, onClose, onPlan, onSaved }: Props) {
  const [id, setId] = useState(initialId);
  const [sessions, setSessions] = useState<Awaited<ReturnType<typeof loadPlannerConversations>>>([]);
  const [conversation, setConversation] = useState<PlannerConversation | null>(null);
  const [draft, setDraft] = useState("");
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
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [pendingMessage, setPendingMessage] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const currentRef = useRef({ plan, editsPending, id });
  currentRef.current = { plan, editsPending, id };
  const callbacks = useRef({ onPlan, onSaved });
  callbacks.current = { onPlan, onSaved };
  useEffect(() => {
    let active = true;
    setLoaded(false);
    try { localStorage.setItem(storageKey, id); } catch { /* Conversation remains usable. */ }
    void plannerConversation("read", id).then(async (state) => {
      if (!active) return;
      setConversation(state); setSelectedSkills(state.selected_skill_ids); setLoaded(true);
      void loadPlannerConversations().then((items) => { if (active) setSessions(items); }).catch(() => { /* Current conversation still works. */ });
      // Recovery is explicit: never replace a plan already open in the workspace.
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
  const send = async () => {
    const text = draft.trim();
    if (busy || !loaded || !text || editsPending) return;
    const base = plan; const submittedId = id;
    setBusy(true); setError(""); setPendingMessage(text);
    try {
      const state = await plannerConversation("turn", id, conversation?.revision ?? 0, text, base, selectedSkills, saved?.plan_sha256 === base?.plan_sha256 ? saved?.plan_filename ?? null : null);
      setConversation(state); setDraft("");
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
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Planning failed; current plan preserved"); }
    finally { setBusy(false); setPendingMessage(""); }
  };
  return <aside hidden={!visible} className="intent-workbench text-planner planner-dialogue" aria-label="Planner agent">
    <header><h2><Bot size={20}/> Planner agent</h2><div><button disabled={busy} title="Start a new conversation; keep the current workflow as context" onClick={() => { setId(newConversationId()); setConversation(null); setSelectedSkills([]); setDraft(""); setError(""); }}><Plus size={15}/> New chat</button><button onClick={onClose} aria-label="Close planner"><X size={18}/></button></div></header>
    {sessions.length > 0 && <select className="planner-session-picker" aria-label="Saved planning conversation" disabled={busy} value={sessions.some((session) => session.conversation_id === id) ? id : ""} onChange={(event) => { if (event.target.value) { setId(event.target.value); setError(""); setDraft(""); } }}><option value="" disabled>Current new conversation</option>{sessions.map((session) => <option key={session.conversation_id} value={session.conversation_id}>{session.summary}</option>)}</select>}
    <div className="planner-messages" ref={scrollRef} role="log" aria-label="Planning conversation" aria-live="polite">
      {!conversation?.messages.length && <p className="planner-welcome">Describe your task and files. Then ask me to add, remove or change workflow steps. Bare filenames resolve under data/input.</p>}
      {conversation?.messages.map((entry, index) => {
        const ids = entry.role === "user" ? entry.selected_skill_ids : entry.plan_skill_ids;
        const previous = conversation.messages.slice(0, index).reverse().find((item) => item.role === "assistant" && item.plan_skill_ids != null)?.plan_skill_ids ?? [];
        const added = entry.role === "assistant" && ids ? ids.filter((skill) => !previous.includes(skill)) : [];
        const removed = entry.role === "assistant" && ids ? previous.filter((skill) => !ids.includes(skill)) : [];
        return <article className={`planner-message role-${entry.role}`} key={`${id}-${index}`}><small>{entry.role === "user" ? "You" : "Planner"}</small><p>{entry.content}</p><div className="conversation-skill-tags" aria-label={entry.role === "user" ? "Submitted skill selection" : "Workflow skills at this reply"}><small>{entry.role === "user" ? "Selected skills" : "Workflow skills"}</small>{ids == null ? <span className="conversation-skill-tag">Not recorded for this older message</span> : ids.length ? ids.map((skill) => <span className="conversation-skill-tag" title={skill} key={skill}>{skillLabel(skill)}</span>) : <span className="conversation-skill-tag">{entry.role === "user" ? "Automatic" : "No proposal yet"}</span>}{added.map((skill) => <span className="conversation-skill-tag skill-added" key={`added-${skill}`} title={skill}>+ {skillLabel(skill)}</span>)}{removed.map((skill) => <span className="conversation-skill-tag skill-removed" key={`removed-${skill}`} title={skill}>− {skillLabel(skill)}</span>)}</div></article>;
      })}
      {pendingMessage && <article className="planner-message role-user"><small>You · sending</small><p>{pendingMessage}</p><div className="conversation-skill-tags"><small>Selected skills</small>{selectedSkills.length ? selectedSkills.map((skill) => <span className="conversation-skill-tag" key={skill}>{skillLabel(skill)}</span>) : <span className="conversation-skill-tag">Automatic</span>}</div></article>}
      {busy && <p className="intent-notice">Thinking and validating…</p>}
    </div>
    {conversation?.planner_result && conversation.planner_result.plan_sha256 !== plan?.plan_sha256 && <button disabled={busy || editsPending} onClick={() => { setBusy(true); setError(""); void publish(conversation.planner_result!).catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not open conversation plan")).finally(() => setBusy(false)); }}>Open conversation plan</button>}
    {error && <div className="intent-error" role="alert"><p>{error}</p><small>Current workflow preserved. Nothing approved or executed.</small><button disabled={busy} onClick={() => { setBusy(true); void plannerConversation("read", id).then((state) => { setConversation(state); setSelectedSkills(state.selected_skill_ids); setError(""); }).catch((e: unknown) => setError(e instanceof Error ? e.message : "Recovery failed")).finally(() => setBusy(false)); }}>Reload conversation</button></div>}
    {editsPending && <p className="intent-notice">Validate and save, or discard your graph edits before sending a planner message.</p>}
    <form className="planner-composer" onSubmit={(event) => { event.preventDefault(); void send(); }}><label className="planning-writing-surface"><span className="sr-only">Message Planner</span><textarea rows={4} maxLength={8000} value={draft} placeholder={plan ? "Ask for a change to this workflow…" : "Inspect sample_points.geojson. Return feature count, fields and CRS."} disabled={busy} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void send(); } }}/></label><button type="submit" disabled={busy || !loaded || !draft.trim() || editsPending}><Send size={15}/>{busy ? "Thinking…" : "Send"}</button>
      <div className="conversation-skill-picker" onKeyDown={(event) => { if (event.key === "Escape") setSkillsOpen(false); }}>
        <button type="button" disabled={busy || !loaded} aria-expanded={skillsOpen} aria-controls="conversation-skill-options" onClick={() => setSkillsOpen((open) => !open)}><ChevronDown size={14}/> Skills · optional{selectedSkills.length ? ` · ${selectedSkills.length} selected` : " · automatic"}</button>
        <div className="conversation-selected-skills">{selectedSkills.map((skill) => <button type="button" key={skill} disabled={busy} title={skill} aria-label={`Remove ${skillLabel(skill)} selection`} onClick={() => setSelectedSkills((items) => items.filter((id) => id !== skill))}>{skillLabel(skill)}<X size={12}/></button>)}</div>
        {skillsOpen && <div id="conversation-skill-options"><label className="conversation-skill-search"><Search size={14}/><input aria-label="Search planning skills" value={skillSearch} placeholder="Search skills…" onChange={(event) => setSkillSearch(event.target.value)}/></label><div className="conversation-skill-options">{catalog?.skills.filter((skill) => conversation?.supported_skill_ids.includes(skill.id) && `${skill.id} ${skillLabel(skill.id)}`.toLowerCase().includes(skillSearch.trim().toLowerCase())).map((skill) => <button type="button" disabled={busy} aria-pressed={selectedSkills.includes(skill.id)} key={skill.id} title={skill.id} onClick={() => setSelectedSkills((items) => items.includes(skill.id) ? items.filter((id) => id !== skill.id) : [...items, skill.id])}>{selectedSkills.includes(skill.id) && <Check size={12}/>}<span>{skillLabel(skill.id)}</span><small>{skill.approval_required ? "Authorization required" : "Read-only"}</small></button>)}</div><button type="button" disabled={busy || !selectedSkills.length} onClick={() => setSelectedSkills([])}>Clear selection · use automatic</button>{catalogError && <small role="status">{catalogError}</small>}<small>Empty selection lets Planner choose. Selected skills permit additions; existing workflow skills and required load dependencies stay available. Selection grants no execution authority.</small></div>}
      </div>
    </form>
    <footer>{saved ? "Current plan saved · " : ""}Enter to send · Shift+Enter for a new line. Messages propose changes; Authorize and Execute remain separate.</footer>
  </aside>;
}
