import { executionBlockReason } from "../lib/execution-state";
import { analyticalGraph } from "../lib/analytical-graph";
import { useGraphLayout } from "../lib/use-graph-layout";
import { CRITIC_NODE_ID, criticState, withCriticReview } from "../lib/critic-graph";
import { useWritePolicy } from "../lib/write-policy";
import { usePlanRun, currentChatId, matchesPlanRun } from "../lib/use-plan-run";
import { useCanvasZoom } from "../lib/use-canvas-zoom";
import { runActive } from "../lib/workflow-tools";
import { useCallback, useMemo } from "react";
import { Map } from "lucide-react";
import { skillRecommendationScore } from "../lib/skill-recommendations";
import { type NodeGroup, type Workflow as WorkflowData } from "../lib/workflow";
import { standardPerformers, groupOf, performerOf, edgePoint, minimapSize, clamp, searchableSkillText, plannerWorkflow, withRecordedOutcome, editedPlannerWorkflow } from './model';
import type {WorkspaceBindings} from './useWorkspaceBindings';

export function useWorkspaceModel(input: WorkspaceBindings) {
 const { runPanelOpen, workflowRun, directExportRun, outcomeOpen, workflowReview, workflowReviewOpen, 
  executionWorkflowBusy, taskTransitionBusy, workflowAuthorization, editedPlan, editBusy, workflow, draft, 
  mode, newEdgeTargetId, connectionDrag, recipeTemplates, selectedTemplateId, recipeInventory, recipeSort, 
  selectedRecipeSha, preparedApproval, recordedApproval, executionResult, executionFailure, 
  executionProgress, executionInventoryOpen, criticInventory, selectedCriticTraceEvidence, 
  selectedStoredCriticTrace, plannerRequest, plannerResult, savedPlannerResult, preparedPlanApproval, 
  recordedPlanApproval, verifiedPlanApproval, compiledPlanRecipe, savedPlanRecipe, plannerSkills, 
  plannerSkillSearch, savedPlanInventory, savedPlanSort, activeRecipe, graphSelection, analyticalRecord, 
  historicalRecord, localGraph, showActiveGraph, selectedId, zoom, orientation, setZoom, setViewport, 
  executionScopeRef, canvasWindowRef, startupView, conversationId, 
}=input;
 const { policy:writePolicy, 
} = useWritePolicy();
 const workflowBusy = executionWorkflowBusy || taskTransitionBusy || runActive(workflowRun);
 const activeRecipeWorkflow = useMemo<WorkflowData | null>(() => {
    if (!activeRecipe) return null;
    type NodeStatus = WorkflowData["nodes"][number]["status"];
    const progressByStep = new globalThis.Map(executionProgress?.steps.map((step) => [step.step_id, step.status] as const) ?? []);
    const stepStatus = (stepId: string): NodeStatus => {
      const status = progressByStep.get(stepId);
      if (status === "interrupted") return "interrupted";
      if (status === "failed" || status === "validation_failed") return "failed";
      if (status === "completed" || status === "validated_success") return "complete";
      return "pending";
    };
    const approvalStatus: NodeStatus = recordedApproval?.decision === "denied" ? "denied" : recordedApproval?.decision === "approved" || executionProgress ? "approved" : "pending";
    const executionStatus: NodeStatus = executionProgress?.status === "interrupted" ? "interrupted" : executionFailure || executionProgress?.status === "failed" ? "failed" : executionResult ? "complete" : executionProgress?.status === "running" ? "pending" : "pending";
    const validationStatus: NodeStatus = executionResult?.status === "validated_success" || executionProgress?.status === "validated_success" ? "verified" : executionResult?.status === "validation_failed" || executionProgress?.status === "validation_failed" ? "failed" : executionProgress?.status === "interrupted" ? "interrupted" : "pending";
    const stepNodes: WorkflowData["nodes"] = activeRecipe.steps.map((step, index) => ({ id: `active_${step.step_id}`, title: step.skill_id.replaceAll("_", " "), subtitle: progressByStep.get(step.step_id)?.replaceAll("_", " ") ?? "Awaiting governed execution", kind: "tool", category: "tool", group: "execution", x: 1050 + index * 220, y: 350, status: stepStatus(step.step_id), authority: "Exact approved recipe step", performedBy: "MCP tool boundary", evidence: executionResult ? "Run evidence recorded" : "Not recorded", details: null }));
    const nodes: WorkflowData["nodes"] = [
      { id: "active_request", title: "User request", subtitle: activeRecipe.recipeId, kind: "input", category: "input", group: "intake", x: 50, y: 90, status: "complete", authority: "Operator-authored request", performedBy: "User", evidence: "Recipe identity", details: null },
      { id: "active_data", title: "Input data", subtitle: "Inputs bound in immutable recipe", kind: "data", category: "input", group: "intake", x: 50, y: 350, status: "complete", authority: "Recipe-bound paths and layers", performedBy: "User", evidence: activeRecipe.recipeSha256, details: null },
      { id: "active_planner", title: "Compile recipe", subtitle: "Typed trusted-template compilation", kind: "agent", category: "planning", group: "planning", x: 310, y: 90, status: "complete", authority: "Planning only", performedBy: "Planner agent", evidence: activeRecipe.recipeSha256, details: null },
      { id: "active_policy", title: "Validate policy", subtitle: "Deterministic recipe policy", kind: "policy", category: "policy", group: "governance", x: 550, y: 90, status: "verified", authority: "Deterministic policy", performedBy: "Policy engine", evidence: activeRecipe.recipeSha256, details: null },
      { id: "active_approval", title: "Human approval", subtitle: recordedApproval ? recordedApproval.decision : preparedApproval ? "Request prepared" : "Not prepared", kind: "approval", category: "approval", group: "governance", x: 760, y: 90, status: approvalStatus, authority: "Human decision required", performedBy: "Human operator", evidence: recordedApproval?.approval_filename ?? "Not recorded", details: null },
      { id: "active_executor", title: "Governed execution", subtitle: executionProgress?.status.replaceAll("_", " ") ?? "Not started", kind: "agent", category: "execution", group: "execution", x: 1050, y: 90, status: executionStatus, authority: "Exact approved envelope", performedBy: "Execution engine", evidence: executionResult?.run_result_path ?? "Not recorded", details: null },
      ...stepNodes,
      { id: "active_validation", title: "Validate outputs", subtitle: executionResult?.status.replaceAll("_", " ") ?? "Awaiting outputs", kind: "evidence", category: "validation", group: "assurance", x: 1070 + activeRecipe.steps.length * 220, y: 90, status: validationStatus, authority: "Deterministic verification", performedBy: "Validator", evidence: executionResult?.evidence_path ?? "Not recorded", details: null },
      { id: "active_evidence", title: "Record evidence", subtitle: executionResult || executionProgress?.execution_performed ? "Durable run evidence" : "Awaiting completed run", kind: "evidence", category: "evidence", group: "assurance", x: 1300 + activeRecipe.steps.length * 220, y: 90, status: executionResult || executionProgress?.execution_performed ? "complete" : executionFailure ? "failed" : executionProgress?.status === "interrupted" ? "interrupted" : "pending", authority: "Append-only evidence", performedBy: "Evidence service", evidence: executionResult?.report_path ?? (executionProgress?.execution_performed ? "Recorded in durable run artifacts" : "Not recorded"), details: null },
    ];
    const dependencyEdges: WorkflowData["edges"] = activeRecipe.steps.flatMap((step) => step.depends_on.length ? step.depends_on.map((dependency) => ({ from: `active_${dependency}`, to: `active_${step.step_id}`, kind: "data" as const, label: "dependency" })) : [{ from: "active_executor", to: `active_${step.step_id}`, kind: "data" as const, label: "dispatch" }]);
    const dependedOn = new Set(activeRecipe.steps.flatMap((step) => step.depends_on));
    const leafSteps = activeRecipe.steps.filter((step) => !dependedOn.has(step.step_id));
    return { schemaVersion: "1.0", id: `active-${activeRecipe.recipeId}`, title: `${activeRecipe.recipeId.replaceAll("_", " ")} · governed run`, correlationId: activeRecipe.recipeSha256.slice(0, 16), readOnly: true, source: "active_workflow", nodes, edges: [{ from: "active_request", to: "active_planner", kind: "control", label: "request" }, { from: "active_data", to: "active_planner", kind: "data", label: "inputs" }, { from: "active_planner", to: "active_policy", kind: "control", label: "proposal" }, { from: "active_policy", to: "active_approval", kind: "control", label: "policy" }, { from: "active_approval", to: "active_executor", kind: "control", label: "authority" }, ...dependencyEdges, ...leafSteps.map((step) => ({ from: `active_${step.step_id}`, to: "active_validation", kind: "data" as const, label: "validate" })), { from: "active_validation", to: "active_evidence", kind: "evidence", label: "record" }] };
  }, [activeRecipe, executionFailure, executionProgress, executionResult, preparedApproval, recordedApproval]);
 const recordedPlan = usePlanRun(savedPlannerResult?.plan_sha256, Boolean(editedPlan), directExportRun&&matchesPlanRun(directExportRun,savedPlannerResult?.plan_sha256,conversationId)?directExportRun:workflowRun,conversationId);
 const editedGraphProjection = useMemo(() => editedPlan ? editedPlannerWorkflow(editedPlan) : null, [editedPlan]);
 const analyticalProjection=useMemo(()=>analyticalRecord?analyticalGraph(analyticalRecord):null,[analyticalRecord]);
 const historicalAnalysis=useMemo(()=>historicalRecord?.analytical_session?{session:historicalRecord.analytical_session,conversationId:currentChatId()??'',revision:historicalRecord.entry.revision??0}:null,[historicalRecord]);
 const historicalProjection=useMemo(()=>{
    if(!historicalRecord)return null;
    if(historicalAnalysis&&['analysis','view'].includes(historicalRecord.entry.kind))return analyticalGraph(historicalAnalysis);
    if(historicalRecord.planner_result)return plannerWorkflow(historicalRecord.planner_result);
    const run=historicalRecord.run;if(!run)return null;
    const graph=plannerWorkflow({model:'Recorded execution',original_request:'Recorded run '+run.run_id,plan:{schema_version:'1.0',status:'planned',summary:'Recorded run · '+run.status,assumptions:[],risks:[],execution_performed:false,validation_performed:false,steps:run.steps.map(step=>({step_id:step.step_id,skill:step.skill_id,purpose:'Recorded operation',arguments:step.arguments,requires_approval:false,expected_artifacts:[],validation_required:false,depends_on:step.depends_on}))}});
    graph.nodes=graph.nodes.map(n=>{const step=run.steps.find(step=>n.id===`planned_${step.step_id}`);return step?{...n,subtitle:step.status,status:(['completed','validated_success','reused_completed'].includes(step.status)?'complete':['failed','validation_failed'].includes(step.status)?'failed':'pending') as WorkflowData['nodes'][number]['status'],performedBy:'Recorded execution',evidence:run.run_id}:n;});
    return withRecordedOutcome(graph,{success:run.status==='completed',running:false,evidence:run.run_id,steps:run.steps.filter(step=>step.outcome!=null).map(step=>`planned_${step.step_id}`)});
  },[historicalRecord,historicalAnalysis]);
 const baseDisplayedWorkflow = (graphSelection==='chat-history'?historicalProjection:null) ?? (graphSelection==='analytical-session'?analyticalProjection:null) ?? (graphSelection === "live-plan" ? editedGraphProjection : null) ?? draft ?? localGraph ?? (showActiveGraph ? activeRecipeWorkflow : null) ?? workflow;
 const displayedWorkflow = useMemo((): typeof baseDisplayedWorkflow => {
    const matchingRun = graphSelection === "live-plan" && !editedPlan ? recordedPlan.run : null;
    const observed = matchingRun ? { ...baseDisplayedWorkflow, nodes:baseDisplayedWorkflow.nodes.map(node=>{
      const step=matchingRun.steps.find(item=>node.id===`planned_${item.step_id}`);
      if(!step)return node;
      const status: WorkflowData["nodes"][number]["status"] = step.status === "running" ? "running" : step.status === "validated_success" ? "verified" : ['completed','reused_completed'].includes(step.status) ? "complete" : ["failed","validation_failed"].includes(step.status) ? "failed" : ["interrupted","skipped"].includes(step.status) ? "interrupted" : "pending";
      return {...node,status,subtitle:step.status.replaceAll("_"," "),performedBy:['queued','skipped'].includes(step.status)?'Not executed':step.status==='reused_completed'?'Recorded source run':'Execution engine',evidence:matchingRun.run_id};
    }) } : baseDisplayedWorkflow;
    if (matchingRun) {
      const finished=!runActive(matchingRun);
      const outcome=withRecordedOutcome(observed,matchingRun.execution_performed||(finished&&criticState(matchingRun).requested)?{success:matchingRun.status==='completed',running:!finished,evidence:matchingRun.run_id,steps:matchingRun.steps.filter(step=>step.outcome!=null).map(step=>`planned_${step.step_id}`)}:null);
      return withCriticReview(outcome,matchingRun);
    }
    return observed;
  },[baseDisplayedWorkflow,graphSelection,editedPlan,recordedPlan.run]);
 const selected = useMemo(() => displayedWorkflow.nodes.find((node) => node.id === selectedId) ?? displayedWorkflow.nodes[0], [displayedWorkflow, selectedId]);
 const selectedCritic = selected.id===CRITIC_NODE_ID && graphSelection==='live-plan' && !editedPlan ? recordedPlan.run : null;
 const selectedOperation = graphSelection === "live-plan" ? (editedPlan ?? plannerResult)?.plan.steps.find(step=>`planned_${step.step_id}`===selectedId) : undefined;
 const performerOptions = useMemo(() => [...new Set([...standardPerformers, ...displayedWorkflow.nodes.map(performerOf)])].sort(), [displayedWorkflow.nodes]);
 const plannerSkillResults = useMemo(() => {
    const query = plannerSkillSearch.trim().toLowerCase();
    const skills = plannerSkills?.skills ?? [];
    if (!query) return skills;
    const queryTokens = query.match(/[a-z0-9]+/g) ?? [];
    return skills.filter((skill) => queryTokens.every((token) => searchableSkillText(skill).includes(token)));
  }, [plannerSkillSearch, plannerSkills]);
 const recommendedPlannerSkills = useMemo(() => (plannerSkills?.skills ?? [])
    .map((skill) => ({ skill, score: skillRecommendationScore(skill, plannerRequest) }))
    .filter(({ score }) => score > 0)
    .sort((left, right) => right.score - left.score || left.skill.id.localeCompare(right.skill.id))
    .slice(0, 5)
    .map(({ skill }) => skill), [plannerRequest, plannerSkills]);
 const selectedTemplate = useMemo(() => recipeTemplates.find((template) => template.template_id === selectedTemplateId), [recipeTemplates, selectedTemplateId]);
 const sortedRecipes = useMemo(() => {
    const recipes = [...(recipeInventory?.recipes ?? [])];
    return recipes.sort((left, right) => {
      if (selectedRecipeSha) {
        if (left.recipe_sha256 === selectedRecipeSha) return -1;
        if (right.recipe_sha256 === selectedRecipeSha) return 1;
      }
      if (recipeSort === "name_asc") return left.recipe_id.localeCompare(right.recipe_id, undefined, { sensitivity: "base" });
      if (recipeSort === "name_desc") return right.recipe_id.localeCompare(left.recipe_id, undefined, { sensitivity: "base" });
      const difference = Date.parse(left.saved_at) - Date.parse(right.saved_at);
      return recipeSort === "time_asc" ? difference : -difference;
    });
  }, [recipeInventory, recipeSort, selectedRecipeSha]);
 const sortedSavedPlans = useMemo(() => [...(savedPlanInventory?.plans ?? [])].sort((left, right) => {
    if (savedPlanSort === "name_asc") return left.planner_result.plan.summary.localeCompare(right.planner_result.plan.summary, undefined, { sensitivity: "base" });
    if (savedPlanSort === "name_desc") return right.planner_result.plan.summary.localeCompare(left.planner_result.plan.summary, undefined, { sensitivity: "base" });
    const difference = Date.parse(left.saved_at) - Date.parse(right.saved_at);
    return savedPlanSort === "time_asc" ? difference : -difference;
  }), [savedPlanInventory, savedPlanSort]);
 const selectedCriticTraceCandidate = useMemo(
    () => criticInventory?.recipe_candidates.find((candidate) => candidate.evidence_name === selectedCriticTraceEvidence) ?? null,
    [criticInventory, selectedCriticTraceEvidence],
  );
 const selectedStoredCriticEvidence = useMemo(
    () => criticInventory?.items.find((item) => item.trace_name === selectedStoredCriticTrace && item.available && item.evidence) ?? null,
    [criticInventory, selectedStoredCriticTrace],
  );
 const runFacts = useMemo(() => ({
    inputReferences: graphSelection==="analytical-session"?String(analyticalRecord?.session.inventory.files.length??0):displayedWorkflow.nodes.find((node) => node.kind === "data")?.details?.observedFacts.find((fact) => fact.label === "Context references")?.value ?? "0",
    tools: displayedWorkflow.nodes.filter((node) => node.kind === "tool").length,
  }), [displayedWorkflow.nodes,graphSelection,analyticalRecord]);
 const { nodes, positions:nodePositions, setPositions:setNodePositions, 
}=useGraphLayout(displayedWorkflow.nodes,graphSelection==="live-plan"?`chat:${currentChatId()??'unsaved'}`:`graph:${displayedWorkflow.id}`,orientation==="horizontal");
 const timelineNodes=graphSelection==='analytical-session'?nodes.filter(n=>n.id.startsWith('analytical_action_')||n.id==='analytical_summary'):nodes;
 const canvasSize = useMemo(() => ({
    width: Math.max(720, Math.ceil(Math.max(...nodes.map((node) => node.x)) + 270)),
    height: Math.max(620, Math.ceil(Math.max(...nodes.map((node) => node.y)) + 190)),
  }), [nodes]);
 const connectionPreviewPath = useMemo(() => {
    if (!connectionDrag) return null;
    const source = nodes.find((node) => node.id === connectionDrag.sourceId);
    if (!source) return null;
    const horizontal = orientation === "horizontal";
    const start = edgePoint(source, connectionDrag.originDirection === "out" ? "from" : "to", connectionDrag.edgeKind, horizontal);
    const bend = horizontal ? (start.x + connectionDrag.x) / 2 : (start.y + connectionDrag.y) / 2;
    return horizontal
      ? `M ${start.x} ${start.y} C ${bend} ${start.y}, ${bend} ${connectionDrag.y}, ${connectionDrag.x} ${connectionDrag.y}`
      : `M ${start.x} ${start.y} C ${start.x} ${bend}, ${connectionDrag.x} ${bend}, ${connectionDrag.x} ${connectionDrag.y}`;
  }, [connectionDrag, nodes, orientation]);
 const groupFrames = useMemo(() => {
    const groups = [...new Set(nodes.map(groupOf).filter((group): group is NodeGroup => Boolean(group)))];
    return groups.map((group) => {
      const members = nodes.filter((node) => groupOf(node) === group);
      const minimumX = Math.min(...members.map((node) => node.x));
      const minimumY = Math.min(...members.map((node) => node.y));
      const maximumX = Math.max(...members.map((node) => node.x + 190));
      const maximumY = Math.max(...members.map((node) => node.y + 108));
      const horizontalPadding = 20;
      const topPadding = group === "planning" ? 24 : group === "governance" ? 20 : 30;
      const bottomPadding = group === "planning" ? 8 : 20;
      return { group, x: minimumX - horizontalPadding, y: minimumY - topPadding, width: maximumX - minimumX + (horizontalPadding * 2), height: maximumY - minimumY + topPadding + bottomPadding };
    });
  }, [nodes]);
 const camera = useCanvasZoom(canvasWindowRef, canvasSize, zoom, setZoom);
 const updateViewport = useCallback(() => {
    const element = canvasWindowRef.current;
    if (!element || camera.active.current) return;
    const scaledWidth = canvasSize.width * zoom;
    const scaledHeight = canvasSize.height * zoom;
    setViewport({
      x: (element.scrollLeft / scaledWidth) * minimapSize.width,
      y: (element.scrollTop / scaledHeight) * minimapSize.height,
      width: clamp((element.clientWidth / scaledWidth) * minimapSize.width, 12, minimapSize.width),
      height: clamp((element.clientHeight / scaledHeight) * minimapSize.height, 10, minimapSize.height),
    });
  }, [canvasSize.height, canvasSize.width, zoom]);
 const fitGraph = useCallback(() => {
    const element = canvasWindowRef.current;
    if (!element) return;
    const nextZoom = clamp(Math.min((element.clientWidth - 32) / canvasSize.width, (element.clientHeight - 32) / canvasSize.height), 0.2, 1.1);
    camera.set(nextZoom);
    requestAnimationFrame(() => element.scrollTo({ left: 0, top: 0, behavior: "smooth" }));
  }, [canvasSize.height, canvasSize.width]);
 startupView.current = {workflow,graphSelection,mode};
 const connectionTarget = draft?.nodes.find((node) => node.id === newEdgeTargetId);
 const rightPanelOpen = workflowReviewOpen || executionInventoryOpen || outcomeOpen || runPanelOpen;
 executionScopeRef.current={sha:savedPlannerResult?.plan_sha256,edited:Boolean(editedPlan),chat:currentChatId()};
 const currentScopeSteps=plannerResult?.plan.steps??[];
 const readOnlyScope=Boolean(currentScopeSteps.length)&&currentScopeSteps.every(step=>{
    const declared=plannerSkills?.skills.find(skill=>skill.id===step.skill);
    return declared?.access==='read_only'&&!declared.approval_required&&!step.requires_approval;
  });
 const currentReview=workflowReview?.plan_sha256===savedPlannerResult?.plan_sha256?workflowReview:null;
 const requiresWorkflowAuthorization=currentReview?Boolean(currentReview.approval_required_step_ids.length):!readOnlyScope;
 const executeBlocked=executionBlockReason({graph:graphSelection,busy:workflowBusy,editing:editBusy,draft:mode==='proposal',saved:Boolean(savedPlannerResult),edited:Boolean(editedPlan),needsApproval:requiresWorkflowAuthorization,authorized:Boolean(workflowAuthorization),available:Boolean(currentReview?.execution_available)});
 const plannerGuide = !plannerResult
    ? { label: "Describe the task and generate a plan", target: ".planner-submit", note: "No plan has been generated." }
    : !savedPlannerResult
      ? { label: "Review and save the exact plan", target: ".planner-result", note: "A validated proposal is available. Nothing has been saved or executed." }
      : !preparedPlanApproval
        ? { label: "Prepare the plan approval scope", target: ".planner-stored", note: "The plan is stored; no approval has been recorded." }
        : preparedPlanApproval.status === "approval_not_required"
          ? { label: "Inspect the read-only plan", target: ".planner-result", note: "No approval-required steps; no execution is implied." }
          : !recordedPlanApproval
            ? { label: "Record an explicit plan decision", target: ".planner-decision", note: "Review the exact scope before approving or denying." }
            : !verifiedPlanApproval?.approved
              ? { label: "Verify the recorded decision", target: ".planner-verification", note: recordedPlanApproval.decision === "denied" ? "The plan was denied; execution is blocked." : "Approval evidence must pass independent verification." }
              : !compiledPlanRecipe
                ? { label: "Compile a governed recipe candidate", target: ".planner-recipe-bridge", note: "Plan approval is verified; recipe review remains separate." }
                : !savedPlanRecipe
                  ? { label: "Review and save the recipe", target: ".compiled-plan-recipe", note: "Compilation grants no recipe approval." }
                  : { label: "Review the stored recipe approval scope", target: ".saved-plan-recipe", note: "The recipe is stored, not approved or executed." };
 return {...input,writePolicy, workflowBusy, activeRecipeWorkflow, recordedPlan, editedGraphProjection, analyticalProjection, historicalAnalysis, historicalProjection, baseDisplayedWorkflow, displayedWorkflow, selected, selectedCritic, selectedOperation, performerOptions, plannerSkillResults, recommendedPlannerSkills, selectedTemplate, sortedRecipes, sortedSavedPlans, selectedCriticTraceCandidate, selectedStoredCriticEvidence, runFacts, nodes, nodePositions, setNodePositions, timelineNodes, canvasSize, connectionPreviewPath, groupFrames, camera, updateViewport, fitGraph, connectionTarget, rightPanelOpen, currentScopeSteps, readOnlyScope, currentReview, requiresWorkflowAuthorization, executeBlocked, plannerGuide};
}
export type WorkspaceModel = ReturnType<typeof useWorkspaceModel>;
