import { useEffect, useState } from "react";
import { z } from "zod";

const reasoningSchema=z.object({selection:z.enum(['environment','provider','none','low','medium','high']),effective:z.string().nullable(),revision:z.number(),source:z.string()});
const catalogSchema = z.object({
  models: z.array(z.object({ name: z.string(), size_bytes: z.number().nullable(), loaded: z.boolean(), compatibility: z.enum(["untested","checked"]) })),
  review_timeout:z.object({seconds:z.number(),revision:z.number(),source:z.string()}),
  reasoning:reasoningSchema,
  count: z.number(), selected_model: z.string().nullable(), revision: z.number(),
  selected_available: z.boolean(), loaded_status_error: z.string().nullable(),
  provider_id:z.string().default('local'),provider_revision:z.number().default(0),
});
const profilesSchema=z.object({revision:z.number(),selected_profile:z.string(),profiles:z.array(z.object({
  id:z.string(),kind:z.string(),location:z.string(),listing:z.string(),data_allowed:z.string(),
  credential_configured:z.boolean(),enabled:z.boolean(),
  effective_data_allowed:z.string().optional(),nonlocal_restricted:z.boolean().optional(),
}))});
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
  const [profiles,setProfiles]=useState<z.infer<typeof profilesSchema>|null>(null);
  const [providerChoice,setProviderChoice]=useState('local');
  const [profileId,setProfileId]=useState('');
  const [endpoint,setEndpoint]=useState('http://127.0.0.1:11434/v1');
  const [profileModel,setProfileModel]=useState('');
  const [credentialRef,setCredentialRef]=useState('');
  const [kind,setKind]=useState('local');
  const [listing,setListing]=useState('openai-compatible');
  const [allowance,setAllowance]=useState('raw');
  const [capability,setCapability]=useState('auto');
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [choice, setChoice] = useState("");
  const [reasoning,setReasoning]=useState<z.infer<typeof reasoningSchema>['selection']>('environment');
  const [reviewSeconds,setReviewSeconds]=useState(15);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [notice, setNotice] = useState("");
  const refresh = async () => {
    setBusy(true); setError(""); setNotice("");
    try {
      const response=await fetch('/api/v1/providers');
      if(!response.ok)throw new Error('Provider configuration unavailable');
      const loaded=profilesSchema.parse(await response.json());setProfiles(loaded);setProviderChoice(loaded.selected_profile);
      const next = await request(""); setCatalog(next); setChoice(next.selected_model ?? "");setReasoning(next.reasoning.selection);setReviewSeconds(next.review_timeout.seconds);
    } catch (e) { setError(e instanceof Error ? e.message : "Model discovery failed"); }
    finally { setBusy(false); }
  };
  useEffect(() => { void refresh(); }, []);
  const apply = async () => {
    if (!catalog) return;
    setBusy(true); setError("");
    try {
      const next=await request("/select", { model: choice, expected_revision: catalog.revision,provider_id:catalog.provider_id,provider_revision:catalog.provider_revision });
      setCatalog(next);if(profiles)setProfiles({...profiles,revision:next.provider_revision});
      setNotice("Model selected for new requests. Active requests keep their starting model.");
    } catch (e) { setError(e instanceof Error ? e.message : "Model selection failed"); }
    finally { setBusy(false); }
  };
  const providerAction=async(path:string,body:unknown)=>{
    const response=await fetch(`/api/v1/providers/${path}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const value:unknown=await response.json();
    if(!response.ok)throw new Error(z.object({error:z.string()}).safeParse(value).success?(value as {error:string}).error:'Provider action failed');
    return value;
  };
  const saveProfile=async()=>{
    if(!profiles)return;setSaveError('');setError('');setNotice('');
    if(profileId==='local'){
      setSaveError('The ID local is reserved for launcher settings. Choose another ID, such as ollama-test; it can use the same Ollama endpoint.');return;
    }
    if(!/^[a-z][a-z0-9_-]{0,63}$/.test(profileId)){
      setSaveError('Profile ID must start with a lowercase letter and contain only lowercase letters, numbers, hyphens or underscores (up to 64 characters).');return;
    }
    setBusy(true);
    try{
      await providerAction('save',{expected_revision:profiles.revision,profile:{id:profileId,base_url:endpoint,kind,listing,data_allowed:allowance,capabilities:capability,
        ...(profileModel?{model:profileModel}:{}),...(credentialRef?{credential_ref:credentialRef}:{})}});
      await refresh();setNotice('Provider saved. Select it explicitly to use it for new requests.');
    }catch(e){setSaveError(e instanceof Error?e.message:'Provider save failed');}finally{setBusy(false);}
  };
  const useProvider=async()=>{
    if(!profiles)return;setBusy(true);setError('');setNotice('');
    try{await providerAction('select',{profile_id:providerChoice,expected_revision:profiles.revision});await refresh();setNotice('Provider selected for new requests. Active requests keep their starting profile.');}
    catch(e){setError(e instanceof Error?e.message:'Provider selection failed');}finally{setBusy(false);}
  };
  const checkProvider=async()=>{
    if(!profiles)return;setBusy(true);setError('');setNotice('');
    try{
      const value=z.object({status:z.string(),response_format:z.string().optional(),code:z.string().optional()}).parse(await providerAction('check',{
        profile_id:profiles.selected_profile,model:choice,expected_revision:profiles.revision}));
      await refresh();setNotice(value.status==='compatible'?`Synthetic check passed: ${value.response_format}. Full workflow compatibility remains untested.`:`Compatibility check: ${value.status} · ${value.code??'refresh before retrying'}`);
    }catch(e){setError(e instanceof Error?e.message:'Compatibility check failed');}finally{setBusy(false);}
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
  const saveDisabledReason=busy?'Wait for the current settings request to finish.'
    :!profileId?'Enter a profile ID to enable Save provider.'
    :!endpoint?'Enter an endpoint to enable Save provider.':'';
  const checkDisabledReason=busy?'Wait for the current settings request to finish.'
    :!profiles?'Load provider settings before checking compatibility.'
    :providerChoice!==profiles.selected_profile?'Click Use provider to apply the chosen profile before checking compatibility.'
    :profiles.selected_profile==='local'?'The local profile uses launcher settings. Compatibility checks currently require a saved profile; add and select one to check the same Ollama service.'
    :!choice?'Select a model before checking compatibility.':'';
  const activeProvider=profiles?.profiles.find(p=>p.id===profiles.selected_profile);
  return <section className="appearance-settings model-service-settings" aria-labelledby="model-settings-title">
    <h3 id="model-settings-title">Model service</h3>
    <p>Choose a provider and model for this project. Active requests keep their starting configuration.</p>
    {profiles && <>
      <label>Provider<select aria-label="Model provider" value={providerChoice} disabled={busy} onChange={e=>setProviderChoice(e.target.value)}>
        {profiles.profiles.map(p=><option key={p.id} value={p.id} disabled={!p.enabled}>{p.id} · {p.id==='local'?'launcher settings':p.kind}{p.enabled?'':' · blocked'}</option>)}
      </select></label>
      <button className="context-intent-toggle" disabled={busy||providerChoice===profiles.selected_profile} onClick={()=>void useProvider()}>Use provider</button>
      {activeProvider&&<p>Active provider: {activeProvider.id} · Effective data allowance: {activeProvider.effective_data_allowed??'Unknown — restart the updated API'}</p>}
      <small>The gateway checks every model request before sending. Explicit non-loopback profiles remain blocked pending provider qualification; ordinary non-loopback launcher endpoints are limited to synthetic requests. The existing Docker host bridge retains its trusted local-runtime scope.</small>
      <details className="model-provider-editor"><summary>Add or replace a provider</summary>
        <label>Profile ID<input aria-label="Provider profile ID" value={profileId} onChange={e=>setProfileId(e.target.value)} placeholder="local-proxy"/></label>
        <small>Use a lowercase ID such as ollama-test. The ID local is reserved. Different profiles may share the same endpoint.</small>
        <label>Endpoint<input aria-label="Provider endpoint" value={endpoint} onChange={e=>setEndpoint(e.target.value)}/></label>
        <label>Default model<input aria-label="Provider default model" value={profileModel} onChange={e=>setProfileModel(e.target.value)} placeholder="Optional; discover models after selection"/></label>
        <label>Provider kind<select aria-label="Provider kind" value={kind} onChange={e=>{setKind(e.target.value);setAllowance(e.target.value==='local'?'raw':'none');}}>
          {['local','onsite','gateway','public'].map(v=><option key={v}>{v}</option>)}
        </select></label>
        <label>Model listing<select aria-label="Provider listing" value={listing} onChange={e=>setListing(e.target.value)}><option value="openai-compatible">Compatible API</option><option value="ollama">Ollama native</option></select></label>
        <label>Credential reference<input aria-label="Provider credential reference" value={credentialRef} onChange={e=>setCredentialRef(e.target.value)} placeholder="env:MODEL_GATEWAY_KEY or secret:model-key"/></label>
        <small>Enter a reference, never the key itself. No credentials are returned by this panel.</small>
        <label>Data allowance<select aria-label="Provider data allowance" value={allowance} onChange={e=>setAllowance(e.target.value)}>{['none','metadata','data_card','aggregates','raw'].map(v=><option key={v}>{v}</option>)}</select></label>
        <small>Ordinary planning currently requires Raw allowance; lower allowances permit only matching explicitly classified requests, including synthetic checks.</small>
        <label>Response format<select aria-label="Provider response format" value={capability} onChange={e=>setCapability(e.target.value)}>{['auto','json_schema','json_object','text'].map(v=><option key={v}>{v}</option>)}</select></label>
        <button className="context-intent-toggle" disabled={Boolean(saveDisabledReason)} aria-describedby={saveDisabledReason?'provider-save-help':undefined} title={saveDisabledReason||undefined} onClick={()=>void saveProfile()}>Save provider</button>
        {saveDisabledReason && <small id="provider-save-help">{saveDisabledReason}</small>}
        {saveError && <p role="alert">{saveError}</p>}
      </details>
    </>}
    <button className="context-intent-toggle" disabled={busy} onClick={() => void refresh()}>{busy ? "Checking…" : "Refresh models"}</button>
    {error && <p role="alert">{error}</p>}
    {catalog && <>
      <p>{catalog.count} available models · Current: {catalog.selected_model ?? "None selected"}</p>
      {!catalog.selected_available && catalog.selected_model && <p role="alert">The selected model is not available. Select another model explicitly.</p>}
      <label>Model<select aria-label="Provider model" value={choice} disabled={busy} onChange={e => setChoice(e.target.value)}>
        <option value="">Select a model</option>
        {catalog.selected_model && !catalog.selected_available && <option value={catalog.selected_model}>{catalog.selected_model} · unavailable</option>}
        {catalog.models.map(model => <option key={model.name} value={model.name}>{model.name}{model.loaded ? " · loaded" : ""}{model.size_bytes !== null ? ` · ${(model.size_bytes / 1024 ** 3).toFixed(1)} GiB` : ""}</option>)}
      </select></label>
      <button className="context-intent-toggle" disabled={busy || !catalog.models.some(m => m.name === choice) || choice === catalog.selected_model} onClick={() => void apply()}>Use selected model</button>
      <button className="context-intent-toggle" disabled={Boolean(checkDisabledReason)} aria-describedby={checkDisabledReason?'provider-compatibility-help':undefined} title={checkDisabledReason||undefined} onClick={()=>void checkProvider()}>Check compatibility</button>
      {checkDisabledReason && <small id="provider-compatibility-help">{checkDisabledReason}</small>}
      <label>Reasoning effort<select aria-label="Model reasoning effort" value={reasoning} disabled={busy} onChange={e=>setReasoning(e.target.value as typeof reasoning)}>
        <option value="environment">Use launcher setting</option><option value="provider">Provider default</option><option value="none">None · no thinking</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
      </select></label>
      <p>Effective reasoning: {catalog.reasoning.effective??'Provider default (not set)'} · {catalog.reasoning.source}</p>
      <button className="context-intent-toggle" disabled={busy||reasoning===catalog.reasoning.selection} onClick={()=>void applyReasoning()}>Use reasoning setting</button>
      <small>For compatible local models, None can reduce planning time. Supported levels vary by model; unsupported choices can be rejected. This setting grants no execution or write permission.</small>
      <label>Critic outcome review timeout (seconds)<input type="number" aria-label="Critic outcome review timeout" min={5} max={180} step={1} value={reviewSeconds} disabled={busy} onChange={e=>setReviewSeconds(Number(e.target.value))}/></label>
      <button className="context-intent-toggle" disabled={busy||!Number.isInteger(reviewSeconds)||reviewSeconds<5||reviewSeconds>180||reviewSeconds===catalog.review_timeout.seconds} onClick={()=>void applyReviewTimeout()}>Save review timeout</button>
      <small>Standalone post-run Critic review only; default 15 seconds, range 5–180. The model request timeout can lower this limit. Coordinated Single/Three reports retain their separate effort budget. Changing this does not retry a review or execute a workflow.</small>
      {catalog.loaded_status_error && <p>{catalog.loaded_status_error}</p>}
    </>}
    {notice && <p role="status">{notice}</p>}
    <small>Listing and selection generate no text and download no models. Check compatibility sends only a bounded synthetic JSON request. The Local profile preserves launcher settings; explicit profiles use their saved connection settings. No choice grants execution or write authority.</small>
  </section>;
}
