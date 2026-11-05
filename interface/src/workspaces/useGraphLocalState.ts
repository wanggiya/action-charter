import { useRef, useState } from "react";
import { type PinDirection } from "../lib/operation-graph";
import { createNodeDragPreview } from "../lib/graph-drag-preview";
import { type EdgeKind, type NodeKind } from "../lib/workflow";
import { Orientation, Viewport, OverlayName, OverlayPosition, ConnectionDrag, PortFamily } from './model';
import type {WorkspaceState} from './state';

export function useGraphLocalState(shared: WorkspaceState) {
  const { workflow, mode, graphSelection, 
}=shared;
  const [addMenu, setAddMenu] = useState<{ x: number; y: number; pin?: { nodeId: string; direction: PinDirection }; position?: OverlayPosition } | null>(null);
  const [pinMenu, setPinMenu] = useState<{ x: number; y: number; nodeId: string; direction: PinDirection; family: PortFamily; scope: "pin" | "node" } | null>(null);
  const [hoveredPin, setHoveredPin] = useState<{ nodeId: string; family: PortFamily; direction: PinDirection } | null>(null);
  const [connectionHover, setConnectionHover] = useState<{ compatible: boolean; message: string } | null>(null);
  const [moveBlocks, setMoveBlocks] = useState(true);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [connectionsOpen, setConnectionsOpen] = useState(false);
  const [operationTarget, setOperationTarget] = useState("");
  const [connectionToRemove, setConnectionToRemove] = useState("");
  const canvasWindowRef = useRef<HTMLDivElement>(null);
  const timelineScrollRef = useRef<HTMLDivElement>(null);
  const [timelineExpanded, setTimelineExpanded] = useState(false);
  const [blockToolsExpanded, setBlockToolsExpanded] = useState(false);
  const nodeFrameRef = useRef<number | null>(null);
  const pendingNodePosition = useRef<{ id: string; position: { x: number; y: number }; proposal: boolean } | null>(null);
  const canvasPanRef = useRef<{ pointerId: number; x: number; y: number; left: number; top: number; moved: boolean } | null>(null);
  const suppressCanvasMenu = useRef(false);
  const lastNodeDragRef = useRef(-Infinity);
  const nodeDragRef = useRef<{ pointerId: number; nodeId: string; x: number; y: number; originX: number; originY: number; moved: boolean; displayOrigin: { x: number; y: number }; preview: ReturnType<typeof createNodeDragPreview> } | null>(null);
  const connectionDragRef = useRef<ConnectionDrag | null>(null);
  const connectionFrameRef = useRef<number | null>(null);
  const connectionTargetRef = useRef<string | null>(null);
  const draftCounterRef = useRef(0);
  const overlayDragRef = useRef<{ name: OverlayName; pointerId: number; x: number; y: number; origin: OverlayPosition; current: OverlayPosition; element: HTMLElement; bounds: { minX: number; maxX: number; minY: number; maxY: number } } | null>(null);
  const [newNodeKind, setNewNodeKind] = useState<NodeKind>("tool");
  const [newEdgeKind, setNewEdgeKind] = useState<EdgeKind>("control");
  const [newEdgeTargetId, setNewEdgeTargetId] = useState("");
  const [connectionDrag, setConnectionDrag] = useState<ConnectionDrag | null>(null);
  const [templateTopologyBaseline, setTemplateTopologyBaseline] = useState<string | null>(null);
  const [loadedTemplateId, setLoadedTemplateId] = useState<string | null>(null);
  const historyReturnRef=useRef('default');
  const graphScopeEpoch=useRef(0);
  const [zoom, setZoom] = useState(0.82);
  const [orientation, setOrientation] = useState<Orientation>(() => window.matchMedia("(max-width: 680px)").matches ? "vertical" : "horizontal");
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, width: 1, height: 1 });
  const [overlayPositions, setOverlayPositions] = useState<Record<OverlayName, OverlayPosition>>({ tools: { x: 0, y: 0 }, legend: { x: 0, y: 0 } });
  const startupView = useRef({workflow,graphSelection,mode});
  return {addMenu, setAddMenu, pinMenu, setPinMenu, hoveredPin, setHoveredPin, connectionHover, setConnectionHover, moveBlocks, setMoveBlocks, draggingNodeId, setDraggingNodeId, connectionsOpen, setConnectionsOpen, operationTarget, setOperationTarget, connectionToRemove, setConnectionToRemove, canvasWindowRef, timelineScrollRef, timelineExpanded, setTimelineExpanded, blockToolsExpanded, setBlockToolsExpanded, nodeFrameRef, pendingNodePosition, canvasPanRef, suppressCanvasMenu, lastNodeDragRef, nodeDragRef, connectionDragRef, connectionFrameRef, connectionTargetRef, draftCounterRef, overlayDragRef, newNodeKind, setNewNodeKind, newEdgeKind, setNewEdgeKind, newEdgeTargetId, setNewEdgeTargetId, connectionDrag, setConnectionDrag, templateTopologyBaseline, setTemplateTopologyBaseline, loadedTemplateId, setLoadedTemplateId, historyReturnRef, graphScopeEpoch, zoom, setZoom, orientation, setOrientation, viewport, setViewport, overlayPositions, setOverlayPositions, startupView};
}
