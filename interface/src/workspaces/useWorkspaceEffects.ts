import { currentChatId, matchesPlanRun } from "../lib/use-plan-run";
import { runActive, runs as workflowRuns, runSchema } from "../lib/workflow-tools";
import { useEffect } from "react";
import { loadWorkflowCatalog, loadWorkflowProjection } from "../lib/load-workflow";
import { loadRecipeTemplates } from "../lib/load-recipe-templates";
import { loadDataResources, loadPlannerSkills, loadSavedPlans, loadTaskContext } from "../lib/interface-api";
import { demoWorkflow, templateParameterDefaults } from './model';
import type {WorkspaceModel} from './useWorkspaceModel';
import type {WorkspaceActions} from './action-contracts';

export function useWorkspaceEffects(context: WorkspaceModel & WorkspaceActions) {
 const { writePolicy, observedWritePolicy, setWorkflowAuthorization, setWorkflowReview, setWorkflowReviewOpen, 
  setWorkflowNotice, setTextPlannerOpen, setOutcomeOpen, setRunPanelOpen, workflowRun, setWorkflowRun, 
  workflowNotice, workflowReviewOpen, workflowBusy, workflowAuthorization, workflowNoticeRef, nodeFrameRef, 
  connectionFrameRef, currentTaskId, setViewedTaskId, setTaskContext, setTaskNotice, canvasWindowRef, 
  updateViewport, workflow, graphScopeEpoch, startupView, setRuns, setWorkflow, setGraphSelection, 
  setBaseGraphSelection, setLoadNotice, setRecipeTemplates, setSelectedTemplateId, setTemplateParameters, 
  setRecipeIdHint, setTemplateNotice, templatePanelOpen, plannerOpen, dataResources, setDataResources, 
  setPlannerSkills, setPlannerNotice, plannerSkills, setSavedPlanInventory, plannerRequestDebounceRef, 
  orientation, zoom, fitGraph, displayedWorkflow, refreshGraphSources, savedPlannerResult, setDraggingNodeId, 
  nodeDragRef, pendingNodePosition, graphSelection, editedPlan, setConnectionsOpen, setOperationTarget, 
  setConnectionToRemove, submittedInspection, setSubmittedInspection, acceptSubmittedInspection, 
}=context;
useEffect(()=>{
    if(!writePolicy?.active)return;
    const identity=`${writePolicy.session_id}:${writePolicy.revision}`;
    if(observedWritePolicy.current&&observedWritePolicy.current!==identity){
      setWorkflowAuthorization(null);setWorkflowReview(null);setWorkflowReviewOpen(false);
      setWorkflowNotice('Write availability changed. Review the workflow and record fresh authorization before writing.');
    }
    observedWritePolicy.current=identity;
  },[writePolicy?.session_id,writePolicy?.revision]);
useEffect(()=>{
    const openGoalAdvice=()=>{setTextPlannerOpen(true);setOutcomeOpen(false);setRunPanelOpen(false);};
    window.addEventListener('actioncharter:planner-propose-goals',openGoalAdvice);
    return()=>window.removeEventListener('actioncharter:planner-propose-goals',openGoalAdvice);
  },[]);
useEffect(()=>{
    if(!workflowRun?.agent_mode||runActive(workflowRun)||!['queued','running'].includes(workflowRun.critic_review?.status??''))return;
    const identity=workflowRun.run_id;let active=true;
    const timer=window.setTimeout(()=>{void workflowRuns({action:'read',run_id:identity}).then(value=>{const next=runSchema.parse(value);if(active)setWorkflowRun(current=>current?.run_id===identity?next:current);}).catch(()=>{});},700);
    return()=>{active=false;window.clearTimeout(timer);};
  },[workflowRun]);
useEffect(() => { if (workflowNotice && workflowReviewOpen && !workflowBusy && !workflowAuthorization) workflowNoticeRef.current?.scrollIntoView({ block: "nearest", behavior: "auto" }); }, [workflowNotice, workflowReviewOpen, workflowBusy, workflowAuthorization]);
useEffect(() => () => { if (nodeFrameRef.current !== null) cancelAnimationFrame(nodeFrameRef.current); if (connectionFrameRef.current !== null) cancelAnimationFrame(connectionFrameRef.current); }, []);
useEffect(() => {
    if (!currentTaskId) return;
    setViewedTaskId(currentTaskId);
    void loadTaskContext(currentTaskId).then((context) => setTaskContext((current) =>
      current?.task_id === context.task_id && current.event_count > context.event_count ? current : context,
    )).catch(() => setTaskNotice("Task context could not be reopened."));
  }, [currentTaskId]);
useEffect(() => {
    const element = canvasWindowRef.current;
    if (!element) return;
    const observer = new ResizeObserver(updateViewport);
    observer.observe(element);
    updateViewport();
    return () => observer.disconnect();
  }, [updateViewport]);
useEffect(() => {
    let active=true;
    const initialWorkflow=workflow, initialChat=currentChatId(),initialEpoch=graphScopeEpoch.current;
    const unchanged=()=>active&&graphScopeEpoch.current===initialEpoch&&currentChatId()===initialChat&&startupView.current.workflow===initialWorkflow&&startupView.current.graphSelection==='default'&&startupView.current.mode==='evidence';
    void (async () => {
      const catalog = await loadWorkflowCatalog();
      if(!active)return;
      setRuns(catalog);
      try {
        const projection=await loadWorkflowProjection(demoWorkflow,catalog[0]?.taskId);
        if(!unchanged())return;
        // A delayed startup projection must not replace a restored chat or edits.
        setWorkflow(current=>current===initialWorkflow?projection:current);
        if(catalog.length){
          setGraphSelection(current=>current==='default'?`trace:${catalog[0].taskId}`:current);
          setBaseGraphSelection(current=>current==='default'?`trace:${catalog[0].taskId}`:current);
        }
        setLoadNotice('');
      } catch {
        if(unchanged())setLoadNotice('Selected run could not be loaded. Re-export the runtime projections.');
      }
    })();
    return()=>{active=false;};
  }, []);
useEffect(() => {
    void loadRecipeTemplates().then((templates) => {
      setRecipeTemplates(templates);
      setSelectedTemplateId(templates[0]?.template_id ?? "");
      setTemplateParameters(templateParameterDefaults(templates[0]));
      setRecipeIdHint(templates[0] ? `${templates[0].template_id}_proposal` : "");
      setTemplateNotice("");
    }).catch(() => setTemplateNotice("Export the trusted recipe catalog before using templates."));
  }, []);
useEffect(() => {
    if ((!templatePanelOpen && !plannerOpen) || dataResources) return;
    void loadDataResources().then(setDataResources).catch(() => setTemplateNotice("Project data could not be listed. Manual relative paths remain available."));
  }, [dataResources, plannerOpen, templatePanelOpen]);
useEffect(() => {
    const refresh=()=>{void loadPlannerSkills().then(setPlannerSkills).catch(()=>setPlannerNotice("Operation registry refresh failed; reopen Settings or refresh the page."));};
    window.addEventListener("actioncharter:operations-changed",refresh);
    return()=>window.removeEventListener("actioncharter:operations-changed",refresh);
  }, []);
useEffect(() => {
    if (plannerSkills) return;
    setPlannerNotice("Loading implemented skills from the trusted registry…");
    void loadPlannerSkills().then((catalog) => {
      setPlannerSkills(catalog);
      setPlannerNotice("");
    }).catch(() => setPlannerNotice("Planner skills could not be loaded. Confirm that the local interface service is running."));
  }, [plannerOpen, plannerSkills]);
useEffect(() => {
    if (!plannerOpen) return;
    void loadSavedPlans().then(setSavedPlanInventory).catch(() => setSavedPlanInventory(null));
  }, [plannerOpen]);
useEffect(() => () => {
    if (plannerRequestDebounceRef.current !== null) window.clearTimeout(plannerRequestDebounceRef.current);
  }, []);
useEffect(() => { requestAnimationFrame(updateViewport); }, [orientation, updateViewport, zoom]);
useEffect(() => { const frame = requestAnimationFrame(fitGraph); return () => cancelAnimationFrame(frame); }, [displayedWorkflow.id, orientation]);
useEffect(() => {
    void refreshGraphSources();
  }, []);
useEffect(() => {
    if (!savedPlannerResult) return;
    try { localStorage.setItem("actioncharter:current-saved-plan:v1", savedPlannerResult.plan_sha256); } catch { /* Optional storage. */ }
  }, [savedPlannerResult?.plan_sha256]);
useEffect(() => { setDraggingNodeId(null); return () => { nodeDragRef.current?.preview.finish(); nodeDragRef.current = null; pendingNodePosition.current = null; if (nodeFrameRef.current !== null) { cancelAnimationFrame(nodeFrameRef.current); nodeFrameRef.current = null; } }; }, [displayedWorkflow.id, graphSelection, orientation]);
useEffect(() => { setWorkflowAuthorization(null); }, [savedPlannerResult?.plan_sha256, editedPlan]);
useEffect(() => { setConnectionsOpen(false); setOperationTarget(""); setConnectionToRemove(""); }, [savedPlannerResult?.plan_sha256]);
useEffect(()=>{
    if(!submittedInspection)return;
    const run=submittedInspection;
    setSubmittedInspection(null);
    if(!matchesPlanRun(run,savedPlannerResult?.plan_sha256,currentChatId())||editedPlan){
      setWorkflowNotice('The submitted inspection belongs to a different workspace scope. Its run is preserved in Execution History.');return;
    }
    void acceptSubmittedInspection(run).catch(()=>{/* Recorded run remains available for read-only recovery. */});
  },[submittedInspection,savedPlannerResult?.plan_sha256,Boolean(editedPlan)]);
}
