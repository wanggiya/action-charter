import { loadWorkflowCatalog, loadWorkflowProjection } from "../lib/load-workflow";
import { loadCriticEvidence, loadExecutionInventory, loadExecutionProgress, loadSavedPlans, loadSavedRecipes } from "../lib/interface-api";
import { type Workflow as WorkflowData } from "../lib/workflow";
import { JourneyStage, demoWorkflow, plannerWorkflow, savedRecipeWorkflow, durableRunWorkflow, taskDraftWorkflow, intentWorkflow } from './model';
import type {ActionContext} from './action-contracts';

export function createSourcesActions(context: ActionContext) {
 const { setRunPanelOpen, setWorkflowReviewOpen, setOutcomeOpen, setTemplatePanelOpen, setExecutionInventoryOpen, 
  setCriticOpen, setRecipePanelOpen, setPlannerOpen, setIntentOpen, setTextPlannerOpen, plannerResult, 
  setSavedPlanInventory, journeyStage, activeRecipe, savedPlanRecipe, setJourneyStage, setShowActiveGraph, 
  setLocalGraph, setGraphSelection, setInspectionHistorySelection, setRecipeInventory, setExecutionInventory, 
  setRuns, setLoadNotice, historicalProjection, setSelectedId, analyticalProjection, setInspectorClosed, 
  taskDraft, intentGraphResult, savedPlanInventory, recipeInventory, executionInventory, setCriticInventory, 
  setWorkflow, setBaseGraphSelection, setActiveRecipe, graphSelection, baseGraphSelection, 
  setPreparedApproval, setRecordedApproval, setApprovalVerification, setApprovalVerificationNotice, 
  setExecutionPreview, setExecutionConfirmed, setExecutionResult, setExecutionNotice, setExecutionFailure, 
  setExecutionProgress, setApprovalConfirmed, setApprovalDecisionNotice, setApprovalDecision, setDraft, 
  setMode, workflow, 
}=context;
const openJourneyStage = (stage: JourneyStage) => {
    setRunPanelOpen(false);
    setWorkflowReviewOpen(false); setOutcomeOpen(false);
    if (stage === "plan") {
      setTemplatePanelOpen(false);
      setExecutionInventoryOpen(false);
      setCriticOpen(false);
      setRecipePanelOpen(false);
      setPlannerOpen(false);
      setIntentOpen(false);
      setTextPlannerOpen(true);
      if (plannerResult) context.actions().viewPlannerGraph();
      void loadSavedPlans().then(setSavedPlanInventory).catch(() => setSavedPlanInventory(null));
    } else if (stage === "review") {
      if (journeyStage !== "review") void context.actions().refreshGraphSources();
      setPlannerOpen(false);
      setTemplatePanelOpen(false);
      setRecipePanelOpen(false);
      setExecutionInventoryOpen(false);
      setCriticOpen(false);
    } else if (stage === "run") {
      if (!activeRecipe) {
        if (plannerResult && !savedPlanRecipe) {
          setTemplatePanelOpen(false);
          setExecutionInventoryOpen(false);
          setCriticOpen(false);
          setRecipePanelOpen(false);
          setPlannerOpen(true);
          void loadSavedPlans().then(setSavedPlanInventory).catch(() => setSavedPlanInventory(null));
          setJourneyStage(stage);
          return;
        }
        setPlannerOpen(false);
        setTemplatePanelOpen(false);
        setExecutionInventoryOpen(false);
        setCriticOpen(false);
        void context.actions().openSavedRecipes(savedPlanRecipe?.recipe_sha256 ?? "");
        setJourneyStage(stage);
        return;
      }
      setPlannerOpen(false);
      setTemplatePanelOpen(false);
      setExecutionInventoryOpen(false);
      setCriticOpen(false);
      setRecipePanelOpen(true);
      setShowActiveGraph(true);
      setLocalGraph(null);
      setGraphSelection("active");
    } else {
      setInspectionHistorySelection(null); setOutcomeOpen(true);
    }
    setJourneyStage(stage);
  };

const refreshGraphSources = async () => {
    const [plans, recipes, attempts, traces] = await Promise.allSettled([
      loadSavedPlans(), loadSavedRecipes(), loadExecutionInventory(), loadWorkflowCatalog(),
    ]);
    if (plans.status === "fulfilled") setSavedPlanInventory(plans.value);
    if (recipes.status === "fulfilled") setRecipeInventory(recipes.value);
    if (attempts.status === "fulfilled") setExecutionInventory(attempts.value);
    if (traces.status === "fulfilled") setRuns(traces.value);
    if ([plans, recipes, attempts, traces].some((result) => result.status === "rejected")) {
      setLoadNotice("Some local graph sources could not be loaded. Check the interface API and refresh the list.");
    }
  };

const selectGraphSource = async (key: string) => {
    if(key==='chat-history'&&historicalProjection){setGraphSelection(key);setSelectedId(historicalProjection.nodes[0].id);return;}
    if(key==='analytical-session'&&analyticalProjection){setGraphSelection(key);setSelectedId('analytical_summary');setInspectorClosed(false);setLoadNotice('Recorded read-only analytical actions · no data writes or workflow dispatch');return;}
    if (key === "active") {
      if (!activeRecipe) return;
      setLocalGraph(null);
      setShowActiveGraph(true);
      setSelectedId("active_executor");
    } else {
      let next: WorkflowData;
      try {
        if (key === "task-draft" && taskDraft) next = taskDraftWorkflow(taskDraft.input, taskDraft.request);
        else if (key === "intent-plan" && intentGraphResult) next = intentWorkflow(intentGraphResult);
        else if (key === "live-plan" && plannerResult) next = plannerWorkflow(plannerResult);
        else if (key.startsWith("plan:")) {
          const item = savedPlanInventory?.plans.find((plan) => plan.plan_sha256 === key.slice(5));
          if (!item) throw new Error("Saved plan is no longer listed. Refresh graph sources.");
          await context.actions().resumeSavedPlan(item);
          setLoadNotice(""); context.actions().openJourneyStage("review"); return;
        } else if (key.startsWith("recipe:")) {
          const item = recipeInventory?.recipes.find((recipe) => recipe.recipe_sha256 === key.slice(7));
          if (!item) throw new Error("Saved recipe is no longer listed. Refresh graph sources.");
          next = savedRecipeWorkflow(item);
        } else if (key.startsWith("run:")) {
          setLoadNotice("Checking exact run, Critic, and release links…");
          const digest = key.slice(4);
          const item = executionInventory?.attempts.find((attempt) => attempt.execution_preview_sha256 === digest);
          if (!item) throw new Error("Durable run is no longer listed. Refresh graph sources.");
          const [progress, assurance] = await Promise.all([
            loadExecutionProgress(digest), loadCriticEvidence().catch(() => null),
          ]);
          if (!progress || progress.execution_preview_sha256 !== digest) throw new Error("Durable run could not be loaded.");
          if (assurance) setCriticInventory(assurance);
          next = durableRunWorkflow(progress, item, assurance, recipeInventory?.recipes.find((recipe) => recipe.recipe_sha256 === progress.recipe_sha256));
        } else if (key === "default") next = await loadWorkflowProjection(demoWorkflow);
        else if (key.startsWith("trace:")) next = await loadWorkflowProjection(demoWorkflow, key.slice(6));
        else throw new Error("Graph source is unavailable.");
      } catch (error) {
        setLoadNotice(error instanceof Error ? error.message : "Graph source could not be loaded.");
        return;
      }
      context.actions().cancelNodeLayoutDrag();
      setLocalGraph(key === "default" || key.startsWith("trace:") ? null : next);
      if (key === "default" || key.startsWith("trace:")) setWorkflow(next);
      if (key === "default" || key.startsWith("trace:")) setBaseGraphSelection(key);
      setShowActiveGraph(false);
      setSelectedId(next.nodes[0].id);
    }
    setGraphSelection(key);
    setLoadNotice("");
    context.actions().openJourneyStage("review");
  };

const closeRecipeFlow = () => {
    setRecipePanelOpen(false);
  };

const exitActiveWorkflow = () => {
    setRecipePanelOpen(false);
    setTemplatePanelOpen(false);
    setActiveRecipe(null);
    setShowActiveGraph(true);
    if (graphSelection === "active") setGraphSelection(baseGraphSelection);
    setPreparedApproval(null);
    setRecordedApproval(null);
    setApprovalVerification(null);
    setApprovalVerificationNotice("");
    setExecutionPreview(null);
    setExecutionConfirmed(false);
    setExecutionResult(null);
    setExecutionNotice("");
    setExecutionFailure("");
    setExecutionProgress(null);
    setApprovalConfirmed(false);
    setApprovalDecisionNotice("");
    setApprovalDecision("approved");
    setDraft(null);
    setMode("evidence");
    setSelectedId(workflow.nodes[0].id);
  };
 return {openJourneyStage, refreshGraphSources, selectGraphSource, closeRecipeFlow, exitActiveWorkflow};
}
