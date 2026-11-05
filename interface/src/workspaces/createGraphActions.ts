import { freePosition } from "../lib/use-graph-layout";
import { materializeDependencies, canConnectOperations, connectOperations, disconnectOperations, deleteOperation, pinConnections, breakPinConnections, movePinConnections, type PinDirection } from "../lib/operation-graph";
import { skillLabel } from "../lib/skill-labels";
import { validatePlanEdit, saveGeneratedPlannerPlan } from "../lib/interface-api";
import { canonicalDragPosition, displayDragPosition, bezierGeometry, createNodeDragPreview } from "../lib/graph-drag-preview";
import { loadSavedPlans, type InterfacePlannerResult, type PlannerSkillCatalog } from "../lib/interface-api";
import { type EdgeKind, type NodeCategory, type NodeGroup, type NodeKind, type Workflow as WorkflowData } from "../lib/workflow";
import { OverlayName, ConnectionDrag, edgeKindOf, PortFamily, portFamilyOf, availablePortFamilies, edgeWouldCreateCycle, edgePoint, clamp, plannerWorkflow } from './model';
import type {ActionContext} from './action-contracts';

export function createGraphActions(context: ActionContext) {
 const { graphSelection, setHistoricalRecord, setGraphSelection, historyReturnRef, setOutcomeOpen, setOrientation, 
  canvasWindowRef, canvasSize, zoom, camera, canvasPanRef, setAddMenu, setPinMenu, updateViewport, 
  suppressCanvasMenu, overlayPositions, overlayDragRef, setOverlayPositions, setTemplateTopologyBaseline, 
  setLoadedTemplateId, setDraft, workflow, setMode, setLoadNotice, connectionDragRef, setConnectionDrag, 
  setSelectedId, draft, draftCounterRef, newNodeKind, selected, editedPlan, plannerResult, connectionTarget, 
  newEdgeKind, setNewEdgeTargetId, workflowBusy, editBusy, setEditNotice, mode, connectionTargetRef, 
  setConnectionHover, connectionFrameRef, setDraggingNodeId, nodeDragRef, pendingNodePosition, nodeFrameRef, 
  moveBlocks, displayedWorkflow, orientation, nodes, nodePositions, lastNodeDragRef, setNodePositions, 
  setEditedPlan, setWorkflowReview, setWorkflowAuthorization, setWorkflowReviewOpen, 
  setExecutionInventoryOpen, setOperationTarget, setConnectionToRemove, connectionToRemove, 
  setConnectionsOpen, selectedId, addMenu, savedPlannerResult, pendingParameters, setEditBusy, 
  setPlannerResult, setSavedPlannerResult, setPreparedPlanApproval, setRecordedPlanApproval, 
  setVerifiedPlanApproval, setCompiledPlanRecipe, setSavedPlanRecipe, setPlanExecutionPreview, 
  setPlannerReviewConfirmed, setPlanRecipeReviewConfirmed, setWorkflow, setLocalGraph, setSavedPlanInventory, 
}=context;
const returnFromHistory=()=>{if(graphSelection!=='chat-history'){setHistoricalRecord(null);return;}setHistoricalRecord(null);setGraphSelection(historyReturnRef.current);setOutcomeOpen(false);};

const toggleOrientation = () => {
    context.actions().cancelNodeLayoutDrag();
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

const startCanvasPan = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    if (!element || ![0, 1, 2].includes(event.button) || (event.target as HTMLElement).closest(".typed-port") || (event.button === 0 && (event.target as HTMLElement).closest("button"))) return;
    camera.stop();
    canvasPanRef.current = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, left: element.scrollLeft, top: element.scrollTop, moved: false };
    element.setPointerCapture(event.pointerId);
    element.classList.add("is-panning");
  };

const moveCanvasPan = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    const pan = canvasPanRef.current;
    if (!element || !pan || pan.pointerId !== event.pointerId) return;
    pan.moved ||= Math.abs(event.clientX - pan.x) + Math.abs(event.clientY - pan.y) > 4;
    if (pan.moved) { setAddMenu(null); setPinMenu(null); }
    element.scrollLeft = pan.left - (event.clientX - pan.x);
    element.scrollTop = pan.top - (event.clientY - pan.y);
    updateViewport();
  };

const endCanvasPan = (event: React.PointerEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    if (!element || canvasPanRef.current?.pointerId !== event.pointerId) return;
    suppressCanvasMenu.current = event.button === 2 && Boolean(canvasPanRef.current.moved);
    canvasPanRef.current = null;
    if (element.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId);
    element.classList.remove("is-panning");
  };

const startOverlayDrag = (name: OverlayName, event: React.PointerEvent<HTMLSpanElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const element = event.currentTarget.parentElement;
    const frame = element?.closest<HTMLElement>(".canvas-frame");
    if (!element || !frame) return;
    const origin = overlayPositions[name];
    const rect = element.getBoundingClientRect();
    const frameRect = frame.getBoundingClientRect();
    const baseLeft = rect.left - origin.x;
    const baseTop = rect.top - origin.y;
    overlayDragRef.current = { name, pointerId: event.pointerId, x: event.clientX, y: event.clientY, origin, current: origin, element, bounds: {
      minX: frameRect.left + 8 - baseLeft,
      maxX: Math.max(frameRect.left + 8 - baseLeft, frameRect.right - rect.width - 8 - baseLeft),
      minY: frameRect.top + 8 - baseTop,
      maxY: Math.max(frameRect.top + 8 - baseTop, frameRect.bottom - rect.height - 8 - baseTop),
    } };
    element.classList.add("is-dragging");
    event.currentTarget.setPointerCapture(event.pointerId);
  };

const moveOverlay = (event: React.PointerEvent<HTMLSpanElement>) => {
    const drag = overlayDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    drag.current = {
      x: clamp(drag.origin.x + event.clientX - drag.x, drag.bounds.minX, drag.bounds.maxX),
      y: clamp(drag.origin.y + event.clientY - drag.y, drag.bounds.minY, drag.bounds.maxY),
    };
    drag.element.style.transform = `translate(${drag.current.x}px, ${drag.current.y}px)`;
  };

const endOverlayDrag = (event: React.PointerEvent<HTMLSpanElement>) => {
    const drag = overlayDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    drag.element.classList.remove("is-dragging");
    setOverlayPositions((positions) => ({ ...positions, [drag.name]: drag.current }));
    overlayDragRef.current = null;
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
    if (graphSelection === "live-plan" && (editedPlan ?? plannerResult)) {
      if (kind !== "data" || !sourceId.startsWith("planned_step_") || !targetId.startsWith("planned_step_")) return false;
      return canConnectOperations((editedPlan ?? plannerResult)!.plan.steps, sourceId.slice(8), targetId.slice(8));
    }
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

const addDraftConnection = () => {
    const connectionCompatible = Boolean(context.connectionTarget && context.actions().canConnect(context.selected.id,context.connectionTarget.id,context.newEdgeKind));
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
    return { x: (clientX - bounds.left + element.scrollLeft) / camera.current.current, y: (clientY - bounds.top + element.scrollTop) / camera.current.current };
  };

const breakConnectionsAtPin = (nodeId: string, family: PortFamily, direction: PinDirection) => {
    if (workflowBusy || editBusy) return;
    if (graphSelection === "live-plan" && family === "data" && nodeId.startsWith("planned_step_")) {
      const current = editedPlan ?? plannerResult;
      if (!current) return;
      if (!pinConnections(current.plan.steps, nodeId.slice(8), direction).length) { setEditNotice("This pin has no operation connections."); return; }
      context.actions().commitOperationEdit(breakPinConnections(current, nodeId.slice(8), direction), "Pin connections broken · validate before authorization/execution.");
    } else if (draft) setDraft({ ...draft, edges: draft.edges.filter((edge) => !(portFamilyOf(edgeKindOf(edge)) === family && (direction === "out" ? edge.from === nodeId : edge.to === nodeId))) });
    setPinMenu(null);
  };

const breakConnectionsAtNode = (nodeId: string) => {
    if (workflowBusy || editBusy) return;
    const current = editedPlan ?? plannerResult;
    if (graphSelection === "live-plan" && current && nodeId.startsWith("planned_step_")) context.actions().commitOperationEdit(breakPinConnections(breakPinConnections(current, nodeId.slice(8), "in"), nodeId.slice(8), "out"), "Block links broken · backend validation required.");
    else if (draft) setDraft({ ...draft, edges: draft.edges.filter((edge) => edge.from !== nodeId && edge.to !== nodeId) });
    setPinMenu(null);
  };

const startConnectionDrag = (nodeId: string, family: PortFamily, direction: PinDirection, event: React.PointerEvent<SVGSVGElement | HTMLSpanElement>) => {
    event.stopPropagation();
    if (event.button !== 0 || workflowBusy || editBusy) return;
    if (mode !== "proposal" && !(graphSelection === "live-plan" && family === "data" && nodeId.startsWith("planned_step_"))) return;
    event.preventDefault(); canvasWindowRef.current?.focus({ preventScroll: true }); setPinMenu(null); setAddMenu(null);
    if (event.altKey) { context.actions().breakConnectionsAtPin(nodeId, family, direction); return; }
    const point = context.actions().pointerToCanvas(event.clientX, event.clientY);
    const kind = graphSelection === "live-plan" ? "data" : portFamilyOf(newEdgeKind) === family ? newEdgeKind : family;
    const drag: ConnectionDrag = { originDirection: direction, moveLinks: event.ctrlKey, pointerId: event.pointerId, sourceId: nodeId, family, edgeKind: kind as EdgeKind, ...point };
    connectionTargetRef.current = null;
    connectionDragRef.current = drag; setConnectionDrag(drag); setConnectionHover(null);
    event.currentTarget.setPointerCapture(event.pointerId);
  };

const moveConnectionDrag = (event: React.PointerEvent<SVGSVGElement | HTMLSpanElement>) => {
    const drag = connectionDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const next = { ...drag, ...context.actions().pointerToCanvas(event.clientX, event.clientY) };
    connectionDragRef.current = next;
    if (connectionFrameRef.current === null) connectionFrameRef.current = requestAnimationFrame(() => {
      connectionFrameRef.current = null;
      setConnectionDrag(connectionDragRef.current);
    });
    const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>("[data-port-node]");
    const targetKey = target ? `${target.dataset.portNode}:${target.dataset.portDirection}:${target.dataset.portFamily}` : "empty";
    if (connectionTargetRef.current === targetKey) return;
    connectionTargetRef.current = targetKey;
    if (!target) { setConnectionHover({ compatible: false, message: drag.moveLinks ? "Drop onto a matching pin to move its links" : "Release on empty canvas to add a connected operation" }); return; }
    const targetId = target.dataset.portNode!;
    const direction = target.dataset.portDirection as PinDirection;
    let compatible = target.dataset.portFamily === drag.family && (drag.moveLinks ? direction === drag.originDirection : direction !== drag.originDirection);
    if (compatible && graphSelection === "live-plan" && (editedPlan ?? plannerResult)) {
      if (drag.moveLinks) {
        try { movePinConnections((editedPlan ?? plannerResult)!, drag.sourceId.slice(8), targetId.slice(8), drag.originDirection); } catch { compatible = false; }
      } else compatible = context.actions().canConnect(drag.originDirection === "out" ? drag.sourceId : targetId, drag.originDirection === "in" ? drag.sourceId : targetId, "data");
    }
    setConnectionHover({ compatible, message: compatible ? (drag.moveLinks ? "Move these connections" : "Connect these pins") : "Incompatible, duplicate or cyclic connection" });
  };

const endConnectionDrag = (event: React.PointerEvent<SVGSVGElement | HTMLSpanElement>) => {
    const drag = connectionDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    if (connectionFrameRef.current !== null) { cancelAnimationFrame(connectionFrameRef.current); connectionFrameRef.current = null; }
    connectionTargetRef.current = null;
    const hit = document.elementFromPoint(event.clientX, event.clientY);
    const target = hit?.closest<HTMLElement>("[data-port-node]");
    const targetId = target?.dataset.portNode;
    const targetDirection = target?.dataset.portDirection as PinDirection | undefined;
    if (event.type !== "pointercancel" && targetId && target?.dataset.portFamily === drag.family) {
      if (drag.moveLinks && targetDirection === drag.originDirection) {
        if (graphSelection === "live-plan" && (editedPlan ?? plannerResult)) {
          try { context.actions().commitOperationEdit(movePinConnections((editedPlan ?? plannerResult)!, drag.sourceId.slice(8), targetId.slice(8), drag.originDirection), "Connections moved · backend validation required."); setSelectedId(targetId); }
          catch (e) { setEditNotice(e instanceof Error ? e.message : "Cannot move these connections"); }
        } else if (draft) {
          let next = { ...draft, edges: draft.edges.filter((edge) => !(portFamilyOf(edgeKindOf(edge)) === drag.family && (drag.originDirection === "out" ? edge.from === drag.sourceId : edge.to === drag.sourceId))) };
          const moved = draft.edges.filter((edge) => portFamilyOf(edgeKindOf(edge)) === drag.family && (drag.originDirection === "out" ? edge.from === drag.sourceId : edge.to === drag.sourceId));
          let valid = moved.length > 0;
          for (const edge of moved) {
            const replacement = { ...edge, ...(drag.originDirection === "out" ? { from: targetId } : { to: targetId }) };
            if (replacement.from === replacement.to || edgeWouldCreateCycle(next, replacement.from, replacement.to)) { valid = false; break; }
            if (!next.edges.some((item) => item.from === replacement.from && item.to === replacement.to && edgeKindOf(item) === edgeKindOf(replacement))) next = { ...next, edges: [...next.edges, replacement] };
          }
          if (valid) { setDraft(next); setSelectedId(targetId); }
        }
      } else if (!drag.moveLinks && targetDirection !== drag.originDirection) {
        const from = drag.originDirection === "out" ? drag.sourceId : targetId;
        const to = drag.originDirection === "in" ? drag.sourceId : targetId;
        if (graphSelection === "live-plan") context.actions().connectPlanOperations(from, to);
        else if (draft && context.actions().canConnect(from, to, drag.edgeKind)) { setDraft({ ...draft, edges: [...draft.edges, { from, to, kind: drag.edgeKind, label: drag.edgeKind }] }); setSelectedId(to); }
      } else setEditNotice("Connect opposite pin directions; Ctrl-drag moves links between matching directions.");
    } else if (event.type !== "pointercancel" && graphSelection === "live-plan" && !drag.moveLinks && !hit?.closest(".flow-node, .canvas-tools, .edge-legend, .minimap")) {
      context.actions().openAddMenuAt(event.clientX, event.clientY, { nodeId: drag.sourceId, direction: drag.originDirection });
    }
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    connectionDragRef.current = null; setConnectionDrag(null); setConnectionHover(null);
  };

const cancelConnectionDrag = () => {
    const drag = connectionDragRef.current;
    connectionDragRef.current = null; setConnectionDrag(null); setConnectionHover(null);
    if (!drag) return;
    const pin = canvasWindowRef.current?.querySelector(`[data-port-node="${drag.sourceId}"][data-port-family="${drag.family}"][data-port-direction="${drag.originDirection}"]`);
    if (pin?.hasPointerCapture(drag.pointerId)) pin.releasePointerCapture(drag.pointerId);
  };

const cancelNodeLayoutDrag = () => {
    setDraggingNodeId(null);
    nodeDragRef.current?.preview.finish(true);
    nodeDragRef.current = null;
    pendingNodePosition.current = null;
    if (nodeFrameRef.current !== null) { cancelAnimationFrame(nodeFrameRef.current); nodeFrameRef.current = null; }
  };

const startNodeDrag = (node: WorkflowData["nodes"][number], event: React.PointerEvent<HTMLButtonElement>) => {
    if (mode !== "proposal" && graphSelection !== "live-plan") return;
    if (event.button !== 0 || !moveBlocks || (mode === "proposal" && (workflowBusy || editBusy))) return;
    if ((event.target as Element).closest(".typed-port")) return;
    event.stopPropagation();
    camera.stop();
    canvasWindowRef.current?.focus({ preventScroll: true });
    setSelectedId(node.id);
    setDraggingNodeId(node.id);
    const sourceNode = displayedWorkflow.nodes.find((candidate) => candidate.id === node.id) ?? node;
    pendingNodePosition.current = null;
    const horizontal = orientation === "horizontal";
    const wires = displayedWorkflow.edges.filter((edge) => edge.from === node.id || edge.to === node.id).flatMap((edge) => {
      const group = canvasWindowRef.current?.querySelector<SVGGElement>(`[data-edge-from="${edge.from}"][data-edge-to="${edge.to}"][data-edge-kind="${edgeKindOf(edge)}"]`);
      const path = group?.querySelector<SVGPathElement>("path");
      const start = nodes.find((item) => item.id === edge.from), end = nodes.find((item) => item.id === edge.to);
      if (!path || !start || !end) return [];
      return [{ path, label: group?.querySelector<SVGTextElement>("text") ?? null, geometry: (position: { x: number; y: number }) => bezierGeometry(edgePoint(edge.from === node.id ? { ...start, ...position } : start, "from", edgeKindOf(edge), horizontal), edgePoint(edge.to === node.id ? { ...end, ...position } : end, "to", edgeKindOf(edge), horizontal), horizontal) }];
    });
    nodeDragRef.current = { pointerId: event.pointerId, nodeId: node.id, x: event.clientX, y: event.clientY, originX: nodePositions[node.id]?.x ?? sourceNode.x, originY: nodePositions[node.id]?.y ?? sourceNode.y, moved: false, displayOrigin: { x: node.x, y: node.y }, preview: createNodeDragPreview(event.currentTarget, node, wires) };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

const moveNode = (event: React.PointerEvent<HTMLButtonElement>) => {
    const drag = nodeDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const delta = { x: event.clientX - drag.x, y: event.clientY - drag.y };
    drag.moved ||= Math.abs(delta.x) + Math.abs(delta.y) > 3;
    const position = canonicalDragPosition({ x: drag.originX, y: drag.originY }, delta, camera.current.current, orientation === "horizontal");
    pendingNodePosition.current = { id: drag.nodeId, position, proposal: mode === "proposal" && graphSelection !== "live-plan" };
    if (nodeFrameRef.current === null) nodeFrameRef.current = requestAnimationFrame(() => {
      nodeFrameRef.current = null;
      const pending = pendingNodePosition.current;
      if (!pending) return;
      const active = nodeDragRef.current;
      if (active) active.preview.move(displayDragPosition({ x: active.originX, y: active.originY }, active.displayOrigin, pending.position, orientation === "horizontal"));
    });
  };

const endNodeDrag = (event: React.PointerEvent<HTMLButtonElement>) => {
    const drag = nodeDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    if (nodeFrameRef.current !== null) { cancelAnimationFrame(nodeFrameRef.current); nodeFrameRef.current = null; }
    const cancelled = event.type === "pointercancel";
    if (!cancelled) context.actions().moveNode(event);
    if (nodeFrameRef.current !== null) { cancelAnimationFrame(nodeFrameRef.current); nodeFrameRef.current = null; }
    const pending = pendingNodePosition.current;
    drag.preview.finish(true);
    setDraggingNodeId(null);
    if (drag.moved && !cancelled) lastNodeDragRef.current = performance.now();
    if (pending && !cancelled) {
      const position = freePosition(pending.position,Object.entries(nodePositions).filter(([id])=>id!==pending.id).map(([,point])=>point),orientation === "horizontal");
      if (pending.proposal) context.actions().updateDraftNode(pending.id, position);
      else setNodePositions((positions) => ({ ...positions, [pending.id]: position }));
    }
    pendingNodePosition.current = null;
    nodeDragRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  };

const revealSelectedOperation = () => requestAnimationFrame(() => {
    const canvas = canvasWindowRef.current;
    const block = canvas?.querySelector<HTMLElement>(".flow-node.selected");
    if (!canvas || !block) return;
    const frame = canvas.getBoundingClientRect();
    const bounds = block.getBoundingClientRect();
    canvas.scrollBy({ left: bounds.left - frame.left + bounds.width / 2 - canvas.clientWidth / 2, top: bounds.top - frame.top + bounds.height / 2 - canvas.clientHeight / 2, behavior: "smooth" });
  });

const commitOperationEdit = (next: InterfacePlannerResult, notice: string) => {
    setEditedPlan(next); setWorkflowReview(null); setWorkflowAuthorization(null); setWorkflowReviewOpen(false); setExecutionInventoryOpen(false); setOutcomeOpen(false); setOperationTarget(""); setConnectionToRemove(""); setEditNotice(notice);
  };

const connectPlanOperations = (fromNode: string, toNode: string) => {
    const current = editedPlan ?? plannerResult;
    if (!current || workflowBusy || editBusy || graphSelection !== "live-plan") return;
    try { context.actions().commitOperationEdit(connectOperations(current, fromNode.replace(/^planned_/, ""), toNode.replace(/^planned_/, "")), "Connection changed · validate and save before authorization/execution."); setOperationTarget(""); setSelectedId(toNode); context.actions().revealSelectedOperation(); }
    catch (e) { setEditNotice(e instanceof Error ? e.message : "Connection blocked"); }
  };

const disconnectPlanOperations = () => {
    const current = editedPlan ?? plannerResult;
    if (!current || !connectionToRemove || workflowBusy || editBusy) return;
    const [from, to] = connectionToRemove.split(":");
    try { context.actions().commitOperationEdit(disconnectOperations(current, from, to), "Dependency disconnected · backend validation required."); setConnectionToRemove(""); }
    catch (e) { setEditNotice(e instanceof Error ? e.message : "Disconnection blocked"); }
  };

const openBlockConnections = () => {
    if (!plannerResult || workflowBusy || editBusy || graphSelection !== "live-plan") return;
    context.actions().beginBlockEdit(); setConnectionsOpen(true); setOperationTarget(""); setConnectionToRemove("");
  };

const beginBlockEdit = () => {
    if (!plannerResult || workflowBusy || editBusy) return;
    if (!editedPlan) context.actions().commitOperationEdit(structuredClone(plannerResult), "Draft edits · backend validation required before execution");
    if (!selectedId.startsWith("planned_step_")) setSelectedId("planned_step_1");
    setWorkflowReview(null); setWorkflowAuthorization(null); setEditNotice("Draft edits · backend validation required before execution");
  };

const addOperation = (skill: PlannerSkillCatalog["skills"][number]) => {
    if (!plannerResult || workflowBusy || editBusy) return;
    const next = materializeDependencies(editedPlan ?? plannerResult);
    if (next.plan.steps.length >= 20) return;
    if (skill.id === "export_snakemake_workflow" && next.plan.steps.length > 18) { setEditNotice("Snakemake export and verification need two available block slots."); return; }
    if (skill.id === "export_snakemake_workflow" && addMenu?.pin?.direction === "in") { setEditNotice("Snakemake export must be appended after the completed source operations."); return; }
    const previousExport = next.plan.steps.find((step) => step.skill === "export_snakemake_workflow");
    const sourceReference = previousExport?.arguments ?? { source_plan_filename: savedPlannerResult?.plan_filename ?? "", source_plan_sha256: savedPlannerResult?.plan_sha256 ?? "" };
    const tableIds = ["decode_csv_codes","select_csv_columns","filter_csv_rows","handle_csv_missing","join_csv","aggregate_csv","calculate_csv_columns","export_csv","vector_attributes_to_csv"];
    const producesTable = (id:string) => tableIds.includes(id) || id.startsWith("ext_");
    const previousTable = next.plan.steps.find((step) => `planned_${step.step_id}` === selectedId && producesTable(step.skill)) ?? next.plan.steps.filter((step) => producesTable(step.skill)).at(-1);
    const tableSource = previousTable ? { source_step:previousTable.step_id, delimiter:"," } : { path:"", delimiter:"," };
    const tableTarget = `data/output/table_${(savedPlannerResult?.plan_sha256 ?? "draft").slice(0,8)}_${next.plan.steps.length + 1}.csv`;
    const argumentsBySkill: Record<string, Record<string, unknown>> = {
      decode_csv_codes:{...tableSource,target_path:tableTarget,codebook_path:"",columns:[],unknown_policy:"error"},
      discover_postgres_tables:{target_schema:"agent_sandbox"},inspect_postgres_table:{target_schema:"agent_sandbox",target_table:""},
      import_csv_to_postgres:{connection_sha256:"",...tableSource,...(!previousTable?{source_sha256:""}:{}),target_schema:"agent_sandbox",target_table:"",columns:[{source:"",name:"",type:"text"}],null_values:[""],key_columns:[],mode:"create"},
      export_postgres_to_csv:{target_schema:"agent_sandbox",target_table:"",target_path:tableTarget,columns:[],expected_table_sha256:"",null_token:"\\N"},
      soft_delete_postgres_rows:{target_schema:"agent_sandbox",target_table:"",expected_table_sha256:"",key_column:"",keys:[],deleted_column:"is_deleted",expected_affected_rows:1},
      restore_postgres_rows:{target_schema:"agent_sandbox",target_table:"",expected_table_sha256:"",key_column:"",keys:[],deleted_column:"is_deleted",expected_affected_rows:1}, calculate_csv_columns:{...tableSource,target_path:tableTarget,missing_policy:"error",calculations:[{output_column:"calculated_value",expression:{kind:"binary",operator:"multiply",left:{kind:"column",name:"amount"},right:{kind:"number",value:2}}}],assumptions:[]},inspect_csv:{path:"",delimiter:",",preview_rows:5},select_csv_columns:{...tableSource,target_path:tableTarget,columns:[]},filter_csv_rows:{...tableSource,target_path:tableTarget,predicates:[{column:"",operator:"ge",value:0,value_type:"number"}],match:"all"},handle_csv_missing:{...tableSource,target_path:tableTarget,method:"fill",fill_values:{},columns:[]},join_csv:{...tableSource,target_path:tableTarget,right_path:"",right_delimiter:",",keys:[],how:"left",cardinality:"many_to_one"},aggregate_csv:{...tableSource,target_path:tableTarget,by:[],aggregations:[{column:"",function:"sum",output_column:"total"}]},export_csv:{...tableSource,target_path:tableTarget},vector_attributes_to_csv:{path:"",target_path:tableTarget}, export_snakemake_workflow: sourceReference, verify_snakemake_export: {}, inspect_vector: { path: "" }, inspect_raster: { path: "" }, convert_vector: { path: "", target_path: "" }, convert_raster: { path: "", target_path: "", target_crs: "" }, load_vector_to_postgis: { path: "", target_schema: "", target_table: "" }, validate_postgis_layer: { target_schema: "", target_table: "" }, generate_report: { task_id: "" } };
    if (skill.id.startsWith("ext_")) {
      const args={...(skill.default_arguments??{}),...tableSource,target_path:tableTarget};
      if ("source_step" in args) delete (args as Record<string,unknown>).path;
      argumentsBySkill[skill.id]=args;
    }
    const id = `step_${next.plan.steps.length + 1}`;
    next.plan.steps.push({ step_id: id, skill: skill.id, purpose: skillLabel(skill.id), arguments: argumentsBySkill[skill.id] ?? {}, requires_approval: skill.approval_required, validation_required: skill.id === "verify_snakemake_export" || skill.validation_required, expected_artifacts: [], depends_on: skill.id === "export_snakemake_workflow" ? next.plan.steps.map((step) => step.step_id) : addMenu?.pin ? (addMenu.pin.direction === "out" ? [addMenu.pin.nodeId.slice(8)] : []) : [(selectedId.startsWith("planned_step_") ? selectedId.slice(8) : next.plan.steps.at(-1)?.step_id)].filter((value): value is string => Boolean(value)) });
    if (producesTable(skill.id) && skill.id !== "vector_attributes_to_csv" && previousTable) {
      const added = next.plan.steps.at(-1)!;
      added.depends_on = [...new Set([...(added.depends_on ?? []), previousTable.step_id])];
    }
    if (skill.id === "export_snakemake_workflow") next.plan.steps.push({ step_id: `step_${next.plan.steps.length + 1}`, skill: "verify_snakemake_export", purpose: "Verify the generated Snakemake package without running it", arguments: {}, requires_approval: false, validation_required: true, expected_artifacts: ["Static package verification"], depends_on: [id] });
    if (addMenu?.pin?.direction === "in") next.plan.steps.find((step) => step.step_id === addMenu.pin!.nodeId.slice(8))!.depends_on!.push(id);
    if (addMenu?.position) setNodePositions((positions) => ({ ...positions, [`planned_${id}`]: addMenu.position! }));
    context.actions().commitOperationEdit(next, "Set parameters in the inspector, then validate edits."); setSelectedId(`planned_${id}`); setAddMenu(null); context.actions().revealSelectedOperation();
  };

const removeOperation = () => {
    const next = structuredClone(editedPlan ?? plannerResult);
    if (!next || !selectedId.startsWith("planned_step_") || next.plan.steps.length <= 1 || workflowBusy || editBusy) return;
    context.actions().commitOperationEdit(deleteOperation(next, selectedId.slice(8)), "Block and its connections removed · backend validation required."); setSelectedId("planned_step_1");  setConnectionToRemove("");
  };

const editParameter = (stepId: string, key: string, value: unknown) => {
    if (!editedPlan || workflowBusy || editBusy) return;
    setEditedPlan({ ...editedPlan, plan: { ...editedPlan.plan, steps: editedPlan.plan.steps.map((step) => step.step_id === stepId ? { ...step, arguments: { ...step.arguments, [key]: value } } : step) } });
    setWorkflowReview(null); setWorkflowAuthorization(null); setEditNotice("Draft edits · backend validation required");
  };

const validateEdits = async () => {
    if (!editedPlan || editBusy || Object.values(pendingParameters).some(Boolean)) return;
    setEditBusy(true); setEditNotice("Validating edited operations and saving the exact proposal…");
    try {
      const validated = await validatePlanEdit(editedPlan);
      const stored = await saveGeneratedPlannerPlan(validated);
      setPlannerResult(validated); setSavedPlannerResult(stored); setEditedPlan(null);
      setPreparedPlanApproval(null); setRecordedPlanApproval(null); setVerifiedPlanApproval(null); setCompiledPlanRecipe(null); setSavedPlanRecipe(null); setPlanExecutionPreview(null); setPlannerReviewConfirmed(false); setPlanRecipeReviewConfirmed(false);
      setWorkflow(plannerWorkflow(validated)); setLocalGraph(null); setEditNotice("Edited plan validated and saved. Review its exact scope with Execute.");
      window.dispatchEvent(new CustomEvent("actioncharter:conversation-workflow-edited", { detail:{ previousPlanSha:plannerResult?.plan_sha256, result:validated } }));
      void loadSavedPlans().then(setSavedPlanInventory).catch(() => setEditNotice("Plan saved; saved-record inventory refresh failed."));
    } catch (e) { setEditNotice(e instanceof Error ? e.message : "Edited operations rejected"); }
    finally { setEditBusy(false); }
  };

const openAddMenu = (x = 24, y = 24) => { setPinMenu(null); if (graphSelection !== "live-plan" || !plannerResult || workflowBusy || editBusy) return; setAddMenu({ x, y }); };

const openAddMenuAt = (clientX: number, clientY: number, pin?: { nodeId: string; direction: PinDirection }) => {
    if (graphSelection !== "live-plan" || !plannerResult || workflowBusy || editBusy) return;
    const frame = canvasWindowRef.current?.closest(".canvas-frame")?.getBoundingClientRect();
    if (!frame) return;
    const point = context.actions().pointerToCanvas(clientX, clientY);
    const minimumX = 0;
    const minimumY = 0;
    const position = orientation === "horizontal" ? { x: point.x - 95, y: point.y - 54 } : { x: minimumX + (point.y - 35) / .72, y: minimumY + (point.x - 120) / 1.25 };
    setPinMenu(null); setAddMenu({ x: Math.max(8, Math.min(clientX - frame.left, frame.width - 290)), y: Math.max(8, Math.min(clientY - frame.top, frame.height - 340)), pin, position: { x: Math.round(clamp(position.x, 0, 16000)), y: Math.round(clamp(position.y, 0, 16000)) } });
  };

const openPinMenuAt = (clientX: number, clientY: number, nodeId: string, family: PortFamily, direction: PinDirection, nodeMenu = false) => {
    if (workflowBusy || editBusy || (graphSelection !== "live-plan" && !draft)) return;
    if (graphSelection === "live-plan" && (!nodeId.startsWith("planned_step_") || family !== "data")) return;
    const frame = canvasWindowRef.current?.closest(".canvas-frame")?.getBoundingClientRect();
    if (!frame) return;
    setAddMenu(null); setPinMenu({ x: Math.max(8, Math.min(clientX - frame.left, frame.width - 270)), y: Math.max(8, Math.min(clientY - frame.top, frame.height - 280)), nodeId, family, direction, scope: nodeMenu ? "node" : "pin" });
  };
 return {returnFromHistory, toggleOrientation, panFromMinimap, centerCanvas, startCanvasPan, moveCanvasPan, endCanvasPan, startOverlayDrag, moveOverlay, endOverlayDrag, beginProposal, closeProposal, updateDraftNode, addDraftNode, deleteDraftNode, canConnect, addDraftConnection, deleteDraftConnection, pointerToCanvas, breakConnectionsAtPin, breakConnectionsAtNode, startConnectionDrag, moveConnectionDrag, endConnectionDrag, cancelConnectionDrag, cancelNodeLayoutDrag, startNodeDrag, moveNode, endNodeDrag, revealSelectedOperation, commitOperationEdit, connectPlanOperations, disconnectPlanOperations, openBlockConnections, beginBlockEdit, addOperation, removeOperation, editParameter, validateEdits, openAddMenu, openAddMenuAt, openPinMenuAt};
}
