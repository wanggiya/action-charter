import { useEffect, useState } from "react";
import { z } from "zod";

const reasoningSchema=z.object({selection:z.enum(['environment','provider','none','low','medium','high']),effective:z.string().nullable(),revision:z.number(),source:z.string()});
const catalogSchema = z.object({
  models: z.array(z.object({ name: z.string(), size_bytes: z.number().nullable(), loaded: z.boolean(), compatibility: z.literal("untested") })),
  review_timeout:z.object({seconds:z.number(),revision:z.number(),source:z.string()}),
  reasoning:reasoningSchema,
  count: z.number(), selected_model: z.string().nullable(), revision: z.number(),
  selected_available: z.boolean(), loaded_status_error: z.string().nullable(),
});
type Catalog = z.infer<typeof catalogSchema>;
async function request(path: string, body?: unknown): Promise<Catalog> {
  const response = await fetch(`/api/v1/models${path}`, body === undefined ? undefined : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const payload: unknown = await response.json();
  if (!response.ok) throw new Error(z.object({ error: z.string() }).safeParse(payload).success
    ? (payload as { error: string }).error : "Model settings unavailable");
  return catalogSchema.parse(payload);
}
export function ModelSettings() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [choice, setChoice] = useState("");
  const [reasoning,setReasoning]=useState<z.infer<typeof reasoningSchema>['selection']>('environment');
  const [reviewSeconds,setReviewSeconds]=useState(15);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const refresh = async () => {
    setBusy(true); setError(""); setNotice("");
    try {
      const next = await request(""); setCatalog(next); setChoice(next.selected_model ?? "");setReasoning(next.reasoning.selection);setReviewSeconds(next.review_timeout.seconds);
    } catch (e) { setError(e instanceof Error ? e.message : "Model discovery failed"); }
    finally { setBusy(false); }
  };
  useEffect(() => { void refresh(); }, []);
  const apply = async () => {
    if (!catalog) return;
    setBusy(true); setError("");
    try {
      setCatalog(await request("/select", { model: choice, expected_revision: catalog.revision }));
      setNotice("Model selected for new requests. Active requests keep their starting model.");
    } catch (e) { setError(e instanceof Error ? e.message : "Model selection failed"); }
    finally { setBusy(false); }
  };
  const applyReasoning=async()=>{
    if(!catalog)return;setBusy(true);setError('');setNotice('');
    try{
      const response=await fetch('/api/v1/models/reasoning',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({selection:reasoning,expected_revision:catalog.reasoning.revision})});
      if(!response.ok)throw new Error('Reasoning setting changed or is unavailable. Refresh before applying.');
      const value=reasoningSchema.parse(await response.json());setCatalog({...catalog,reasoning:value});
      setNotice('Reasoning setting saved for new requests. No launcher restart, model call or execution occurred.');
    }catch(e){setError(e instanceof Error?e.message:'Reasoning setting unavailable');}finally{setBusy(false);}
  };
  const applyReviewTimeout=async()=>{
    if(!catalog)return;setBusy(true);setError('');setNotice('');
    try{
      const response=await fetch('/api/v1/models/review-timeout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seconds:reviewSeconds,expected_revision:catalog.review_timeout.revision})});
      if(!response.ok)throw new Error('Review timeout was rejected or changed. Refresh before applying.');
      const value=catalogSchema.shape.review_timeout.parse(await response.json());setCatalog({...catalog,review_timeout:value});
      setNotice('Review timeout saved for future requests. Active work keeps its starting setting; no review or execution was retried.');
    }catch(e){setError(e instanceof Error?e.message:'Review timeout unavailable');}finally{setBusy(false);}
  };
  return <section className="appearance-settings" aria-labelledby="model-settings-title">
    <h3 id="model-settings-title">Model service</h3>
    <p>Choose an available model from the configured Ollama service. Changes are saved for this project; no launcher restart is needed.</p>
    <button className="context-intent-toggle" disabled={busy} onClick={() => void refresh()}>{busy ? "Checking…" : "Refresh models"}</button>
    {error && <p role="alert">{error}</p>}
    {catalog && <>
      <p>{catalog.count} available models · Current: {catalog.selected_model ?? "None selected"}</p>
      {!catalog.selected_available && catalog.selected_model && <p role="alert">The selected model is not available. Select another model explicitly.</p>}
      <label>Model<select aria-label="Ollama model" value={choice} disabled={busy} onChange={e => setChoice(e.target.value)}>
        <option value="">Select a model</option>
        {catalog.selected_model && !catalog.selected_available && <option value={catalog.selected_model}>{catalog.selected_model} · unavailable</option>}
        {catalog.models.map(model => <option key={model.name} value={model.name}>{model.name}{model.loaded ? " · loaded" : ""}{model.size_bytes !== null ? ` · ${(model.size_bytes / 1024 ** 3).toFixed(1)} GiB` : ""}</option>)}
      </select></label>
      <button disabled={busy || !catalog.models.some(m => m.name === choice) || choice === catalog.selected_model} onClick={() => void apply()}>Use selected model</button>
      <label>Reasoning effort<select aria-label="Model reasoning effort" value={reasoning} disabled={busy} onChange={e=>setReasoning(e.target.value as typeof reasoning)}>
        <option value="environment">Use launcher setting</option><option value="provider">Provider default</option><option value="none">None · no thinking</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
      </select></label>
      <p>Effective reasoning: {catalog.reasoning.effective??'Provider default (not set)'} · {catalog.reasoning.source}</p>
      <button disabled={busy||reasoning===catalog.reasoning.selection} onClick={()=>void applyReasoning()}>Use reasoning setting</button>
      <small>For compatible local models, None can reduce planning time. Supported levels vary by model; unsupported choices can be rejected. This setting grants no execution or write permission.</small>
      <label>Critic outcome review timeout (seconds)<input type="number" aria-label="Critic outcome review timeout" min={5} max={180} step={1} value={reviewSeconds} disabled={busy} onChange={e=>setReviewSeconds(Number(e.target.value))}/></label>
      <button disabled={busy||!Number.isInteger(reviewSeconds)||reviewSeconds<5||reviewSeconds>180||reviewSeconds===catalog.review_timeout.seconds} onClick={()=>void applyReviewTimeout()}>Save review timeout</button>
      <small>Standalone post-run Critic review only; default 15 seconds, range 5–180. The model request timeout can lower this limit. Coordinated Single/Three reports retain their separate effort budget. Changing this does not retry a review or execute a workflow.</small>
      {catalog.loaded_status_error && <p>{catalog.loaded_status_error}</p>}
    </>}
    {notice && <p role="status">{notice}</p>}
    <small>Listing and selection do not generate text or download models. Planning compatibility is untested until a request succeeds. The project selection overrides MODEL_NAME; the endpoint remains launcher-configured.</small>
  </section>;
}
