import { loadInspectionRuns } from "../lib/interface-api";
import { compileRecipeProposal, createRecipeRelease, exportSnakemakeRecipe, executeExactPreview, loadCriticEvidence, loadExecutionInventory, loadExecutionProgress, loadSavedRecipes, loadTaskContext, loadTaskInventory, recordTaskEvent, prepareExecutionPreview, prepareRecipeRelease, prepareRecipeApproval, previewSnakemakeExport, recordCriticAssessment, recordRecipeApproval, runCriticAssessment, saveAdaptedRecipeTrace, saveReviewedRecipe, verifyRecordedRecipeApproval } from "../lib/interface-api";
import { browserRecipeProposalSchema, type BrowserRecipeProposal } from "../lib/recipe-templates";
import { ProposalDraft, topologySignature } from './model';
import type {ActionContext} from './action-contracts';

export function createAdvancedActions(context: ActionContext) {
 const { releaseId, 
}=context;
 const { selectedTemplate, proposalRequest, setDraft, setTemplateTopologyBaseline, setLoadedTemplateId, setMode, 
  setSelectedId, setTemplatePanelOpen, setTemplateNotice, mode, loadedTemplateId, templateTopologyBaseline, 
  draft, templateParameters, recipeIdHint, setCompilationPending, setCompilation, setReviewConfirmed, 
  setSavedRecipe, compilation, reviewConfirmed, setSavePending, setShowActiveGraph, setLocalGraph, 
  setGraphSelection, setActiveRecipe, setPlannerOpen, setExecutionInventoryOpen, setRecipePanelOpen, 
  setRecipeInventoryNotice, setPreparedApproval, setRecordedApproval, setApprovalVerification, 
  setApprovalVerificationNotice, setExecutionPreview, setExecutionConfirmed, setExecutionResult, 
  setExecutionNotice, setExecutionFailure, setExecutionProgress, setSnakemakePlan, setSnakemakeResult, 
  setSnakemakeConfirmed, setSnakemakeNotice, setApprovalConfirmed, setApprovalDecisionNotice, 
  setSelectedRecipeSha, setRecipeInventory, setWorkflowReviewOpen, setOutcomeOpen, setRunPanelOpen, 
  setTextPlannerOpen, setIntentOpen, setExecutionInventoryNotice, setInspectionNotice, setInspectionRuns, 
  setExecutionInventory, setCriticOpen, setCriticNotice, setCriticInventory, setSelectedCriticTraceEvidence, 
  setSelectedStoredCriticTrace, setCriticTraceSaving, setStoredCriticTrace, selectedStoredCriticEvidence, 
  setCriticInvocationNotice, setCriticInvocationPending, setCriticAssessment, setCriticRecordConfirmed, 
  setRecordedCriticResult, setCriticInvocationCollapsed, setCriticTraceDrawerCollapsed, criticAssessment, 
  setCriticRecordPending, setReleaseId, setReleaseAssessment, setReleaseResult, setReleaseConfirmed, 
  recordedCriticResult, setReleasePending, setReleaseNotice, releaseAssessment, criticOpen, setViewedTaskId, 
  setTaskContext, setTaskNotice, viewedTaskId, setTaskPaneOpen, setTaskInventory, setTaskInventoryOpen, 
  setApprovalPreparationPending, approvalRequestRef, preparedApproval, approvalConfirmed, recordedApproval, 
  approvalApproverRef, approvalApprover, approvalReasonRef, approvalReason, approvalValidMinutesRef, 
  approvalValidMinutes, setApprovalRecording, approvalDecision, approvalVerifying, setApprovalVerifying, 
  approvalVerification, executionPreviewPending, setExecutionPreviewPending, snakemakePending, 
  setSnakemakePending, snakemakePlan, snakemakeConfirmed, executionPreview, executionConfirmed, 
  executionPending, executionResult, setExecutionPending, currentTaskId, savedPlanRecipe, activeRecipe, 
}=context;
const applyRecipeTemplate = () => {
    if (!selectedTemplate) return;
    const stepNodes: ProposalDraft["nodes"] = selectedTemplate.steps.map((step, index) => ({
      id: `template_${step.step_id}`,
      title: step.skill_id.replaceAll("_", " "),
      subtitle: `Trusted skill · ${step.output_ids.join(", ")}`,
      kind: "tool",
      category: "tool",
      group: "execution",
      x: 720 + (index * 220),
      y: 330,
      status: "pending",
      authority: "Template proposal only",
      performedBy: "MCP tool boundary",
      evidence: "Not recorded",
      details: null,
    }));
    const templateNodes: ProposalDraft["nodes"] = [
      { id: "template_request", title: "Describe outcome", subtitle: proposalRequest || selectedTemplate.template_id.replaceAll("_", " "), kind: "input", category: "input", group: "intake", x: 60, y: 80, status: "pending", authority: "Operator proposal", performedBy: "User", evidence: "Not recorded", details: null },
      { id: "template_data", title: "Template parameters", subtitle: selectedTemplate.required_parameters.join(", "), kind: "data", category: "input", group: "intake", x: 60, y: 330, status: "pending", authority: "Bounded parameter selection", performedBy: "User", evidence: "Not recorded", details: null },
      { id: "template_planner", title: "Review proposal", subtitle: selectedTemplate.template_id, kind: "agent", category: "planning", group: "planning", x: 360, y: 150, status: "pending", authority: "Planning only", performedBy: "Planner agent", evidence: "Not recorded", details: null },
      ...stepNodes,
      { id: "template_validation", title: "Validate outputs", subtitle: "Deterministic postconditions", kind: "evidence", category: "validation", group: "assurance", x: 720 + (selectedTemplate.steps.length * 220), y: 150, status: "pending", authority: "Validation only", performedBy: "Validator", evidence: "Not recorded", details: null },
    ];
    const stepEdges: ProposalDraft["edges"] = selectedTemplate.steps.flatMap((step) => step.depends_on.length
      ? step.depends_on.map((dependency) => ({ from: `template_${dependency}`, to: `template_${step.step_id}`, kind: "data" as const, label: "dependency" }))
      : [{ from: "template_planner", to: `template_${step.step_id}`, kind: "data" as const, label: "proposed step" }]);
    const dependedOn = new Set(selectedTemplate.steps.flatMap((step) => step.depends_on));
    const leafEdges: ProposalDraft["edges"] = selectedTemplate.steps.filter((step) => !dependedOn.has(step.step_id)).map((step) => ({ from: `template_${step.step_id}`, to: "template_validation", kind: "data" as const, label: "validate" }));
    const templateDraft: ProposalDraft = { schemaVersion: "1.0", id: `${selectedTemplate.template_id}-draft`, title: `${selectedTemplate.template_id.replaceAll("_", " ")} proposal`, correlationId: `template-${selectedTemplate.template_id}`, readOnly: false, source: "proposal_draft", nodes: templateNodes, edges: [{ from: "template_request", to: "template_planner", kind: "control", label: "request" }, { from: "template_data", to: "template_planner", kind: "data", label: "parameters" }, ...stepEdges, ...leafEdges] };
    setDraft(templateDraft);
    setTemplateTopologyBaseline(topologySignature(templateDraft));
    setLoadedTemplateId(selectedTemplate.template_id);
    setMode("proposal");
    setSelectedId("template_request");
    setTemplatePanelOpen(false);
    setTemplateNotice("Template loaded as an uncommitted graph proposal.");
  };

const buildRecipeProposal = (): BrowserRecipeProposal | null => {
    if (!selectedTemplate) return null;
    if (mode === "proposal" && loadedTemplateId && loadedTemplateId !== selectedTemplate.template_id) {
      setTemplateNotice("Load the selected template graph before downloading its proposal.");
      return null;
    }
    if (templateTopologyBaseline && draft && topologySignature(draft) !== templateTopologyBaseline) {
      setTemplateNotice("This graph topology was edited. The current CLI proposal contract cannot represent those structural edits yet.");
      return null;
    }
    const missing = selectedTemplate.required_parameters.filter((name) => !templateParameters[name]?.trim());
    if (!proposalRequest.trim() || missing.length) {
      setTemplateNotice(!proposalRequest.trim() ? "Describe the requested outcome before downloading." : `Complete required parameters: ${missing.join(", ")}`);
      return null;
    }
    if (!/^[a-z0-9][a-z0-9_-]{0,100}$/.test(recipeIdHint.trim())) {
      setTemplateNotice("Recipe ID must use lowercase letters, numbers, underscores, or hyphens.");
      return null;
    }
    const parameterNames = [...selectedTemplate.required_parameters, ...selectedTemplate.optional_parameters];
    const parameters = Object.fromEntries(parameterNames.flatMap((name) => {
      const value = templateParameters[name]?.trim();
      return value ? [[name, value]] : [];
    }));
    return browserRecipeProposalSchema.parse({ schema_version: "1.0", status: "proposed_not_compiled", original_request: proposalRequest.trim(), summary: `Operator-selected trusted template: ${selectedTemplate.template_id}`, recipe_id_hint: recipeIdHint.trim(), selection: { template_id: selectedTemplate.template_id, parameters }, assumptions: [], missing_information: [], warnings: ["Browser-authored proposal; backend validation and compilation are still required."], compilation_performed: false, execution_requested: false, approval_performed: false, execution_performed: false });
  };

const downloadRecipeProposal = () => {
    const proposal = context.actions().buildRecipeProposal();
    if (!proposal || !selectedTemplate) return;
    const url = URL.createObjectURL(new Blob([`${JSON.stringify(proposal, null, 2)}\n`], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedTemplate.template_id}-proposal.json`;
    link.click();
    URL.revokeObjectURL(url);
    setTemplateNotice("Proposal downloaded for backend validation; nothing was executed.");
  };

const compileTemplateProposal = async () => {
    const proposal = context.actions().buildRecipeProposal();
    if (!proposal) return;
    setCompilationPending(true);
    setCompilation(null);
    setReviewConfirmed(false);
    setSavedRecipe(null);
    setTemplateNotice("Compiling through the local typed service…");
    try {
      const result = await compileRecipeProposal(proposal);
      setCompilation(result);
      setTemplateNotice("Compilation passed. Nothing was saved, approved, or executed.");
    } catch (error) {
      setTemplateNotice(error instanceof Error ? error.message : "Proposal compilation failed.");
    } finally {
      setCompilationPending(false);
    }
  };

const saveCompiledRecipe = async () => {
    if (!compilation || !reviewConfirmed) return;
    const proposal = context.actions().buildRecipeProposal();
    if (!proposal) return;
    setSavePending(true);
    setSavedRecipe(null);
    setTemplateNotice("Recompiling and checking the reviewed digest before immutable storage…");
    try {
      const stored = await saveReviewedRecipe(proposal, compilation.recipe_sha256);
      setSavedRecipe(stored);
      setShowActiveGraph(true);
      setLocalGraph(null);
      setGraphSelection("active");
      setActiveRecipe({ recipeId: stored.recipe_id, recipeSha256: stored.recipe_sha256, steps: compilation.result.recipe.steps.map((step) => ({ step_id: step.step_id, skill_id: step.skill_id, depends_on: step.depends_on })) });
      setDraft(null);
      setMode("evidence");
      setSelectedId("active_request");
      setTemplateNotice("Reviewed recipe stored immutably. It is not approved and was not executed.");
    } catch (error) {
      setTemplateNotice(error instanceof Error ? error.message : "Reviewed recipe could not be stored.");
    } finally {
      setSavePending(false);
    }
  };

const openSavedRecipes = async (preferredRecipeSha = "") => {
    setTemplatePanelOpen(false);
    setPlannerOpen(false);
    setExecutionInventoryOpen(false);
    setRecipePanelOpen(true);
    setRecipeInventoryNotice("Loading immutable recipes…");
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
    setSnakemakePlan(null);
    setSnakemakeResult(null);
    setSnakemakeConfirmed(false);
    setSnakemakeNotice("");
    setSnakemakeNotice("");
    setApprovalConfirmed(false);
    setApprovalDecisionNotice("");
    setSelectedRecipeSha(preferredRecipeSha);
    try {
      const inventory = await loadSavedRecipes();
      setRecipeInventory(inventory);
      setRecipeInventoryNotice(preferredRecipeSha && !inventory.recipes.some((recipe) => recipe.recipe_sha256 === preferredRecipeSha)
        ? "The newly stored recipe was not found in the refreshed inventory. Confirm the API and project root."
        : preferredRecipeSha ? "Newly stored recipe selected. Review its exact scope before preparing approval." : "");
    } catch {
      setRecipeInventory(null);
      setRecipeInventoryNotice("Saved recipes could not be loaded. Confirm that the local interface service is running.");
    }
  };

const openExecutionInventory = async () => {
    setWorkflowReviewOpen(false); setOutcomeOpen(false); setRunPanelOpen(false);
    setTextPlannerOpen(false);
    setIntentOpen(false);
    setPlannerOpen(false);
    setTemplatePanelOpen(false);
    setRecipePanelOpen(false);
    setExecutionInventoryOpen(true);
    setExecutionInventoryNotice("Loading durable execution attempts…");
    setInspectionNotice("Loading inspection attempts…");
    void loadInspectionRuns().then((runs) => { setInspectionRuns(runs); setInspectionNotice(runs.length ? "" : "No inspection attempts yet."); }).catch((e: unknown) => setInspectionNotice(e instanceof Error ? e.message : "Inspection history unavailable"));
    try {
      const inventory = await loadExecutionInventory();
      setExecutionInventory(inventory);
      setExecutionInventoryNotice(inventory.attempt_count ? "" : "No durable execution attempts are available yet.");
    } catch {
      setExecutionInventory(null);
      setExecutionInventoryNotice("Execution attempts could not be loaded. Confirm that the local interface service is running.");
    }
  };

const openCriticEvidence = async () => {
    setTemplatePanelOpen(false);
    setRecipePanelOpen(false);
    setExecutionInventoryOpen(false);
    setPlannerOpen(false);
    setCriticOpen(true);
    setCriticNotice("Building deterministic assurance summaries…");
    try {
      const inventory = await loadCriticEvidence();
      setCriticInventory(inventory);
      setSelectedCriticTraceEvidence((current) => current || inventory.recipe_candidates.find((candidate) => candidate.adaptable && !candidate.stored)?.evidence_name || "");
      setSelectedStoredCriticTrace((current) => current || inventory.items.find((item) => item.available)?.trace_name || "");
      setCriticNotice(inventory.item_count ? "" : "No WorkflowTrace and matching report pairs are available yet.");
    } catch {
      setCriticInventory(null);
      setCriticNotice("Critic evidence could not be loaded. Confirm that the local interface service is running.");
    }
  };

const storeCriticTrace = async (evidenceName: string, traceSha256: string) => {
    setCriticTraceSaving(evidenceName);
    setCriticNotice("Rebuilding and verifying the exact reviewed trace…");
    try {
      const stored = await saveAdaptedRecipeTrace(evidenceName, traceSha256);
      setStoredCriticTrace(stored);
      setCriticNotice("Adapted trace and deterministic report stored immutably. Critic not invoked; no release created.");
      setCriticInventory(await loadCriticEvidence());
    } catch (error) {
      setCriticNotice(error instanceof Error ? error.message : "Adapted trace could not be stored.");
    } finally {
      setCriticTraceSaving("");
    }
  };

const invokeCritic = async () => {
    if (!selectedStoredCriticEvidence?.evidence || !selectedStoredCriticEvidence.report_name) return;
    const traceReference = selectedStoredCriticEvidence.evidence.evidence_references.find((item) => item.path.endsWith(`/${selectedStoredCriticEvidence.trace_name}`));
    const reportReference = selectedStoredCriticEvidence.evidence.evidence_references.find((item) => item.path.endsWith(`/${selectedStoredCriticEvidence.report_name}`));
    if (!traceReference || !reportReference) {
      setCriticInvocationNotice("Exact stored evidence digests are unavailable.");
      return;
    }
    setCriticInvocationPending(true);
    setCriticInvocationNotice("Calling the read-only Critic and validating its assessment…");
    setCriticAssessment(null);
    try {
      const result = await runCriticAssessment({ traceName: selectedStoredCriticEvidence.trace_name, reportName: selectedStoredCriticEvidence.report_name, traceSha256: traceReference.sha256, reportSha256: reportReference.sha256 });
      setCriticAssessment(result);
      setCriticRecordConfirmed(false);
      setRecordedCriticResult(null);
      setCriticInvocationCollapsed(true);
      setCriticTraceDrawerCollapsed(true);
      setCriticInvocationNotice("Critic assessment validated in memory. Nothing recorded and no release created.");
    } catch (error) {
      setCriticInvocationNotice(error instanceof Error ? error.message : "Critic assessment failed.");
    } finally {
      setCriticInvocationPending(false);
    }
  };

const recordCriticResult = async () => {
    if (!criticAssessment || !selectedStoredCriticEvidence?.evidence || !selectedStoredCriticEvidence.report_name) return;
    const traceReference = selectedStoredCriticEvidence.evidence.evidence_references.find((item) => item.path.endsWith(`/${selectedStoredCriticEvidence.trace_name}`));
    const reportReference = selectedStoredCriticEvidence.evidence.evidence_references.find((item) => item.path.endsWith(`/${selectedStoredCriticEvidence.report_name}`));
    if (!traceReference || !reportReference) {
      setCriticInvocationNotice("Exact stored evidence digests are unavailable.");
      return;
    }
    setCriticRecordPending(true);
    setCriticInvocationNotice("Revalidating evidence and recording the exact reviewed Critic result…");
    try {
      const recorded = await recordCriticAssessment({ traceName: selectedStoredCriticEvidence.trace_name, reportName: selectedStoredCriticEvidence.report_name, traceSha256: traceReference.sha256, reportSha256: reportReference.sha256, assessment: criticAssessment });
      setRecordedCriticResult(recorded);
      setReleaseId(`release-${recorded.task_id}`.slice(0, 128));
      setReleaseAssessment(null);
      setReleaseResult(null);
      setReleaseConfirmed(false);
      setCriticInvocationNotice("Exact Critic result recorded immutably. No release created and nothing executed.");
    } catch (error) {
      setCriticInvocationNotice(error instanceof Error ? error.message : "Critic result could not be recorded.");
    } finally {
      setCriticRecordPending(false);
    }
  };

const prepareRelease = async () => {
    if (!recordedCriticResult || !selectedStoredCriticEvidence?.report_name) return;
    setReleasePending(true); setReleaseNotice("Reverifying the complete evidence chain and preparing operational history…");
    try {
      const assessed = await prepareRecipeRelease({ releaseId, traceName: selectedStoredCriticEvidence.trace_name, reportName: selectedStoredCriticEvidence.report_name, criticRecordFile: recordedCriticResult.record_file, criticRecordSha256: recordedCriticResult.critic_record_sha256 });
      setReleaseAssessment(assessed); setReleaseResult(null); setReleaseConfirmed(false);
      setReleaseNotice(assessed.candidate.ready_for_release ? "Exact candidate is release-ready. Review its digest before creating the immutable package." : "Release is blocked by deterministic findings.");
    } catch (error) { setReleaseNotice(error instanceof Error ? error.message : "Release readiness assessment failed."); }
    finally { setReleasePending(false); }
  };

const createRelease = async () => {
    if (!recordedCriticResult || !selectedStoredCriticEvidence?.report_name || !releaseAssessment) return;
    setReleasePending(true); setReleaseNotice("Reassessing exact evidence and creating the immutable release…");
    try {
      const released = await createRecipeRelease({ releaseId, traceName: selectedStoredCriticEvidence.trace_name, reportName: selectedStoredCriticEvidence.report_name, criticRecordFile: recordedCriticResult.record_file, criticRecordSha256: recordedCriticResult.critic_record_sha256, candidateSha256: releaseAssessment.candidate_sha256, assessedAt: releaseAssessment.candidate.assessed_at });
      setReleaseResult(released); setReleaseNotice("Immutable release created from the exact reviewed candidate.");
    } catch (error) { setReleaseNotice(error instanceof Error ? error.message : "Immutable release creation failed."); }
    finally { setReleasePending(false); }
  };

const reopenExecutionAttempt = async (digest: string) => {
    setExecutionInventoryNotice("Revalidating the durable attempt…");
    try {
      const progress = await loadExecutionProgress(digest);
      if (!progress) throw new Error("execution progress is not available");
      if (!progress.recipe_id || !progress.recipe_sha256) {
        throw new Error("This older attempt does not contain enough recipe identity to rebuild its graph.");
      }
      setExecutionProgress(progress);
      setExecutionResult(null);
      setExecutionFailure("");
      setShowActiveGraph(true);
      setLocalGraph(null);
      setGraphSelection("active");
      setActiveRecipe({
        recipeId: progress.recipe_id,
        recipeSha256: progress.recipe_sha256,
        steps: progress.steps.map((step) => ({
          step_id: step.step_id,
          skill_id: step.skill_id,
          depends_on: step.depends_on,
        })),
      });
      setSelectedId("active_executor");
      setExecutionInventoryOpen(false);
      setCriticOpen(false);
      setExecutionInventoryNotice("");
    } catch (error) {
      setExecutionInventoryNotice(error instanceof Error ? error.message : "Execution attempt could not be reopened.");
      if (criticOpen) setCriticNotice(error instanceof Error ? error.message : "Linked run could not be reopened.");
    }
  };

const appendCurrentTaskEvent = async (taskId: string, type: "selection" | "decision" | "outcome" | "failure", summary: string) => {
    try {
      await recordTaskEvent(type, summary.slice(0, 1000), taskId);
      const context = await loadTaskContext(taskId);
      setViewedTaskId(taskId);
      setTaskContext((current) => current?.task_id === context.task_id && current.event_count > context.event_count ? current : context);
      setTaskNotice("");
    } catch {
      setTaskNotice("Task history could not be updated. Check the original plan and approval evidence; history grants no authority.");
    }
  };

const refreshViewedTask = async () => {
    if (!viewedTaskId) return;
    const pane = document.querySelector<HTMLElement>(".task-context-content");
    const inspector = document.querySelector<HTMLElement>(".inspector");
    const paneTop = pane?.scrollTop ?? 0, inspectorTop = inspector?.scrollTop ?? 0;
    const pageX = window.scrollX, pageY = window.scrollY;
    try { setTaskContext(await loadTaskContext(viewedTaskId)); }
    catch { setTaskNotice("Task context could not be reopened."); }
    requestAnimationFrame(() => {
      if (pane) pane.scrollTop = paneTop;
      if (inspector) inspector.scrollTop = inspectorTop;
      window.scrollTo({ left: pageX, top: pageY, behavior: "instant" });
    });
  };

const showTaskHistory = () => {
    context.actions().openJourneyStage("review");
    setTaskPaneOpen(true);
    requestAnimationFrame(() => document.getElementById("task-history")?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
  };

const openSavedTasks = async () => {
    try {
      setTaskInventory(await loadTaskInventory());
      setTaskInventoryOpen(true);
      setTaskNotice("");
    } catch (error) { setTaskNotice(error instanceof Error ? error.message : "Saved task history is unavailable."); }
  };

const inspectSavedTask = async (taskId: string) => {
    try {
      const context = await loadTaskContext(taskId);
      setViewedTaskId(taskId);
      setTaskContext(context);
      setTaskInventoryOpen(false);
      setTaskNotice("History inspected. This does not resume a plan, decision or execution.");
    } catch { setTaskNotice("Task history could not be independently reopened."); }
  };

const prepareApproval = async (recipeFilename: string, recipeSha256: string) => {
    setSelectedRecipeSha(recipeSha256);
    setApprovalPreparationPending(true);
    setPreparedApproval(null);
    setRecipeInventoryNotice("Revalidating the stored recipe and preparing an exact approval request…");
    try {
      const request = await prepareRecipeApproval(recipeFilename, recipeSha256);
      setPreparedApproval(request);
      setShowActiveGraph(true);
      setLocalGraph(null);
      setGraphSelection("active");
      setActiveRecipe({ recipeId: request.recipe_id, recipeSha256: request.recipe_sha256, steps: request.steps.map((step) => ({ step_id: step.step_id, skill_id: step.skill_id, depends_on: step.depends_on })) });
      setDraft(null);
      setMode("evidence");
      setSelectedId("active_approval");
      setRecordedApproval(null);
      setApprovalVerification(null);
      setApprovalVerificationNotice("");
      setExecutionPreview(null);
      setExecutionConfirmed(false);
      setExecutionResult(null);
      setExecutionNotice("");
      setExecutionFailure("");
      setExecutionProgress(null);
      setSnakemakePlan(null);
      setSnakemakeResult(null);
      setSnakemakeConfirmed(false);
      setSnakemakeNotice("");
      setApprovalConfirmed(false);
      setApprovalDecisionNotice("");
      setRecipeInventoryNotice("");
      requestAnimationFrame(() => {
        approvalRequestRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        approvalRequestRef.current?.focus({ preventScroll: true });
      });
    } catch (error) {
      setRecipeInventoryNotice(error instanceof Error ? error.message : "Approval request could not be prepared.");
    } finally {
      setApprovalPreparationPending(false);
    }
  };

const recordApprovalDecision = async () => {
    if (!preparedApproval || !approvalConfirmed || recordedApproval) return;
    const approver = approvalApproverRef.current?.value.trim() ?? approvalApprover.trim();
    const reason = approvalReasonRef.current?.value.trim() ?? approvalReason.trim();
    const validMinutes = approvalValidMinutesRef.current?.value.trim() ?? approvalValidMinutes.trim();
    if (!approver || !reason) {
      setApprovalDecisionNotice("Approver and reason are required.");
      return;
    }
    const minutes = validMinutes ? Number(validMinutes) : null;
    if (minutes !== null && (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440)) {
      setApprovalDecisionNotice("Expiration must be a whole number from 1 to 1440 minutes.");
      return;
    }
    setApprovalRecording(true);
    setApprovalDecisionNotice("Revalidating the prepared request before append-only recording…");
    try {
      const result = await recordRecipeApproval({ request: preparedApproval, decision: approvalDecision, approver, reason, validForMinutes: minutes });
      setRecordedApproval(result);
      setSelectedId("active_approval");
      setApprovalDecisionNotice("Decision recorded. Nothing was executed.");
    } catch (error) {
      setApprovalDecisionNotice(error instanceof Error ? error.message : "Approval decision could not be recorded.");
    } finally {
      setApprovalRecording(false);
    }
  };

const verifyApprovalDecision = async () => {
    if (!preparedApproval || !recordedApproval || approvalVerifying) return;
    setApprovalVerifying(true);
    setApprovalVerificationNotice("Re-reading immutable recipe and approval evidence…");
    try {
      const result = await verifyRecordedRecipeApproval(preparedApproval, recordedApproval);
      setApprovalVerification(result);
      setApprovalVerificationNotice("");
    } catch (error) {
      setApprovalVerification(null);
      setApprovalVerificationNotice(error instanceof Error ? error.message : "Approval verification failed.");
    } finally {
      setApprovalVerifying(false);
    }
  };

const previewApprovedExecution = async () => {
    if (!preparedApproval || !recordedApproval || !approvalVerification?.approved || executionPreviewPending) return;
    setExecutionPreviewPending(true);
    setApprovalVerificationNotice("Rebuilding the exact non-executing envelope…");
    try {
      setExecutionPreview(await prepareExecutionPreview(preparedApproval, recordedApproval));
      setExecutionConfirmed(false);
      setExecutionResult(null);
      setExecutionFailure("");
      setExecutionProgress(null);
      setApprovalVerificationNotice("");
    } catch (error) {
      setExecutionPreview(null);
      setApprovalVerificationNotice(error instanceof Error ? error.message : "Execution preview failed.");
    } finally {
      setExecutionPreviewPending(false);
    }
  };

const previewApprovedSnakemakeExport = async () => {
    if (!preparedApproval || !recordedApproval || !approvalVerification?.approved || snakemakePending) return;
    setSnakemakePending(true); setSnakemakeNotice("Rebuilding approved authority and previewing the replay package…");
    try {
      const result = await previewSnakemakeExport(preparedApproval, recordedApproval);
      setSnakemakePlan(result); setSnakemakeResult(null); setSnakemakeConfirmed(false);
      setSnakemakeNotice("Export plan validated. Nothing exported or executed.");
    } catch (error) { setSnakemakeNotice(error instanceof Error ? error.message : "Snakemake export preview failed."); }
    finally { setSnakemakePending(false); }
  };

const createApprovedSnakemakeExport = async () => {
    if (!preparedApproval || !recordedApproval || !snakemakePlan || !snakemakeConfirmed || snakemakePending) return;
    setSnakemakePending(true); setSnakemakeNotice("Revalidating approval, exporting, and checking the static contract…");
    try {
      const result = await exportSnakemakeRecipe(preparedApproval, recordedApproval, snakemakePlan);
      setSnakemakeResult(result); setSnakemakeNotice(result.export_already_existed ? "The exact export already existed and passed static validation again. Nothing executed." : "Replay package exported and statically validated. Nothing executed.");
    } catch (error) { setSnakemakeNotice(error instanceof Error ? error.message : "Snakemake export failed."); }
    finally { setSnakemakePending(false); }
  };

const runExactPreview = async () => {
    if (!preparedApproval || !recordedApproval || !executionPreview || !executionConfirmed || executionPending || executionResult) return;
    setExecutionPending(true);
    setExecutionFailure("");
    setExecutionProgress(null);
    setExecutionNotice("Executing the exact verified envelope and recording durable evidence…");
    const refreshProgress = async () => {
      try {
        const progress = await loadExecutionProgress(executionPreview.execution_preview_sha256);
        if (progress) setExecutionProgress(progress);
        return progress;
      } catch {
        // The authoritative execution request still determines the final result.
        return null;
      }
    };
    const progressTimer = window.setInterval(() => void refreshProgress(), 250);
    try {
      const result = await executeExactPreview(preparedApproval, recordedApproval, executionPreview, currentTaskId && savedPlanRecipe?.recipe_sha256 === activeRecipe?.recipeSha256 ? currentTaskId : null);
      setExecutionResult(result);
      await refreshProgress();
      setSelectedId("active_validation");
      setExecutionNotice("");
      if (currentTaskId && savedPlanRecipe?.recipe_sha256 === activeRecipe?.recipeSha256) await context.actions().appendCurrentTaskEvent(currentTaskId, "outcome", `Governed run response: ${result.status}. Result ${result.run_result_sha256}. Inspect durable run evidence for authority and validation.`);
      if (result.task_references?.some((reference) => reference.status === "failed")) setTaskNotice("Run completed, but some task evidence references could not be recorded. Inspect durable run evidence before retrying.");
    } catch (error) {
      const finalProgress = await refreshProgress();
      setExecutionNotice("");
      setExecutionFailure(error instanceof Error ? error.message : "Approved execution failed. Inspect outputs and evidence before retrying.");
      setSelectedId(finalProgress?.failed_step_id ? `active_${finalProgress.failed_step_id}` : "active_executor");
      if (currentTaskId && savedPlanRecipe?.recipe_sha256 === activeRecipe?.recipeSha256) await context.actions().appendCurrentTaskEvent(currentTaskId, "failure", `Governed execution did not complete successfully. Inspect durable attempt ${executionPreview.execution_preview_sha256}.`);
    } finally {
      window.clearInterval(progressTimer);
      setExecutionPending(false);
    }
  };
 return {applyRecipeTemplate, buildRecipeProposal, downloadRecipeProposal, compileTemplateProposal, saveCompiledRecipe, openSavedRecipes, openExecutionInventory, openCriticEvidence, storeCriticTrace, invokeCritic, recordCriticResult, prepareRelease, createRelease, reopenExecutionAttempt, appendCurrentTaskEvent, refreshViewedTask, showTaskHistory, openSavedTasks, inspectSavedTask, prepareApproval, recordApprovalDecision, verifyApprovalDecision, previewApprovedExecution, previewApprovedSnakemakeExport, createApprovedSnakemakeExport, runExactPreview};
}
