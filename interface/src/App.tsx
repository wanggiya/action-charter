import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown, ArrowRight, Bot, CheckCircle2, ChevronDown, CircleDot,
  Database, FileCheck2, GitBranch, LockKeyhole, Map, Maximize2, Minus,
  GripVertical, LayoutList, LayoutTemplate, Plus, Search, ShieldCheck, Workflow, X, ZoomIn,
} from "lucide-react";
import workflowFixture from "./data/demo-workflow.json";
import { loadWorkflowCatalog, loadWorkflowProjection } from "./lib/load-workflow";
import { loadRecipeTemplates } from "./lib/load-recipe-templates";
import { compileRecipeProposal, loadSavedRecipes, prepareRecipeApproval, saveReviewedRecipe, type InterfaceCompilation, type PreparedApprovalRequest, type SavedInterfaceRecipe, type SavedRecipeInventory } from "./lib/interface-api";
import { browserRecipeProposalSchema, type BrowserRecipeProposal, type RecipeTemplate } from "./lib/recipe-templates";
import { workflowSchema, type EdgeKind, type NodeCategory, type NodeGroup, type NodeKind, type Workflow as WorkflowData, type WorkflowSummary } from "./lib/workflow";

type Orientation = "horizontal" | "vertical";
type Viewport = { x: number; y: number; width: number; height: number };
type OverlayName = "tools" | "legend";
type OverlayPosition = { x: number; y: number };
type InterfaceMode = "evidence" | "proposal";
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
  const [preparedApproval, setPreparedApproval] = useState<PreparedApprovalRequest | null>(null);
  const [approvalPreparationPending, setApprovalPreparationPending] = useState(false);
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
  const displayedWorkflow = draft ?? workflow;
  const selected = useMemo(() => displayedWorkflow.nodes.find((node) => node.id === selectedId) ?? displayedWorkflow.nodes[0], [displayedWorkflow, selectedId]);
  const performerOptions = useMemo(() => [...new Set([...standardPerformers, ...displayedWorkflow.nodes.map(performerOf)])].sort(), [displayedWorkflow.nodes]);
  const selectedTemplate = useMemo(() => recipeTemplates.find((template) => template.template_id === selectedTemplateId), [recipeTemplates, selectedTemplateId]);
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
      setTemplateParameters(Object.fromEntries((templates[0]?.required_parameters ?? []).map((name) => [name, ""])));
      setRecipeIdHint(templates[0] ? `${templates[0].template_id}_proposal` : "");
      setTemplateNotice("");
    }).catch(() => setTemplateNotice("Export the trusted recipe catalog before using templates."));
  }, []);
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
    return browserRecipeProposalSchema.parse({ schema_version: "1.0", status: "proposed_not_compiled", original_request: proposalRequest.trim(), summary: `Operator-selected trusted template: ${selectedTemplate.template_id}`, recipe_id_hint: recipeIdHint.trim(), selection: { template_id: selectedTemplate.template_id, parameters: Object.fromEntries(selectedTemplate.required_parameters.map((name) => [name, templateParameters[name].trim()])) }, assumptions: [], missing_information: [], warnings: ["Browser-authored proposal; backend validation and compilation are still required."], compilation_performed: false, execution_requested: false, approval_performed: false, execution_performed: false });
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
      setTemplateNotice("Reviewed recipe stored immutably. It is not approved and was not executed.");
    } catch (error) {
      setTemplateNotice(error instanceof Error ? error.message : "Reviewed recipe could not be stored.");
    } finally {
      setSavePending(false);
    }
  };
  const openSavedRecipes = async () => {
    setTemplatePanelOpen(false);
    setRecipePanelOpen(true);
    setRecipeInventoryNotice("Loading immutable recipes…");
    setPreparedApproval(null);
    try {
      const inventory = await loadSavedRecipes();
      setRecipeInventory(inventory);
      setRecipeInventoryNotice("");
    } catch {
      setRecipeInventory(null);
      setRecipeInventoryNotice("Saved recipes could not be loaded. Confirm that the local interface service is running.");
    }
  };
  const prepareApproval = async (recipeFilename: string, recipeSha256: string) => {
    setApprovalPreparationPending(true);
    setPreparedApproval(null);
    setRecipeInventoryNotice("Revalidating the stored recipe and preparing an exact approval request…");
    try {
      const request = await prepareRecipeApproval(recipeFilename, recipeSha256);
      setPreparedApproval(request);
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
      <div className="brand"><span className="brand-mark"><GitBranch size={18}/></span><span>ActionCharter</span><span className="checkpoint">17P</span></div>
      <label className="run-switcher"><CircleDot size={15}/><span className="sr-only">Select workflow run</span><select value={selectedTaskId} disabled={!runs.length || mode === "proposal"} onChange={(event) => { const taskId = event.target.value; setSelectedTaskId(taskId); void loadWorkflowProjection(demoWorkflow, taskId).then((next) => { setWorkflow(next); setSelectedId(next.nodes[0].id); setLoadNotice(""); }).catch(() => setLoadNotice("Selected run could not be loaded. Re-export the runtime projections.")); }}><option value="">{runs.length ? "Select a validated trace" : "Demonstration workflow"}</option>{runs.map((run) => <option key={run.taskId} value={run.taskId}>{run.taskId} · {run.status}</option>)}</select><ChevronDown size={14}/></label>
      <div className="top-actions"><button className="template-launch" onClick={() => setTemplatePanelOpen(true)}><LayoutTemplate size={15}/><span>Templates</span></button><button className="recipe-launch" onClick={() => void openSavedRecipes()}><LayoutList size={15}/><span>Recipes</span></button><button className="mode-button" onClick={mode === "evidence" ? beginProposal : closeProposal}>{mode === "evidence" ? "New proposal" : "Exit draft"}</button><button className="icon-button" aria-label="Search"><Search size={17}/></button><div className={`safe-mode ${mode === "proposal" ? "draft-mode" : ""}`}><ShieldCheck size={15}/><span>{mode === "proposal" ? "Draft only" : "Read-only"}</span></div><div className="avatar">JQ</div></div>
    </header>
    {templatePanelOpen && <div className="template-overlay" role="presentation" onPointerDown={(event) => { if (event.target === event.currentTarget) setTemplatePanelOpen(false); }}>
      <section className="template-workspace" role="dialog" aria-modal="true" aria-labelledby="template-title">
        <header className="template-workspace-head"><div><p className="eyebrow">Reusable governed starting points</p><h2 id="template-title">Choose a recipe template</h2><p>Select a recipe, review the skills it uses, provide its inputs, then preview the workflow graph.</p></div><button aria-label="Close templates" onClick={() => setTemplatePanelOpen(false)}><X size={18}/></button></header>
        <div className="concept-strip"><article><strong>Workflow</strong><span>One planned or recorded process from request through validation and evidence.</span></article><article><strong>Recipe</strong><span>A reusable, parameterized workflow definition with fixed governed steps.</span></article><article><strong>Skill</strong><span>One bounded capability a recipe step may invoke, such as inspecting a raster.</span></article></div>
        {recipeTemplates.length ? <div className="template-layout">
          <div className="template-gallery" role="list" aria-label="Trusted recipe templates">{recipeTemplates.map((template) => <button role="listitem" className={`template-card ${selectedTemplateId === template.template_id ? "selected" : ""}`} key={template.template_id} onClick={() => { setSelectedTemplateId(template.template_id); setTemplateParameters(Object.fromEntries(template.required_parameters.map((name) => [name, ""]))); setRecipeIdHint(`${template.template_id}_proposal`); setTemplateNotice(""); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}><span className="template-card-title"><LayoutTemplate size={16}/><strong>{template.template_id.replaceAll("_", " ")}</strong></span><span>{template.steps.length} governed step{template.steps.length === 1 ? "" : "s"}</span><small>Skills: {template.skill_ids.map((skill) => skill.replaceAll("_", " ")).join(" · ")}</small><small>Inputs: {template.required_parameters.map((name) => name.replaceAll("_", " ")).join(" · ")}</small></button>)}</div>
          <div className="template-form">
            <div className="template-selection-summary"><span>Selected recipe</span><strong>{selectedTemplate?.template_id.replaceAll("_", " ")}</strong><small>{selectedTemplate?.assessment_policy === "none" ? "Standard deterministic checks" : `${selectedTemplate?.assessment_policy.replaceAll("_", " ")} assessment`}</small></div>
            <label>Recipe ID<input value={recipeIdHint} maxLength={101} placeholder="unique_recipe_id" onChange={(event) => { setRecipeIdHint(event.target.value); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}/></label>
            <label>Requested outcome<textarea value={proposalRequest} maxLength={8000} rows={4} placeholder="Describe what this workflow should accomplish" onChange={(event) => { setProposalRequest(event.target.value); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}/></label>
            {selectedTemplate?.required_parameters.map((name) => <label key={name}>{name.replaceAll("_", " ")}<input value={templateParameters[name] ?? ""} maxLength={2000} placeholder={name} onChange={(event) => { setTemplateParameters((current) => ({ ...current, [name]: event.target.value })); setCompilation(null); setReviewConfirmed(false); setSavedRecipe(null); }}/></label>)}
            {templateNotice && <p className="template-notice">{templateNotice}</p>}
            <p className="template-boundary">Compilation is available through the loopback-only typed service. Save, approval, and execution remain unavailable.</p>
            <div className="template-actions"><button onClick={applyRecipeTemplate}>Preview workflow graph</button><button disabled={compilationPending} onClick={() => void compileTemplateProposal()}>{compilationPending ? "Compiling…" : "Compile proposal"}</button><button onClick={downloadRecipeProposal}>Download proposal</button></div>
            {compilation && <section className="compilation-result"><div><CheckCircle2 size={17}/><span><strong>Compilation passed</strong><small>{compilation.result.recipe.recipe_id}</small></span></div><div className="review-digest"><span>Recipe SHA-256</span><code title={compilation.recipe_sha256}>{compilation.recipe_sha256}</code></div><dl><div><dt>Ordered steps</dt><dd>{compilation.result.recipe_validation.topological_step_ids.length}</dd></div><div><dt>Approval gates</dt><dd>{compilation.result.recipe_validation.approval_required_step_ids.length}</dd></div><div><dt>Validation gates</dt><dd>{compilation.result.recipe_validation.validation_required_step_ids.length}</dd></div></dl><ol>{compilation.result.recipe.steps.map((step) => <li key={step.step_id}><code>{step.step_id}</code><span>{step.skill_id.replaceAll("_", " ")}</span></li>)}</ol><p><LockKeyhole size={13}/> Not saved · not approved · not executed</p><label className="review-confirm"><input type="checkbox" checked={reviewConfirmed} disabled={Boolean(savedRecipe)} onChange={(event) => setReviewConfirmed(event.target.checked)}/><span>I reviewed this exact recipe digest and step order.</span></label><button className="save-reviewed" disabled={!reviewConfirmed || savePending || Boolean(savedRecipe)} onClick={() => void saveCompiledRecipe()}>{savePending ? "Verifying and saving…" : savedRecipe ? "Recipe stored" : "Save reviewed recipe"}</button>{savedRecipe && <div className="saved-recipe"><CheckCircle2 size={15}/><span><strong>Stored immutably</strong><small>{savedRecipe.recipe_filename}</small></span><button onClick={() => void openSavedRecipes()}>Done — view saved recipes</button></div>}</section>}
          </div>
        </div> : <div className="template-unavailable"><strong>No validated template catalog loaded</strong><p>Export the trusted catalog into the ignored interface runtime directory, then reload this page.</p><code>.venv/bin/geoagent recipe-template-catalog --project-root . --pretty</code></div>}
      </section>
    </div>}
    {recipePanelOpen && <div className="template-overlay" role="presentation" onPointerDown={(event) => { if (event.target === event.currentTarget) setRecipePanelOpen(false); }}><section className="recipe-workspace" role="dialog" aria-modal="true" aria-labelledby="recipes-title"><header className="template-workspace-head"><div><p className="eyebrow">Immutable local definitions</p><h2 id="recipes-title">Saved recipes</h2><p>Inspect exact identities and prepare a digest-bound approval request. Preparing does not record approval or execute anything.</p></div><button aria-label="Close saved recipes" onClick={() => setRecipePanelOpen(false)}><X size={18}/></button></header>{recipeInventoryNotice && <p className="recipe-inventory-notice">{recipeInventoryNotice}</p>}{recipeInventory && <div className="recipe-inventory"><div className="recipe-inventory-summary"><strong>{recipeInventory.recipe_count}</strong><span>immutable recipe{recipeInventory.recipe_count === 1 ? "" : "s"}</span><small>No approval or execution performed</small></div>{recipeInventory.recipes.length ? <div className="recipe-cards">{preparedApproval && <section ref={approvalRequestRef} tabIndex={-1} className="approval-request"><header><ShieldCheck size={18}/><span><strong>Approval request prepared</strong><small>{preparedApproval.recipe_id}</small></span></header><div><span>Request SHA-256</span><code title={preparedApproval.approval_request_sha256}>{preparedApproval.approval_request_sha256}</code></div><div><span>Recipe SHA-256</span><code title={preparedApproval.recipe_sha256}>{preparedApproval.recipe_sha256}</code></div><h3>Exact approval scope</h3><ul>{preparedApproval.approval_required_step_ids.map((stepId) => { const step = preparedApproval.steps.find((candidate) => candidate.step_id === stepId); return <li key={stepId}><code>{stepId}</code><span>{step?.skill_id.replaceAll("_", " ")}</span></li>; })}</ul><p><LockKeyhole size={13}/> Prepared only · no decision recorded · nothing executed</p></section>}{recipeInventory.recipes.map((recipe) => <article className={`recipe-card ${preparedApproval?.recipe_sha256 === recipe.recipe_sha256 ? "selected" : ""}`} key={recipe.recipe_sha256}><header><LayoutList size={16}/><span><strong>{recipe.recipe_id}</strong><small>{recipe.recipe_filename}</small></span></header><div className="recipe-card-digest"><span>SHA-256</span><code title={recipe.recipe_sha256}>{recipe.recipe_sha256}</code></div><ol>{recipe.steps.map((step) => <li key={step.step_id}><code>{step.step_id}</code><span>{step.skill_id.replaceAll("_", " ")}</span>{recipe.approval_required_step_ids.includes(step.step_id) && <em>Approval required</em>}</li>)}</ol><footer><span>{recipe.validation_required_step_ids.length} validation gate{recipe.validation_required_step_ids.length === 1 ? "" : "s"}</span><button disabled={approvalPreparationPending || !recipe.approval_required_step_ids.length} onClick={() => void prepareApproval(recipe.recipe_filename, recipe.recipe_sha256)}>{approvalPreparationPending ? "Preparing…" : "Prepare approval request"}</button></footer></article>)}</div> : <div className="recipe-inventory-empty"><LayoutList size={22}/><strong>No saved recipes yet</strong><span>Compile and explicitly save a reviewed template proposal first.</span></div>}</div>}</section></div>}
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
                {nodes.map((node) => { const Icon = icons[node.kind]; const category = categoryOf(node); const incoming = [...new Set(displayedWorkflow.edges.filter((edge) => edge.to === node.id).map((edge) => portFamilyOf(edgeKindOf(edge))))]; const outgoing = [...new Set(displayedWorkflow.edges.filter((edge) => edge.from === node.id).map((edge) => portFamilyOf(edgeKindOf(edge))))]; const available = availablePortFamilies(node); const inputPorts = [...new Set([...available, ...incoming])]; const outputPorts = [...new Set([...available, ...outgoing])]; const renderPort = (family: PortFamily, direction: "in" | "out", connected: boolean) => family === "control" ? <svg key={direction + "-" + family} className={"typed-port control-port port-" + family + " " + direction + " " + (connected ? "connected" : "unconnected")} viewBox="0 0 16 16" aria-hidden="true" data-port-node={node.id} data-port-family={family} data-port-direction={direction} onPointerDown={(event) => startConnectionDrag(node.id, family, direction, event)} onPointerMove={moveConnectionDrag} onPointerUp={endConnectionDrag} onPointerCancel={endConnectionDrag}><polygon points="2,2 14,8 2,14"/></svg> : <span key={direction + "-" + family} className={"typed-port port-" + family + " " + direction + " " + (connected ? "connected" : "unconnected")} data-port-node={node.id} data-port-family={family} data-port-direction={direction} onPointerDown={(event) => startConnectionDrag(node.id, family, direction, event)} onPointerMove={moveConnectionDrag} onPointerUp={endConnectionDrag} onPointerCancel={endConnectionDrag}/>; return <button key={node.id} className={`flow-node orientation-${orientation} category-${category} status-${node.status} ${mode === "proposal" ? "editable" : ""} ${selectedId === node.id ? "selected" : ""}`} style={{ left: node.x, top: node.y }} onPointerDown={(event) => startNodeDrag(node, event)} onPointerMove={moveNode} onPointerUp={endNodeDrag} onPointerCancel={endNodeDrag} onClick={() => setSelectedId(node.id)}><span className="node-accent"/>{inputPorts.map((family) => renderPort(family, "in", incoming.includes(family)))}{outputPorts.map((family) => renderPort(family, "out", outgoing.includes(family)))}<span className="node-kicker">{category.toUpperCase()}<span className="node-state"><CheckCircle2 size={13}/>{node.status}</span></span><span className="node-main"><span className="node-icon"><Icon size={19}/></span><span><strong>{titleOf(node)}</strong><small>{node.subtitle}</small></span></span><span className="node-footer"><span className="actor-label">{performerOf(node)}</span><ZoomIn size={13}/></span></button>; })}
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
