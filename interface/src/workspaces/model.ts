import { type ResultRecord } from "../components/ResultsWorkspace";
import { formulaText } from "../components/CalculationEditor";
import { Bot, Database, FileCheck2, LockKeyhole, Map, ShieldCheck } from "lucide-react";
import { operationDependencies, type PinDirection } from "../lib/operation-graph";
import { skillLabel } from "../lib/skill-labels";
import { type InspectionRun } from "../lib/interface-api";
import type { Handoff } from "../lib/intent-api";
import workflowFixture from "../data/demo-workflow.json";
import { type CriticEvidenceInventory, type ExecutionInventory, type ExecutionProgress, type InterfacePlannerResult, type PlannerSkillCatalog, type SavedRecipeInventory } from "../lib/interface-api";
import { type RecipeTemplate } from "../lib/recipe-templates";
import { workflowSchema, type EdgeKind, type NodeCategory, type NodeGroup, type NodeKind, type Workflow as WorkflowData } from "../lib/workflow";

export type Orientation = "horizontal" | "vertical";

export type Viewport = { x: number; y: number; width: number; height: number };

export type OverlayName = "tools" | "legend";

export type OverlayPosition = { x: number; y: number };

export type InterfaceMode = "evidence" | "proposal";

export type JourneyStage = "plan" | "review" | "run" | "outcome";

export type RecipeSort = "time_desc" | "time_asc" | "name_asc" | "name_desc";

export type ActiveRecipe = { recipeId: string; recipeSha256: string; steps: Array<{ step_id: string; skill_id: string; depends_on: string[] }> };

export type ProposalDraft = Omit<WorkflowData, "readOnly" | "source"> & { readOnly: false; source: "proposal_draft" };

export type ConnectionDrag = { originDirection: PinDirection; moveLinks: boolean; pointerId: number; sourceId: string; family: PortFamily; edgeKind: EdgeKind; x: number; y: number };

export const demoWorkflow = workflowSchema.parse(workflowFixture);

export const labels: Record<NodeKind, string> = { input: "INPUT", data: "DATA", agent: "AGENT", policy: "CONTROL", approval: "HUMAN GATE", tool: "TOOL", evidence: "EVIDENCE" };

export const icons: Record<NodeKind, typeof Bot> = { input: Map, data: Database, agent: Bot, policy: ShieldCheck, approval: LockKeyhole, tool: Database, evidence: FileCheck2 };

export const fallbackCategory: Record<NodeKind, NodeCategory> = { input: "input", data: "input", agent: "planning", policy: "policy", approval: "approval", tool: "tool", evidence: "evidence" };

export const groupLabels: Record<NodeGroup, string> = { intake: "Operator intake", planning: "Planner agent", governance: "Governance", execution: "Executor + tools", assurance: "Validation + evidence" };

export const legacyCategories: Record<string, NodeCategory> = { request: "input", planner: "planning", policy: "policy", approval: "approval", executor: "execution", mcp: "tool", validation: "validation", release: "evidence", evidence: "evidence" };

export const legacyGroups: Record<string, NodeGroup> = { request: "intake", planner: "planning", policy: "governance", approval: "governance", executor: "execution", mcp: "execution", validation: "assurance", release: "assurance", evidence: "assurance" };

export const legacyTitles: Record<string, string> = { request: "Submit request", planner: "Create plan", policy: "Evaluate policy", approval: "Record approval", executor: "Execute plan", mcp: "Run GIS tool", validation: "Validate result", release: "Record evidence", evidence: "Record evidence" };

export const legacyPerformers: Record<string, string> = { request: "User", planner: "Planner agent", policy: "Policy engine", approval: "Human operator", executor: "Execution engine", mcp: "MCP tool boundary", validation: "Validator", release: "Evidence service", evidence: "Evidence service" };

export const standardPerformers = ["Unassigned", "User", "Planner agent", "Policy engine", "Human operator", "Execution engine", "Validator", "Critic agent", "Evidence service", "MCP tool boundary", "Snakemake runner"];

export const categoryOf = (node: WorkflowData["nodes"][number]) => node.category ?? legacyCategories[node.id] ?? fallbackCategory[node.kind];

export const groupOf = (node: WorkflowData["nodes"][number]) => node.group ?? legacyGroups[node.id];

export const titleOf = (node: WorkflowData["nodes"][number]) => node.category ? node.title : legacyTitles[node.id] ?? node.title;

export const performerOf = (node: WorkflowData["nodes"][number]) => node.performedBy ?? legacyPerformers[node.id] ?? labels[node.kind];

export const edgeKindOf = (edge: WorkflowData["edges"][number]): EdgeKind => {
  if (edge.kind) return edge.kind;
  if (edge.from === "validation" || edge.to === "release" || edge.to === "evidence") return "evidence";
  if (edge.from === "policy" || edge.to === "approval") return "governance";
  if (edge.from === "executor" || edge.from === "mcp" || edge.to === "mcp" || edge.to === "validation") return "data";
  return "control";
};

export type PortFamily = "control" | "governance" | "data" | "evidence";

export const portFamilyOf = (kind: EdgeKind): PortFamily => kind === "tool" ? "data" : kind;

export const availablePortFamilies = (node: WorkflowData["nodes"][number]): PortFamily[] => {
  const category = categoryOf(node);
  if (category === "input") return ["control", "data"];
  if (category === "planning" || category === "execution") return ["control", "data"];
  if (category === "policy" || category === "approval") return ["control", "governance"];
  if (category === "tool") return ["data"];
  if (category === "validation") return ["data", "evidence"];
  return ["evidence"];
};

export const edgeWouldCreateCycle = (workflow: Pick<WorkflowData, "edges">, from: string, to: string) => {
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

export const portOffsets: Record<PortFamily, { horizontal: number; vertical: number }> = {
  control: { horizontal: 32, vertical: 45 },
  governance: { horizontal: 52, vertical: 78 },
  data: { horizontal: 76, vertical: 112 },
  evidence: { horizontal: 92, vertical: 145 },
};

export const edgePoint = (node: WorkflowData["nodes"][number], role: "from" | "to", kind: EdgeKind, horizontal: boolean) => {
  const offset = portOffsets[portFamilyOf(kind)];
  return horizontal
    ? { x: node.x + (role === "from" ? 190 : -3), y: node.y + offset.horizontal }
    : { x: node.x + offset.vertical, y: node.y + (role === "from" ? 108 : -3) };
};

export const minimapSize = { width: 140, height: 90 };

export const clamp = (value: number, minimum: number, maximum: number) => Math.min(maximum, Math.max(minimum, value));

export const topologySignature = (workflow: Pick<ProposalDraft, "nodes" | "edges">) => JSON.stringify({ nodes: workflow.nodes.map(({ id, kind, category }) => ({ id, kind, category })), edges: workflow.edges.map(({ from, to, kind }) => ({ from, to, kind })) });

export const templateParameterDefaults = (template?: RecipeTemplate) => Object.fromEntries([
  ...(template?.required_parameters ?? []),
  ...(template?.optional_parameters ?? []),
].map((name) => [name, name === "target_format" ? "geopackage" : name === "resampling" ? "nearest" : ""]));

export const templateParameterLabel = (name: string) => name === "path" ? "Input file" : name === "target_path" ? "Output file" : name.replaceAll("_", " ");

export const templateParameterPlaceholder = (template: RecipeTemplate | undefined, name: string) => {
  const root = template?.parameter_roots[name];
  if (!root) return name;
  return `Filename or relative path (default: ${root}/)`;
};

export const outcomeFacts = (value: unknown): Array<[string, string]> => {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return Object.entries(value as Record<string, unknown>).filter(([name]) => name !== "preview").map(([name, item]) => [
      name.replaceAll("_", " "),
      typeof item === "string" ? item : JSON.stringify(item),
    ]);
  }
  return [["Result", typeof value === "string" ? value : JSON.stringify(value)]];
};

export const evidencePathParts = (path: string) => {
  const normalized = path.replaceAll("\\\\", "/");
  const separator = normalized.lastIndexOf("/");
  return separator < 0
    ? { filename: normalized, directory: "Project root" }
    : { filename: normalized.slice(separator + 1), directory: normalized.slice(0, separator) || "/" };
};

export const searchableSkillText = (skill: PlannerSkillCatalog["skills"][number]) =>
  `${skill.id} ${skill.id.replaceAll("_", " ")} ${skill.kind ?? ""} ${skill.access ?? ""}`.toLowerCase();

export const plannerInputPaths = (result: Pick<InterfacePlannerResult, "plan">): string[] => [...new Set(result.plan.steps.flatMap(step => [step.arguments.path, step.arguments.right_path, ...(step.arguments.analysis && typeof step.arguments.analysis === 'object' ? [(step.arguments.analysis as Record<string,unknown>).codebook_path] : [])].filter((path): path is string => typeof path === "string" && path.length > 0).map(plannerInputPath)))];

export const plannerInputPath = (path: string): string => !path.includes("/") && !path.includes("\\") && ![".",".."].includes(path) ? `data/input/${path}` : path;

export const plannerReferenceFacts = (result: Pick<InterfacePlannerResult, "plan">, id: string): [string, string][] => {
  const input = /^planned_input_([0-9]+)$/.exec(id);
  if (input) {
    const path = plannerInputPaths(result)[Number(input[1])];
    return path ? [["Source path", path]] : [];
  }
  const step = result.plan.steps.find(item => `planned_${item.step_id}` === id);
  return step ? Object.entries(step.arguments).filter(([key,value]) => ["path","right_path","source_step","right_step","target_path"].includes(key) && typeof value === "string").map(([key,value]) => [key === "path" ? "Source path" : key.replaceAll("_"," "), ["path","right_path"].includes(key) ? plannerInputPath(String(value)) : String(value)]) : [];
};

export const plannerWorkflow = (result: Pick<InterfacePlannerResult, "plan" | "original_request" | "model">): WorkflowData => {
  const stepNodes: WorkflowData["nodes"] = result.plan.steps.map((step, index) => ({
    id: `planned_${step.step_id}`,
    title: skillLabel(step.skill),
    subtitle: step.skill === "calculate_csv_columns" && Array.isArray(step.arguments.calculations) ? step.arguments.calculations.map((row: {output_column:string;expression:unknown}) => `${row.output_column} = ${formulaText(row.expression)}`).join("; ") : "Select to inspect parameters",
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
  const inputPaths = plannerInputPaths(result);
  const inputs: WorkflowData["nodes"] = inputPaths.map((path, index) => ({
    id: `planned_input_${index}`, title: (path.split("/").at(-1) ?? "Input file").slice(0, 80), subtitle: "Declared source file · not yet inspected", kind: "input", category: "input", group: "intake", x: 40 + index * 230, y: 550, status: "pending", authority: "Data reference only", performedBy: "Not executed", evidence: "Declared path; contents not verified", details: null,
  }));
  return {
    schemaVersion: "1.0",
    id: `planner-${Date.now()}`,
    title: result.plan.steps.length === 1 ? skillLabel(result.plan.steps[0].skill) : `Proposed workflow · ${result.plan.steps.length} steps`,
    correlationId: `planner-${Date.now()}`,
    readOnly: true,
    source: "planner_projection",
    nodes: [
      { id: "planned_request", title: "Task request", subtitle: "Select to read planning context", kind: "input", category: "input", group: "intake", x: 40, y: 100, status: "complete", authority: "User-authored request", performedBy: "User", evidence: "In-memory planner request", details: null },
      { id: "planned_planner", title: "Plan workflow", subtitle: result.model, kind: "agent", category: "planning", group: "planning", x: 300, y: 100, status: "complete", authority: "Planning only", performedBy: "Planner agent", evidence: "Schema-validated model output", details: null },
      { id: "planned_policy", title: "Review proposed plan", subtitle: "Not saved, approved, or executed", kind: "policy", category: "policy", group: "governance", x: 620, y: 100, status: "pending", authority: "Operator review required", performedBy: "Policy engine", evidence: "No durable plan evidence yet", details: null },
      ...inputs,
      ...stepNodes,
    ],
    edges: [
      { from: "planned_request", to: "planned_planner", kind: "control", label: "request" },
      { from: "planned_planner", to: "planned_policy", kind: "control", label: "proposed plan" },
      ...result.plan.steps.flatMap<WorkflowData["edges"][number]>(step => inputPaths.flatMap((path, index) => plannerInputPaths({plan:{...result.plan,steps:[step]}}).includes(path) ? [{from:`planned_input_${index}`,to:`planned_${step.step_id}`,kind:"data" as const,label:"source file"}] : [])),
      ...result.plan.steps.flatMap<WorkflowData["edges"][number]>((step) => {
        const parents = operationDependencies(result.plan.steps)[step.step_id];
        return parents.length ? parents.map((parent) => ({ from: `planned_${parent}`, to: `planned_${step.step_id}`, kind: "data" as const, label: "dependency" })) : [{ from: "planned_planner", to: `planned_${step.step_id}`, kind: "control" as const, label: "proposed root" }];
      }),
    ],
  };
};

export const withRecordedOutcome = (graph: WorkflowData | ProposalDraft, record: {success:boolean;evidence:string;steps:string[];running?:boolean} | null): WorkflowData | ProposalDraft => {
  if (!record || !graph.readOnly || graph.nodes.some(node=>node.id==="planned_outcome")) return graph;
  const operations=graph.nodes.filter(node=>record.steps.includes(node.id));
  const terminal=operations.filter(node=>!graph.edges.some(edge=>edge.from===node.id&&operations.some(other=>other.id===edge.to)));
  return {...graph,nodes:[...graph.nodes,{id:"planned_outcome",title:"Workflow outcome",subtitle:record.running?"Execution in progress":record.success?"Completed · select to view results":"Recorded attempt · review findings",kind:"evidence",category:"evidence",group:"assurance",x:Math.min(15000,Math.max(620,...operations.map(node=>node.x))+230),y:330,status:record.running?"running":record.success?"complete":"failed",authority:"Recorded result only",performedBy:"Governed backend",evidence:record.evidence.slice(0,160),details:null}],edges:[...graph.edges,...terminal.map(node=>({from:node.id,to:"planned_outcome",kind:"evidence" as const,label:"recorded result"}))]};
};

export const editedPlannerWorkflow = (result: InterfacePlannerResult): WorkflowData => {
  const graph = plannerWorkflow(result);
  return { ...graph, id: `edited-${result.plan_sha256}`, correlationId: `draft-${result.plan_sha256.slice(0,16)}`, title: `Workflow draft · ${result.plan.steps.length} operations`, nodes: graph.nodes.map((node) => node.id === "planned_planner" ? { ...node, title: "Edit workflow", subtitle: "Operator changes · not revalidated", performedBy: "Operator", evidence: "Unvalidated browser draft" } : node.id === "planned_policy" || node.kind === "tool" ? { ...node, authority: "Backend validation required", evidence: "Unvalidated operation draft", ...(node.id === "planned_policy" ? { subtitle: "Validate edits before authorization or execution" } : {}) } : node) };
};

export const savedRecipeWorkflow = (recipe: SavedRecipeInventory["recipes"][number]): WorkflowData => {
  const approval = recipe.approvals.find((item) => item.authority_link === "verified");
  const denied = recipe.approvals.some((item) => item.decision === "denied");
  const stepNodes: WorkflowData["nodes"] = recipe.steps.map((step, index) => ({
    id: `recipe_${step.step_id}`, title: step.skill_id.replaceAll("_", " "),
    subtitle: recipe.approval_required_step_ids.includes(step.step_id) ? "Approval required" : "Defined step",
    kind: "tool", category: "tool", group: "execution", x: 1000 + index * 220, y: 350,
    status: "pending", authority: "Stored recipe definition · not executed", performedBy: "MCP tool boundary",
    evidence: recipe.recipe_filename, details: null,
  }));
  const dependedOn = new Set(recipe.steps.flatMap((step) => step.depends_on));
  const dependencies: WorkflowData["edges"] = recipe.steps.flatMap((step) => step.depends_on.length
    ? step.depends_on.map((id) => ({ from: `recipe_${id}`, to: `recipe_${step.step_id}`, kind: "data" as const, label: "declared dependency" }))
    : [{ from: "recipe_executor", to: `recipe_${step.step_id}`, kind: "data" as const, label: "defined step" }]);
  return {
    schemaVersion: "1.0", id: `stored-${recipe.recipe_id}`, title: `${recipe.recipe_id.replaceAll("_", " ")} · stored recipe`,
    correlationId: recipe.recipe_sha256.slice(0, 16), readOnly: true, source: "recipe_definition",
    nodes: [
      ...(recipe.plan_definition_link === "verified" && recipe.matching_plan_sha256 ? [{ id: "matching_plan", title: "Saved Planner definition", subtitle: "Exact definition match", kind: "evidence" as const, category: "evidence" as const, group: "intake" as const, x: 40, y: 350, status: "verified" as const, authority: "Canonical content equivalence", performedBy: "Planner agent", evidence: recipe.matching_plan_sha256, details: null }] : []),
      { id: "recipe_request", title: "Stored recipe", subtitle: recipe.recipe_id, kind: "input", category: "input", group: "intake", x: 40, y: 100, status: "complete", authority: "Immutable definition", performedBy: "User", evidence: recipe.recipe_filename, details: null },
      { id: "recipe_planner", title: "Stored definition", subtitle: "Typed stored steps", kind: "agent", category: "planning", group: "planning", x: 300, y: 100, status: "complete", authority: "Definition only", performedBy: "Recipe compiler", evidence: recipe.recipe_sha256, details: null },
      { id: "recipe_policy", title: "Review policy", subtitle: "Stored recipe identity", kind: "policy", category: "policy", group: "governance", x: 530, y: 100, status: "pending", authority: "Definition view only", performedBy: "Policy engine", evidence: recipe.recipe_sha256, details: null },
      { id: "recipe_approval", title: "Human approval", subtitle: approval ? "Exact scope verified" : denied ? "Denied" : "No active exact approval", kind: "approval", category: "approval", group: "governance", x: 760, y: 100, status: approval ? "approved" : denied ? "denied" : "pending", authority: "Decision evidence is separate", performedBy: "Human operator", evidence: approval?.approval_filename ?? "No verified authority", details: null },
      { id: "recipe_executor", title: "Defined execution", subtitle: "No run selected", kind: "agent", category: "execution", group: "execution", x: 1000, y: 100, status: "pending", authority: "Recipe is not an execution", performedBy: "Execution engine", evidence: "Select a durable run for results", details: null },
      ...stepNodes,
      { id: "recipe_validation", title: "Required validation", subtitle: `${recipe.validation_required_step_ids.length} validation gate(s)`, kind: "evidence", category: "validation", group: "assurance", x: 1030 + recipe.steps.length * 220, y: 100, status: "pending", authority: "Defined checks only", performedBy: "Validator", evidence: "No run selected", details: null },
    ],
    edges: [
      ...(recipe.plan_definition_link === "verified" && recipe.matching_plan_sha256 ? [{ from: "matching_plan", to: "recipe_planner", kind: "evidence" as const, label: "exact definition" }] : []),
      { from: "recipe_request", to: "recipe_planner", kind: "control", label: "definition" },
      { from: "recipe_planner", to: "recipe_policy", kind: "control", label: "policy" },
      { from: "recipe_policy", to: "recipe_approval", kind: "control", label: "decision" },
      ...(approval ? [{ from: "recipe_approval", to: "recipe_executor", kind: "control" as const, label: "verified authority" }] : []),
      ...dependencies,
      ...recipe.steps.filter((step) => recipe.validation_required_step_ids.includes(step.step_id) && !dependedOn.has(step.step_id)).map((step) => ({ from: `recipe_${step.step_id}`, to: "recipe_validation", kind: "data" as const, label: "required check" })),
    ],
  };
};

export const durableRunWorkflow = (progress: ExecutionProgress, attempt: ExecutionInventory["attempts"][number], assurance: CriticEvidenceInventory | null, sourceRecipe?: SavedRecipeInventory["recipes"][number]): WorkflowData => {
  const recipe = {
    recipe_id: progress.recipe_id ?? "legacy_run", recipe_sha256: progress.recipe_sha256 ?? "0".repeat(64),
    recipe_filename: progress.recipe_filename ?? "Legacy run", saved_at: progress.started_at,
    steps: progress.steps.map((step) => ({ step_id: step.step_id, skill_id: step.skill_id, depends_on: step.depends_on })),
    approval_required_step_ids: [], validation_required_step_ids: [], approvals: [],
    matching_plan_sha256: sourceRecipe && sourceRecipe.recipe_sha256 === progress.recipe_sha256 ? sourceRecipe.matching_plan_sha256 : null,
    plan_definition_link: sourceRecipe && sourceRecipe.recipe_sha256 === progress.recipe_sha256 ? sourceRecipe.plan_definition_link : "unavailable" as const,
    plan_definition_reason: sourceRecipe && sourceRecipe.recipe_sha256 === progress.recipe_sha256 ? sourceRecipe.plan_definition_reason : "Stored recipe unavailable",
  };
  const graph = savedRecipeWorkflow(recipe);
  const outputNodes: WorkflowData["nodes"] = attempt.recorded_outputs.map((artifact, index) => ({
    id: `recorded_output_${index}`, title: artifact.path.split("/").at(-1) || artifact.artifact_id,
    subtitle: "Recorded output · current file not checked", kind: "data", category: "input", group: "assurance",
    x: 1050 + index * 200, y: 610, status: "pending", authority: "Immutable recipe evidence only",
    performedBy: "Evidence service", evidence: artifact.path,
    details: { summary: "Digest recorded at run time; the current physical file has not been rehashed.", observedFacts: [{ label: "Recorded SHA-256", value: artifact.sha256 }], findings: [], evidencePreviews: [] },
  }));
  const candidate = attempt.result_link === "verified"
    ? assurance?.recipe_candidates.find((item) => item.adaptable && item.stored && item.execution_preview_sha256 === progress.execution_preview_sha256)
    : undefined;
  const traceTaskId = candidate?.trace?.task_id;
  const storedTrace = traceTaskId && assurance?.items.find((item) => item.available && item.evidence?.task_id === traceTaskId && item.trace_name === `${traceTaskId}.json`);
  const assuranceX = 1300 + recipe.steps.length * 220;
  const assuranceNodes: WorkflowData["nodes"] = storedTrace ? [
    { id: "linked_trace", title: "Stored trace and report", subtitle: "Exact adapted evidence", kind: "evidence", category: "evidence", group: "assurance", x: assuranceX, y: 830, status: "verified", authority: "Exact stored pair", performedBy: "Evidence service", evidence: storedTrace.trace_name, details: null },
    ...(storedTrace.critic_record_link === "verified" ? [{ id: "linked_critic", title: "Critic result", subtitle: "Exact result record linked", kind: "evidence" as const, category: "evidence" as const, group: "assurance" as const, x: assuranceX + 240, y: 830, status: "verified" as const, authority: "Canonical Critic record", performedBy: "Critic agent", evidence: storedTrace.critic_record_files?.[0] ?? "Verified record", details: null }] : []),
    ...(storedTrace.release_link === "verified" && storedTrace.critic_record_link === "verified" ? [{ id: "linked_release", title: "Immutable release", subtitle: "Exact package linked", kind: "evidence" as const, category: "evidence" as const, group: "assurance" as const, x: assuranceX + 480, y: 830, status: "verified" as const, authority: "Verified release package", performedBy: "Evidence service", evidence: storedTrace.release_manifests?.[0] ?? "Verified release", details: null }] : []),
  ] : [];
  const statusOf = (status: string): WorkflowData["nodes"][number]["status"] =>
    status === "validated_success" || status === "completed" ? "complete" :
    status === "failed" || status === "validation_failed" ? "failed" : status === "interrupted" ? "interrupted" : "pending";
  return {
    ...graph, id: `run-${progress.execution_preview_sha256}`, title: `${recipe.recipe_id.replaceAll("_", " ")} · durable run`,
    correlationId: progress.execution_preview_sha256.slice(0, 16), source: "durable_run",
    edges: graph.edges.filter((edge) => edge.from !== "recipe_approval" && edge.to !== "recipe_validation").concat(
      attempt.authority_link === "verified" ? [{ from: "recipe_approval", to: "recipe_executor", kind: "control", label: "verified authority" }] : [],
      attempt.result_link === "verified" ? progress.steps.filter((step) => !progress.steps.some((other) => other.depends_on.includes(step.step_id))).map((step) => ({ from: `recipe_${step.step_id}`, to: "recipe_validation", kind: "evidence" as const, label: "verified result" })) : [],
      attempt.recorded_outputs.flatMap((artifact, index) => artifact.producer_step_id && progress.steps.some((step) => step.step_id === artifact.producer_step_id)
        ? [{ from: `recipe_${artifact.producer_step_id}`, to: `recorded_output_${index}`, kind: "data" as const, label: "recorded output" }] : []),
      assuranceNodes.length ? [{ from: "recipe_validation", to: "linked_trace", kind: "evidence", label: "exact trace" }] : [],
      assuranceNodes.some((node) => node.id === "linked_critic") ? [{ from: "linked_trace", to: "linked_critic", kind: "evidence", label: "exact record" }] : [],
      assuranceNodes.some((node) => node.id === "linked_release") ? [{ from: "linked_critic", to: "linked_release", kind: "evidence", label: "exact release" }] : [],
    ),
    nodes: graph.nodes.map<WorkflowData["nodes"][number]>((node) => {
      if (node.id === "recipe_policy") return { ...node, subtitle: attempt.authority_link === "verified" ? "Authority independently verified" : "Authority not verified", status: attempt.authority_link === "verified" ? "verified" : "pending" };
      if (node.id === "recipe_approval") return { ...node, subtitle: attempt.authority_link === "verified" ? "Approved at run start" : attempt.authority_reason, status: attempt.authority_link === "verified" ? "approved" : "pending", evidence: attempt.approval_id ?? "Identity unavailable" };
      if (node.id === "recipe_executor") return { ...node, title: "Governed execution", subtitle: progress.status.replaceAll("_", " "), status: statusOf(progress.status), evidence: progress.execution_preview_sha256 };
      if (node.id === "recipe_validation") return { ...node, title: "Workflow outcome", subtitle: attempt.result_reason, status: attempt.result_link === "verified" && progress.status === "validated_success" ? "verified" : statusOf(progress.status), evidence: attempt.result_link === "verified" ? "Exact result and evidence verified" : "Result link unavailable or blocked", details: { summary: "Recorded attempt outcome; current output files are not rehashed by opening this graph.", observedFacts: [{label:"Attempt status",value:progress.status},{label:"Result linkage",value:attempt.result_link},{label:"Recorded outputs shown",value:String(attempt.recorded_outputs.length)}], findings: attempt.outputs_truncated ? ["Recorded output list is truncated."] : [], evidencePreviews: [] } };
      const step = progress.steps.find((item) => node.id === `recipe_${item.step_id}`);
      return step ? { ...node, subtitle: step.status.replaceAll("_", " "), status: statusOf(step.status), evidence: attempt.result_link === "verified" ? "Durable run evidence verified" : "Result link unavailable or blocked" } : node;
    }).concat(outputNodes, assuranceNodes),
  };
};

export const readablePlannerRequest = (original: string): string => {
  try {
    const source = JSON.parse(original);
    const objective = source?.reviewed_intent_untrusted?.objective;
    if (typeof source?.intent_review_filename === "string" && typeof objective === "string" && objective.trim() && objective.length <= 4000) return objective;
  } catch { /* Ordinary Planner requests are already human-readable text. */ }
  return original;
};

export const taskDraftWorkflow = (input: string, request: string): WorkflowData => ({
  schemaVersion: "1.0", id: "current-task-draft", title: "Current task · input and request", correlationId: "Browser draft · not a plan or execution", readOnly: true, source: "planner_projection",
  nodes: [
    { id: "task_request", title: "Your task", subtitle: request.trim().slice(0, 120) || "Describe the metadata you need", kind: "input", category: "input", group: "intake", x: 70, y: 140, status: "pending", authority: "Current user statement", performedBy: "Human", evidence: "Unsaved browser draft" },
    { id: "task_input", title: "Input dataset", subtitle: input.trim().slice(0, 120) || "No input selected", kind: "data", category: "input", group: "intake", x: 70, y: 330, status: "pending", authority: "Checked on task submission", performedBy: "Human", evidence: input.trim().slice(0, 160) || "Choose an input" },
    { id: "task_intent", title: "Intent agent", subtitle: "Clarification and review before planning", kind: "agent", category: "planning", group: "planning", x: 360, y: 140, status: "pending", authority: "No work permission", performedBy: "Intent", evidence: "No completed tool operation" },
  ],
  edges: [{ from: "task_request", to: "task_intent", kind: "control", label: "current request" }, { from: "task_input", to: "task_intent", kind: "data", label: "selected input" }],
});

export const intentWorkflow = (handoff: Handoff): WorkflowData => {
  let reviewed: { objective?: string; known_inputs?: string[] } = {};
  try { reviewed = JSON.parse(handoff.planner_result.original_request).reviewed_intent_untrusted ?? {}; } catch { /* Fall back to validated plan summary. */ }
  const graph = plannerWorkflow({ ...handoff.planner_result, original_request: reviewed.objective ?? handoff.planner_result.plan.summary });
  return { ...graph, nodes: graph.nodes.map((node) => node.id === "planned_planner" ? { ...node, x: 620 } : node.id === "planned_policy" ? { ...node, x: 940 } : node).concat([
    ...(handoff.context_sha256 ? [{ id: "intent_context", title: "Reviewed history", subtitle: "Historical context · no authority", kind: "evidence", category: "evidence", group: "intake", x: 40, y: 330, status: "complete", authority: "Reasoning context only", performedBy: "Human operator", evidence: handoff.context_sha256, details: null } as WorkflowData["nodes"][number]] : []),
    { id: "intent_data", title: "Selected input", subtitle: reviewed.known_inputs?.join(", ") ?? "Reviewed input reference", kind: "data", category: "input", group: "intake", x: 40, y: 560, status: "pending", authority: "Not inspected or executed", performedBy: "User", evidence: "Input reference in reviewed intent", details: null },
    { id: "intent_agent", title: "Interpret and clarify", subtitle: "Resolved intent reviewed", kind: "agent", category: "planning", group: "planning", x: 320, y: 100, status: "complete", authority: "Reasoning only · not work approval", performedBy: "Intent agent", evidence: handoff.intent_review_filename, details: null },
  ]), edges: [
    { from: "planned_request", to: "intent_agent", kind: "control", label: "current request" },
    ...(handoff.context_sha256 ? [{ from: "intent_context", to: "intent_agent", kind: "data" as const, label: "historical context" }] : []),
    { from: "intent_data", to: "intent_agent", kind: "data", label: "selected input" },
    { from: "intent_agent", to: "planned_planner", kind: "control", label: "reviewed intent" },
    { from: "planned_planner", to: "planned_policy", kind: "control", label: "proposed plan" },
    ...graph.nodes.filter((node) => node.kind === "tool").flatMap((node) => [
      { from: "planned_planner", to: node.id, kind: "data" as const, label: "proposed capability" },
      { from: "intent_data", to: node.id, kind: "data" as const, label: "proposed input" },
    ]),
  ] };
};

export function legacyResultRecord(result:{status:string;step_results:{step_id:string;skill_id:string;status:string;outcome?:unknown;validation_outcome?:unknown}[]}, identity:string):ResultRecord {
  return {run_id:identity,status:result.status,steps:result.step_results.map(step=>({...step,outcome:step.outcome??null,arguments:{},depends_on:[],validation_outcome:step.validation_outcome??null}))};
}

export function inspectionResultRecord(result:InspectionRun):ResultRecord {
  return {...legacyResultRecord(result,result.run_id),plan_sha256:result.plan_sha256,started_at:result.started_at};
}
