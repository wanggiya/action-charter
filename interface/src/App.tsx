import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown, ArrowRight, Bot, CheckCircle2, ChevronDown, CircleDot,
  Database, FileCheck2, GitBranch, LockKeyhole, Map, Maximize2, Minus,
  Plus, Search, ShieldCheck, Workflow, ZoomIn,
} from "lucide-react";
import workflowFixture from "./data/demo-workflow.json";
import { workflowSchema, type NodeKind } from "./lib/workflow";

type Orientation = "horizontal" | "vertical";
type Point = { x: number; y: number };
type Viewport = { x: number; y: number; width: number; height: number };

const workflow = workflowSchema.parse(workflowFixture);
const labels: Record<NodeKind, string> = { input: "INPUT", agent: "AGENT", policy: "CONTROL", approval: "HUMAN GATE", tool: "TOOL", evidence: "EVIDENCE" };
const icons: Record<NodeKind, typeof Bot> = { input: Map, agent: Bot, policy: ShieldCheck, approval: LockKeyhole, tool: Database, evidence: FileCheck2 };
const canvasSizes: Record<Orientation, { width: number; height: number }> = {
  horizontal: { width: 1530, height: 650 },
  vertical: { width: 1050, height: 1030 },
};
const verticalPositions: Record<string, Point> = {
  request: { x: 430, y: 35 }, planner: { x: 255, y: 205 }, policy: { x: 605, y: 205 },
  approval: { x: 430, y: 375 }, executor: { x: 255, y: 545 }, mcp: { x: 605, y: 545 },
  validation: { x: 430, y: 715 }, release: { x: 430, y: 885 },
};
const minimapSize = { width: 140, height: 90 };
const clamp = (value: number, minimum: number, maximum: number) => Math.min(maximum, Math.max(minimum, value));

export default function App() {
  const canvasWindowRef = useRef<HTMLDivElement>(null);
  const [selectedId, setSelectedId] = useState("approval");
  const [zoom, setZoom] = useState(0.82);
  const [orientation, setOrientation] = useState<Orientation>(() => window.matchMedia("(max-width: 680px)").matches ? "vertical" : "horizontal");
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, width: 1, height: 1 });
  const selected = useMemo(() => workflow.nodes.find((node) => node.id === selectedId)!, [selectedId]);
  const canvasSize = canvasSizes[orientation];
  const nodes = useMemo(() => workflow.nodes.map((node) => ({
    ...node,
    ...(orientation === "vertical" ? verticalPositions[node.id] : { x: node.x, y: node.y }),
  })), [orientation]);

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

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark"><GitBranch size={18}/></span><span>ActionCharter</span><span className="checkpoint">17A</span></div>
      <div className="run-switcher"><CircleDot size={15}/><span>checkpoint14f / vector-release</span><ChevronDown size={14}/></div>
      <div className="top-actions"><button className="icon-button" aria-label="Search"><Search size={17}/></button><div className="safe-mode"><ShieldCheck size={15}/><span>Read-only</span></div><div className="avatar">JQ</div></div>
    </header>
    <div className="workspace">
      <aside className="rail">
        <button className="rail-item active"><Workflow size={19}/><span>Flow</span></button><button className="rail-item"><Bot size={19}/><span>Agents</span></button><button className="rail-item"><FileCheck2 size={19}/><span>Evidence</span></button><button className="rail-item"><Database size={19}/><span>Data</span></button><div className="rail-spacer"/><button className="rail-item"><Map size={19}/><span>Guide</span></button>
      </aside>
      <section className="flow-stage" aria-label="Governed workflow graph">
        <div className="stage-heading"><div><p className="eyebrow">Governed workflow</p><h1>{workflow.title}</h1></div><div className="stage-meta"><span><span className="pulse"/> Verified</span><span>{nodes.length} nodes</span><span>{workflow.edges.length} links</span></div></div>
        <div className="canvas-frame">
          <div className="canvas-tools">
            <button aria-label="Zoom in" title="Zoom in" onClick={() => setZoom((value) => Math.min(1.1, value + 0.08))}><Plus size={16}/></button>
            <button aria-label="Zoom out" title="Zoom out" onClick={() => setZoom((value) => Math.max(0.2, value - 0.08))}><Minus size={16}/></button>
            <button aria-label="Fit entire graph" title="Fit entire graph" onClick={fitGraph}><Maximize2 size={16}/></button>
            <button className="orientation-button" aria-label={`Switch to ${orientation === "horizontal" ? "vertical" : "horizontal"} layout`} title={`Switch to ${orientation === "horizontal" ? "vertical" : "horizontal"} layout`} onClick={toggleOrientation}>{orientation === "horizontal" ? <ArrowDown size={16}/> : <ArrowRight size={16}/>}</button>
            <span>{Math.round(zoom * 100)}%</span>
          </div>
          <div className="minimap" role="button" tabIndex={0} aria-label="Workflow minimap; click to pan or press Enter to center" onPointerDown={panFromMinimap} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); centerCanvas(); } }}>
            <svg viewBox={`0 0 ${canvasSize.width} ${canvasSize.height}`} aria-hidden="true">
              {workflow.edges.map((edge) => { const start = nodes.find((node) => node.id === edge.from)!; const end = nodes.find((node) => node.id === edge.to)!; return <line key={`${edge.from}-${edge.to}`} x1={start.x + 95} y1={start.y + 54} x2={end.x + 95} y2={end.y + 54}/>; })}
              {nodes.map((node) => <rect key={node.id} x={node.x} y={node.y} width="190" height="108" rx="14"/>)}
            </svg>
            <div className="mini-view" style={{ left: viewport.x, top: viewport.y, width: viewport.width, height: viewport.height }}/>
          </div>
          <div className="canvas-window" ref={canvasWindowRef} onScroll={updateViewport}>
            <div className="canvas-sizer" style={{ width: canvasSize.width * zoom, height: canvasSize.height * zoom }}>
              <div className="canvas" style={{ width: canvasSize.width, height: canvasSize.height, transform: `scale(${zoom})` }}>
              <svg className="connections" width={canvasSize.width} height={canvasSize.height} aria-hidden="true"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#468ac7"/></marker></defs>{workflow.edges.map((edge) => {
                const start = nodes.find((node) => node.id === edge.from)!; const end = nodes.find((node) => node.id === edge.to)!; const horizontal = orientation === "horizontal";
                const x1 = horizontal ? start.x + 190 : start.x + 95; const y1 = horizontal ? start.y + 54 : start.y + 108; const x2 = horizontal ? end.x : end.x + 95; const y2 = horizontal ? end.y + 54 : end.y; const bend = horizontal ? (x1 + x2) / 2 : (y1 + y2) / 2;
                const path = horizontal ? `M ${x1} ${y1} C ${bend} ${y1}, ${bend} ${y2}, ${x2} ${y2}` : `M ${x1} ${y1} C ${x1} ${bend}, ${x2} ${bend}, ${x2} ${y2}`;
                return <path key={`${edge.from}-${edge.to}`} d={path} markerEnd="url(#arrow)"/>;
              })}</svg>
                {nodes.map((node) => { const Icon = icons[node.kind]; return <button key={node.id} className={`flow-node orientation-${orientation} kind-${node.kind} ${selectedId === node.id ? "selected" : ""}`} style={{ left: node.x, top: node.y }} onClick={() => setSelectedId(node.id)}><span className="node-port in"/><span className="node-port out"/><span className="node-kicker">{labels[node.kind]}<span className="node-state"><CheckCircle2 size={13}/>{node.status}</span></span><span className="node-main"><span className="node-icon"><Icon size={19}/></span><span><strong>{node.title}</strong><small>{node.subtitle}</small></span></span><span className="node-footer"><span>{node.evidence}</span><ZoomIn size={13}/></span></button>; })}
              </div>
            </div>
          </div>
        </div>
        <div className="timeline"><div className="timeline-title"><span>Execution timeline</span><small>correlation · {workflow.correlationId}</small></div><div className="timeline-track"><span className="track-fill"/><i style={{left:"8%"}}/><i style={{left:"28%"}}/><i style={{left:"49%"}}/><i style={{left:"72%"}}/><i style={{left:"94%"}}/></div><div className="timeline-labels"><span>Proposed</span><span>Approved</span><span>Executed</span><span>Validated</span><span>Released</span></div></div>
      </section>
      <aside className="inspector">
        <div className="inspector-head"><div><p className="eyebrow">Inspector</p><h2>{selected.title}</h2></div><span className={`type-chip kind-${selected.kind}`}>{labels[selected.kind]}</span></div>
        <div className="status-card"><CheckCircle2 size={20}/><div><strong>{selected.status === "approved" ? "Human approved" : "Evidence verified"}</strong><span>Deterministic status</span></div></div>
        <section className="detail-section"><h3>Authority boundary</h3><p>{selected.authority}</p><div className="boundary-line"><LockKeyhole size={15}/><span>No unrestricted execution</span></div></section>
        <section className="detail-section"><h3>Evidence</h3><button className="evidence-file"><FileCheck2 size={17}/><span><strong>{selected.evidence}</strong><small>SHA-256 bound · immutable</small></span><ChevronDown size={14}/></button></section>
        <section className="detail-section"><h3>Observed facts</h3><dl><div><dt>Result</dt><dd>{selected.status}</dd></div><div><dt>Model called</dt><dd>No</dd></div><div><dt>Mutation</dt><dd>{selected.kind === "tool" ? "Approved" : "None"}</dd></div></dl></section>
        <div className="inspector-note"><ShieldCheck size={16}/><p>This view can inspect evidence, but cannot approve or execute work.</p></div>
      </aside>
    </div>
  </main>;
}
