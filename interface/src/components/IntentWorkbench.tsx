import { useEffect, useRef, useState } from "react";
import { X, ChevronDown, MessageSquare, RefreshCw } from "lucide-react";
import { loadTaskInventory, type TaskInventory } from "../lib/interface-api";
import { retrieveContext, reviewContext, reasonIntent, inspectIntent, reviewIntent, handoffIntent, saveIntentPlan, loadReviewInventory, recoverContext, recoverIntent, type ReviewInventory, type RetrievedContext, type InspectedIntent, type Handoff } from "../lib/intent-api";

type Props = { visible: boolean; onClose: () => void; onGraph: (handoff: Handoff) => void; onInvalidate: () => void; onContinue: (filename: string) => Promise<void> };
export function IntentWorkbench({ visible, onClose, onGraph, onInvalidate, onContinue }: Props) {
  const panelRef = useRef<HTMLElement | null>(null);
  const feedbackRef = useRef<HTMLDivElement | null>(null);
  const [activeStage, setActiveStage] = useState<"context" | "intent" | "plan" | "continue">("context");
  const [recoveryOpen, setRecoveryOpen] = useState(false);
  const [reviews, setReviews] = useState<ReviewInventory | null>(null);
  const [reviewSort, setReviewSort] = useState("newest");
  const [inventory, setInventory] = useState<TaskInventory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [reviewer, setReviewer] = useState("operator");
  const [context, setContext] = useState<RetrievedContext | null>(null);
  const [inspectionSkill, setInspectionSkill] = useState<"inspect_vector" | "inspect_raster">("inspect_vector");
  const [withoutHistory, setWithoutHistory] = useState(false);
  const [contextReview, setContextReview] = useState<string | null>(null);
  const [contextConfirmed, setContextConfirmed] = useState(false);
  const [request, setRequest] = useState("");
  const [answers, setAnswers] = useState("");
  const [intent, setIntent] = useState<InspectedIntent | null>(null);
  const [intentConfirmed, setIntentConfirmed] = useState(false);
  const [intentReview, setIntentReview] = useState<string | null>(null);
  const [plan, setPlan] = useState<Handoff | null>(null);
  const [planConfirmed, setPlanConfirmed] = useState(false);
  const [storedPlan, setStoredPlan] = useState<string | null>(null);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!visible || inventory || historyError) return;
    let active = true;
    setHistoryLoading(true);
    void loadTaskInventory().then((next) => { if (active) { setInventory(next); setHistoryLoading(false); } })
      .catch((e: unknown) => { if (active) { setHistoryError(e instanceof Error ? e.message : "History unavailable"); setHistoryLoading(false); } });
    return () => { active = false; };
  }, [visible]);
  useEffect(() => {
    const panel = panelRef.current;
    const target = panel?.querySelector<HTMLElement>(`[data-intent-stage="${activeStage}"]`);
    if (panel && target && visible) {
      // Scroll this panel only; never move the graph or the surrounding page.
      const top = target.getBoundingClientRect().top - panel.getBoundingClientRect().top + panel.scrollTop;
      panel.scrollTo({ top: Math.max(0, top - 16), behavior: "auto" });
    }
  }, [activeStage]);
  useEffect(() => {
    const panel = panelRef.current;
    const feedback = feedbackRef.current;
    if (error && visible && panel && feedback) {
      const top = feedback.getBoundingClientRect().top - panel.getBoundingClientRect().top + panel.scrollTop;
      panel.scrollTo({ top: Math.max(0, top - 16), behavior: "auto" });
    }
  }, [error]);
  const clearIntent = () => { setIntent(null); setIntentReview(null); setIntentConfirmed(false); if (plan) onInvalidate(); setPlan(null); setStoredPlan(null); setPlanConfirmed(false); setNotice(""); setError(""); if (contextReview || withoutHistory) setActiveStage("intent"); };
  const clearContext = () => { setWithoutHistory(false); setContext(null); setContextReview(null); setContextConfirmed(false); clearIntent(); setActiveStage("context"); };
  const run = async (label: string, action: () => Promise<void>) => { if (busy) return; setBusy(label); setError(""); setNotice(""); try { await action(); } catch (e) { setError(e instanceof Error ? e.message : "Request blocked"); } finally { setBusy(""); } };
  const reopenReview = async (item: ReviewInventory["reviews"][number]) => {
    // Clear old downstream proposals before checking a different saved review.
    clearContext();
    if (item.kind === "context") {
      const stored = await recoverContext(item.review_filename);
      setContext(stored.context); setContextReview(item.review_filename); setContextConfirmed(true);
      setSelected(stored.context.selected_task_ids); setQuery(stored.context.query); setReviewer(stored.reviewer);
      setRequest(""); setAnswers(""); setActiveStage("intent"); setRecoveryOpen(false);
      setNotice("Context review reopened and sources checked. Describe a new task; no model called or work approved.");
    } else {
      const stored = await recoverIntent(item.review_filename);
      const source = stored.intent.review_filename ? await recoverContext(stored.intent.review_filename) : null;
      const checked = await inspectIntent(stored.intent);
      setContext(source?.context ?? null); setContextReview(stored.intent.review_filename); setContextConfirmed(Boolean(source)); setWithoutHistory(!source);
      setSelected(source?.context.selected_task_ids ?? []); setQuery(source?.context.query ?? ""); setReviewer(stored.reviewer);
      setRequest(stored.intent.original_request); setAnswers(stored.intent.clarification_answers.join("\n"));
      setIntent(checked); setIntentReview(item.review_filename); setIntentConfirmed(true); setActiveStage("plan"); setRecoveryOpen(false);
      setNotice(source ? "Reviewed intent reopened and sources checked. Generate inspection plan is available. No model called, work approved or executed." : "History-free reviewed intent reopened. Generate inspection plan is available. No model called, work approved or executed.");
    }
  };
  const sortedReviews = [...(reviews?.reviews ?? [])].sort((a, b) => reviewSort.startsWith("name")
    ? (reviewSort === "name-asc" ? 1 : -1) * a.summary.localeCompare(b.summary)
    : (reviewSort === "oldest" ? 1 : -1) * (a.reviewed_at ?? "").localeCompare(b.reviewed_at ?? ""));
  const canReason = Boolean((contextReview || withoutHistory) && request.trim());
  const lines = answers.split("\n").map((line) => line.trim()).filter(Boolean);
  return <aside ref={panelRef} hidden={!visible} className="intent-workbench" aria-label="Context and intent workspace">
    <header><div><p className="eyebrow">Current task · optional history</p><h2><MessageSquare size={20}/> Context & intent</h2></div><button aria-label="Close context and intent" onClick={onClose}><X size={18}/></button></header>
    <div className="intent-authority"><strong>Reasoning and planning only</strong><span>Review stores context or intent evidence. It does not approve or execute work.</span></div>
    <div className="intent-task-state" aria-live="polite"><strong>{storedPlan ? "Stored plan · separate approval review next" : plan ? "Plan ready · review before storage" : intentReview ? "Intent reviewed · ready to plan" : intent ? intent.review_allowed ? "Intent proposed · confirm its accuracy" : "Clarification needed · answer the questions" : withoutHistory ? "No history selected · describe your task" : contextReview ? "Context reviewed · describe your task" : context ? "Context retrieved · review the excerpts" : "Start a new task or choose historical context"}</strong><span>Nothing approved · nothing executed</span>{request.trim() && <details><summary>Current task request</summary><p>{request}</p></details>}</div>
    <nav className="intent-stage-nav" aria-label="Context and intent stages">{([ ["context", "Context"], ["intent", "Task"], ["plan", "Plan"], ["continue", "Continue"] ] as const).map(([stage, title]) => <button key={stage} disabled={Boolean(busy) || (stage === "intent" && !contextReview && !withoutHistory) || (stage === "plan" && !intentReview) || (stage === "continue" && !storedPlan)} aria-current={activeStage === stage ? "step" : undefined} onClick={() => setActiveStage(stage)}>{title}</button>)}</nav>
    <div ref={feedbackRef} aria-live="polite">{busy && <p className="intent-notice">{busy}… {busy.includes("Intent") || busy.includes("plan") ? "Local model requests can take time." : ""}</p>}{error && <div role="alert" className="intent-error"><strong>Request blocked</strong><span>{error}</span><small>Nothing executed. Stored reviews remain on disk.</small></div>}{notice && <p className="intent-notice">{notice}</p>}</div>
    <fieldset disabled={Boolean(busy)}>
      <details className="intent-recovery" open={recoveryOpen} onToggle={(e) => setRecoveryOpen(e.currentTarget.open)}><summary>Resume a saved context or intent review</summary><p>Reopening checks current source history. It does not run a model or approve work. Unsaved drafts will be replaced.</p>
        <button className="intent-secondary" onClick={() => void run("Checking saved reviews", async () => { setReviews(await loadReviewInventory()); })}><RefreshCw size={14}/> Load saved reviews</button>
        {reviews && <><label>Order<select value={reviewSort} onChange={(e) => setReviewSort(e.target.value)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="name-asc">Name A–Z</option><option value="name-desc">Name Z–A</option></select></label><div className="intent-review-list">{sortedReviews.map((item) => <article key={item.review_filename}><strong>{item.kind === "intent" ? "Intent" : "Context"} · {item.status === "available" ? "Sources checked" : "Reopening blocked"}</strong><p>{item.summary}</p><time>{item.reviewed_at ? new Date(item.reviewed_at).toLocaleString() : "Review date unavailable"}</time><small>{item.reason}</small><button disabled={item.status !== "available"} onClick={() => void run("Reopening saved review", () => reopenReview(item))}>Reopen {item.kind} review</button><details><summary>Artifact identity</summary><code>{item.review_filename}</code></details></article>)}</div>{!reviews.reviews.length && <p>No saved reviews found. Create a context review below.</p>}{reviews.inventory_truncated && <p className="intent-warning">Bounded inventory: only part of the saved reviews is shown.</p>}{reviews.findings.map((finding) => <p className="intent-warning" key={finding}>{finding}</p>)}</>}
      </details>
      <label>Reviewer<input value={reviewer} maxLength={200} onChange={(e) => { setReviewer(e.target.value); setContextConfirmed(false); setIntentConfirmed(false); }}/></label>
      <section data-intent-stage="context"><button className="intent-stage-heading" aria-expanded={activeStage === "context"} aria-controls="intent-context-body" onClick={() => setActiveStage("context")}><span>1 · Historical context</span><small>{withoutHistory ? "Not used" : contextReview ? "Reviewed" : context ? "Review needed" : "Optional"}</small></button><div id="intent-context-body" hidden={activeStage !== "context"}><p>Start a new task directly, or select history when it is relevant. Historical decisions never approve new work.</p><button onClick={() => { clearContext(); setWithoutHistory(true); setRequest(""); setAnswers(""); setActiveStage("intent"); setNotice("New task without historical context. Describe your input and desired outcome."); }}>Start without history</button>
        <button className="intent-secondary" disabled={historyLoading} onClick={() => void run("Refreshing history", async () => { setHistoryLoading(true); setHistoryError(""); clearContext(); try { setInventory(await loadTaskInventory()); } catch (e) { setHistoryError(e instanceof Error ? e.message : "History unavailable"); } finally { setHistoryLoading(false); } })}><RefreshCw size={14}/> {historyLoading ? "Loading histories…" : "Refresh histories"}</button>
        {historyError && <div role="alert" className="intent-error"><strong>Histories unavailable</strong><span>{historyError}</span><small>Restart the updated API, then click Refresh histories. Typing a query does not select a history.</small></div>}
        <p className="intent-selection-count" role="status">{selected.length} of 5 histories selected{selected.length === 0 ? " · tick a checkbox below" : " · explicit selection only"}</p>
        <div className="intent-history-list">{inventory?.tasks.map((task) => <label key={task.task_id} className={`intent-history-choice ${selected.includes(task.task_id) ? "is-selected" : ""}`}><input type="checkbox" checked={selected.includes(task.task_id)} disabled={!selected.includes(task.task_id) && selected.length >= 5} onChange={() => { clearContext(); setSelected((current) => current.includes(task.task_id) ? current.filter((id) => id !== task.task_id) : [...current, task.task_id]); }}/><span><strong>{task.summary || task.task_id}</strong><small>{task.task_id} · {task.event_count} events</small></span></label>)}{inventory && !inventory.tasks.length && <p>No saved history. Create a task through the existing Plan flow first.</p>}</div>
        {inventory?.findings.length ? <p className="intent-warning">Some histories are unavailable or damaged; see Task history in Advanced.</p> : null}
        <label>Search selected histories<input value={query} maxLength={1000} placeholder="For example: denied" onChange={(e) => { clearContext(); setQuery(e.target.value); }}/></label>
        <p id="intent-retrieve-requirement" className="intent-retrieve-hint">{historyLoading ? "Wait for the history list to load." : !selected.length ? "Select a history checkbox above to enable retrieval." : !query.trim() ? "Enter a search term to enable retrieval." : "Ready to search the selected histories."}</p>
        <button aria-describedby="intent-retrieve-requirement" disabled={historyLoading || !selected.length || !query.trim()} onClick={() => void run("Retrieving context", async () => { clearContext(); const found = await retrieveContext(query, selected); setContext(found); setNotice("Retrieved only. Read the excerpts before storing a context review."); })}>Retrieve context</button>
        {context && <div className="intent-result"><strong>{contextReview ? "Context reviewed · historical only" : "Retrieved · not reviewed"}</strong>{context.excerpts.map((excerpt) => <article key={`${excerpt.task_id}:${excerpt.sequence}`}><p>{excerpt.text}</p><small>{excerpt.task_id} · event {excerpt.sequence}</small><details><summary>Source identity</summary><code>{excerpt.source.path}</code><code>{excerpt.source.sha256}</code></details></article>)}{!context.excerpts.length && <p>No matching excerpts. Change the query before review.</p>}
          {!contextReview ? <><label className="intent-confirm"><input type="checkbox" checked={contextConfirmed} onChange={(e) => setContextConfirmed(e.target.checked)}/> I reviewed these excerpts as history, not approval.</label><button disabled={!contextConfirmed || !reviewer.trim() || !context.excerpts.length} onClick={() => void run("Storing context review", async () => { const saved = await reviewContext(context, reviewer); setContextReview(saved.review_filename); setActiveStage("intent"); setNotice("Context review stored. No work approved."); })}>Store context review</button></> : <p className="intent-stored">Context reviewed · no work approved</p>}
          <details><summary>Context audit details</summary><code>{context.context_sha256}</code>{contextReview && <code>{contextReview}</code>}</details></div>}
      </div></section>
      <section data-intent-stage="intent"><button className="intent-stage-heading" disabled={!contextReview && !withoutHistory} aria-expanded={activeStage === "intent"} aria-controls="intent-task-body" onClick={() => setActiveStage("intent")}><span>2 · Describe and review task</span><small>{intentReview ? "Reviewed" : intent ? "Review needed" : "Describe task"}</small></button><div id="intent-task-body" hidden={activeStage !== "intent"}><p>Describe one input file and the metadata you need. Vector inspection supports feature count, fields and CRS; raster inspection supports width, height, band count and CRS.</p>
        <label>Current request<textarea rows={4} maxLength={4000} value={request} placeholder="Inspect the selected dataset and return feature count, fields and CRS. Read-only." onChange={(e) => { clearIntent(); setRequest(e.target.value); }}/></label>
        <label>Explicit answers <small>One answer per line · up to five</small><textarea rows={4} value={answers} maxLength={5000} placeholder={'Input: data/input/sample_points.geojson.\nReturn feature count, fields and CRS. Memory reads allowed; no writes or database loading.'} onChange={(e) => { clearIntent(); setAnswers(e.target.value); }}/></label>
        {!contextReview && !withoutHistory && <small>Choose Start without history, or store a context review first.</small>}{withoutHistory && <p className="intent-notice">No historical context will be sent. Only your current request and answers are used.</p>}{(lines.length > 5 || lines.some((line) => line.length > 1000)) && <p className="intent-warning">Use at most five answers, each no longer than 1,000 characters.</p>}<button disabled={!canReason || lines.length > 5 || lines.some((line) => line.length > 1000)} onClick={() => void run("Intent reasoning", async () => { clearIntent(); const proposed = await reasonIntent(withoutHistory ? null : contextReview, request, lines); setIntent(await inspectIntent(proposed)); setNotice("Intent proposed. Inspect the objective, input, outputs and constraints."); })}>Reason about task</button>
        {intent && <div className="intent-result"><strong>{intentReview ? "Intent reviewed · no work approved" : intent.review_allowed ? "Resolved proposal · review required" : "Clarification needed · review blocked"}</strong><p>{intent.intent.proposal.objective}</p>{([ ["Inputs", intent.intent.proposal.known_inputs], ["Requested outputs", intent.intent.proposal.requested_outputs], ["Constraints", intent.intent.proposal.constraints], ["Questions", intent.intent.proposal.clarification_questions] ] as const).map(([title, items]) => items.length ? <div key={title}><h4>{title}</h4><ul>{items.map((item, i) => <li key={i}>{item}</li>)}</ul></div> : null)}{intent.intent.correction_attempted && <small>One clarification re-evaluation was attempted.</small>}
          {!intentReview ? <><label className="intent-confirm"><input type="checkbox" checked={intentConfirmed} disabled={!intent.review_allowed} onChange={(e) => setIntentConfirmed(e.target.checked)}/> The displayed intent accurately matches my request. This is not work approval.</label><button disabled={!intent.review_allowed || !intentConfirmed || !reviewer.trim()} onClick={() => void run("Storing intent review", async () => { const stored = await reviewIntent(intent, reviewer); setIntentReview(stored.review_filename); setActiveStage("plan"); setNotice("Intent review stored. Planning is available; work remains unapproved."); })}>Store reviewed intent</button></> : <p className="intent-stored">Intent reviewed · no work approved</p>}
          <details><summary>Intent audit details</summary><code>{intent.intent_sha256}</code>{intentReview && <code>{intentReview}</code>}<small>Cited history events: {intent.intent.proposal.cited_sequences.join(", ") || "none"}</small></details></div>}
      </div></section>
      <section data-intent-stage="plan"><button className="intent-stage-heading" disabled={!intentReview} aria-expanded={activeStage === "plan"} aria-controls="intent-plan-body" onClick={() => setActiveStage("plan")}><span>3 · Generate and review plan</span><small>{storedPlan ? "Stored" : plan ? "Review needed" : "Not generated"}</small></button><div id="intent-plan-body" hidden={activeStage !== "plan"}><p>Choose the existing inspection capability matching your reviewed intent. Nothing runs.</p>
        <label>Inspection capability<select value={inspectionSkill} onChange={(e) => { if (plan) onInvalidate(); setPlan(null); setStoredPlan(null); setPlanConfirmed(false); setInspectionSkill(e.target.value as "inspect_vector" | "inspect_raster"); }}><option value="inspect_vector">Vector — feature count, fields, CRS</option><option value="inspect_raster">Raster — width, height, band count, CRS</option></select></label><button disabled={!intentReview} onClick={() => void run("Generating plan", async () => { const next = await handoffIntent(intentReview!, inspectionSkill); setPlan(next); setStoredPlan(null); setPlanConfirmed(false); onGraph(next); setNotice("Plan generated and shown beside this panel. Not saved, approved or executed."); })}>Generate inspection plan</button>
        {plan && <div className="intent-result"><strong>{storedPlan ? "Plan stored · nothing approved or executed" : "Planned only · nothing executed"}</strong><p>{plan.planner_result.plan.summary}</p>{plan.additional_human_approval_required && <p className="intent-warning">The Planner requires a separate human approval. Intent review does not supply it.</p>}<button className="intent-secondary" onClick={() => onGraph(plan)}>Show plan graph</button>{!storedPlan ? <><label className="intent-confirm"><input type="checkbox" checked={planConfirmed} onChange={(e) => setPlanConfirmed(e.target.checked)}/> I reviewed this exact inspection plan. Storing it does not approve work.</label><button disabled={!planConfirmed} onClick={() => void run("Storing reviewed plan", async () => { const stored = await saveIntentPlan(plan); setStoredPlan(stored.plan_filename); setActiveStage("continue"); setNotice("STORED · NOT APPROVED · NOTHING EXECUTED. Continue in Plan to review its separate approval scope."); })}>Store reviewed plan</button></> : <><p className="intent-stored">Stored · not approved · nothing executed</p><button onClick={() => setActiveStage("continue")}>Go to continuation</button><details><summary>Stored artifact</summary><code>{storedPlan}</code></details></>}<details><summary><ChevronDown size={14}/> Plan details</summary><pre>{JSON.stringify(plan.planner_result.plan.steps, null, 2)}</pre></details></div>}
      </div></section>
      <section data-intent-stage="continue"><button className="intent-stage-heading" disabled={!storedPlan} aria-expanded={activeStage === "continue"} aria-controls="intent-continue-body" onClick={() => setActiveStage("continue")}><span>4 · Continue with stored plan</span><small>{storedPlan ? "Ready" : "Not stored"}</small></button><div id="intent-continue-body" hidden={activeStage !== "continue"}>{storedPlan && <><div className="intent-result"><strong>Stored · not approved · nothing executed</strong><p>The reviewed plan is saved. Continue to its separate approval scope in the existing Plan panel.</p><button onClick={() => void run("Opening stored plan", () => onContinue(storedPlan))}>Continue in Plan</button><button className="intent-secondary" onClick={() => { setActiveStage("plan"); if (plan) onGraph(plan); }}>Review plan and graph</button><details><summary>Stored artifact</summary><code>{storedPlan}</code></details></div></>}</div></section>
    </fieldset>
    <footer>Closing this panel keeps its drafts; refreshing the page clears them. Context and intent reviews are stored on disk; reopen them using Resume a saved review. No automatic task linking or execution.</footer>
  </aside>;
}
