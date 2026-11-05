import type { ResultViewSpec } from "../lib/result-exploration";
import { currentChatId, matchesPlanRun } from "../lib/use-plan-run";
import { startWorkflowRun, runActive, runs as workflowRuns, runSchema, type WorkflowRun } from "../lib/workflow-tools";
import { parseWorkflowExecution } from "../lib/interface-api";
import { prepareCurrentWorkflow, authorizeCurrentWorkflow, executeCurrentWorkflow, type InspectionRun } from "../lib/interface-api";
import { loadSavedPlans, loadSavedRecipes, type RecipeExecutionResult } from "../lib/interface-api";
import type {ActionContext} from './action-contracts';

export function createResultsActions(context: ActionContext) {
 const { taskTransitionBusy, editedPlan, mode, setTextPlannerOpen, setIntentOpen, setOutcomeOpen, 
  setWorkflowReviewOpen, setExecutionInventoryOpen, setRecordsOpen, setRecordsNotice, setSavedPlanInventory, 
  setRecipeInventory, graphSelection, setRunPanelOpen, setWorkflowNotice, setAuthorizationFocus, 
  savedPlannerResult, plannerResult, setWorkflowBusy, setWorkflowReview, setWorkflow, workflowAuthorization, 
  setWorkflowAuthorization, nodeDragRef, connectionDragRef, fitGraph, workflowReview, workflowBusy, 
  executionScopeRef, recordedPlan, setDirectExportRun, setWorkflowOutcomeNotice, setCurrentInspection, 
  setInspectionHistorySelection, setExecutionResult, setWorkflowRun, setOutcomeSelection, editBusy, 
  executionStartRef, 
}=context;
const openChatWorkflowHistory=()=>{if(taskTransitionBusy||editedPlan||mode==='proposal')return;setTextPlannerOpen(true);setIntentOpen(false);if(window.innerWidth<850)setOutcomeOpen(false);window.dispatchEvent(new Event('actioncharter:open-chat-history'));};

const openRecords = async () => {
    setWorkflowReviewOpen(false); setExecutionInventoryOpen(false); setOutcomeOpen(false);
    setRecordsOpen(true); setRecordsNotice("Loading saved records…");
    const results = await Promise.allSettled([loadSavedPlans(), loadSavedRecipes()]);
    if (results[0].status === "fulfilled") setSavedPlanInventory(results[0].value); else setSavedPlanInventory(null);
    if (results[1].status === "fulfilled") setRecipeInventory(results[1].value); else setRecipeInventory(null);
    setRecordsNotice(results.some((result) => result.status === "rejected") ? "Some saved records could not be loaded. Restart the updated API and refresh." : "");
  };

const openWorkflowExecution = async (authorization = false) => {
    if(graphSelection==="analytical-session"||graphSelection==="chat-history")return;
    setRunPanelOpen(false); setWorkflowReviewOpen(true); setExecutionInventoryOpen(false); setOutcomeOpen(false); setTextPlannerOpen(false); setIntentOpen(false); setWorkflowNotice(""); setAuthorizationFocus(authorization);
    if (editedPlan) { setWorkflowNotice("Validate and save block edits before execution."); return; }
    if (!savedPlannerResult) { setWorkflowNotice("Generate or restore a saved plan first."); return; }
    if (plannerResult) context.actions().viewPlannerGraph();
    setWorkflowBusy(true);
    try {
      const review = await prepareCurrentWorkflow(savedPlannerResult);
      setWorkflowReview(review);
      if (review.workflow_kind === "snakemake_export") setWorkflow((current) => ({ ...current, nodes: current.nodes.map((node) => review.steps.some((step) => `planned_${step.step_id}` === node.id && step.execution_mode === "reuse_completed") ? { ...node, status: "complete", subtitle: "Completed source · reusing evidence", performedBy: "Recorded source run", evidence: review.source_attempt_sha256 ?? review.recipe_filename } : node) }));
      if (workflowAuthorization?.review_sha256 !== review.review_sha256) setWorkflowAuthorization(null);
      if (authorization) requestAnimationFrame(() => { if (!nodeDragRef.current && !connectionDragRef.current) fitGraph(); });
      if (authorization && !review.approval_required_step_ids.length) setWorkflowNotice("No authorization required. Use Execute for this read-only inspection.");
    } catch (e) { setWorkflowReview(null); setWorkflowNotice(e instanceof Error ? e.message : "Workflow review blocked"); }
    finally { setWorkflowBusy(false); }
  };

const authorizeReviewedWorkflow = async (approver: string, reason: string) => {
    if (!workflowReview || !workflowReview.approval_required_step_ids.length || workflowBusy || editedPlan || workflowReview.plan_sha256 !== savedPlannerResult?.plan_sha256 || !approver.trim() || !reason.trim()) return;
    setWorkflowBusy(true); setAuthorizationFocus(true); setWorkflowNotice("Recording exact authorization; nothing will execute…");
    try {
      setWorkflowAuthorization(await authorizeCurrentWorkflow(workflowReview, approver.trim(), reason.trim()));
      setWorkflowNotice("Authorization recorded for 30 minutes. Click Execute to run this exact workflow.");
    } catch (e) { setWorkflowAuthorization(null); setWorkflowNotice(e instanceof Error ? e.message : "Authorization blocked"); }
    finally { setWorkflowBusy(false); }
  };

const executeReviewedWorkflow = async (review=workflowReview, authorization=workflowAuthorization) => {
    if (!review || workflowBusy || editedPlan || review.plan_sha256 !== executionScopeRef.current.sha || executionScopeRef.current.edited) return;
    if (review.approval_required_step_ids.length && authorization?.review_sha256 !== review.review_sha256) { setAuthorizationFocus(true); setWorkflowNotice("Authorize the highlighted operations before execution."); return; }
    recordedPlan.select(null);
    setDirectExportRun(null);
    const executingChat=currentChatId();
    setWorkflowBusy(true); setWorkflowNotice("Executing the exact reviewed workflow…"); setWorkflowOutcomeNotice(""); setCurrentInspection(null); setInspectionHistorySelection(null); setExecutionResult(null);
    try {
      let result: InspectionRun | RecipeExecutionResult;
      if (review.workflow_kind === "snakemake_export") {
        result = await executeCurrentWorkflow(review, authorization);
        if ('run_id' in result) setDirectExportRun({
          run_id:result.run_id,plan_sha256:result.plan_sha256,plan_filename:result.plan_filename,conversation_id:executingChat,
          status:result.status,started_at:result.started_at,finished_at:result.finished_at,cancel_requested:false,
          failed_step_id:null,finding:result.finding??null,recovery_guidance:'Inspect recorded export evidence before recovery.',
          execution_performed:result.execution_performed,result,partial_outputs:[],
          steps:result.step_results.map(step=>({...step,arguments:review.steps.find(item=>item.step_id===step.step_id)?.arguments??{},depends_on:review.steps.find(item=>item.step_id===step.step_id)?.depends_on??[]})),
        });
      }
      else {
        let run = await startWorkflowRun(review, authorization);
        setWorkflowRun(run);
        while (runActive(run)) {
          await new Promise(resolve => window.setTimeout(resolve, 700));
          run = runSchema.parse(await workflowRuns({action:"read",run_id:run.run_id}));
          setWorkflowRun(run);
        }
        if (run.status !== "completed" && run.status !== "validation_failed") {
          setRunPanelOpen(true); setWorkflowReviewOpen(false); setOutcomeOpen(false);
          throw new Error(run.finding ?? "Workflow stopped. Inspect run history before recovery.");
        }
        if (run.result == null) {
          setRunPanelOpen(true); setWorkflowReviewOpen(false); setOutcomeOpen(false);
          setWorkflowNotice("Run finished. The full result exceeds the interface budget; inspect per-step previews and durable evidence in workflow runs.");
          return;
        }
        result = parseWorkflowExecution(run.result);
      }
      if ("run_id" in result) {
        setCurrentInspection(result); setExecutionResult(null);
        if (result.workflow_kind === "snakemake_export") setWorkflow((current) => ({ ...current, nodes: current.nodes.map((node) => { const step = result.step_results.find((item) => `planned_${item.step_id}` === node.id); return step ? { ...node, status: "complete", subtitle: step.status.replaceAll("_", " "), performedBy: step.status === "reused_completed" ? "Recorded source run" : "Governed export service", evidence: result.run_id } : node; }) }));
      }
      else { setExecutionResult(result); setCurrentInspection(null); setInspectionHistorySelection(null); }
      setWorkflowReviewOpen(false); setExecutionInventoryOpen(false); setInspectionHistorySelection(null); setOutcomeSelection({view:"Overview"}); setOutcomeOpen(true); setWorkflowNotice("");
    } catch (e) { const message = e instanceof Error ? e.message : "Workflow execution failed. Inspect history before retrying."; setWorkflowNotice(message); setWorkflowOutcomeNotice(message); setWorkflowAuthorization(null); }
    finally { setWorkflowBusy(false); }
  };

const openPlannerResultView = async (spec:ResultViewSpec) => {
    const chat=currentChatId();
    if(spec.plan_sha256!==executionScopeRef.current.sha||executionScopeRef.current.edited)throw new Error('The proposed result view belongs to a different workflow.');
    const run=runSchema.parse(await workflowRuns({action:'read',run_id:spec.run_id}));
    if(currentChatId()!==chat||executionScopeRef.current.sha!==spec.plan_sha256||executionScopeRef.current.edited||!matchesPlanRun(run,spec.plan_sha256,chat))throw new Error('Workspace changed while opening recorded results. Nothing executed.');
    setWorkflowRun(run);recordedPlan.select(run);setInspectionHistorySelection(null);
    setOutcomeSelection({step:spec.step_id,view:spec.view,spec});setWorkflowReviewOpen(false);setExecutionInventoryOpen(false);setRunPanelOpen(false);setOutcomeOpen(true);
  };

const acceptSubmittedInspection = async (initial:WorkflowRun) => {
    const chat=currentChatId();
    if(initial.conversation_id!==chat)return;
    setWorkflowBusy(true);
    const matches=()=>currentChatId()===chat && !executionScopeRef.current.edited && executionScopeRef.current.sha===initial.plan_sha256;
    try{
      // Plan callbacks and this run arrive together; allow the saved scope to render.
      await new Promise(resolve=>window.setTimeout(resolve,0));
      if(!matches())return;
      recordedPlan.select(null);
      setWorkflowRun(initial);setWorkflowNotice('Inspecting the explicitly submitted dataset…');
      setCurrentInspection(null);setExecutionResult(null);setInspectionHistorySelection(null);
      let run=initial;
      let characteristicsShown=false;
      while(runActive(run)){
        await new Promise(resolve=>window.setTimeout(resolve,500));
        run=runSchema.parse(await workflowRuns({action:'read',run_id:run.run_id}));
        if(!matches())return;
        setWorkflowRun(run);
        if(!characteristicsShown&&run.steps.some(step=>{
          const value=step.outcome as {discovery?:{phase?:string}}|null;
          return value?.discovery?.phase==='verifying';
        })){
          characteristicsShown=true;
          setWorkflowReviewOpen(false);setExecutionInventoryOpen(false);setRunPanelOpen(false);
          setOutcomeSelection({view:'Overview'});setOutcomeOpen(true);
          setWorkflowNotice('Dataset characteristics are available. Full-file verification is continuing…');
        }
      }
      if(!matches())return;
      if(run.status!=='completed'||run.result==null){
        setRunPanelOpen(true);setWorkflowReviewOpen(false);setOutcomeOpen(false);
        setWorkflowNotice(run.finding??'Inspection stopped. Inspect the recorded run; nothing was retried.');return;
      }
      const result=parseWorkflowExecution(run.result);
      if('run_id' in result){setCurrentInspection(result);setExecutionResult(null);}
      else{setExecutionResult(result);setCurrentInspection(null);}
      setWorkflowReviewOpen(false);setExecutionInventoryOpen(false);setRunPanelOpen(false);
      setOutcomeSelection({view:'Overview'});setOutcomeOpen(true);setWorkflowNotice('');setWorkflowOutcomeNotice('');
    }catch(e){setWorkflowNotice(e instanceof Error?e.message:'Inspection status unavailable. Check Execution History; nothing was retried.');throw e;}
    finally{setWorkflowBusy(false);}
  };

const executeFromHeader = async () => {
    if(graphSelection==="analytical-session"||graphSelection==="chat-history")return;
    if(workflowBusy||editBusy||editedPlan||!savedPlannerResult||executionStartRef.current)return;
    executionStartRef.current=true;
    const expected={...executionScopeRef.current};
    setWorkflowBusy(true);setWorkflowNotice('Checking the exact workflow before execution…');
    try{
      const review=await prepareCurrentWorkflow(savedPlannerResult);
      if(executionScopeRef.current.sha!==expected.sha||executionScopeRef.current.chat!==expected.chat||executionScopeRef.current.edited)throw new Error('Workspace changed during preparation. Nothing executed.');
      setWorkflowReview(review);
      const authorized=workflowAuthorization?.review_sha256===review.review_sha256?workflowAuthorization:null;
      if(!review.execution_available||(review.approval_required_step_ids.length&&!authorized)){
        setWorkflowAuthorization(authorized);setWorkflowReviewOpen(true);setTextPlannerOpen(false);setIntentOpen(false);setOutcomeOpen(false);setExecutionInventoryOpen(false);setRunPanelOpen(false);setAuthorizationFocus(true);
        setWorkflowNotice(!review.execution_available?'Write operations are OFF. Enable Allow writes, then authorize this exact workflow.':'Authorize the highlighted operations, then click Execute.');
        return;
      }
      // This deliberate click runs read-only scope directly. Writes still require
      // exact existing authorization; the backend independently rechecks both.
      await context.actions().executeReviewedWorkflow(review,authorized);
    }catch(error){setWorkflowReviewOpen(true);setWorkflowNotice(error instanceof Error?error.message:'Workflow preparation failed. Nothing executed.');}
    finally{executionStartRef.current=false;setWorkflowBusy(false);}
  };
 return {openChatWorkflowHistory, openRecords, openWorkflowExecution, authorizeReviewedWorkflow, executeReviewedWorkflow, openPlannerResultView, acceptSubmittedInspection, executeFromHeader};
}
