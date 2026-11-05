import { WritePolicyStatus } from "../lib/write-policy";
import { runActive, runs as workflowRuns, runSchema } from "../lib/workflow-tools";
import { Bot, ChevronDown, FileCheck2, GitBranch, CircleAlert, Play, Settings as SettingsIcon, History, LayoutList, LayoutTemplate, ShieldCheck, Workflow, XCircle } from "lucide-react";
import {useWorkspace} from './WorkspaceContext';

export function WorkspaceHeader() {
 const { textPlannerOpen, mode, workflowBusy, editBusy, openJourneyStage, intentOpen, rightPanelOpen, 
  setTextPlannerOpen, setIntentOpen, executionInventoryOpen, setRunPanelOpen, openExecutionInventory, 
  outcomeOpen, setWorkflowReviewOpen, setExecutionInventoryOpen, setInspectionHistorySelection, 
  setOutcomeOpen, graphSelection, requiresWorkflowAuthorization, savedPlannerResult, editedPlan, 
  openWorkflowExecution, executeBlocked, executeFromHeader, setReusableOpen, workflowRun, setWorkflowRun, 
  setWorkflowNotice, recordsOpen, openRecords, settingsOpen, setSettingsOpen, advancedOpen, setAdvancedOpen, 
}=useWorkspace();
 return <><header className="topbar">
      <div className="brand"><span className="brand-mark"><GitBranch size={18}/></span><span>ActionCharter</span></div>
      <nav className="journey-nav" aria-label="Workspace navigation"><div className="journey-steps">
        <button className={`journey-step ${textPlannerOpen ? "active" : ""}`} disabled={mode === "proposal" || workflowBusy || editBusy} onClick={() => openJourneyStage("plan")}><Bot size={16}/><strong>Planner agent</strong></button>
        <button className={`journey-step ${!textPlannerOpen && !intentOpen && !rightPanelOpen ? "active" : ""}`} aria-pressed={!textPlannerOpen && !intentOpen && !rightPanelOpen} onClick={() => { setTextPlannerOpen(false); setIntentOpen(false); openJourneyStage("review"); }}><Workflow size={16}/><strong>Flow graph</strong></button>
        <button className={`journey-step ${executionInventoryOpen ? "active" : ""}`} aria-pressed={executionInventoryOpen} onClick={() => {setRunPanelOpen(false);void openExecutionInventory();}}><History size={16}/><strong>Execution History</strong></button>
        <button className={`journey-step ${outcomeOpen ? "active" : ""}`} aria-pressed={outcomeOpen} onClick={() => { setWorkflowReviewOpen(false); setExecutionInventoryOpen(false); setIntentOpen(false); setRunPanelOpen(false);setInspectionHistorySelection(null); setOutcomeOpen(true); }}><FileCheck2 size={16}/><strong>Outcome</strong></button>
      </div></nav>
      <div className="top-actions"><div className="workflow-primary-actions"><WritePolicyStatus/>
        {graphSelection!=="analytical-session"&&graphSelection!=="chat-history"&&requiresWorkflowAuthorization&&<button className="context-intent-toggle authorize-button" disabled={workflowBusy || editBusy || mode === "proposal" || !savedPlannerResult || Boolean(editedPlan)} onClick={() => void openWorkflowExecution(true)}><CircleAlert size={16}/> Authorize</button>}
        <button className="context-intent-toggle execute-button" disabled={Boolean(executeBlocked)} title={executeBlocked||"Execute the current workflow"} aria-describedby={executeBlocked?"execute-block-reason":undefined} onClick={()=>void executeFromHeader()}><Play size={16} fill="currentColor"/> Execute</button>
        </div>
        <button className="context-intent-toggle utility-button" disabled={workflowBusy || editBusy || Boolean(editedPlan)} onClick={() => setReusableOpen(true)}><LayoutTemplate size={15}/> Reusable recipes</button>
        {runActive(workflowRun) && <button className="context-intent-toggle authorize-button" disabled={workflowRun?.cancel_requested} onClick={() => { setRunPanelOpen(true); setWorkflowReviewOpen(false); setExecutionInventoryOpen(false); setOutcomeOpen(false); if(workflowRun)void workflowRuns({action:"cancel",run_id:workflowRun.run_id}).then(value=>setWorkflowRun(runSchema.parse(value))).catch(()=>setWorkflowNotice("Cancellation request failed. Reopen workflow runs to check status.")); }}><XCircle size={15}/>{workflowRun?.cancel_requested ? "Stopping after current operation…" : "Cancel"}</button>}
        <button className="context-intent-toggle utility-button" disabled={mode === "proposal" || workflowBusy || editBusy} aria-expanded={recordsOpen} onClick={() => void openRecords()}><LayoutList size={15}/> Saved records</button>
        <button className="context-intent-toggle utility-button" aria-expanded={settingsOpen} onClick={() => setSettingsOpen(true)}><SettingsIcon size={16}/> Settings</button>
        <button className="advanced-toggle utility-button" aria-expanded={advancedOpen} aria-controls="advanced-actions" onClick={() => setAdvancedOpen((open) => !open)}><span>{advancedOpen ? "Close Advanced" : "Advanced"}</span><ChevronDown size={15}/></button>
        <div className={`safe-mode ${mode === "proposal" || editedPlan ? "draft-mode" : ""}`}><ShieldCheck size={15}/><span>{mode === "proposal" || editedPlan ? "Draft only" : "Governed"}</span></div>
      </div>
    </header></>;
}
