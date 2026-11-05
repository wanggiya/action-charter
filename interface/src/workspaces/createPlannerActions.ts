import { saveGeneratedPlannerPlan } from "../lib/interface-api";
import { compilePlannerRecipe, createPlannerPlan, PlannerRequestError, loadSavedPlans, loadTaskContext, recordTaskEvent, preparePlannerApproval, previewPlannerExecution, recordPlannerApproval, saveCompiledPlannerRecipe, saveReviewedPlannerPlan, verifyPlannerApproval, type InterfacePlannerResult, type SavedPlanInventory, type SavedPlannerResult } from "../lib/interface-api";
import { plannerWorkflow, readablePlannerRequest } from './model';
import type {ActionContext} from './action-contracts';

export function createPlannerActions(context: ActionContext) {
 const { plannerRequestRef, plannerRequest, setPlannerNotice, selectedPlannerSkills, setPlannerRequest, 
  setPlannerPending, setPlannerRetryAvailable, setPlannerResult, setPlannerReviewConfirmed, 
  setSavedPlannerResult, setPreparedPlanApproval, setRecordedPlanApproval, setVerifiedPlanApproval, 
  setPlanExecutionPreview, setPlanPreviewError, setCompiledPlanRecipe, setPlanRecipeReviewConfirmed, 
  setSavedPlanRecipe, setPlanRecipeSaveError, setCurrentTaskId, setViewedTaskId, setTaskContext, 
  setTaskNotice, selectedPlannerInputs, setMode, setDraft, setEditedPlan, setPendingParameters, 
  setWorkflowReview, setWorkflowAuthorization, setWorkflowReviewOpen, setExecutionInventoryOpen, 
  setOutcomeOpen, setWorkflow, setLocalGraph, setShowActiveGraph, setGraphSelection, setBaseGraphSelection, 
  setSelectedId, setSelectedSavedPlanSha, setSelectedPlannerSkills, setPlannerSkillSearch, 
  setSavedPlansExpanded, plannerResult, plannerReviewConfirmed, plannerSavePending, savedPlannerResult, 
  setPlannerSavePending, currentTaskId, setSavedPlanInventory, planApprovalPending, setPlanApprovalPending, 
  preparedPlanApproval, planDecisionPending, recordedPlanApproval, planValidMinutes, planApprover, 
  planReason, setPlanDecisionPending, planDecision, planVerificationPending, setPlanVerificationPending, 
  setPlanDecision, setPlanReason, setPlanValidMinutes, verifiedPlanApproval, planPreviewPending, 
  setPlanPreviewPending, planRecipePending, setPlanRecipePending, compiledPlanRecipe, 
  planRecipeReviewConfirmed, planRecipeSavePending, setPlanRecipeSavePending, plannerPending, 
  setPlannerSkillHighlight, plannerSkillResults, plannerSkillHighlight, plannerSkillSearch, setPlannerOpen, 
  setJourneyStage, setCurrentInspection, setInspectionHistorySelection, setExecutionResult, setEditNotice, 
  plannerGuide, 
}=context;
const createPlan = async () => {
    const submittedRequest = plannerRequestRef.current?.value.trim() ?? plannerRequest.trim();
    if (!submittedRequest) {
      setPlannerNotice("Enter a task request before generating a plan.");
      return;
    }
    if (!selectedPlannerSkills.length) return;
    setPlannerRequest(submittedRequest);
    setPlannerPending(true);
    setPlannerRetryAvailable(false);
    setPlannerResult(null);
    setPlannerReviewConfirmed(false);
    setSavedPlannerResult(null);
    setPreparedPlanApproval(null);
    setRecordedPlanApproval(null);
    setVerifiedPlanApproval(null);
    setPlanExecutionPreview(null);
    setPlanPreviewError("");
    setCompiledPlanRecipe(null);
    setPlanRecipeReviewConfirmed(false);
    setSavedPlanRecipe(null);
    setPlanRecipeSaveError("");
    setPlannerNotice("Planner agent is building and validating a planning-only workflow through the configured model service…");
    setCurrentTaskId(null);
    setViewedTaskId(null);
    try { window.sessionStorage.removeItem("actioncharter:currentTaskId"); } catch { /* Storage may be unavailable. */ }
    setTaskContext(null);
    setTaskNotice("");
    let taskId: string | null = null;
    try {
      const requestEvent = await recordTaskEvent("request", submittedRequest.slice(0, 1000), undefined, submittedRequest);
      taskId = requestEvent.task_id;
      setCurrentTaskId(taskId);
      try { window.sessionStorage.setItem("actioncharter:currentTaskId", taskId); } catch { /* Context remains available through its task ID. */ }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Task history is unavailable.";
      setTaskNotice(message);
      setPlannerNotice(`Task request was not recorded: ${message} Planning did not start.`);
      setPlannerPending(false);
      return;
    }
    try {
      const selection = `Selected skills: ${selectedPlannerSkills.join(", ")}. Inputs: ${selectedPlannerInputs.join(", ") || "none selected"}.`;
      await recordTaskEvent("selection", selection.slice(0, 1000), taskId, selection.slice(0, 8000));
      setTaskContext(await loadTaskContext(taskId));
    } catch (error) {
      setTaskNotice(error instanceof Error ? `Task was created, but selection/context could not be recorded: ${error.message}` : "Task was created, but selection/context could not be recorded.");
    }
    try {
      const result = await createPlannerPlan(submittedRequest, selectedPlannerSkills, selectedPlannerInputs);
      setPlannerResult(result);
      setPlannerNotice("Validated plan returned. Nothing was saved, approved, or executed.");
      if (taskId) await context.actions().appendCurrentTaskEvent(taskId, "outcome", `Validated planning-only proposal ${result.plan_sha256}. Nothing approved or executed.`);
    } catch (error) {
      if (error instanceof PlannerRequestError) {
        setPlannerNotice(`${error.detail.error}: ${error.detail.finding} ${error.detail.retry_guidance} Nothing was saved, approved, or executed.`);
        setPlannerRetryAvailable(error.detail.retryable);
      } else {
        setPlannerNotice(error instanceof Error ? error.message : "Planner could not produce a validated plan.");
      }
      if (taskId) await context.actions().appendCurrentTaskEvent(taskId, "failure", "Planner did not return a validated plan. Nothing approved or executed.");
    } finally {
      setPlannerPending(false);
    }
  };

const resumeSavedPlan = async (item: SavedPlanInventory["plans"][number]) => {
    context.actions().cancelNodeLayoutDrag();
    setMode("evidence"); setDraft(null); setEditedPlan(null); setPendingParameters({});
    setWorkflowReview(null); setWorkflowAuthorization(null); setWorkflowReviewOpen(false);
    setExecutionInventoryOpen(false); setOutcomeOpen(false);
    setWorkflow(plannerWorkflow(item.planner_result)); setLocalGraph(null); setShowActiveGraph(false);
    setGraphSelection("live-plan"); setBaseGraphSelection("live-plan"); setSelectedId("planned_planner");
    setCurrentTaskId(null);
    setViewedTaskId(null);
    try { window.sessionStorage.removeItem("actioncharter:currentTaskId"); } catch { /* Storage may be unavailable. */ }
    setTaskContext(null);
    setTaskNotice("Existing saved plans do not have a task-history link yet.");
    setSelectedSavedPlanSha(item.plan_sha256);
    setPlannerNotice("Restoring the exact saved plan and matching decision evidence…");
    const allowed = [...new Set(item.planner_result.plan.steps.map((step) => step.skill))];
    const displayedRequest = readablePlannerRequest(item.planner_result.original_request);
    setPlannerRequest(displayedRequest);
    requestAnimationFrame(() => {
      if (plannerRequestRef.current) plannerRequestRef.current.value = displayedRequest;
    });
    setSelectedPlannerSkills(allowed);
    setPlannerSkillSearch("");
    const result: InterfacePlannerResult = { schema_version: "1.0", status: "planned_not_saved", ...item.planner_result, allowed_skill_ids: allowed, plan_sha256: item.plan_sha256, plan_saved: false, approval_performed: false, execution_performed: false };
    const stored: SavedPlannerResult = { schema_version: "1.0", status: "already_stored", plan_sha256: item.plan_sha256, plan_filename: item.plan_filename, plan_saved: true, plan_modified: false, approval_performed: false, execution_performed: false };
    setPlannerResult(result); setSavedPlannerResult(stored); setPlannerReviewConfirmed(true); setVerifiedPlanApproval(null); setPlanExecutionPreview(null); setPlanPreviewError(""); setCompiledPlanRecipe(null); setPlanRecipeReviewConfirmed(false); setSavedPlanRecipe(null); setPlanRecipeSaveError("");
    try {
      const prepared = await preparePlannerApproval(stored); setPreparedPlanApproval(prepared);
      const latest = item.approvals.at(-1);
      if (latest) setRecordedPlanApproval({ schema_version: "1.0", status: "recorded", decision: latest.decision, approval_id: latest.approval_id, approval_filename: latest.approval_filename, plan_sha256: item.plan_sha256, approved_step_ids: latest.decision === "approved" ? latest.step_ids : [], expires_at: latest.expires_at, secrets_redacted: true, approval_recorded: true, execution_performed: false });
      else setRecordedPlanApproval(null);
      setSavedPlansExpanded(false);
      setPlannerNotice(latest ? "Saved plan and latest append-only decision restored. Verify it before preview." : "Saved plan restored. No recorded decision was found.");
    } catch (error) { setPlannerNotice(error instanceof Error ? error.message : "Saved plan could not be restored."); }
  };

const savePlannerPlan = async () => {
    if (!plannerResult || !plannerReviewConfirmed || plannerSavePending || savedPlannerResult) return;
    setPlannerSavePending(true);
    setPlannerNotice("Revalidating the exact plan and confirmed digest before immutable storage…");
    try {
      const stored = await saveReviewedPlannerPlan(plannerResult, currentTaskId);
      setSavedPlannerResult(stored);
      if (stored.task_reference?.status === "failed") setTaskNotice(stored.task_reference.reason ?? "Task reference could not be recorded.");
      else if (currentTaskId) void loadTaskContext(currentTaskId).then(setTaskContext).catch(() => setTaskNotice("Task context could not be reopened."));

      void loadSavedPlans().then(setSavedPlanInventory).catch(() => setSavedPlanInventory(null));
      setPlannerNotice(stored.status === "already_stored"
        ? "Exact reviewed plan was already stored. The artifact was not modified; approval preparation is now available."
        : "Reviewed plan stored immutably. It is not approved and was not executed.");
    } catch (error) {
      setPlannerNotice(error instanceof Error ? error.message : "Reviewed plan could not be stored.");
    } finally {
      setPlannerSavePending(false);
    }
  };

const preparePlanApproval = async () => {
    if (!savedPlannerResult || planApprovalPending) return;
    setPlanApprovalPending(true);
    setPlannerNotice("Re-reading the immutable plan and deriving exact approval scope…");
    try {
      const prepared = await preparePlannerApproval(savedPlannerResult);
      setPreparedPlanApproval(prepared);
      setPlannerNotice(prepared.status === "approval_not_required"
        ? "This plan has no approval-required steps. No decision was recorded."
        : "Exact approval request prepared. No decision was recorded and nothing was executed.");
    } catch (error) {
      setPlannerNotice(error instanceof Error ? error.message : "Plan approval request could not be prepared.");
    } finally {
      setPlanApprovalPending(false);
    }
  };

const recordPlanDecision = async () => {
    if (!savedPlannerResult || !preparedPlanApproval || preparedPlanApproval.status !== "prepared_not_recorded" || planDecisionPending || recordedPlanApproval) return;
    const minutes = planValidMinutes.trim() ? Number(planValidMinutes) : null;
    if (!planApprover.trim() || !planReason.trim()) { setPlannerNotice("Approver and reason are required."); return; }
    if (minutes !== null && (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440)) { setPlannerNotice("Expiration must be a whole number from 1 to 1440 minutes."); return; }
    setPlanDecisionPending(true);
    setPlannerNotice("Revalidating the immutable plan and prepared request before append-only recording…");
    try {
      const recorded = await recordPlannerApproval({ taskId: currentTaskId, stored: savedPlannerResult, prepared: preparedPlanApproval, decision: planDecision, approver: planApprover.trim(), reason: planReason.trim(), validForMinutes: minutes });
      setRecordedPlanApproval(recorded);
      void loadSavedPlans().then(setSavedPlanInventory).catch(() => setSavedPlanInventory(null));
      setPlannerNotice(`${recorded.decision === "approved" ? "Approval" : "Denial"} recorded. Nothing was executed.`);
      if (currentTaskId) await context.actions().appendCurrentTaskEvent(currentTaskId, "decision", `Plan ${recorded.decision} recorded as ${recorded.approval_filename}. History entry is not approval authority.`);
      if (recorded.task_reference?.status === "failed") setTaskNotice(recorded.task_reference.reason ?? "Task reference could not be recorded.");
    } catch (error) {
      setPlannerNotice(error instanceof Error ? error.message : "Plan decision could not be recorded.");
    } finally { setPlanDecisionPending(false); }
  };

const verifyPlanDecision = async () => {
    if (!savedPlannerResult || !preparedPlanApproval || !recordedPlanApproval || planVerificationPending) return;
    setPlanVerificationPending(true);
    setPlannerNotice("Independently re-reading immutable plan and approval evidence…");
    try {
      const verified = await verifyPlannerApproval(savedPlannerResult, preparedPlanApproval, recordedPlanApproval);
      setVerifiedPlanApproval(verified);
      setPlannerNotice(verified.approved ? "Recorded plan approval independently verified. Nothing was executed." : `Execution remains blocked: ${verified.reason}`);
    } catch (error) { setPlannerNotice(error instanceof Error ? error.message : "Plan approval verification failed."); }
    finally { setPlanVerificationPending(false); }
  };

const beginFreshPlanDecision = () => {
    setRecordedPlanApproval(null);
    setVerifiedPlanApproval(null);
    setPlanDecision("approved");
    setPlanReason("");
    setPlanValidMinutes("");
    setPlanExecutionPreview(null);
    setPlanPreviewError("");
    setCompiledPlanRecipe(null);
    setPlanRecipeReviewConfirmed(false);
    setSavedPlanRecipe(null);
    setPlanRecipeSaveError("");
    setPlannerNotice("Expired approval evidence was preserved. Record a fresh append-only decision for the same prepared scope.");
  };

const previewPlanExecution = async () => {
    if (!savedPlannerResult || !preparedPlanApproval || !recordedPlanApproval || !verifiedPlanApproval?.approved || planPreviewPending) return;
    setPlanPreviewPending(true); setPlanPreviewError(""); setPlannerNotice("Building the exact non-executing Planner envelope…");
    try { const preview = await previewPlannerExecution(savedPlannerResult, preparedPlanApproval, recordedPlanApproval); setPlanExecutionPreview(preview); setPlannerNotice("Exact execution envelope previewed. Execution remains unavailable."); }
    catch (error) { const message = error instanceof Error ? error.message : "Execution preview failed."; setPlanPreviewError(message); setPlannerNotice(""); }
    finally { setPlanPreviewPending(false); }
  };

const compilePlanRecipe = async () => {
    if (!savedPlannerResult || !preparedPlanApproval || !recordedPlanApproval || !verifiedPlanApproval?.approved || planRecipePending) return;
    setPlanRecipePending(true); setPlanPreviewError("");
    try { setCompiledPlanRecipe(await compilePlannerRecipe(savedPlannerResult, preparedPlanApproval, recordedPlanApproval)); setPlanRecipeReviewConfirmed(false); setSavedPlanRecipe(null); setPlanRecipeSaveError(""); }
    catch (error) { setPlanPreviewError(error instanceof Error ? error.message : "Planner recipe compilation failed."); }
    finally { setPlanRecipePending(false); }
  };

const savePlanRecipe = async () => {
    if (!compiledPlanRecipe || !savedPlannerResult || !preparedPlanApproval || !recordedPlanApproval || !planRecipeReviewConfirmed || planRecipeSavePending) return;
    setPlanRecipeSavePending(true); setPlanRecipeSaveError("");
    try {
      const saved = await saveCompiledPlannerRecipe(compiledPlanRecipe, savedPlannerResult, preparedPlanApproval, recordedPlanApproval, currentTaskId);
      setSavedPlanRecipe(saved);
      if (saved.task_reference?.status === "failed") setTaskNotice(saved.task_reference.reason ?? "Recipe reference could not be recorded.");
      else if (currentTaskId) {
        setViewedTaskId(currentTaskId);
        void loadTaskContext(currentTaskId).then(setTaskContext).catch(() => setTaskNotice("Task context could not be reopened."));
      }
      setPlannerNotice("Reviewed Planner recipe stored immutably. Separate recipe approval is still required.");
    } catch (error) { setPlanRecipeSaveError(error instanceof Error ? error.message : "Reviewed Planner recipe could not be saved."); }
    finally { setPlanRecipeSavePending(false); }
  };

const togglePlannerSkill = (skillId: string) => {
    if (plannerPending) return;
    setSelectedPlannerSkills((current) => current.includes(skillId)
      ? current.filter((item) => item !== skillId)
      : [...current, skillId]);
    setPlannerResult(null);
    setPlannerReviewConfirmed(false);
    setSavedPlannerResult(null);
    setPreparedPlanApproval(null);
    setRecordedPlanApproval(null);
    setVerifiedPlanApproval(null);
    setPlanExecutionPreview(null);
    setPlanPreviewError("");
    setCompiledPlanRecipe(null);
    setPlanRecipeReviewConfirmed(false);
    setSavedPlanRecipe(null);
    setPlanRecipeSaveError("");
    setPlannerNotice("");
  };

const navigatePlannerSkills = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setPlannerSkillHighlight((current) => Math.min(current + 1, Math.max(0, plannerSkillResults.length - 1)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setPlannerSkillHighlight((current) => Math.max(0, current - 1));
    } else if (event.key === "Enter" && plannerSkillResults[plannerSkillHighlight]) {
      event.preventDefault();
      context.actions().togglePlannerSkill(plannerSkillResults[plannerSkillHighlight].id);
    } else if (event.key === "Backspace" && !plannerSkillSearch && selectedPlannerSkills.length) {
      context.actions().togglePlannerSkill(selectedPlannerSkills[selectedPlannerSkills.length - 1]);
    } else if (event.key === "Escape") {
      event.currentTarget.blur();
    }
  };

const viewPlannerGraph = () => {
    if (!plannerResult) return;
    context.actions().cancelNodeLayoutDrag();
    const next = plannerWorkflow(plannerResult);
    if (savedPlannerResult) next.nodes = next.nodes.map((node) => node.id === "planned_policy" ? { ...node, subtitle: "Saved proposal · not approved or executed", evidence: savedPlannerResult.plan_filename } : node);
    setWorkflow(next);
    setLocalGraph(null);
    setShowActiveGraph(false);
    setGraphSelection("live-plan");
    setBaseGraphSelection("live-plan");
    setSelectedId("planned_planner");
    setPlannerOpen(false);
    setJourneyStage("review");
  };

const acceptReusablePlan = async (result: InterfacePlannerResult) => {
    const stored = await saveGeneratedPlannerPlan(result);
    const previousPlanSha = plannerResult?.plan_sha256;
    context.actions().cancelNodeLayoutDrag();
    setPlannerResult(result); setSavedPlannerResult(stored); setEditedPlan(null); setPendingParameters({});
    setWorkflowReview(null); setWorkflowAuthorization(null); setPreparedPlanApproval(null); setRecordedPlanApproval(null);
    setVerifiedPlanApproval(null); setCompiledPlanRecipe(null); setSavedPlanRecipe(null); setPlanExecutionPreview(null);
    setCurrentInspection(null); setInspectionHistorySelection(null); setExecutionResult(null); setWorkflowReviewOpen(false); setOutcomeOpen(false);
    setWorkflow(plannerWorkflow(result)); setLocalGraph(null); setShowActiveGraph(false); setGraphSelection("live-plan"); setBaseGraphSelection("live-plan");
    setSelectedId("planned_planner"); setMode("evidence"); setDraft(null);
    window.dispatchEvent(new CustomEvent("actioncharter:conversation-workflow-edited", {detail:{previousPlanSha,result,bindToCurrentConversation:true}}));
    void loadSavedPlans().then(setSavedPlanInventory).catch(()=>setEditNotice("Plan saved; inventory refresh unavailable."));
  };

const focusPlannerGuide = () => {
    document.querySelector<HTMLElement>(`.planner-workspace ${plannerGuide.target}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
 return {createPlan, resumeSavedPlan, savePlannerPlan, preparePlanApproval, recordPlanDecision, verifyPlanDecision, beginFreshPlanDecision, previewPlanExecution, compilePlanRecipe, savePlanRecipe, togglePlannerSkill, navigatePlannerSkills, viewPlannerGraph, acceptReusablePlan, focusPlannerGuide};
}
