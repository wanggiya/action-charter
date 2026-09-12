import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown, ArrowRight, Bot, CheckCircle2, ChevronDown, CircleDot,
  Database, FileCheck2, GitBranch, LockKeyhole, Map, Maximize2, Minus,
  Plus, Search, ShieldCheck, Workflow, ZoomIn,
} from "lucide-react";
import workflowFixture from "./data/demo-workflow.json";
import { loadWorkflowCatalog, loadWorkflowProjection } from "./lib/load-workflow";
import { workflowSchema, type NodeKind, type Workflow as WorkflowData, type WorkflowSummary } from "./lib/workflow";

type Orientation = "horizontal" | "vertical";
type Viewport = { x: number; y: number; width: number; height: number };

const demoWorkflow = workflowSchema.parse(workflowFixture);
const labels: Record<NodeKind, string> = { input: "INPUT", agent: "AGENT", policy: "CONTROL", approval: "HUMAN GATE", tool: "TOOL", evidence: "EVIDENCE" };
const icons: Record<NodeKind, typeof Bot> = { input: Map, agent: Bot, policy: ShieldCheck, approval: LockKeyhole, tool: Database, evidence: FileCheck2 };
const nodeRadius: Record<NodeKind, number> = { input: 14, agent: 9, policy: 3, approval: 18, tool: 5, evidence: 12 };
const minimapSize = { width: 140, height: 90 };
const clamp = (value: number, minimum: number, maximum: number) => Math.min(maximum, Math.max(minimum, value));

export default function App() {
  const canvasWindowRef = useRef<HTMLDivElement>(null);
  const [workflow, setWorkflow] = useState<WorkflowData>(demoWorkflow);
  const [runs, setRuns] = useState<WorkflowSummary[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [selectedId, setSelectedId] = useState("approval");
  const [zoom, setZoom] = useState(0.82);
  const [orientation, setOrientation] = useState<Orientation>(() => window.matchMedia("(max-width: 680px)").matches ? "vertical" : "horizontal");
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, width: 1, height: 1 });
  const selected = useMemo(() => workflow.nodes.find((node) => node.id === selectedId) ?? workflow.nodes[0], [selectedId, workflow.nodes]);
  const nodes = useMemo(() => {
    if (orientation === "horizontal") return workflow.nodes;
    const minimumX = Math.min(...workflow.nodes.map((node) => node.x));
    const minimumY = Math.min(...workflow.nodes.map((node) => node.y));
    return workflow.nodes.map((node) => ({
      ...node,
      x: 120 + ((node.y - minimumY) * 1.25),
      y: 35 + ((node.x - minimumX) * 0.72),
    }));
  }, [orientation, workflow.nodes]);
  const canvasSize = useMemo(() => ({
    width: Math.max(720, Math.ceil(Math.max(...nodes.map((node) => node.x)) + 270)),
    height: Math.max(620, Math.ceil(Math.max(...nodes.map((node) => node.y)) + 190)),
  }), [nodes]);

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
        setWorkflow(await loadWorkflowProjection(demoWorkflow, catalog[0].taskId));
      } else {
        setWorkflow(await loadWorkflowProjection(demoWorkflow));
      }
    })();
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
  const handleCanvasWheel = (event: React.WheelEvent<HTMLDivElement>) => {
    const element = canvasWindowRef.current;
    if (!element) return;
    event.preventDefault();
    if (event.shiftKey) {
      element.scrollLeft += event.deltaY || event.deltaX;
      updateViewport();
      return;
    }
    setZoom((value) => clamp(value + (event.deltaY < 0 ? 0.08 : -0.08), 0.2, 1.1));
  };

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark"><GitBranch size={18}/></span><span>ActionCharter</span><span className="checkpoint">17F</span></div>
      <label className="run-switcher"><CircleDot size={15}/><span className="sr-only">Select workflow run</span><select value={selectedTaskId} disabled={!runs.length} onChange={(event) => { const taskId = event.target.value; setSelectedTaskId(taskId); void loadWorkflowProjection(demoWorkflow, taskId).then(setWorkflow); }}><option value="">{runs.length ? "Select a validated trace" : "Demonstration workflow"}</option>{runs.map((run) => <option key={run.taskId} value={run.taskId}>{run.taskId} · {run.status}</option>)}</select><ChevronDown size={14}/></label>
      <div className="top-actions"><button className="icon-button" aria-label="Search"><Search size={17}/></button><div className="safe-mode"><ShieldCheck size={15}/><span>Read-only</span></div><div className="avatar">JQ</div></div>
    </header>
    <div className="workspace">
      <aside className="rail">
        <button className="rail-item active"><Workflow size={19}/><span>Flow</span></button><button className="rail-item"><Bot size={19}/><span>Agents</span></button><button className="rail-item"><FileCheck2 size={19}/><span>Evidence</span></button><button className="rail-item"><Database size={19}/><span>Data</span></button><div className="rail-spacer"/><button className="rail-item"><Map size={19}/><span>Guide</span></button>
      </aside>
      <section className="flow-stage" aria-label="Governed workflow graph">
        <div className="stage-heading"><div><p className="eyebrow">Governed workflow</p><h1>{workflow.title}</h1></div><div className="stage-meta"><span><span className="pulse"/> {workflow.source === "validated_trace" ? "Validated trace" : "Demonstration"}</span><span>{nodes.length} nodes</span><span>{workflow.edges.length} links</span></div></div>
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
              {workflow.edges.map((edge) => { const start = nodes.find((node) => node.id === edge.from); const end = nodes.find((node) => node.id === edge.to); if (!start || !end) return null; return <line key={`${edge.from}-${edge.to}`} x1={start.x + 95} y1={start.y + 54} x2={end.x + 95} y2={end.y + 54}/>; })}
              {nodes.map((node) => <rect className={`mini-node kind-${node.kind} status-${node.status}`} key={node.id} x={node.x} y={node.y} width="190" height="108" rx={nodeRadius[node.kind]}/>)}
            </svg>
            <div className="mini-view" style={{ left: viewport.x, top: viewport.y, width: viewport.width, height: viewport.height }}/>
          </div>
          <div className="canvas-window" ref={canvasWindowRef} onScroll={updateViewport} onWheel={handleCanvasWheel}>
            <div className="canvas-sizer" style={{ width: canvasSize.width * zoom, height: canvasSize.height * zoom }}>
              <div className="canvas" style={{ width: canvasSize.width, height: canvasSize.height, transform: `scale(${zoom})` }}>
              <svg className="connections" width={canvasSize.width} height={canvasSize.height} aria-hidden="true"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#468ac7"/></marker></defs>{workflow.edges.map((edge) => {
                const start = nodes.find((node) => node.id === edge.from); const end = nodes.find((node) => node.id === edge.to); if (!start || !end) return null; const horizontal = orientation === "horizontal";
                const x1 = horizontal ? start.x + 190 : start.x + 95; const y1 = horizontal ? start.y + 54 : start.y + 108; const x2 = horizontal ? end.x : end.x + 95; const y2 = horizontal ? end.y + 54 : end.y; const bend = horizontal ? (x1 + x2) / 2 : (y1 + y2) / 2;
                const path = horizontal ? `M ${x1} ${y1} C ${bend} ${y1}, ${bend} ${y2}, ${x2} ${y2}` : `M ${x1} ${y1} C ${x1} ${bend}, ${x2} ${bend}, ${x2} ${y2}`;
                return <path key={`${edge.from}-${edge.to}`} d={path} markerEnd="url(#arrow)"/>;
              })}</svg>
                {nodes.map((node) => { const Icon = icons[node.kind]; return <button key={node.id} className={`flow-node orientation-${orientation} kind-${node.kind} status-${node.status} ${selectedId === node.id ? "selected" : ""}`} style={{ left: node.x, top: node.y, borderRadius: nodeRadius[node.kind] }} onClick={() => setSelectedId(node.id)}><span className="node-port in"/><span className="node-port out"/><span className="node-kicker">{labels[node.kind]}<span className="node-state"><CheckCircle2 size={13}/>{node.status}</span></span><span className="node-main"><span className="node-icon"><Icon size={19}/></span><span><strong>{node.title}</strong><small>{node.subtitle}</small></span></span><span className="node-footer"><span className="actor-label">{node.performedBy ?? labels[node.kind]}</span><ZoomIn size={13}/></span></button>; })}
              </div>
            </div>
          </div>
        </div>
        <div className="timeline"><div className="timeline-title"><span>Execution timeline</span><small>correlation · {workflow.correlationId}</small></div><div className="timeline-scroll"><div className="timeline-content" style={{ minWidth: Math.max(600, nodes.length * 108) }}><div className="timeline-track"><span className="track-fill"/>{nodes.map((node, index) => <button key={node.id} aria-label={`Inspect ${node.title}`} className={`timeline-marker status-${node.status} ${selected.id === node.id ? "selected" : ""}`} style={{ left: `${nodes.length === 1 ? 0 : (index / (nodes.length - 1)) * 100}%` }} onClick={() => setSelectedId(node.id)}/>)}</div><div className="timeline-labels" style={{ gridTemplateColumns: `repeat(${nodes.length}, minmax(88px, 1fr))` }}>{nodes.map((node) => <button key={node.id} className={selected.id === node.id ? "selected" : ""} onClick={() => setSelectedId(node.id)}><strong>{node.title}</strong><small>{node.status}</small></button>)}</div></div></div></div>
      </section>
      <aside className="inspector">
        <div className="inspector-head"><div><p className="eyebrow">Inspector</p><h2>{selected.title}</h2></div><span className={`type-chip kind-${selected.kind}`}>{labels[selected.kind]}</span></div>
        <div className={`status-card status-${selected.status}`}><CheckCircle2 size={20}/><div><strong>{selected.status.replace("_", " ")}</strong><span>Evidence-backed status</span></div></div>
        <section className="detail-section"><h3>Performed by</h3><p className="performer"><Bot size={15}/>{selected.performedBy ?? labels[selected.kind]}</p></section>
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
        <div className="inspector-note"><ShieldCheck size={16}/><p>This view can inspect evidence, but cannot approve or execute work.</p></div>
      </aside>
    </div>
  </main>;
}
