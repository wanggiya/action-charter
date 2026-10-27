import { useEffect, useState } from "react";
import { z } from "zod";

const catalogSchema = z.object({
  models: z.array(z.object({ name: z.string(), size_bytes: z.number().nullable(), loaded: z.boolean(), compatibility: z.literal("untested") })),
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
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const refresh = async () => {
    setBusy(true); setError(""); setNotice("");
    try {
      const next = await request(""); setCatalog(next); setChoice(next.selected_model ?? "");
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
      {catalog.loaded_status_error && <p>{catalog.loaded_status_error}</p>}
    </>}
    {notice && <p role="status">{notice}</p>}
    <small>Listing and selection do not generate text or download models. Planning compatibility is untested until a request succeeds. The project selection overrides MODEL_NAME; the endpoint remains launcher-configured.</small>
  </section>;
}
