import { TextPlanner } from "../components/TextPlanner";
import { IntentWorkbench } from "../components/IntentWorkbench";
import { loadSavedPlans } from "../lib/interface-api";
import { demoWorkflow, plannerWorkflow, taskDraftWorkflow, intentWorkflow } from './model';
import {useWorkspace} from './WorkspaceContext';

export function PlannerWorkspace() {
 const { batchWorkspace, setConversationId, returnFromHistory, graphSelection, historyReturnRef, 
  setHistoricalRecord, setGraphSelection, setOutcomeOpen, setWorkflowReviewOpen, setExecutionInventoryOpen, 
  setRunPanelOpen, setInspectorClosed, setSelectedId, setAnalyticalRecord, graphScopeEpoch, setPlannerResult, 
  setSavedPlannerResult, setWorkflowReview, setWorkflowAuthorization, cancelNodeLayoutDrag, setLoadNotice, 
  openPlannerResultView, setSubmittedInspection, setTaskTransitionBusy, setEditedPlan, setExecutionResult, 
  setCurrentInspection, setInspectionHistorySelection, setOutcomeSelection, setWorkflowNotice, 
  setWorkflowOutcomeNotice, setTaskDraft, setIntentGraphResult, setCurrentTaskId, setViewedTaskId, 
  setTaskContext, setPreparedPlanApproval, setRecordedPlanApproval, setVerifiedPlanApproval, 
  setPlanExecutionPreview, setCompiledPlanRecipe, setSavedPlanRecipe, setPlannerReviewConfirmed, 
  setPlanRecipeReviewConfirmed, setLocalGraph, setShowActiveGraph, setBaseGraphSelection, setWorkflow, 
  resumeSavedPlan, editedPlan, mode, executionWorkflowBusy, editBusy, plannerResult, savedPlannerResult, 
  textPlannerOpen, setTextPlannerOpen, setSavedPlanInventory, setIntentOpen, setPlannerOpen, intentOpen, 
  setJourneyStage, 
}=useWorkspace();
 return <><TextPlanner onConversationChange={setConversationId} onHistoryCurrent={returnFromHistory} onHistoryOpen={item=>{
        if(graphSelection!=='chat-history')historyReturnRef.current=graphSelection;
        setHistoricalRecord(item);setGraphSelection('chat-history');setOutcomeOpen(Boolean(item.run||item.analytical_session&&['analysis','view'].includes(item.entry.kind)));setWorkflowReviewOpen(false);setExecutionInventoryOpen(false);setRunPanelOpen(false);setInspectorClosed(false);setSelectedId(item.analytical_session&&['analysis','view'].includes(item.entry.kind)?'analytical_summary':'planned_planner');
      }} onAnalyticalSession={(session,conversationId,revision,activate,planSha)=>{
        setAnalyticalRecord({session,conversationId,revision:session.conversation_revision??revision,chatRevision:revision});
        if(activate){graphScopeEpoch.current++;if(planSha===null){setPlannerResult(null);setSavedPlannerResult(null);setWorkflowReview(null);setWorkflowAuthorization(null);}cancelNodeLayoutDrag();setGraphSelection('analytical-session');setSelectedId('analytical_summary');setInspectorClosed(false);setWorkflowReviewOpen(false);setOutcomeOpen(false);setRunPanelOpen(false);setExecutionInventoryOpen(false);setLoadNotice('Recorded analytical actions · read-only · saved workflow preserved');}
      }} onResultView={openPlannerResultView} onSubmittedRun={async(run)=>{setSubmittedInspection(run);}} onTaskBusyChange={setTaskTransitionBusy} onScopeChange={() => batchWorkspace(() => {
        setConversationId(null);
        graphScopeEpoch.current++;setHistoricalRecord(null);setAnalyticalRecord(null);cancelNodeLayoutDrag();setPlannerResult(null);setSavedPlannerResult(null);setEditedPlan(null);
        setWorkflowReview(null);setWorkflowAuthorization(null);setWorkflowReviewOpen(false);setOutcomeOpen(false);
        setExecutionResult(null);setCurrentInspection(null); setInspectionHistorySelection(null);setOutcomeSelection({view:'Overview'});setWorkflowNotice('');setWorkflowOutcomeNotice('');
        setTaskDraft(null);setIntentGraphResult(null);setCurrentTaskId(null);setViewedTaskId(null);setTaskContext(null);
        try { sessionStorage.removeItem('actioncharter:currentTaskId'); } catch { /* Optional browser persistence. */ }
        setPreparedPlanApproval(null);setRecordedPlanApproval(null);setVerifiedPlanApproval(null);setPlanExecutionPreview(null);
        setCompiledPlanRecipe(null);setSavedPlanRecipe(null);setPlannerReviewConfirmed(false);setPlanRecipeReviewConfirmed(false);
        setLocalGraph(null);setShowActiveGraph(false);setGraphSelection('default');setBaseGraphSelection('default');
        setWorkflow({...demoWorkflow,title:"No active workflow · describe this task",nodes:[{id:"active_task_placeholder",title:"Describe this task",subtitle:"No workflow proposed or executed",kind:"input",category:"planning",group:"planning",x:120,y:150,status:"pending",authority:"Planning context only",performedBy:"User",evidence:"No execution evidence",details:null}],edges:[]});setSelectedId("active_task_placeholder");
        try { localStorage.removeItem('actioncharter:current-saved-plan:v1'); } catch { /* Optional browser persistence. */ }
      })} onRestore={resumeSavedPlan} editsPending={Boolean(editedPlan) || mode === "proposal" || executionWorkflowBusy || editBusy} currentPlan={plannerResult} currentSaved={savedPlannerResult} visible={textPlannerOpen} onClose={() => setTextPlannerOpen(false)} onPlan={(result) => { graphScopeEpoch.current++;cancelNodeLayoutDrag(); setEditedPlan(null); setWorkflowReview(null); setWorkflowAuthorization(null);  setPlannerResult(result); setPlannerReviewConfirmed(false); setSavedPlannerResult(null); setPreparedPlanApproval(null); setRecordedPlanApproval(null); setVerifiedPlanApproval(null); setPlanExecutionPreview(null); setCompiledPlanRecipe(null); setSavedPlanRecipe(null); setPlanRecipeReviewConfirmed(false); setTaskDraft(null); setWorkflow(plannerWorkflow(result)); setLocalGraph(null); setShowActiveGraph(false); setGraphSelection("live-plan"); setBaseGraphSelection("live-plan"); setSelectedId("planned_planner"); }} onSaved={(stored) => { setSavedPlannerResult(stored); setWorkflow((current) => ({ ...current, nodes: current.nodes.map((node) => node.id === "planned_policy" ? { ...node, subtitle: "Saved proposal · not approved or executed", evidence: stored.plan_filename } : node) })); void loadSavedPlans().then(setSavedPlanInventory).catch(() => { /* Saved artifact still exists if inventory refresh fails. */ }); }}/>
<IntentWorkbench onDraft={(input, request) => { if (plannerResult) return; setTaskDraft({ input, request }); setWorkflow(taskDraftWorkflow(input, request)); setLocalGraph(null); setShowActiveGraph(false); setGraphSelection("task-draft"); setBaseGraphSelection("task-draft"); setSelectedId("task_request"); }} onContinue={async (filename) => { const inventory = await loadSavedPlans(); const item = inventory.plans.find((entry) => entry.plan_filename === filename); if (!item) throw new Error("Stored plan is not in the bounded inventory. Reopen it through Saved plans."); setSavedPlanInventory(inventory); await resumeSavedPlan(item); setIntentOpen(false); setPlannerOpen(true); }} visible={intentOpen} onClose={() => setIntentOpen(false)} onInvalidate={() => { setIntentGraphResult(null); if (graphSelection === "intent-plan") { setWorkflow(demoWorkflow); setGraphSelection("default"); setBaseGraphSelection("default"); } }} onGraph={(next) => { setTaskDraft(null); setIntentGraphResult(next); setWorkflow(intentWorkflow(next)); setLocalGraph(null); setShowActiveGraph(false); setGraphSelection("intent-plan"); setBaseGraphSelection("intent-plan"); setSelectedId("planned_planner"); setJourneyStage("review"); }}/></>;
}
