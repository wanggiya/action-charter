import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown, ArrowRight, Bot, CheckCircle2, ChevronDown, CircleDot,
  Database, FileCheck2, GitBranch, LockKeyhole, Map, Maximize2, Minus,
  GripVertical, History, LayoutList, LayoutTemplate, Plus, Search, ShieldCheck, Workflow, X, XCircle, ZoomIn,
} from "lucide-react";
import workflowFixture from "./data/demo-workflow.json";
import { loadWorkflowCatalog, loadWorkflowProjection } from "./lib/load-workflow";
import { loadRecipeTemplates } from "./lib/load-recipe-templates";
import { compilePlannerRecipe, compileRecipeProposal, createPlannerPlan, executeExactPreview, loadExecutionInventory, loadExecutionProgress, loadPlannerSkills, loadSavedPlans, loadSavedRecipes, prepareExecutionPreview, preparePlannerApproval, previewPlannerExecution, prepareRecipeApproval, recordPlannerApproval, recordRecipeApproval, saveCompiledPlannerRecipe, saveReviewedPlannerPlan, saveReviewedRecipe, verifyPlannerApproval, verifyRecordedRecipeApproval, type CompiledPlanRecipe, type ExecutionInventory, type ExecutionPreview, type ExecutionProgress, type InterfaceCompilation, type InterfacePlannerResult, type PlanExecutionPreview, type PlannerSkillCatalog, type PreparedApprovalRequest, type PreparedPlanApproval, type RecipeExecutionResult, type RecordedPlanApproval, type RecordedRecipeApproval, type SavedInterfaceRecipe, type SavedPlanInventory, type SavedPlannerResult, type SavedRecipeInventory, type VerifiedPlanApproval, type VerifiedRecipeApproval } from "./lib/interface-api";
import { browserRecipeProposalSchema, type BrowserRecipeProposal, type RecipeTemplate } from "./lib/recipe-templates";
import { workflowSchema, type EdgeKind, type NodeCategory, type NodeGroup, type NodeKind, type Workflow as WorkflowData, type WorkflowSummary } from "./lib/workflow";

type Orientation = "horizontal" | "vertical";
type Viewport = { x: number; y: number; width: number; height: number };
type OverlayName = "tools" | "legend";
type OverlayPosition = { x: number; y: number };
type InterfaceMode = "evidence" | "proposal";
type RecipeSort = "time_desc" | "time_asc" | "name_asc" | "name_desc";
type ActiveRecipe = { recipeId: string; recipeSha256: string; steps: Array<{ step_id: string; skill_id: string; depends_on: string[] }> };
type ProposalDraft = Omit<WorkflowData, "readOnly" | "source"> & { readOnly: false; source: "proposal_draft" };
type ConnectionDrag = { pointerId: number; sourceId: string; family: PortFamily; edgeKind: EdgeKind; x: number; y: number };

const demoWorkflow = workflowSchema.parse(workflowFixture);
const labels: Record<NodeKind, string> = { input: "INPUT", data: "DATA", agent: "AGENT", policy: "CONTROL", approval: "HUMAN GATE", tool: "TOOL", evidence: "EVIDENCE" };
const icons: Record<NodeKind, typeof Bot> = { input: Map, data: Database, agent: Bot, policy: ShieldCheck, approval: LockKeyhole, tool: Database, evidence: FileCheck2 };
const fallbackCategory: Record<NodeKind, NodeCategory> = { input: "input", data: "input", agent: "planning", policy: "policy", approval: "approval", tool: "tool", evidence: "evidence" };
const groupLabels: Record<NodeGroup, string> = { intake: "Operator intake", planning: "Planner agent", governance: "Governance", execution: "Executor + tools", assurance: "Validation + evidence" };
const legacyCategories: Record<string, NodeCategory> = { request: "input", planner: "planning", policy: "policy", approval: "approval", executor: "execution", mcp: "tool", validation: "validation", release: "evidence", evidence: "evidence" };
const legacyGroups: Record<string, NodeGroup> = { request: "intake", planner: "planning", policy: "governance", approval: "governance", executor: "execution", mcp: "execution", validation: "assurance", release: "assurance", evidence: "assurance" };
const legacyTitles: Record<string, string> = { request: "Submit request", planner: "Create plan", policy: "Evaluate policy", approval: "Record approval", executor: "Execute plan", mcp: "Run GIS tool", validation: "Validate result", release: "Record evidence", evidence: "Record evidence" };
const legacyPerformers: Record<string, string> = { request: "User", planner: "Planner agent", policy: "Policy engine", approval: "Human operator", executor: "Executor agent", mcp: "MCP tool boundary", validation: "Validator", release: "Evidence service", evidence: "Evidence service" };
const standardPerformers = ["Unassigned", "User", "Planner agent", "Policy engine", "Human operator", "Executor agent", "Validator", "Critic agent", "Builder agent", "Evidence service", "MCP tool boundary", "Snakemake runner"];
const categoryOf = (node: WorkflowData["nodes"][number]) => node.category ?? legacyCategories[node.id] ?? fallbackCategory[node.kind];
const groupOf = (node: WorkflowData["nodes"][number]) => node.group ?? legacyGroups[node.id];
const titleOf = (node: WorkflowData["nodes"][number]) => node.category ? node.title : legacyTitles[node.id] ?? node.title;
const performerOf = (node: WorkflowData["nodes"][number]) => node.performedBy ?? legacyPerformers[node.id] ?? labels[node.kind];
const edgeKindOf = (edge: WorkflowData["edges"][number]): EdgeKind => {
  if (edge.kind) return edge.kind;
  if (edge.from === "validation" || edge.to === "release" || edge.to === "evidence") return "evidence";
  if (edge.from === "policy" || edge.to === "approval") return "governance";
  if (edge.from === "executor" || edge.from === "mcp" || edge.to === "mcp" || edge.to === "validation") return "data";
  return "control";
};
type PortFamily = "control" | "governance" | "data" | "evidence";
const portFamilyOf = (kind: EdgeKind): PortFamily => kind === "tool" ? "data" : kind;
const availablePortFamilies = (node: WorkflowData["nodes"][number]): PortFamily[] => {
  const category = categoryOf(node);
  if (category === "input") return ["control", "data"];
  if (category === "planning" || category === "execution") return ["control", "data"];
  if (category === "policy" || category === "approval") return ["control", "governance"];
  if (category === "tool") return ["data"];
  if (category === "validation") return ["data", "evidence"];
  return ["evidence"];
};
const edgeWouldCreateCycle = (workflow: Pick<WorkflowData, "edges">, from: string, to: string) => {
  const reachable = new Set([to]);
  const pending = [to];
  while (pending.length) {
    const current = pending.pop()!;
    for (const edge of workflow.edges.filter((candidate) => candidate.from === current)) {
      if (edge.to === from) return true;
      if (!reachable.has(edge.to)) {
        reachable.add(edge.to);
        pending.push(edge.to);
      }
    }
  }
  return false;
};
const portOffsets: Record<PortFamily, { horizontal: number; vertical: number }> = {
  control: { horizontal: 32, vertical: 45 },
  governance: { horizontal: 52, vertical: 78 },
  data: { horizontal: 76, vertical: 112 },
  evidence: { horizontal: 92, vertical: 145 },
};
const edgePoint = (node: WorkflowData["nodes"][number], role: "from" | "to", kind: EdgeKind, horizontal: boolean) => {
  const offset = portOffsets[portFamilyOf(kind)];
  return horizontal
    ? { x: node.x + (role === "from" ? 182 : 8), y: node.y + offset.horizontal }
    : { x: node.x + offset.vertical, y: node.y + (role === "from" ? 100 : 8) };
};
const minimapSize = { width: 140, height: 90 };
const clamp = (value: number, minimum: number, maximum: number) => Math.min(maximum, Math.max(minimum, value));
const topologySignature = (workflow: Pick<ProposalDraft, "nodes" | "edges">) => JSON.stringify({ nodes: workflow.nodes.map(({ id, kind, category }) => ({ id, kind, category })), edges: workflow.edges.map(({ from, to, kind }) => ({ from, to, kind })) });
const templateParameterDefaults = (template?: RecipeTemplate) => Object.fromEntries([
  ...(template?.required_parameters ?? []),
  ...(template?.optional_parameters ?? []),
].map((name) => [name, name === "target_format" ? "geopackage" : name === "resampling" ? "nearest" : ""]));
const outcomeFacts = (value: unknown): Array<[string, string]> => {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return Object.entries(value as Record<string, unknown>).map(([name, item]) => [
      name.replaceAll("_", " "),
      typeof item === "string" ? item : JSON.stringify(item),
    ]);
  }
  return [["Result", typeof value === "string" ? value : JSON.stringify(value)]];
};
const evidencePathParts = (path: string) => {
  const normalized = path.replaceAll("\\\\", "/");
  const separator = normalized.lastIndexOf("/");
  return separator < 0
    ? { filename: normalized, directory: "Project root" }
    : { filename: normalized.slice(separator + 1), directory: normalized.slice(0, separator) || "/" };
};
const searchableSkillText = (skill: PlannerSkillCatalog["skills"][number]) =>
  `${skill.id} ${skill.id.replaceAll("_", " ")} ${skill.kind ?? ""} ${skill.access ?? ""}`.toLowerCase();
const skillRecommendationScore = (skill: PlannerSkillCatalog["skills"][number], request: string) => {
  const text = request.toLowerCase();
  const tokens = new Set(text.match(/[a-z0-9]+/g) ?? []);
  const skillTokens = skill.id.split("_");
  let score = skillTokens.filter((token) => tokens.has(token)).length * 3;
  if (/\b(geojson|gpkg|shapefile|vector|feature)\b/.test(text) && skill.id.includes("vector")) score += 2;
  if (/\b(tif|tiff|raster|imagery)\b/.test(text) && skill.id.includes("raster")) score += 2;
  if (/\bpostgis\b/.test(text) && skill.id.includes("postgis")) score += 3;
  if (/\bgeoserver\b/.test(text) && skill.id.includes("geoserver")) score += 3;
  if (/\binspect\b/.test(text) && skill.id.startsWith("inspect_")) score += 4;
  if (/\b(convert|conversion)\b/.test(text) && skill.id.startsWith("convert_")) score += 4;
  if (/\b(load|import)\b/.test(text) && skill.id.startsWith("load_")) score += 4;
  if (/\b(validate|validation|verify)\b/.test(text) && /validate|verify/.test(skill.id)) score += 4;
  if (/\b(report|reporting)\b/.test(text) && skill.id.includes("report")) score += 4;
  return score;
};
const plannerWorkflow = (result: InterfacePlannerResult): WorkflowData => {
  const stepNodes: WorkflowData["nodes"] = result.plan.steps.map((step, index) => ({
    id: `planned_${step.step_id}`,
    title: step.skill.replaceAll("_", " "),
    subtitle: step.purpose,
    kind: "tool",
    category: "tool",
    group: "execution",
    x: 620 + index * 230,
    y: 330,
    status: "pending",
    authority: step.requires_approval ? "Human approval required" : "Proposed only",
    performedBy: "Not executed",
    evidence: step.expected_artifacts.join(", ") || "No artifact created",
    details: null,
  }));
  return {
    schemaVersion: "1.0",
    id: `planner-${Date.now()}`,
    title: result.plan.summary,
    correlationId: `planner-${Date.now()}`,
    readOnly: true,
    source: "validated_trace",
    nodes: [
      { id: "planned_request", title: "User request", subtitle: result.original_request, kind: "input", category: "input", group: "intake", x: 40, y: 100, status: "complete", authority: "User-authored request", performedBy: "User", evidence: "In-memory planner request", details: null },
      { id: "planned_planner", title: "Create plan", subtitle: result.model, kind: "agent", category: "planning", group: "planning", x: 300, y: 100, status: "complete", authority: "Planning only", performedBy: "Planner agent", evidence: "Schema-validated model output", details: null },
      { id: "planned_policy", title: "Review proposed plan", subtitle: "Not saved, approved, or executed", kind: "policy", category: "policy", group: "governance", x: 620, y: 100, status: "pending", authority: "Operator review required", performedBy: "Policy engine", evidence: "No durable plan evidence yet", details: null },
      ...stepNodes,
    ],
    edges: [
      { from: "planned_request", to: "planned_planner", kind: "control", label: "request" },
      { from: "planned_planner", to: "planned_policy", kind: "control", label: "proposed plan" },
      ...stepNodes.map((node) => ({ from: "planned_planner", to: node.id, kind: "data" as const, label: "proposed step" })),
    ],
  };
};

export default function App() {
  const canvasWindowRef = useRef<HTMLDivElement>(null);
  const canvasPanRef = useRef<{ pointerId: number; x: number; y: number; left: number; top: number } | null>(null);
  const nodeDragRef = useRef<{ pointerId: number; nodeId: string; x: number; y: number; originX: number; originY: number; moved: boolean } | null>(null);
  const connectionDragRef = useRef<ConnectionDrag | null>(null);
  const approvalRequestRef = useRef<HTMLElement>(null);
  const draftCounterRef = useRef(0);
  const overlayDragRef = useRef<{ name: OverlayName; pointerId: number; x: number; y: number; origin: OverlayPosition } | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowData>(demoWorkflow);
  const [draft, setDraft] = useState<ProposalDraft | null>(null);
  const [mode, setMode] = useState<InterfaceMode>("evidence");
  const [newNodeKind, setNewNodeKind] = useState<NodeKind>("tool");
  const [newEdgeKind, setNewEdgeKind] = useState<EdgeKind>("control");
  const [newEdgeTargetId, setNewEdgeTargetId] = useState("");
  const [connectionDrag, setConnectionDrag] = useState<ConnectionDrag | null>(null);
  const [recipeTemplates, setRecipeTemplates] = useState<RecipeTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [templateParameters, setTemplateParameters] = useState<Record<string, string>>({});
  const [proposalRequest, setProposalRequest] = useState("");
  const [recipeIdHint, setRecipeIdHint] = useState("");
  const [templateNotice, setTemplateNotice] = useState("");
  const [compilation, setCompilation] = useState<InterfaceCompilation | null>(null);
  const [compilationPending, setCompilationPending] = useState(false);
  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [savePending, setSavePending] = useState(false);
  const [savedRecipe, setSavedRecipe] = useState<SavedInterfaceRecipe | null>(null);
  const [templatePanelOpen, setTemplatePanelOpen] = useState(false);
  const [recipePanelOpen, setRecipePanelOpen] = useState(false);
  const [recipeInventory, setRecipeInventory] = useState<SavedRecipeInventory | null>(null);
  const [recipeInventoryNotice, setRecipeInventoryNotice] = useState("");
  const [recipeSort, setRecipeSort] = useState<RecipeSort>("time_desc");
  const [selectedRecipeSha, setSelectedRecipeSha] = useState("");
  const [preparedApproval, setPreparedApproval] = useState<PreparedApprovalRequest | null>(null);
  const [approvalPreparationPending, setApprovalPreparationPending] = useState(false);
  const [approvalDecision, setApprovalDecision] = useState<"approved" | "denied">("approved");
  const [approvalApprover, setApprovalApprover] = useState("");
  const [approvalReason, setApprovalReason] = useState("");
  const [approvalValidMinutes, setApprovalValidMinutes] = useState("60");
  const approvalApproverRef = useRef<HTMLInputElement>(null);
  const approvalReasonRef = useRef<HTMLTextAreaElement>(null);
  const approvalValidMinutesRef = useRef<HTMLInputElement>(null);
  const [approvalConfirmed, setApprovalConfirmed] = useState(false);
  const [approvalRecording, setApprovalRecording] = useState(false);
  const [recordedApproval, setRecordedApproval] = useState<RecordedRecipeApproval | null>(null);
  const [approvalDecisionNotice, setApprovalDecisionNotice] = useState("");
  const [approvalVerification, setApprovalVerification] = useState<VerifiedRecipeApproval | null>(null);
  const [approvalVerifying, setApprovalVerifying] = useState(false);
  const [approvalVerificationNotice, setApprovalVerificationNotice] = useState("");
  const [executionPreview, setExecutionPreview] = useState<ExecutionPreview | null>(null);
  const [executionPreviewPending, setExecutionPreviewPending] = useState(false);
  const [executionConfirmed, setExecutionConfirmed] = useState(false);
  const [executionPending, setExecutionPending] = useState(false);
  const [executionResult, setExecutionResult] = useState<RecipeExecutionResult | null>(null);
  const [executionNotice, setExecutionNotice] = useState("");
  const [executionFailure, setExecutionFailure] = useState("");
  const [executionProgress, setExecutionProgress] = useState<ExecutionProgress | null>(null);
  const [executionInventory, setExecutionInventory] = useState<ExecutionInventory | null>(null);
  const [executionInventoryOpen, setExecutionInventoryOpen] = useState(false);
  const [executionInventoryNotice, setExecutionInventoryNotice] = useState("");
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [plannerRequest, setPlannerRequest] = useState("");
  const [plannerPending, setPlannerPending] = useState(false);
  const [plannerNotice, setPlannerNotice] = useState("");
  const [plannerResult, setPlannerResult] = useState<InterfacePlannerResult | null>(null);
  const [plannerReviewConfirmed, setPlannerReviewConfirmed] = useState(false);
  const [plannerSavePending, setPlannerSavePending] = useState(false);
  const [savedPlannerResult, setSavedPlannerResult] = useState<SavedPlannerResult | null>(null);
  const [planApprovalPending, setPlanApprovalPending] = useState(false);
  const [preparedPlanApproval, setPreparedPlanApproval] = useState<PreparedPlanApproval | null>(null);
  const [planDecision, setPlanDecision] = useState<"approved" | "denied">("approved");
  const [planApprover, setPlanApprover] = useState("operator");
  const [planReason, setPlanReason] = useState("");
  const [planValidMinutes, setPlanValidMinutes] = useState("60");
  const [planDecisionPending, setPlanDecisionPending] = useState(false);
  const [recordedPlanApproval, setRecordedPlanApproval] = useState<RecordedPlanApproval | null>(null);
  const [planVerificationPending, setPlanVerificationPending] = useState(false);
  const [verifiedPlanApproval, setVerifiedPlanApproval] = useState<VerifiedPlanApproval | null>(null);
  const [planPreviewPending, setPlanPreviewPending] = useState(false);
  const [planExecutionPreview, setPlanExecutionPreview] = useState<PlanExecutionPreview | null>(null);
  const [planPreviewError, setPlanPreviewError] = useState("");
  const [compiledPlanRecipe, setCompiledPlanRecipe] = useState<CompiledPlanRecipe | null>(null);
  const [planRecipePending, setPlanRecipePending] = useState(false);
  const [planRecipeReviewConfirmed, setPlanRecipeReviewConfirmed] = useState(false);
  const [planRecipeSavePending, setPlanRecipeSavePending] = useState(false);
  const [savedPlanRecipe, setSavedPlanRecipe] = useState<SavedInterfaceRecipe | null>(null);
  const [planRecipeSaveError, setPlanRecipeSaveError] = useState("");
  const [plannerSkills, setPlannerSkills] = useState<PlannerSkillCatalog | null>(null);
  const [selectedPlannerSkills, setSelectedPlannerSkills] = useState<string[]>([]);
  const [plannerSkillSearch, setPlannerSkillSearch] = useState("");
  const [plannerSkillHighlight, setPlannerSkillHighlight] = useState(0);
  const [savedPlanInventory, setSavedPlanInventory] = useState<SavedPlanInventory | null>(null);
  const [savedPlansExpanded, setSavedPlansExpanded] = useState(false);
  const [savedPlanSort, setSavedPlanSort] = useState<"time_desc" | "time_asc" | "name_asc" | "name_desc">("time_desc");
  const [selectedSavedPlanSha, setSelectedSavedPlanSha] = useState("");
  const [activeRecipe, setActiveRecipe] = useState<ActiveRecipe | null>(null);
  const [templateTopologyBaseline, setTemplateTopologyBaseline] = useState<string | null>(null);
  const [loadedTemplateId, setLoadedTemplateId] = useState<string | null>(null);
  const [runs, setRuns] = useState<WorkflowSummary[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [loadNotice, setLoadNotice] = useState("");
  const [selectedId, setSelectedId] = useState("approval");
  const [zoom, setZoom] = useState(0.82);
  const [orientation, setOrientation] = useState<Orientation>(() => window.matchMedia("(max-width: 680px)").matches ? "vertical" : "horizontal");
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, width: 1, height: 1 });
  const [overlayPositions, setOverlayPositions] = useState<Record<OverlayName, OverlayPosition>>({ tools: { x: 0, y: 0 }, legend: { x: 0, y: 0 } });
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
      { id: "active_executor", title: "Governed execution", subtitle: executionProgress?.status.replaceAll("_", " ") ?? "Not started", kind: "agent", category: "execution", group: "execution", x: 1050, y: 90, status: executionStatus, authority: "Exact approved envelope", performedBy: "Executor agent", evidence: executionResult?.run_result_path ?? "Not recorded", details: null },
      ...stepNodes,
      { id: "active_validation", title: "Validate outputs", subtitle: executionResult?.status.replaceAll("_", " ") ?? "Awaiting outputs", kind: "evidence", category: "validation", group: "assurance", x: 1070 + activeRecipe.steps.length * 220, y: 90, status: validationStatus, authority: "Deterministic verification", performedBy: "Validator", evidence: executionResult?.evidence_path ?? "Not recorded", details: null },
      { id: "active_evidence", title: "Record evidence", subtitle: executionResult || executionProgress?.execution_performed ? "Durable run evidence" : "Awaiting completed run", kind: "evidence", category: "evidence", group: "assurance", x: 1300 + activeRecipe.steps.length * 220, y: 90, status: executionResult || executionProgress?.execution_performed ? "complete" : executionFailure ? "failed" : executionProgress?.status === "interrupted" ? "interrupted" : "pending", authority: "Append-only evidence", performedBy: "Evidence service", evidence: executionResult?.report_path ?? (executionProgress?.execution_performed ? "Recorded in durable run artifacts" : "Not recorded"), details: null },
    ];
    const dependencyEdges: WorkflowData["edges"] = activeRecipe.steps.flatMap((step) => step.depends_on.length ? step.depends_on.map((dependency) => ({ from: `active_${dependency}`, to: `active_${step.step_id}`, kind: "data" as const, label: "dependency" })) : [{ from: "active_executor", to: `active_${step.step_id}`, kind: "data" as const, label: "dispatch" }]);
    const dependedOn = new Set(activeRecipe.steps.flatMap((step) => step.depends_on));
    const leafSteps = activeRecipe.steps.filter((step) => !dependedOn.has(step.step_id));
    return { schemaVersion: "1.0", id: `active-${activeRecipe.recipeId}`, title: `${activeRecipe.recipeId.replaceAll("_", " ")} · governed run`, correlationId: activeRecipe.recipeSha256.slice(0, 16), readOnly: true, source: "validated_trace", nodes, edges: [{ from: "active_request", to: "active_planner", kind: "control", label: "request" }, { from: "active_data", to: "active_planner", kind: "data", label: "inputs" }, { from: "active_planner", to: "active_policy", kind: "control", label: "proposal" }, { from: "active_policy", to: "active_approval", kind: "control", label: "policy" }, { from: "active_approval", to: "active_executor", kind: "control", label: "authority" }, ...dependencyEdges, ...leafSteps.map((step) => ({ from: `active_${step.step_id}`, to: "active_validation", kind: "data" as const, label: "validate" })), { from: "active_validation", to: "active_evidence", kind: "evidence", label: "record" }] };
  }, [activeRecipe, executionFailure, executionProgress, executionResult, preparedApproval, recordedApproval]);
  const displayedWorkflow = draft ?? activeRecipeWorkflow ?? workflow;
  const selected = useMemo(() => displayedWorkflow.nodes.find((node) => node.id === selectedId) ?? displayedWorkflow.nodes[0], [displayedWorkflow, selectedId]);
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
  const runFacts = useMemo(() => ({
    inputReferences: displayedWorkflow.nodes.find((node) => node.kind === "data")?.details?.observedFacts.find((fact) => fact.label === "Context references")?.value ?? "0",
    tools: displayedWorkflow.nodes.filter((node) => node.kind === "tool").length,
  }), [displayedWorkflow.nodes]);
  const nodes = useMemo(() => {
    if (orientation === "horizontal") return displayedWorkflow.nodes;
    const minimumX = Math.min(...displayedWorkflow.nodes.map((node) => node.x));
    const minimumY = Math.min(...displayedWorkflow.nodes.map((node) => node.y));
    return displayedWorkflow.nodes.map((node) => ({
      ...node,
      x: 120 + ((node.y - minimumY) * 1.25),
      y: 35 + ((node.x - minimumX) * 0.72),
    }));
  }, [displayedWorkflow.nodes, orientation]);
  const canvasSize = useMemo(() => ({
    width: Math.max(720, Math.ceil(Math.max(...nodes.map((node) => node.x)) + 270)),
    height: Math.max(620, Math.ceil(Math.max(...nodes.map((node) => node.y)) + 190)),
  }), [nodes]);
  const connectionPreviewPath = useMemo(() => {
    if (!connectionDrag) return null;
    const source = nodes.find((node) => node.id === connectionDrag.sourceId);
    if (!source) return null;
    const horizontal = orientation === "horizontal";
    const start = edgePoint(source, "from", connectionDrag.edgeKind, horizontal);
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

  const updateViewport = useCallback(() => {
    const element = canvasWindowRef.current;
    if (!element) return;
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
    setZoom(nextZoom);
    requestAnimationFrame(() => element.scrollTo({ left: 0, top: 0, behavior: "smooth" }));
  }, [canvasSize.height, canvasSize.width]);

  useEffect(() => {
    const element = canvasWindowRef.current;
    if (!element) return;
    const observer = new ResizeObserver(updateViewport);
    observer.observe(element);
    updateViewport();
    return () => observer.disconnect();
  }, [updateViewport]);
  useEffect(() => {
    void (async () => {
      const catalog = await loadWorkflowCatalog();
      setRuns(catalog);
      if (catalog.length) {
        setSelectedTaskId(catalog[0].taskId);
        try {
          setWorkflow(await loadWorkflowProjection(demoWorkflow, catalog[0].taskId));
          setLoadNotice("");
        } catch {
          setLoadNotice("Selected run could not be loaded. Re-export the runtime projections.");
        }
      } else {
        setWorkflow(await loadWorkflowProjection(demoWorkflow));
      }
    })();
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
    if (!plannerOpen || plannerSkills) return;
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
  useEffect(() => { requestAnimationFrame(updateViewport); }, [orientation, updateViewport, zoom]);
  useEffect(() => { requestAnimationFrame(fitGraph); }, [fitGraph, orientation]);

  const toggleOrientation = () => {
    setOrientation((current) => current === "horizontal" ? "vertical" : "horizontal");
    requestAnimationFrame(() => canvasWindowRef.current?.scrollTo({ left: 0, top: 0 }));
  };
  const panFromMinimap = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    if (!element) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const targetX = ((event.clientX - bounds.left) / bounds.width) * canvasSize.width * zoom;
    const targetY = ((event.clientY - bounds.top) / bounds.height) * canvasSize.height * zoom;
    element.scrollTo({ left: targetX - element.clientWidth / 2, top: targetY - element.clientHeight / 2, behavior: "smooth" });
  };
  const centerCanvas = () => {
    const element = canvasWindowRef.current;
    if (!element) return;
    element.scrollTo({ left: (canvasSize.width * zoom - element.clientWidth) / 2, top: (canvasSize.height * zoom - element.clientHeight) / 2, behavior: "smooth" });
  };
  const handleCanvasWheel = useCallback((event: WheelEvent) => {
    const element = canvasWindowRef.current;
    if (!element) return;
    event.preventDefault();
    if (event.shiftKey) {
      element.scrollLeft += event.deltaY || event.deltaX;
      updateViewport();
      return;
    }
    setZoom((value) => clamp(value + (event.deltaY < 0 ? 0.08 : -0.08), 0.2, 1.1));
  }, [updateViewport]);
  useEffect(() => {
    const element = canvasWindowRef.current;
    if (!element) return;
    element.addEventListener("wheel", handleCanvasWheel, { passive: false });
    return () => element.removeEventListener("wheel", handleCanvasWheel);
  }, [handleCanvasWheel]);
  const startCanvasPan = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    if (!element || event.button !== 0 || (event.target as HTMLElement).closest("button")) return;
    canvasPanRef.current = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, left: element.scrollLeft, top: element.scrollTop };
    element.setPointerCapture(event.pointerId);
    element.classList.add("is-panning");
  };
  const moveCanvasPan = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    const pan = canvasPanRef.current;
    if (!element || !pan || pan.pointerId !== event.pointerId) return;
    element.scrollLeft = pan.left - (event.clientX - pan.x);
    element.scrollTop = pan.top - (event.clientY - pan.y);
    updateViewport();
  };
  const endCanvasPan = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    if (!element || canvasPanRef.current?.pointerId !== event.pointerId) return;
    canvasPanRef.current = null;
    if (element.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId);
    element.classList.remove("is-panning");
  };
  const startOverlayDrag = (name: OverlayName, event: React.PointerEvent<HTMLSpanElement>) => {
    event.preventDefault();
    event.stopPropagation();
    overlayDragRef.current = { name, pointerId: event.pointerId, x: event.clientX, y: event.clientY, origin: overlayPositions[name] };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveOverlay = (event: React.PointerEvent<HTMLSpanElement>) => {
    const drag = overlayDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    setOverlayPositions((positions) => ({ ...positions, [drag.name]: { x: drag.origin.x + event.clientX - drag.x, y: drag.origin.y + event.clientY - drag.y } }));
  };
  const endOverlayDrag = (event: React.PointerEvent<HTMLSpanElement>) => {
    if (overlayDragRef.current?.pointerId !== event.pointerId) return;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    overlayDragRef.current = null;
  };
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
    const proposal = buildRecipeProposal();
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
    const proposal = buildRecipeProposal();
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
    const proposal = buildRecipeProposal();
    if (!proposal) return;
    setSavePending(true);
    setSavedRecipe(null);
    setTemplateNotice("Recompiling and checking the reviewed digest before immutable storage…");
    try {
      const stored = await saveReviewedRecipe(proposal, compilation.recipe_sha256);
      setSavedRecipe(stored);
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
    setTemplatePanelOpen(false);
    setRecipePanelOpen(false);
    setExecutionInventoryOpen(true);
    setExecutionInventoryNotice("Loading durable execution attempts…");
    try {
      const inventory = await loadExecutionInventory();
      setExecutionInventory(inventory);
      setExecutionInventoryNotice(inventory.attempt_count ? "" : "No durable execution attempts are available yet.");
    } catch {
      setExecutionInventory(null);
      setExecutionInventoryNotice("Execution attempts could not be loaded. Confirm that the local interface service is running.");
    }
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
      setExecutionInventoryNotice("");
    } catch (error) {
      setExecutionInventoryNotice(error instanceof Error ? error.message : "Execution attempt could not be reopened.");
    }
  };
  const createPlan = async () => {
    if (!plannerRequest.trim() || !selectedPlannerSkills.length) return;
    setPlannerPending(true);
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
    try {
      const result = await createPlannerPlan(plannerRequest, selectedPlannerSkills);
      setPlannerResult(result);
      setPlannerNotice("Validated plan returned. Nothing was saved, approved, or executed.");
    } catch (error) {
      setPlannerNotice(error instanceof Error ? error.message : "Planner could not produce a validated plan.");
    } finally {
      setPlannerPending(false);
    }
  };
  const resumeSavedPlan = async (item: SavedPlanInventory["plans"][number]) => {
    setSelectedSavedPlanSha(item.plan_sha256);
    setPlannerNotice("Restoring the exact saved plan and matching decision evidence…");
    const allowed = [...new Set(item.planner_result.plan.steps.map((step) => step.skill))];
    setPlannerRequest(item.planner_result.original_request);
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
      const stored = await saveReviewedPlannerPlan(plannerResult);
      setSavedPlannerResult(stored);
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
      const recorded = await recordPlannerApproval({ stored: savedPlannerResult, prepared: preparedPlanApproval, decision: planDecision, approver: planApprover.trim(), reason: planReason.trim(), validForMinutes: minutes });
      setRecordedPlanApproval(recorded);
      setPlannerNotice(`${recorded.decision === "approved" ? "Approval" : "Denial"} recorded. Nothing was executed.`);
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
      setSavedPlanRecipe(await saveCompiledPlannerRecipe(compiledPlanRecipe, savedPlannerResult, preparedPlanApproval, recordedPlanApproval));
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
      togglePlannerSkill(plannerSkillResults[plannerSkillHighlight].id);
    } else if (event.key === "Backspace" && !plannerSkillSearch && selectedPlannerSkills.length) {
      togglePlannerSkill(selectedPlannerSkills[selectedPlannerSkills.length - 1]);
    } else if (event.key === "Escape") {
      event.currentTarget.blur();
    }
  };
  const viewPlannerGraph = () => {
    if (!plannerResult) return;
    const next = plannerWorkflow(plannerResult);
    setWorkflow(next);
    setSelectedTaskId("");
    setSelectedId("planned_planner");
    setPlannerOpen(false);
  };
  const closeRecipeFlow = () => {
    setRecipePanelOpen(false);
  };
  const exitActiveWorkflow = () => {
    setRecipePanelOpen(false);
    setTemplatePanelOpen(false);
    setActiveRecipe(null);
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
  const prepareApproval = async (recipeFilename: string, recipeSha256: string) => {
    setSelectedRecipeSha(recipeSha256);
    setApprovalPreparationPending(true);
    setPreparedApproval(null);
    setRecipeInventoryNotice("Revalidating the stored recipe and preparing an exact approval request…");
    try {
      const request = await prepareRecipeApproval(recipeFilename, recipeSha256);
      setPreparedApproval(request);
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
      setExecutionResult(await executeExactPreview(preparedApproval, recordedApproval, executionPreview));
      await refreshProgress();
      setSelectedId("active_validation");
      setExecutionNotice("");
    } catch (error) {
      const finalProgress = await refreshProgress();
      setExecutionNotice("");
      setExecutionFailure(error instanceof Error ? error.message : "Approved execution failed. Inspect outputs and evidence before retrying.");
      setSelectedId(finalProgress?.failed_step_id ? `active_${finalProgress.failed_step_id}` : "active_executor");
    } finally {
      window.clearInterval(progressTimer);
      setExecutionPending(false);
    }
  };
  const beginProposal = () => {
    setTemplateTopologyBaseline(null);
    setLoadedTemplateId(null);
    setDraft({ ...structuredClone(workflow), id: `${workflow.id}-draft`, title: `${workflow.title} draft`, readOnly: false, source: "proposal_draft" });
    setMode("proposal");
    setLoadNotice("");
  };
  const closeProposal = () => {
    connectionDragRef.current = null;
    setConnectionDrag(null);
    setTemplateTopologyBaseline(null);
    setLoadedTemplateId(null);
    setDraft(null);
    setMode("evidence");
    setSelectedId(workflow.nodes[0].id);
  };
  const updateDraftNode = (nodeId: string, patch: Partial<WorkflowData["nodes"][number]>) => {
    setDraft((current) => current ? { ...current, nodes: current.nodes.map((node) => node.id === nodeId ? { ...node, ...patch } : node) } : current);
  };
  const addDraftNode = () => {
    if (!draft || draft.nodes.length >= 100) return;
    draftCounterRef.current += 1;
    const definitions: Record<NodeKind, { title: string; subtitle: string; category: NodeCategory; group: NodeGroup; performer: string }> = {
      input: { title: "New request", subtitle: "Define operator intent", category: "input", group: "intake", performer: "User" },
      data: { title: "New input data", subtitle: "Select a bounded input", category: "input", group: "intake", performer: "Input boundary" },
      agent: { title: "New agent action", subtitle: "Define proposal responsibility", category: "planning", group: "planning", performer: "Agent" },
      policy: { title: "New policy gate", subtitle: "Define deterministic checks", category: "policy", group: "governance", performer: "Policy engine" },
      approval: { title: "New human gate", subtitle: "Define operator review", category: "approval", group: "governance", performer: "Human operator" },
      tool: { title: "New tool action", subtitle: "Select an allowlisted capability", category: "tool", group: "execution", performer: "Tool boundary" },
      evidence: { title: "New evidence step", subtitle: "Define recorded output", category: "evidence", group: "assurance", performer: "Evidence service" },
    };
    const definition = definitions[newNodeKind];
    const node = {
      id: `draft-${newNodeKind}-${draftCounterRef.current}`,
      title: definition.title,
      subtitle: definition.subtitle,
      kind: newNodeKind,
      category: definition.category,
      group: definition.group,
      x: 120 + ((draft.nodes.length % 5) * 220),
      y: 180 + (Math.floor(draft.nodes.length / 5) * 150),
      status: "pending" as const,
      authority: "Proposal only",
      performedBy: definition.performer,
      evidence: "Not recorded",
      details: null,
    };
    setDraft({ ...draft, nodes: [...draft.nodes, node] });
    setSelectedId(node.id);
  };
  const deleteDraftNode = () => {
    if (!draft || draft.nodes.length <= 1) return;
    const remaining = draft.nodes.filter((node) => node.id !== selected.id);
    setDraft({ ...draft, nodes: remaining, edges: draft.edges.filter((edge) => edge.from !== selected.id && edge.to !== selected.id) });
    setSelectedId(remaining[0].id);
  };
  const canConnect = (sourceId: string, targetId: string, kind: EdgeKind) => {
    if (!draft || sourceId === targetId) return false;
    const source = draft.nodes.find((node) => node.id === sourceId);
    const target = draft.nodes.find((node) => node.id === targetId);
    if (!source || !target) return false;
    const family = portFamilyOf(kind);
    const targetInputOccupied = draft.edges.some((edge) => edge.to === targetId && portFamilyOf(edgeKindOf(edge)) === family);
    return availablePortFamilies(source).includes(family)
      && availablePortFamilies(target).includes(family)
      && !targetInputOccupied
      && !draft.edges.some((edge) => edge.from === sourceId && edge.to === targetId && edgeKindOf(edge) === kind)
      && !edgeWouldCreateCycle(draft, sourceId, targetId);
  };
  const connectionTarget = draft?.nodes.find((node) => node.id === newEdgeTargetId);
  const connectionCompatible = Boolean(connectionTarget && canConnect(selected.id, connectionTarget.id, newEdgeKind));
  const addDraftConnection = () => {
    if (!draft || !connectionTarget || !connectionCompatible) return;
    setDraft({ ...draft, edges: [...draft.edges, { from: selected.id, to: connectionTarget.id, kind: newEdgeKind, label: newEdgeKind }] });
    setNewEdgeTargetId("");
  };
  const deleteDraftConnection = (index: number) => {
    if (!draft) return;
    setDraft({ ...draft, edges: draft.edges.filter((_, edgeIndex) => edgeIndex !== index) });
  };
  const pointerToCanvas = (clientX: number, clientY: number) => {
    const element = canvasWindowRef.current;
    if (!element) return { x: 0, y: 0 };
    const bounds = element.getBoundingClientRect();
    return { x: (clientX - bounds.left + element.scrollLeft) / zoom, y: (clientY - bounds.top + element.scrollTop) / zoom };
  };
  const startConnectionDrag = (nodeId: string, family: PortFamily, direction: "in" | "out", event: React.PointerEvent<SVGSVGElement | HTMLSpanElement>) => {
    event.stopPropagation();
    if (mode !== "proposal" || direction !== "out") return;
    const point = pointerToCanvas(event.clientX, event.clientY);
    const kind = portFamilyOf(newEdgeKind) === family ? newEdgeKind : family;
    const drag = { pointerId: event.pointerId, sourceId: nodeId, family, edgeKind: kind as EdgeKind, ...point };
    connectionDragRef.current = drag;
    setConnectionDrag(drag);
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveConnectionDrag = (event: React.PointerEvent<SVGSVGElement | HTMLSpanElement>) => {
    const drag = connectionDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const next = { ...drag, ...pointerToCanvas(event.clientX, event.clientY) };
    connectionDragRef.current = next;
    setConnectionDrag(next);
  };
  const endConnectionDrag = (event: React.PointerEvent<SVGSVGElement | HTMLSpanElement>) => {
    const drag = connectionDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>('[data-port-direction="in"]');
    const targetId = target?.dataset.portNode;
    const targetFamily = target?.dataset.portFamily;
    if (event.type !== "pointercancel" && draft && targetId && targetFamily === drag.family && canConnect(drag.sourceId, targetId, drag.edgeKind)) {
      setDraft({ ...draft, edges: [...draft.edges, { from: drag.sourceId, to: targetId, kind: drag.edgeKind, label: drag.edgeKind }] });
      setSelectedId(targetId);
    }
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    connectionDragRef.current = null;
    setConnectionDrag(null);
  };
  const startNodeDrag = (node: WorkflowData["nodes"][number], event: React.PointerEvent<HTMLButtonElement>) => {
    if (mode !== "proposal") return;
    event.stopPropagation();
    const sourceNode = displayedWorkflow.nodes.find((candidate) => candidate.id === node.id) ?? node;
    nodeDragRef.current = { pointerId: event.pointerId, nodeId: node.id, x: event.clientX, y: event.clientY, originX: sourceNode.x, originY: sourceNode.y, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveNode = (event: React.PointerEvent<HTMLButtonElement>) => {
    const drag = nodeDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId || mode !== "proposal") return;
    const dx = (event.clientX - drag.x) / zoom;
    const dy = (event.clientY - drag.y) / zoom;
    drag.moved ||= Math.abs(dx) + Math.abs(dy) > 3;
    const x = orientation === "horizontal" ? drag.originX + dx : drag.originX + (dy / 0.72);
    const y = orientation === "horizontal" ? drag.originY + dy : drag.originY + (dx / 1.25);
    updateDraftNode(drag.nodeId, { x: Math.round(clamp(x, 0, 4000)), y: Math.round(clamp(y, 0, 4000)) });
  };
  const endNodeDrag = (event: React.PointerEvent<HTMLButtonElement>) => {
    if (nodeDragRef.current?.pointerId !== event.pointerId) return;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    nodeDragRef.current = null;
  };

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark"><GitBranch size={18}/></span><span>ActionCharter</span><span className="checkpoint">17W</span></div>
      <label className="run-switcher"><CircleDot size={15}/><span className="sr-only">Select workflow run</span><select value={selectedTaskId} disabled={!runs.length || mode === "proposal"} onChange={(event) => { const taskId = event.target.value; setSelectedTaskId(taskId); void loadWorkflowProjection(demoWorkflow, taskId).then((next) => { setWorkflow(next); setSelectedId(next.nodes[0].id); setLoadNotice(""); }).catch(() => setLoadNotice("Selected run could not be loaded. Re-export the runtime projections.")); }}><option value="">{runs.length ? "Select a validated trace" : "Demonstration workflow"}</option>{runs.map((run) => <option key={run.taskId} value={run.taskId}>{run.taskId} · {run.status}</option>)}</select><ChevronDown size={14}/></label>
      <div className="top-actions">{activeRecipe && preparedApproval && !recipePanelOpen && <button className="resume-governed-run" onClick={() => setRecipePanelOpen(true)}><ArrowRight size={15}/><span>{executionResult ? "Review execution" : recordedApproval?.decision === "denied" ? "Review denial" : recordedApproval ? "Resume execution" : "Resume approval"}</span></button>}{activeRecipe && <button className="exit-active-workflow" onClick={exitActiveWorkflow}><X size={15}/><span>Exit workflow</span></button>}<button className="planner-launch" onClick={() => setPlannerOpen(true)}><Bot size={15}/><span>Plan</span></button><button className="template-launch" onClick={() => setTemplatePanelOpen(true)}><LayoutTemplate size={15}/><span>Templates</span></button><button className="recipe-launch" onClick={() => void openSavedRecipes()}><LayoutList size={15}/><span>Recipes</span></button><button className="run-history-launch" onClick={() => void openExecutionInventory()}><History size={15}/><span>Runs</span></button><button className="mode-button" onClick={mode === "evidence" ? beginProposal : closeProposal}>{mode === "evidence" ? "New proposal" : "Exit draft"}</button><button className="icon-button" aria-label="Search"><Search size={17}/></button><div className={`safe-mode ${mode === "proposal" ? "draft-mode" : ""}`}><ShieldCheck size={15}/><span>{mode === "proposal" ? "Draft only" : "Read-only"}</span></div><div className="avatar">JQ</div></div>
    </header>
    {templatePanelOpen && <div className="template-overlay" role="presentation" onPointerDown={(event) => { if (event.target === event.currentTarget) setTemplatePanelOpen(false); }}>
      <section className="template-workspace" role="dialog" aria-modal="true" aria-labelledby="template-title">
        <header className="template-workspace-head"><div><p className="eyebrow">Reusable governed starting points</p><h2 id="template-title">Choose a recipe template</h2><p>Select a recipe, review the skills it uses, provide its inputs, then preview the workflow graph.</p></div><button aria-label="Close templates" onClick={() => setTemplatePanelOpen(false)}><X size={18}/></button></header>
        <div className="concept-strip"><article><strong>Workflow</strong><span>One planned or recorded process from request through validation and evidence.</span></article><article><strong>Recipe</strong><span>A reusable, parameterized workflow definition with fixed governed steps.</span></article><article><strong>Skill</strong><span>One bounded capability a recipe step may invoke, such as inspecting a raster.</span></article></div>
        {recipeTemplates.length ? <div className="template-layout">
          <div className="template-gallery" role="list" aria-label="Trusted recipe templates">{recipeTemplates.map((template) => <button role="listitem" className={`template-card ${selectedTemplateId === template.template_id ? "selected" : ""}`} key={template.template_id} onClick={() => { setSelectedTemplateId(template.template_id); setTemplateParameters(templateParameterDefaults(template)); setRecipeIdHint(`${template.template_id}_proposal`); setTemplateNotice(""); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}><span className="template-card-title"><LayoutTemplate size={16}/><strong>{template.template_id.replaceAll("_", " ")}</strong></span><span>{template.steps.length} governed step{template.steps.length === 1 ? "" : "s"}</span><small>Skills: {template.skill_ids.map((skill) => skill.replaceAll("_", " ")).join(" · ")}</small><small>Required: {template.required_parameters.map((name) => name.replaceAll("_", " ")).join(" · ")}</small><small>Optional: {template.optional_parameters.length ? template.optional_parameters.map((name) => name.replaceAll("_", " ")).join(" · ") : "none"}</small></button>)}</div>
          <div className="template-form">
            <div className="template-selection-summary"><span>Selected recipe</span><strong>{selectedTemplate?.template_id.replaceAll("_", " ")}</strong><small>{selectedTemplate?.assessment_policy === "none" ? "Standard deterministic checks" : `${selectedTemplate?.assessment_policy.replaceAll("_", " ")} assessment`}</small></div>
            <label>Recipe ID<input value={recipeIdHint} maxLength={101} placeholder="unique_recipe_id" onChange={(event) => { setRecipeIdHint(event.target.value); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}/></label>
            <label>Requested outcome<textarea value={proposalRequest} maxLength={8000} rows={4} placeholder="Describe what this workflow should accomplish" onChange={(event) => { setProposalRequest(event.target.value); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}/></label>
            {selectedTemplate?.required_parameters.map((name) => <label key={name}>{name.replaceAll("_", " ")}<input value={templateParameters[name] ?? ""} maxLength={2000} placeholder={name} onChange={(event) => { setTemplateParameters((current) => ({ ...current, [name]: event.target.value })); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}/></label>)}
            {selectedTemplate?.optional_parameters.map((name) => <label key={name}>{name.replaceAll("_", " ")} <small>Optional</small>{name === "target_format" ? <select value={templateParameters[name] ?? ""} onChange={(event) => { setTemplateParameters((current) => ({ ...current, [name]: event.target.value })); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}><option value="">Infer from target path</option><option value="geopackage">GeoPackage</option><option value="geojson">GeoJSON</option></select> : name === "resampling" ? <select value={templateParameters[name] ?? "nearest"} onChange={(event) => { setTemplateParameters((current) => ({ ...current, [name]: event.target.value })); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}><option value="nearest">Nearest</option><option value="bilinear">Bilinear</option><option value="cubic">Cubic</option></select> : <input value={templateParameters[name] ?? ""} maxLength={2000} placeholder={`${name} (optional)`} onChange={(event) => { setTemplateParameters((current) => ({ ...current, [name]: event.target.value })); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}/>}</label>)}
            {templateNotice && <p className="template-notice">{templateNotice}</p>}
            <p className="template-boundary">Compilation is available through the loopback-only typed service. Save, approval, and execution remain unavailable.</p>
            <div className="template-actions"><button onClick={applyRecipeTemplate}>Preview workflow graph</button><button disabled={compilationPending} onClick={() => void compileTemplateProposal()}>{compilationPending ? "Compiling…" : "Compile proposal"}</button><button onClick={downloadRecipeProposal}>Download proposal</button></div>
            {compilation && <section className="compilation-result"><div><CheckCircle2 size={17}/><span><strong>Compilation passed</strong><small>{compilation.result.recipe.recipe_id}</small></span></div><div className="review-digest"><span>Recipe SHA-256</span><code title={compilation.recipe_sha256}>{compilation.recipe_sha256}</code></div><dl><div><dt>Ordered steps</dt><dd>{compilation.result.recipe_validation.topological_step_ids.length}</dd></div><div><dt>Approval gates</dt><dd>{compilation.result.recipe_validation.approval_required_step_ids.length}</dd></div><div><dt>Validation gates</dt><dd>{compilation.result.recipe_validation.validation_required_step_ids.length}</dd></div></dl><ol>{compilation.result.recipe.steps.map((step) => <li key={step.step_id}><code>{step.step_id}</code><span>{step.skill_id.replaceAll("_", " ")}</span></li>)}</ol><p><LockKeyhole size={13}/> Not saved · not approved · not executed</p><label className="review-confirm"><input type="checkbox" checked={reviewConfirmed} disabled={Boolean(savedRecipe)} onChange={(event) => setReviewConfirmed(event.target.checked)}/><span>I reviewed this exact recipe digest and step order.</span></label><button className="save-reviewed" disabled={!reviewConfirmed || savePending || Boolean(savedRecipe)} onClick={() => void saveCompiledRecipe()}>{savePending ? "Verifying and saving…" : savedRecipe ? "Recipe stored" : "Save reviewed recipe"}</button>{savedRecipe && <div className="saved-recipe"><CheckCircle2 size={15}/><span><strong>Stored immutably</strong><small>{savedRecipe.recipe_filename}</small></span><button onClick={() => setTemplatePanelOpen(false)}>View governed graph</button><button onClick={() => void openSavedRecipes()}>View saved recipes</button></div>}</section>}
          </div>
        </div> : <div className="template-unavailable"><strong>No validated template catalog loaded</strong><p>Export the trusted catalog into the ignored interface runtime directory, then reload this page.</p><code>.venv/bin/geoagent recipe-template-catalog --project-root . --pretty</code></div>}
      </section>
    </div>}
    {recipePanelOpen && <div className="template-overlay" role="presentation" onPointerDown={(event) => { if (event.target === event.currentTarget) setRecipePanelOpen(false); }}><section className="recipe-workspace" role="dialog" aria-modal="true" aria-labelledby="recipes-title"><header className="template-workspace-head"><div><p className="eyebrow">Immutable local definitions</p><h2 id="recipes-title">Saved recipes</h2><p>Inspect exact identities and prepare a digest-bound approval request. Preparing does not record approval or execute anything.</p></div><button aria-label="Close saved recipes" onClick={() => setRecipePanelOpen(false)}><X size={18}/></button></header>{recipeInventoryNotice && <p className="recipe-inventory-notice">{recipeInventoryNotice}</p>}{recipeInventory && <div className="recipe-inventory"><div className="recipe-inventory-summary"><strong>{recipeInventory.recipe_count}</strong><span>immutable recipe{recipeInventory.recipe_count === 1 ? "" : "s"}</span><small>No approval or execution performed</small><label className="recipe-sort">Order recipes<select value={recipeSort} onChange={(event) => setRecipeSort(event.target.value as RecipeSort)}><option value="time_desc">Newest first</option><option value="time_asc">Oldest first</option><option value="name_asc">Name A–Z</option><option value="name_desc">Name Z–A</option></select></label></div>{recipeInventory.recipes.length ? <div className="recipe-cards">{preparedApproval && <section ref={approvalRequestRef} tabIndex={-1} className="approval-request"><header><ShieldCheck size={18}/><span><strong>Approval request prepared</strong><small>{preparedApproval.recipe_id}</small></span></header><div><span>Request SHA-256</span><code title={preparedApproval.approval_request_sha256}>{preparedApproval.approval_request_sha256}</code></div><div><span>Recipe SHA-256</span><code title={preparedApproval.recipe_sha256}>{preparedApproval.recipe_sha256}</code></div><h3>Exact approval scope</h3><ul>{preparedApproval.approval_required_step_ids.map((stepId) => { const step = preparedApproval.steps.find((candidate) => candidate.step_id === stepId); return <li key={stepId}><code>{stepId}</code><span>{step?.skill_id.replaceAll("_", " ")}</span></li>; })}</ul><p><LockKeyhole size={13}/> Prepared only · no decision recorded · nothing executed</p></section>}{sortedRecipes.map((recipe) => <article className={`recipe-card ${preparedApproval?.recipe_sha256 === recipe.recipe_sha256 ? "selected" : ""}`} key={recipe.recipe_sha256}><header><LayoutList size={16}/><span><strong>{recipe.recipe_id}</strong><small>{recipe.recipe_filename}</small></span><time dateTime={recipe.saved_at}>{new Date(recipe.saved_at).toLocaleString()}</time></header><div className="recipe-card-digest"><span>SHA-256</span><code title={recipe.recipe_sha256}>{recipe.recipe_sha256}</code></div><ol>{recipe.steps.map((step) => <li key={step.step_id}><code>{step.step_id}</code><span>{step.skill_id.replaceAll("_", " ")}</span>{recipe.approval_required_step_ids.includes(step.step_id) && <em>Approval required</em>}</li>)}</ol><footer><span>{recipe.validation_required_step_ids.length} validation gate{recipe.validation_required_step_ids.length === 1 ? "" : "s"}</span><button disabled={approvalPreparationPending || !recipe.approval_required_step_ids.length} onClick={() => void prepareApproval(recipe.recipe_filename, recipe.recipe_sha256)}>{approvalPreparationPending ? "Preparing…" : "Prepare approval request"}</button></footer></article>)}</div> : <div className="recipe-inventory-empty"><LayoutList size={22}/><strong>No saved recipes yet</strong><span>Compile and explicitly save a reviewed template proposal first.</span></div>}</div>}</section></div>}
    {executionInventoryOpen && <div className="template-overlay" role="presentation" onPointerDown={(event) => { if (event.target === event.currentTarget) setExecutionInventoryOpen(false); }}><section className="execution-inventory-workspace" role="dialog" aria-modal="true" aria-labelledby="runs-title"><header className="template-workspace-head"><div><p className="eyebrow">Durable governed history</p><h2 id="runs-title">Execution attempts</h2><p>Reopen persisted progress after closing the browser or restarting the interface API. This view cannot retry an execution.</p></div><button aria-label="Close execution attempts" onClick={() => setExecutionInventoryOpen(false)}><X size={18}/></button></header>{executionInventoryNotice && <p className="recipe-inventory-notice">{executionInventoryNotice}</p>}{executionInventory && <div className="execution-attempts"><div className="execution-attempt-summary"><strong>{executionInventory.attempt_count}</strong><span>durable attempt{executionInventory.attempt_count === 1 ? "" : "s"}</span><small>Read-only inventory · no execution performed</small></div>{executionInventory.attempts.map((attempt) => <article className={`execution-attempt status-${attempt.status}`} key={attempt.execution_preview_sha256}><header><span><strong>{attempt.recipe_id ?? "Legacy execution attempt"}</strong><small>{attempt.status.replaceAll("_", " ")}</small></span><time dateTime={attempt.started_at}>{new Date(attempt.started_at).toLocaleString()}</time></header><dl><div><dt>Steps</dt><dd>{attempt.step_count}</dd></div><div><dt>Stopped at</dt><dd>{attempt.failed_step_id ?? "—"}</dd></div><div><dt>Finished</dt><dd>{attempt.finished_at ? new Date(attempt.finished_at).toLocaleString() : "In progress"}</dd></div></dl><code title={attempt.execution_preview_sha256}>{attempt.execution_preview_sha256}</code><button disabled={!attempt.recipe_id || !attempt.recipe_sha256} onClick={() => void reopenExecutionAttempt(attempt.execution_preview_sha256)}>{attempt.status === "running" ? "View live graph" : "Reopen run graph"}</button></article>)}</div>}</section></div>}
    {plannerOpen && <div className="template-overlay" role="presentation" onPointerDown={(event) => { if (event.target === event.currentTarget && !plannerPending) setPlannerOpen(false); }}>
      <section className="planner-workspace" role="dialog" aria-modal="true" aria-labelledby="planner-title">
        <header className="template-workspace-head"><div><p className="eyebrow">Planner agent · configured model service</p><h2 id="planner-title">Plan a governed task</h2><p>Describe the result and explicitly choose the only skills the model may propose. This action cannot save, approve, or execute anything.</p></div><button aria-label="Close planner" disabled={plannerPending} onClick={() => setPlannerOpen(false)}><X size={18}/></button></header>
        <div className="planner-body">
          {savedPlanInventory && savedPlanInventory.plans.length > 0 && <section className={`saved-plan-strip ${savedPlansExpanded ? "expanded" : "collapsed"}`}><header><button type="button" className="saved-plan-toggle" aria-expanded={savedPlansExpanded} onClick={() => setSavedPlansExpanded((value) => !value)}><span><strong>Saved plans</strong><small>{selectedSavedPlanSha ? "Plan selected · click to change" : "Restore immutable plan evidence"}</small></span><em>{savedPlanInventory.plan_count}</em><ArrowRight className={savedPlansExpanded ? "expanded" : ""} size={14}/></button></header>{savedPlansExpanded && <><label className="saved-plan-sort">Order<select value={savedPlanSort} onChange={(event) => setSavedPlanSort(event.target.value as typeof savedPlanSort)}><option value="time_desc">Newest first</option><option value="time_asc">Oldest first</option><option value="name_asc">Name A–Z</option><option value="name_desc">Name Z–A</option></select></label><div className="saved-plan-list">{sortedSavedPlans.map((item) => { const decisionDetails = item.approvals.length ? item.approvals.map((approval) => `${approval.decision.toUpperCase()} · ${approval.step_ids.join(", ")} · ${new Date(approval.created_at).toLocaleString()}`).join("\n") : "No decisions recorded"; return <button type="button" className={selectedSavedPlanSha === item.plan_sha256 ? "selected" : ""} title={decisionDetails} key={item.plan_sha256} onClick={(event) => { event.preventDefault(); event.stopPropagation(); void resumeSavedPlan(item); }}><span className="saved-plan-main"><strong>{item.planner_result.plan.summary}</strong><small>{item.planner_result.plan.steps.map((step) => step.skill.replaceAll("_", " ")).join(" · ")}</small></span><span className="saved-plan-metrics"><time dateTime={item.saved_at}>{new Date(item.saved_at).toLocaleString()}</time><em>{item.approvals.length} decision{item.approvals.length === 1 ? "" : "s"}</em></span><ArrowRight size={14}/></button>})}</div></>}</section>}
          <label>Task request<textarea value={plannerRequest} maxLength={8000} rows={6} placeholder="Inspect data/input/sample_points.geojson." onChange={(event) => { setPlannerRequest(event.target.value); setPlannerResult(null); setPlannerNotice(""); }}/></label>
          <fieldset className="planner-skill-selector"><legend>Allowed skills</legend><p>Search and explicitly select the only implemented capabilities this plan may contain. Recommendations never grant authority.</p>
            <label className="planner-skill-search"><Search size={15}/><input value={plannerSkillSearch} placeholder="Search skills by name, kind, or access…" disabled={plannerPending} onChange={(event) => { setPlannerSkillSearch(event.target.value); setPlannerSkillHighlight(0); }} onKeyDown={navigatePlannerSkills}/><kbd>↑↓ Enter</kbd></label>
            {selectedPlannerSkills.length > 0 && <section className="planner-selected-skills" aria-label="Selected planner skills"><h3>Selected · {selectedPlannerSkills.length}</h3><div>{selectedPlannerSkills.map((skillId) => <button key={skillId} type="button" disabled={plannerPending} onClick={() => togglePlannerSkill(skillId)}><span>{skillId.replaceAll("_", " ")}</span><X size={12}/></button>)}</div></section>}
            {!plannerSkillSearch && recommendedPlannerSkills.length > 0 && <section className="planner-recommended-skills"><h3>Recommended for this request</h3><div>{recommendedPlannerSkills.map((skill) => <button key={skill.id} type="button" className={selectedPlannerSkills.includes(skill.id) ? "selected" : ""} disabled={plannerPending} onClick={() => togglePlannerSkill(skill.id)}><span><strong>{skill.id.replaceAll("_", " ")}</strong><small>{skill.kind} · {skill.access}</small></span>{selectedPlannerSkills.includes(skill.id) ? <CheckCircle2 size={15}/> : <Plus size={15}/>}</button>)}</div></section>}
            <section className="planner-skill-results"><h3>{plannerSkillSearch ? `Search results · ${plannerSkillResults.length}` : `All implemented skills · ${plannerSkillResults.length}`}</h3><div role="listbox" aria-label="Implemented planner skills">{plannerSkillResults.map((skill, index) => <button key={skill.id} type="button" role="option" aria-selected={selectedPlannerSkills.includes(skill.id)} className={`${selectedPlannerSkills.includes(skill.id) ? "selected" : ""} ${plannerSkillHighlight === index ? "highlighted" : ""}`} disabled={plannerPending} onMouseEnter={() => setPlannerSkillHighlight(index)} onClick={() => togglePlannerSkill(skill.id)}><span><strong>{skill.id.replaceAll("_", " ")}</strong><small>{skill.kind} · {skill.access}</small><em>{skill.approval_required ? "Approval required" : "No write approval"}{skill.validation_required ? " · validation required" : ""}</em></span>{selectedPlannerSkills.includes(skill.id) ? <CheckCircle2 size={16}/> : <Plus size={16}/>}</button>)}</div>{!plannerSkillResults.length && <p>No implemented skills match this search.</p>}</section>
          </fieldset>
          <div className="planner-authority"><Bot size={18}/><span><strong>Planning authority only</strong><small>{selectedPlannerSkills.length} explicitly allowed skill{selectedPlannerSkills.length === 1 ? "" : "s"} · compact context · no tools executed</small></span></div>
          <button className="planner-submit" disabled={plannerPending || !plannerRequest.trim() || !selectedPlannerSkills.length} onClick={() => void createPlan()}>{plannerPending ? "Planning and validating…" : "Generate validated plan"}</button>
          {plannerNotice && <p className="planner-notice">{plannerNotice}</p>}
          {plannerResult && <section className="planner-result"><header><CheckCircle2 size={22}/><span><strong>Validated plan ready</strong><small>{plannerResult.model} · {plannerResult.plan.steps.length} proposed steps</small></span></header><p>{plannerResult.plan.summary}</p><ol>{plannerResult.plan.steps.map((step) => <li key={step.step_id}><code>{step.step_id}</code><span><strong>{step.skill.replaceAll("_", " ")}</strong><small>{step.purpose}</small></span>{step.requires_approval && <em>Approval required</em>}</li>)}</ol><div className="planner-plan-digest"><span>Plan SHA-256</span><code title={plannerResult.plan_sha256}>{plannerResult.plan_sha256}</code></div><div className="planner-outcome"><strong>{preparedPlanApproval ? preparedPlanApproval.status === "approval_not_required" ? "APPROVAL NOT REQUIRED" : "APPROVAL REQUEST PREPARED" : savedPlannerResult ? "STORED · NOT APPROVED" : "PLANNED ONLY"}</strong><span>{preparedPlanApproval ? "No decision recorded · nothing executed" : savedPlannerResult ? "Immutable plan evidence created · nothing approved · nothing executed" : "Nothing saved · nothing approved · nothing executed"}</span></div><label className="planner-review-confirm"><input type="checkbox" checked={plannerReviewConfirmed} disabled={Boolean(savedPlannerResult)} onChange={(event) => setPlannerReviewConfirmed(event.target.checked)}/><span>I reviewed this exact plan digest, steps, arguments, and approval requirements.</span></label><div className="planner-result-actions"><button onClick={viewPlannerGraph}>View plan graph</button><button className="planner-save" disabled={!plannerReviewConfirmed || plannerSavePending || Boolean(savedPlannerResult)} onClick={() => void savePlannerPlan()}>{plannerSavePending ? "Verifying and saving…" : savedPlannerResult ? "Plan stored" : "Save reviewed plan"}</button></div>{savedPlannerResult && <div className="planner-stored"><CheckCircle2 size={16}/><span><strong>Stored immutably</strong><small>{savedPlannerResult.plan_filename}</small></span><button disabled={planApprovalPending || Boolean(preparedPlanApproval)} onClick={() => void preparePlanApproval()}>{planApprovalPending ? "Preparing…" : preparedPlanApproval ? "Request prepared" : "Prepare approval request"}</button></div>}{preparedPlanApproval && <div className="planner-approval-prepared"><ShieldCheck size={18}/><span><strong>{preparedPlanApproval.status === "approval_not_required" ? "No approval-required steps" : "Exact approval scope prepared"}</strong><small>{preparedPlanApproval.approval_required_step_ids.length ? preparedPlanApproval.approval_required_step_ids.join(" · ") : "The validated plan is read-only."}</small></span><code title={preparedPlanApproval.approval_request_sha256}>{preparedPlanApproval.approval_request_sha256}</code></div>}</section>}
          {plannerResult && preparedPlanApproval?.status === "prepared_not_recorded" && <section className="planner-scope-review"><h3>Exact scope under review</h3>{preparedPlanApproval.steps.map((step) => <article key={step.step_id}><header><code>{step.step_id}</code><strong>{step.skill.replaceAll("_", " ")}</strong></header><p>{step.purpose}</p><pre>{JSON.stringify(step.arguments, null, 2)}</pre><dl><div><dt>Approval required</dt><dd>{step.requires_approval ? "true" : "false"}</dd></div><div><dt>Validation required</dt><dd>{step.validation_required ? "true" : "false"}</dd></div></dl></article>)}</section>}
          {plannerResult && preparedPlanApproval?.status === "prepared_not_recorded" && <section className="planner-decision"><h3>Human decision</h3><div className="planner-decision-choice"><button className={planDecision === "approved" ? "selected approved" : ""} disabled={Boolean(recordedPlanApproval)} onClick={() => setPlanDecision("approved")}>Approve exact scope</button><button className={planDecision === "denied" ? "selected denied" : ""} disabled={Boolean(recordedPlanApproval)} onClick={() => setPlanDecision("denied")}>Deny</button></div><label>Approver<input value={planApprover} disabled={Boolean(recordedPlanApproval)} maxLength={200} onChange={(event) => setPlanApprover(event.target.value)}/></label><label>Reason<textarea value={planReason} disabled={Boolean(recordedPlanApproval)} maxLength={2000} rows={3} onChange={(event) => setPlanReason(event.target.value)}/></label><label>Valid for minutes <small>Optional</small><input value={planValidMinutes} disabled={Boolean(recordedPlanApproval)} inputMode="numeric" onChange={(event) => setPlanValidMinutes(event.target.value)}/></label><button className="record-plan-decision" disabled={planDecisionPending || Boolean(recordedPlanApproval) || !planApprover.trim() || !planReason.trim()} onClick={() => void recordPlanDecision()}>{planDecisionPending ? "Recording…" : recordedPlanApproval ? `${recordedPlanApproval.decision === "approved" ? "Approval" : "Denial"} recorded` : `Record ${planDecision}`}</button>{recordedPlanApproval && <div className={`recorded-plan-decision ${recordedPlanApproval.decision}`}><strong>{recordedPlanApproval.decision === "approved" ? "APPROVED" : "DENIED"}</strong><span>Append-only evidence created · nothing executed</span><code>{recordedPlanApproval.approval_filename}</code></div>}</section>}
          {recordedPlanApproval && <section className={`planner-verification ${verifiedPlanApproval?.approved ? "approved" : verifiedPlanApproval ? "blocked" : ""}`}><h3>Independent verification</h3>{verifiedPlanApproval ? <><strong>{verifiedPlanApproval.approved ? "APPROVAL VERIFIED" : "EXECUTION BLOCKED"}</strong><p>{verifiedPlanApproval.reason}</p><small>Nothing executed</small>{!verifiedPlanApproval.approved && <button className="fresh-plan-decision" onClick={beginFreshPlanDecision}>Record a fresh decision</button>}</> : <button disabled={planVerificationPending} onClick={() => void verifyPlanDecision()}>{planVerificationPending ? "Verifying immutable evidence…" : "Verify recorded decision"}</button>}</section>}
          {verifiedPlanApproval?.approved && <section className="planner-envelope-preview"><h3>Execution envelope</h3>{planExecutionPreview ? <><div><span>Preview SHA-256</span><code>{planExecutionPreview.execution_preview_sha256}</code></div><pre>{JSON.stringify(planExecutionPreview.envelope, null, 2)}</pre><strong>PREVIEW ONLY · EXECUTION UNAVAILABLE</strong></> : <button disabled={planPreviewPending} onClick={() => void previewPlanExecution()}>{planPreviewPending ? "Building exact envelope…" : "Preview approved execution"}</button>}{planPreviewError && <div className="planner-preview-blocked" role="alert"><strong>PREVIEW BLOCKED</strong><span>{planPreviewError}</span><small>Approval evidence remains recorded · nothing executed</small></div>}</section>}
          {verifiedPlanApproval?.approved && <section className="planner-recipe-bridge"><header><span>Next governed boundary</span><h3>Compile a recipe candidate</h3><p>Translate this verified plan into the existing typed recipe contract. Compilation does not save, approve, or execute it.</p></header><button className="compile-plan-recipe" disabled={planRecipePending || Boolean(compiledPlanRecipe)} onClick={() => void compilePlanRecipe()}><span>{planRecipePending ? "Compiling…" : compiledPlanRecipe ? "Recipe candidate ready" : "Compile governed recipe"}</span><small>{compiledPlanRecipe ? "Review the exact digest below" : "Deterministic policy validation"}</small></button>{compiledPlanRecipe && <div className="compiled-plan-recipe"><strong>COMPILED · NOT SAVED</strong><code>{compiledPlanRecipe.recipe_sha256}</code><pre>{JSON.stringify(compiledPlanRecipe.recipe, null, 2)}</pre><small>Separate recipe review and approval still required · nothing executed</small><label className="plan-recipe-review"><input type="checkbox" checked={planRecipeReviewConfirmed} disabled={Boolean(savedPlanRecipe)} onChange={(event) => setPlanRecipeReviewConfirmed(event.target.checked)}/><span>I reviewed this exact recipe digest and ordered steps.</span></label><button className="save-plan-recipe" disabled={!planRecipeReviewConfirmed || planRecipeSavePending || Boolean(savedPlanRecipe)} onClick={() => void savePlanRecipe()}>{planRecipeSavePending ? "Recompiling and saving…" : savedPlanRecipe ? "Recipe stored immutably" : "Save reviewed recipe"}</button>{savedPlanRecipe && <div className="saved-plan-recipe"><strong>STORED · NOT APPROVED</strong><code>{savedPlanRecipe.recipe_filename}</code><button onClick={() => void openSavedRecipes(savedPlanRecipe.recipe_sha256)}>Review recipe approval scope</button></div>}</div>}</section>}
          {planRecipeSaveError && <div className="plan-recipe-save-error" role="alert"><strong>RECIPE NOT STORED</strong><span>{planRecipeSaveError}</span><small>Nothing approved · nothing executed</small></div>}
        </div>
      </section>
    </div>}
    {recipePanelOpen && preparedApproval && <aside className="approval-decision-drawer" aria-label="Record human approval decision"><header><div><p className="eyebrow">Human decision</p><h2>Record approval</h2></div><span className="decision-no-execute"><LockKeyhole size={14}/> No execution</span></header>{recordedApproval ? <div className={`recorded-decision decision-${recordedApproval.decision}`}><CheckCircle2 size={22}/><strong>{recordedApproval.decision === "approved" ? "Approval recorded" : "Denial recorded"}</strong><small>{recordedApproval.approval_filename}</small><dl><div><dt>Decision</dt><dd>{recordedApproval.decision}</dd></div><div><dt>Steps</dt><dd>{recordedApproval.approved_step_ids.join(", ")}</dd></div><div><dt>Expires</dt><dd>{recordedApproval.expires_at ? new Date(recordedApproval.expires_at).toLocaleString() : "No expiry"}</dd></div></dl><p><ShieldCheck size={14}/> Append-only evidence created · nothing executed</p></div> : <><div className="decision-binding"><span>Bound request</span><code title={preparedApproval.approval_request_sha256}>{preparedApproval.approval_request_sha256}</code><small>{preparedApproval.approval_required_step_ids.join(", ")}</small></div><label>Decision<select value={approvalDecision} onChange={(event) => { setApprovalDecision(event.target.value as "approved" | "denied"); setApprovalConfirmed(false); }}><option value="approved">Approve exact steps</option><option value="denied">Deny request</option></select></label><label>Approver<input ref={approvalApproverRef} defaultValue={approvalApprover} maxLength={200} placeholder="Operator name or role" onBlur={(event) => { setApprovalApprover(event.target.value); setApprovalConfirmed(false); }}/></label><label>Reason<textarea ref={approvalReasonRef} defaultValue={approvalReason} maxLength={2000} rows={4} placeholder="Why is this decision appropriate?" onBlur={(event) => { setApprovalReason(event.target.value); setApprovalConfirmed(false); }}/></label><label>Valid for minutes <small>Leave blank for no expiry; maximum 1440</small><input ref={approvalValidMinutesRef} defaultValue={approvalValidMinutes} inputMode="numeric" placeholder="60" onBlur={(event) => { setApprovalValidMinutes(event.target.value); setApprovalConfirmed(false); }}/></label><label className="decision-confirm"><input type="checkbox" checked={approvalConfirmed} onChange={(event) => setApprovalConfirmed(event.target.checked)}/><span>I confirm this decision applies to the displayed request digest and exact step scope.</span></label>{approvalDecisionNotice && <p className="decision-notice">{approvalDecisionNotice}</p>}<button className={`record-decision decision-${approvalDecision}`} disabled={!approvalConfirmed || approvalRecording} onClick={() => void recordApprovalDecision()}>{approvalRecording ? "Revalidating and recording…" : approvalDecision === "approved" ? "Record approval" : "Record denial"}</button><p className="decision-boundary"><ShieldCheck size={14}/> This writes approval evidence only. It cannot execute the recipe.</p></>}</aside>}
    {recipePanelOpen && preparedApproval && <button className="close-recipe-flow" aria-label="Close recipe workflow" title="Close recipe workflow" onClick={closeRecipeFlow}><X size={18}/></button>}
    {recipePanelOpen && recordedApproval && <section className={`authority-outcome-dock decision-${recordedApproval.decision}`} aria-live="polite">
      <div className="authority-outcome-primary"><ShieldCheck size={26}/><span><small>Authority evidence</small><strong>Append-only {recordedApproval.decision} recorded</strong><em>{recordedApproval.approval_filename}</em></span></div>
      <div className="authority-outcome-safety"><LockKeyhole size={24}/><span><small>Execution boundary</small><strong>Nothing executed</strong><em>No tool or workflow run was started.</em></span></div>
      {approvalVerification ? <div className={`authority-verification ${approvalVerification.approved ? "verified-approved" : "verified-blocked"}`}><CheckCircle2 size={24}/><span><small>Independent verification</small><strong>{approvalVerification.approved ? "Approval verified" : "Execution remains blocked"}</strong><em>{approvalVerification.reason}</em></span></div> : <button className="verify-approval" disabled={approvalVerifying} onClick={() => void verifyApprovalDecision()}>{approvalVerifying ? "Verifying immutable evidence…" : "Verify recorded decision"}</button>}
      {approvalVerification?.approved && !executionPreview && <button className="preview-execution" disabled={executionPreviewPending} onClick={() => void previewApprovedExecution()}>{executionPreviewPending ? "Preparing exact preview…" : "Preview approved execution"}</button>}
      {approvalVerificationNotice && <p>{approvalVerificationNotice}</p>}
      <button className="view-live-workflow" onClick={() => setRecipePanelOpen(false)}>View live workflow graph</button>
    </section>}
    {recipePanelOpen && executionPreview && <section className="execution-preview-panel" aria-label="Non-executing execution preview">
      <header><div><p className="eyebrow">Exact execution envelope</p><h2>Execution preview</h2></div><span><LockKeyhole size={14}/> Preview only</span></header>
      <div className="preview-identities"><div><small>Recipe</small><strong>{executionPreview.recipe_id}</strong><code title={executionPreview.recipe_sha256}>{executionPreview.recipe_sha256}</code></div><div><small>Approval</small><strong>{executionPreview.approval_id}</strong><code>{executionPreview.approval_filename}</code></div></div>
      <ol>{executionPreview.steps.map((step) => <li key={step.step_id}><span className="preview-position">{step.position}</span><div><strong>{step.skill_id.replaceAll("_", " ")}</strong><small>{step.access?.replaceAll("_", " ")} · {step.validation_required ? "validation required" : "no post-write validation"}</small><dl>{Object.entries(step.arguments).map(([name, value]) => <div key={name}><dt>{name.replaceAll("_", " ")}</dt><dd>{typeof value === "string" ? value : JSON.stringify(value)}</dd></div>)}</dl><em>Outputs: {step.output_ids.join(", ") || "none declared"}</em></div></li>)}</ol>
      <footer><div><small>Evidence destinations</small><strong>{executionPreview.evidence_destinations.join(" · ")}</strong></div>{executionResult ? <div className={`execution-complete ${executionResult.status}`}>{executionResult.status === "validated_success" ? <CheckCircle2 size={20}/> : <XCircle size={20}/>}<span><strong>{executionResult.status === "validated_success" ? "Execution validated" : "Validation failed"}</strong><small>Evidence and report were recorded.</small></span></div> : <div className="preview-not-executed"><LockKeyhole size={19}/><span><strong>Not executed yet</strong><small>{executionPreview.execution_available ? "A separate confirmation is required." : "Restart the API with write tools explicitly enabled."}</small></span></div>}</footer>
      {!executionResult && <section className="execution-confirmation"><label><input type="checkbox" checked={executionConfirmed} disabled={!executionPreview.execution_available || executionPending} onChange={(event) => setExecutionConfirmed(event.target.checked)}/><span>I reviewed this exact preview digest and authorize this one governed execution.</span></label><code title={executionPreview.execution_preview_sha256}>{executionPreview.execution_preview_sha256}</code><button disabled={!executionPreview.execution_available || !executionConfirmed || executionPending} onClick={() => void runExactPreview()}>{executionPending ? "Executing and recording evidence…" : "Execute exact approved preview"}</button>{executionNotice && <p>{executionNotice}</p>}</section>}
      {executionFailure && <section className="execution-failure-verdict" role="alert" aria-live="assertive"><XCircle size={38}/><span><small>Final execution status</small><strong>EXECUTION FAILED</strong><em>{executionFailure}</em><b>No success was recorded. Review the target and prepare a fresh governed run before retrying.</b></span></section>}
      {executionProgress && <section className={`execution-progress progress-${executionProgress.status}`} aria-live="polite"><header><span><small>Live execution state</small><strong>{executionProgress.status.replaceAll("_", " ")}</strong></span><time dateTime={executionProgress.started_at}>Started {new Date(executionProgress.started_at).toLocaleTimeString()}</time></header><ol>{executionProgress.steps.map((step) => <li key={step.step_id} className={`progress-step status-${step.status}`}><span className="progress-step-marker">{step.status === "running" ? <CircleDot size={17}/> : step.status === "failed" || step.status === "validation_failed" || step.status === "interrupted" ? <XCircle size={17}/> : <CheckCircle2 size={17}/>}</span><span><strong>{step.step_id} · {step.skill_id.replaceAll("_", " ")}</strong><small>{step.status.replaceAll("_", " ")}{executionProgress.failed_step_id === step.step_id ? executionProgress.status === "interrupted" ? " · interruption location" : " · failure location" : ""}</small></span></li>)}</ol>{executionProgress.failed_step_id && <p><XCircle size={16}/> {executionProgress.status === "interrupted" ? "Interruption localized to" : "Failure localized to"} <strong>{executionProgress.failed_step_id}</strong></p>}{executionProgress.recovery_guidance && <p className="recovery-guidance"><ShieldCheck size={16}/><span><strong>Safe recovery</strong>{executionProgress.recovery_guidance}</span></p>}</section>}
      {executionResult && <section className={`execution-result result-${executionResult.status}`} aria-live="assertive"><header className="execution-verdict">{executionResult.status === "validated_success" ? <CheckCircle2 size={34}/> : <XCircle size={34}/>}<span><small>Final execution status</small><strong>{executionResult.status === "validated_success" ? "SUCCESS — OUTPUT VALIDATED" : "FAILURE — VALIDATION DID NOT PASS"}</strong><em>{executionResult.status === "validated_success" ? "The approved recipe ran and its deterministic checks passed." : "Do not treat the produced output as a successful result."}</em></span></header><ol>{executionResult.step_results.map((step) => <li key={step.step_id}><div className="execution-step-line">{step.status === "validation_failed" ? <XCircle size={15}/> : <CheckCircle2 size={15}/>}<strong>{step.step_id} · {step.skill_id.replaceAll("_", " ")}</strong><small>{step.status} · validation {step.validation_performed ? "performed" : "not required"}</small></div><div className="execution-outcome"><h3>Outcome</h3>{outcomeFacts(step.outcome).map(([name, value]) => <div key={name}><span>{name}</span><strong>{value}</strong></div>)}{step.validation_outcome !== null && <><h3>Validation</h3>{outcomeFacts(step.validation_outcome).map(([name, value]) => <div key={`validation-${name}`}><span>{name}</span><strong>{value}</strong></div>)}</>}</div></li>)}</ol><dl>{[["Run result", executionResult.run_result_path], ["Evidence", executionResult.evidence_path], ["Report", executionResult.report_path]].map(([label, path]) => { const parts = evidencePathParts(path); return <div key={label}><dt>{label}</dt><dd><strong>{parts.filename}</strong><small>{parts.directory}</small></dd></div>; })}</dl></section>}
    </section>}
    <div className="workspace">
      <aside className="rail">
        <button className="rail-item active"><Workflow size={19}/><span>Flow</span></button><button className="rail-item"><Bot size={19}/><span>Agents</span></button><button className="rail-item"><FileCheck2 size={19}/><span>Evidence</span></button><button className="rail-item"><Database size={19}/><span>Data</span></button><div className="rail-spacer"/><button className="rail-item"><Map size={19}/><span>Guide</span></button>
      </aside>
      <section className="flow-stage" aria-label="Governed workflow graph">
        <div className="stage-heading"><div><p className="eyebrow">{mode === "proposal" ? "Proposal editor" : "Governed workflow"}</p><h1>{displayedWorkflow.title}</h1><p className="run-identity">{displayedWorkflow.correlationId}</p>{loadNotice && <p className="load-notice">{loadNotice}</p>}</div><div className="stage-meta"><span><span className="pulse"/> {mode === "proposal" ? "Uncommitted draft" : displayedWorkflow.source === "validated_trace" ? "Validated trace" : "Demonstration"}</span><span>{runFacts.inputReferences} input ref{runFacts.inputReferences === "1" ? "" : "s"}</span><span>{runFacts.tools} tool{runFacts.tools === 1 ? "" : "s"}</span><span>{nodes.length} nodes</span></div></div>
        <div className="canvas-frame">
          {mode === "proposal" && <div className="proposal-toolbar"><strong>Draft only</strong>{loadedTemplateId && <button className="return-template" onClick={() => setTemplatePanelOpen(true)}><LayoutTemplate size={14}/> Back to template setup</button>}<select aria-label="Node type" value={newNodeKind} onChange={(event) => setNewNodeKind(event.target.value as NodeKind)}>{Object.keys(labels).map((kind) => <option key={kind} value={kind}>{labels[kind as NodeKind]}</option>)}</select><button onClick={addDraftNode}><Plus size={14}/> Add node</button><span>No approval or execution authority</span></div>}
          <div className="canvas-tools draggable-overlay" style={{ transform: `translate(${overlayPositions.tools.x}px, ${overlayPositions.tools.y}px)` }}>
            <span className="overlay-grip" title="Drag controls" onPointerDown={(event) => startOverlayDrag("tools", event)} onPointerMove={moveOverlay} onPointerUp={endOverlayDrag} onPointerCancel={endOverlayDrag}><GripVertical size={14}/></span>
            <button aria-label="Zoom in" title="Zoom in" onClick={() => setZoom((value) => Math.min(1.1, value + 0.08))}><Plus size={16}/></button>
            <button aria-label="Zoom out" title="Zoom out" onClick={() => setZoom((value) => Math.max(0.2, value - 0.08))}><Minus size={16}/></button>
            <button aria-label="Fit entire graph" title="Fit entire graph" onClick={fitGraph}><Maximize2 size={16}/></button>
            <button className="orientation-button" aria-label={`Switch to ${orientation === "horizontal" ? "vertical" : "horizontal"} layout`} title={`Switch to ${orientation === "horizontal" ? "vertical" : "horizontal"} layout`} onClick={toggleOrientation}>{orientation === "horizontal" ? <ArrowDown size={16}/> : <ArrowRight size={16}/>}</button>
            <span>{Math.round(zoom * 100)}%</span>
          </div>
          <div className="edge-legend draggable-overlay" style={{ transform: `translate(${overlayPositions.legend.x}px, ${overlayPositions.legend.y}px)` }} aria-label="Connection legend"><span className="overlay-grip" title="Drag connection legend" onPointerDown={(event) => startOverlayDrag("legend", event)} onPointerMove={moveOverlay} onPointerUp={endOverlayDrag} onPointerCancel={endOverlayDrag}><GripVertical size={13}/></span><span className="legend-control">Agent control</span><span className="legend-governance">Governance</span><span className="legend-tool">Tool relation</span><span className="legend-data">Typed data</span><span className="legend-evidence">Evidence</span></div>
          <div className="minimap" role="button" tabIndex={0} aria-label="Workflow minimap; click to pan or press Enter to center" onPointerDown={panFromMinimap} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); centerCanvas(); } }}>
            <svg viewBox={`0 0 ${canvasSize.width} ${canvasSize.height}`} aria-hidden="true">
              {displayedWorkflow.edges.map((edge) => { const start = nodes.find((node) => node.id === edge.from); const end = nodes.find((node) => node.id === edge.to); if (!start || !end) return null; return <line className={`edge-${edgeKindOf(edge)}`} key={`${edge.from}-${edge.to}`} x1={start.x + 95} y1={start.y + 54} x2={end.x + 95} y2={end.y + 54}/>; })}
              {nodes.map((node) => <rect className={`mini-node category-${categoryOf(node)} status-${node.status}`} key={node.id} x={node.x} y={node.y} width="190" height="108" rx="10"/>)}
            </svg>
            <div className="mini-view" style={{ left: viewport.x, top: viewport.y, width: viewport.width, height: viewport.height }}/>
          </div>
          <div className="canvas-window" ref={canvasWindowRef} onScroll={updateViewport} onPointerDown={startCanvasPan} onPointerMove={moveCanvasPan} onPointerUp={endCanvasPan} onPointerCancel={endCanvasPan}>
            <div className="canvas-sizer" style={{ width: canvasSize.width * zoom, height: canvasSize.height * zoom }}>
              <div className="canvas" style={{ width: canvasSize.width, height: canvasSize.height, transform: `scale(${zoom})` }}>
              {orientation === "horizontal" && <><div className="lane-guide lane-control"><span>Agent / control lane</span></div><div className="lane-guide lane-data"><span>Tool / data lane</span></div></>}
              {groupFrames.map((frame) => <div className={`node-group group-${frame.group}`} key={frame.group} style={{ left: frame.x, top: frame.y, width: frame.width, height: frame.height }}><span>{groupLabels[frame.group]}</span></div>)}
              <svg className="connections" width={canvasSize.width} height={canvasSize.height} aria-hidden="true">{displayedWorkflow.edges.map((edge) => {
                const start = nodes.find((node) => node.id === edge.from); const end = nodes.find((node) => node.id === edge.to); if (!start || !end) return null; const horizontal = orientation === "horizontal";
                const edgeKind = edgeKindOf(edge); const startPoint = edgePoint(start, "from", edgeKind, horizontal); const endPoint = edgePoint(end, "to", edgeKind, horizontal); const { x: x1, y: y1 } = startPoint; const { x: x2, y: y2 } = endPoint; const bend = horizontal ? (x1 + x2) / 2 : (y1 + y2) / 2;
                const path = horizontal ? `M ${x1} ${y1} C ${bend} ${y1}, ${bend} ${y2}, ${x2} ${y2}` : `M ${x1} ${y1} C ${x1} ${bend}, ${x2} ${bend}, ${x2} ${y2}`;
                const labelX = horizontal ? bend : (x1 + x2) / 2; const labelY = horizontal ? (y1 + y2) / 2 - 7 : bend - 7;
                return <g key={`${edge.from}-${edge.to}`} className={`connection edge-${edgeKind}`}><path d={path}/><text x={labelX} y={labelY}>{edge.label ?? edgeKind}</text></g>;
              })}{connectionDrag && connectionPreviewPath && <g className={`connection edge-${connectionDrag.edgeKind} draft-connection`}><path d={connectionPreviewPath}/></g>}</svg>
                {nodes.map((node) => { const Icon = icons[node.kind]; const category = categoryOf(node); const incoming = [...new Set(displayedWorkflow.edges.filter((edge) => edge.to === node.id).map((edge) => portFamilyOf(edgeKindOf(edge))))]; const outgoing = [...new Set(displayedWorkflow.edges.filter((edge) => edge.from === node.id).map((edge) => portFamilyOf(edgeKindOf(edge))))]; const available = availablePortFamilies(node); const inputPorts = [...new Set([...available, ...incoming])]; const outputPorts = [...new Set([...available, ...outgoing])]; const renderPort = (family: PortFamily, direction: "in" | "out", connected: boolean) => family === "control" ? <svg key={direction + "-" + family} className={"typed-port control-port port-" + family + " " + direction + " " + (connected ? "connected" : "unconnected")} viewBox="0 0 16 16" aria-hidden="true" data-port-node={node.id} data-port-family={family} data-port-direction={direction} onPointerDown={(event) => startConnectionDrag(node.id, family, direction, event)} onPointerMove={moveConnectionDrag} onPointerUp={endConnectionDrag} onPointerCancel={endConnectionDrag}><polygon points="2,2 14,8 2,14"/></svg> : <span key={direction + "-" + family} className={"typed-port port-" + family + " " + direction + " " + (connected ? "connected" : "unconnected")} data-port-node={node.id} data-port-family={family} data-port-direction={direction} onPointerDown={(event) => startConnectionDrag(node.id, family, direction, event)} onPointerMove={moveConnectionDrag} onPointerUp={endConnectionDrag} onPointerCancel={endConnectionDrag}/>; return <button key={node.id} className={`flow-node orientation-${orientation} category-${category} status-${node.status} ${mode === "proposal" ? "editable" : ""} ${selectedId === node.id ? "selected" : ""}`} style={{ left: node.x, top: node.y }} onPointerDown={(event) => startNodeDrag(node, event)} onPointerMove={moveNode} onPointerUp={endNodeDrag} onPointerCancel={endNodeDrag} onClick={() => setSelectedId(node.id)}><span className="node-accent"/>{inputPorts.map((family) => renderPort(family, "in", incoming.includes(family)))}{outputPorts.map((family) => renderPort(family, "out", outgoing.includes(family)))}<span className="node-kicker">{category.toUpperCase()}<span className="node-state">{node.status === "failed" || node.status === "denied" || node.status === "interrupted" ? <XCircle size={13}/> : <CheckCircle2 size={13}/ >}{node.status}</span></span><span className="node-main"><span className="node-icon"><Icon size={19}/></span><span><strong>{titleOf(node)}</strong><small>{node.subtitle}</small></span></span><span className="node-footer"><span className="actor-label">{performerOf(node)}</span><ZoomIn size={13}/></span></button>; })}
              </div>
            </div>
          </div>
        </div>
        <div className="timeline"><div className="timeline-title"><span>{mode === "proposal" ? "Proposed structure" : "Execution timeline"}</span><small>correlation · {displayedWorkflow.correlationId}</small></div><div className="timeline-scroll"><div className="timeline-content" style={{ minWidth: Math.max(600, nodes.length * 112) }}><div className="timeline-events" style={{ gridTemplateColumns: `repeat(${nodes.length}, minmax(96px, 1fr))` }}>{nodes.map((node) => <button key={node.id} aria-label={`Inspect ${titleOf(node)}`} className={`timeline-event category-${categoryOf(node)} status-${node.status} ${selected.id === node.id ? "selected" : ""}`} onClick={() => setSelectedId(node.id)}><span className="timeline-event-status">{node.status}</span><span className="timeline-event-marker"/><strong>{titleOf(node)}</strong></button>)}</div></div></div></div>
      </section>
      <aside className="inspector">
        <div className="inspector-head"><div><p className="eyebrow">Inspector</p><h2>{titleOf(selected)}</h2></div><span className={`type-chip category-${categoryOf(selected)}`}>{categoryOf(selected)}</span></div>
        <div className={`status-card status-${selected.status}`}><CheckCircle2 size={20}/><div><strong>{selected.status.replace("_", " ")}</strong><span>{mode === "proposal" ? "Uncommitted proposal state" : "Evidence-backed status"}</span></div></div>
        {mode === "proposal" && <>
          <section className="detail-section proposal-fields">
            <h3>Edit selected block</h3>
            <p className="proposal-help">Changes remain in this browser-only draft.</p>
            <label>Title<input value={selected.title} maxLength={80} onChange={(event) => updateDraftNode(selected.id, { title: event.target.value || "Untitled node" })}/></label>
            <label>Description<input value={selected.subtitle} maxLength={120} onChange={(event) => updateDraftNode(selected.id, { subtitle: event.target.value || "Draft node" })}/></label>
            <label>Performer<select value={performerOf(selected)} onChange={(event) => updateDraftNode(selected.id, { performedBy: event.target.value })}>{performerOptions.map((performer) => <option key={performer} value={performer}>{performer}</option>)}</select></label>
            <button className="delete-node" disabled={displayedWorkflow.nodes.length <= 1} onClick={deleteDraftNode}>Delete selected block</button>
          </section>
          <section className="detail-section connection-editor">
            <h3>Connect selected block</h3>
            <p className="proposal-help">Create a typed, directed connection from this block.</p>
            <label>Connection type<select value={newEdgeKind} onChange={(event) => setNewEdgeKind(event.target.value as EdgeKind)}>{(["control", "governance", "tool", "data", "evidence"] as EdgeKind[]).map((kind) => <option key={kind} value={kind}>{kind}</option>)}</select></label>
            <label>Target block<select value={newEdgeTargetId} onChange={(event) => setNewEdgeTargetId(event.target.value)}><option value="">Select a target</option>{displayedWorkflow.nodes.filter((node) => node.id !== selected.id).map((node) => <option key={node.id} value={node.id}>{titleOf(node)}</option>)}</select></label>
            {newEdgeTargetId && !connectionCompatible && <p className="connection-warning">That connection is incompatible, duplicated, or would create a cycle.</p>}
            <button className="add-connection" disabled={!connectionCompatible} onClick={addDraftConnection}>Add typed connection</button>
            <div className="connection-list"><h4>Connections on this block</h4>{displayedWorkflow.edges.map((edge, index) => edge.from === selected.id || edge.to === selected.id ? <div className="connection-row" key={`${edge.from}-${edge.to}-${edgeKindOf(edge)}-${index}`}><span><strong>{edgeKindOf(edge)}</strong>{edge.from === selected.id ? ` → ${titleOf(displayedWorkflow.nodes.find((node) => node.id === edge.to)!)}` : ` ← ${titleOf(displayedWorkflow.nodes.find((node) => node.id === edge.from)!)}`}</span><button aria-label={`Delete ${edgeKindOf(edge)} connection`} onClick={() => deleteDraftConnection(index)}>Delete</button></div> : null)}{!displayedWorkflow.edges.some((edge) => edge.from === selected.id || edge.to === selected.id) && <p className="connection-empty">No connections yet.</p>}</div>
          </section>
        </>}
        <section className="detail-section"><h3>Performed by</h3><p className="performer"><Bot size={15}/>{performerOf(selected)}</p></section>
        {selected.details && <section className="detail-section"><h3>Summary</h3><p>{selected.details.summary}</p></section>}
        <section className="detail-section"><h3>Authority boundary</h3><p>{selected.authority}</p><div className="boundary-line"><LockKeyhole size={15}/><span>No unrestricted execution</span></div></section>
        <section className="detail-section"><h3>Evidence</h3>
          {selected.details?.evidencePreviews.length ? <div className="evidence-list">{selected.details.evidencePreviews.map((item, index) => <details className="evidence-preview" key={`${item.category}-${item.reference}-${index}`} open={index === 0}>
            <summary><span className={`evidence-category category-${item.category}`}><FileCheck2 size={15}/></span><span><strong>{item.title}</strong><small>{item.category} · {item.reference}</small></span><span className={`evidence-status evidence-${item.status}`}>{item.status}</span><ChevronDown className="evidence-chevron" size={14}/></summary>
            <div className="evidence-content">{item.digest && <div className="digest-row"><span>SHA-256</span><code title={item.digest}>{item.digest.slice(0, 16)}…{item.digest.slice(-8)}</code></div>}<dl>{item.facts.map((fact) => <div key={fact.label}><dt>{fact.label}</dt><dd>{fact.value}</dd></div>)}</dl><p className="evidence-safety"><ShieldCheck size={13}/> Sanitized projection</p></div>
          </details>)}</div> : <div className="evidence-empty"><FileCheck2 size={17}/><span><strong>{selected.evidence}</strong><small>Regenerate this runtime projection for evidence previews</small></span></div>}
        </section>
        <section className="detail-section"><h3>Observed facts</h3><dl><div><dt>Result</dt><dd>{selected.status}</dd></div>{selected.details?.observedFacts.map((fact) => <div key={fact.label}><dt>{fact.label}</dt><dd>{fact.value}</dd></div>)}</dl></section>
        {selected.details?.startedAt && selected.details.finishedAt && <section className="detail-section"><h3>Timing</h3><dl><div><dt>Started</dt><dd>{new Date(selected.details.startedAt).toLocaleString()}</dd></div><div><dt>Finished</dt><dd>{new Date(selected.details.finishedAt).toLocaleString()}</dd></div>{selected.details.durationMs !== null && selected.details.durationMs !== undefined && <div><dt>Duration</dt><dd>{selected.details.durationMs} ms</dd></div>}</dl></section>}
        {!!selected.details?.findings.length && <section className="detail-section findings"><h3>Findings</h3>{selected.details.findings.map((finding) => <p key={finding}>{finding}</p>)}</section>}
        <div className={`inspector-note ${mode === "proposal" ? "draft-note" : ""}`}><ShieldCheck size={16}/><p>{mode === "proposal" ? "This draft exists only in browser memory. It cannot approve, execute, call tools, or modify evidence." : "This view can inspect evidence, but cannot approve or execute work."}</p></div>
      </aside>
    </div>
  </main>;
}
