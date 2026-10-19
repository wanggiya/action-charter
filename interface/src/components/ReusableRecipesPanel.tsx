import { recipeKeywords, successfulSummary } from "../lib/recipe-browser";
import { SuccessfulRecipes } from "./SuccessfulRecipes";
import { useEffect, useState } from "react";
import { X, Layers, Search } from "lucide-react";
import { plannerResultSchema } from "../lib/interface-api";
import type { InterfacePlannerResult } from "../lib/interface-api";
import { recipes, recipeCatalogSchema, plannerBase } from "../lib/workflow-tools";
import type { ReusableRecipe, SuccessfulMethod } from "../lib/workflow-tools";
import { z } from "zod";

type Entry={definition:ReusableRecipe;recipe_sha256:string;origin:string};
type Candidate={definition:Record<string,unknown>;recipe_sha256:string;critic:{conclusion:string;findings:string[];limitations:string[]};test_report?:unknown};
type Use={recipe_id:string;recipe_sha256:string;alias:string;parameters:Record<string,unknown>};
export function ReusableRecipesPanel({base,onClose,onPlan,onDiscuss,onInspectRun}:{base:InterfacePlannerResult|null;onClose:()=>void;onPlan:(result:InterfacePlannerResult)=>Promise<void>;onDiscuss:(message:string,methodId?:string)=>void;onInspectRun:(id:string)=>void}){
  const [view,setView]=useState<"recipes"|"keywords">("recipes"),[keyword,setKeyword]=useState<string|null>(null),[selectedSuccessful,setSelectedSuccessful]=useState<SuccessfulMethod|null>(null);
  const [successful,setSuccessful]=useState<SuccessfulMethod[]>([]),[retentionFinding,setRetentionFinding]=useState<string|null>(null);
  const [catalog,setCatalog]=useState<Entry[]>([]),[query,setQuery]=useState("");
  const [selected,setSelected]=useState<Entry|null>(null),[values,setValues]=useState<Record<string,string>>({});
  const [busy,setBusy]=useState(false),[notice,setNotice]=useState(""),[candidate,setCandidate]=useState<Candidate|null>(null);
  const [queue,setQueue]=useState<Use[]>([]);
  const [unavailable,setUnavailable]=useState<Array<{id:string;name:string;finding:string}>>([]);
  const refresh=async()=>{let conversation_id:string|undefined;try{const value=localStorage.getItem('actioncharter:planner-conversation:v1');if(value&&/^[a-f0-9]{32}$/.test(value))conversation_id=value;}catch{/* Unlinked records only. */}const result=recipeCatalogSchema.parse(await recipes({action:"list",conversation_id}));setCatalog(result.recipes);setUnavailable(result.unavailable);setSuccessful(result.successful_records);setRetentionFinding(result.successful_records_finding??null);};
  useEffect(()=>{void refresh().catch(()=>setNotice("Reusable recipes unavailable. Restart the updated API."));},[]);
  const choose=(item:Entry)=>{setSelectedSuccessful(null);setSelected(item);setNotice("");setValues(Object.fromEntries(Object.entries(item.definition.parameters).map(([key,p])=>[key,p.type==="array"?"[]":p.type==="object"?"{}":""])));};
  const currentUse=():Use=>{if(!selected)throw new Error("Choose a recipe");const parameters=Object.fromEntries(Object.entries(selected.definition.parameters).map(([key,p])=>[key,["array","object","integer","number","boolean"].includes(p.type)?JSON.parse(values[key]):p.type==="csv_source"&&values[key].trim().startsWith("{")?JSON.parse(values[key]):values[key]]));return {recipe_id:selected.definition.id,recipe_sha256:selected.recipe_sha256,alias:`recipe_${queue.length+1}`,parameters};};
  const enqueue=()=>{try{setQueue([...queue,currentUse()]);setSelected(null);setNotice("Recipe added to Advanced composition. Bind another recipe or validate the draft.");}catch{setNotice("Check typed recipe parameters before adding.");}};
  const compose=async()=>{if(!selected&&!queue.length)return;setBusy(true);setNotice("Validating recipe inputs and expanded operations…");try{
    const result=plannerResultSchema.parse(await recipes({action:"compose",uses:selected?[...queue,currentUse()]:queue}));
    await onPlan(result);onClose();
  }catch(e){setNotice(e instanceof Error?e.message:"Recipe parameters rejected");}finally{setBusy(false);}};
  const prepare=async()=>{if(!base)return;setBusy(true);setNotice("Planner is preparing a recipe and synthetic tests; Critic reviews after fixture verification. Your workflow stays unchanged.");try{
    const parsed=z.object({definition:z.record(z.unknown()),recipe_sha256:z.string(),test_report:z.unknown(),critic:z.object({conclusion:z.string(),findings:z.array(z.string()),limitations:z.array(z.string())})}).parse(await recipes({action:"prepare",base:plannerBase(base)}));setCandidate(parsed);setNotice("Candidate prepared. Registration stores a reusable definition; it does not execute your data.");
  }catch(e){setNotice(e instanceof Error?e.message:"Recipe preparation failed");}finally{setBusy(false);}};
  const register=async()=>{if(!candidate)return;setBusy(true);try{await recipes({action:"register",definition:candidate.definition,confirmed_recipe_sha256:candidate.recipe_sha256,confirm_register:true});setCandidate(null);await refresh();setNotice("Recipe registered. Available across restarts; execution still requires current authority.");}catch(e){setNotice(e instanceof Error?e.message:"Registration failed");}finally{setBusy(false);}};
  const matchesSuccessful=successful.filter(record=>(!keyword||record.tags.includes(keyword))&&`${successfulSummary(record)} ${record.name} ${record.tags.join(' ')}`.toLowerCase().includes(query.toLowerCase()));
  const matchesTemplates=catalog.filter(entry=>(!keyword||recipeKeywords(entry.definition).includes(keyword))&&`${entry.definition.name} ${entry.definition.description} ${recipeKeywords(entry.definition).join(' ')}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="template-overlay"><section className="record-workspace reusable-recipes-workspace" role="dialog" aria-modal="true" aria-labelledby="reusable-title"><header className="template-workspace-head"><h2 id="reusable-title"><Layers size={20}/> Reusable recipes</h2><button aria-label="Close reusable recipes" disabled={busy} onClick={onClose}><X size={18}/></button></header>
    <nav className="recipe-browser-tabs" aria-label="Recipe browser views">
      <button className="context-intent-toggle utility-button" aria-pressed={view==='recipes'} onClick={()=>setView('recipes')}>Recipe list</button>
      <button className="context-intent-toggle utility-button" aria-pressed={view==='keywords'} onClick={()=>{setView('keywords');setSelected(null);setSelectedSuccessful(null);}}>Keywords</button>
    </nav>
    {view==='keywords'?<section className="recipe-keyword-view" aria-label="Recipe keywords">
      {[...new Set([...catalog.flatMap(entry=>recipeKeywords(entry.definition)),...successful.flatMap(record=>record.tags)])].sort().map(word=><button key={word} className="context-intent-toggle utility-button" aria-pressed={keyword===word} onClick={()=>{setKeyword(word);setView('recipes');setSelected(null);setSelectedSuccessful(null);}}>{word}</button>)}
    </section>:<section className="recipe-list-view" aria-label="Recipe list">
      <label className="recipe-search"><Search size={15}/> Find a recipe<input value={query} onChange={e=>{setQuery(e.target.value);setSelected(null);setSelectedSuccessful(null);}} placeholder="Search recipe summaries…"/></label>
      {keyword&&<div className="recipe-active-filter"><span>Keyword: {keyword}</span><button className="context-intent-toggle" onClick={()=>setKeyword(null)}>Clear filter</button></div>}
      <div className="recipe-summary-list">
        {matchesSuccessful.map(record=><button key={record.method_id} className="context-intent-toggle recipe-summary-row" aria-pressed={selectedSuccessful?.method_id===record.method_id} onClick={()=>{setSelected(null);setSelectedSuccessful(record);}}><strong>{successfulSummary(record)}</strong><small>Recorded success · {record.sources.length} source {record.sources.length===1?'run':'runs'}</small></button>)}
        {matchesTemplates.map(item=><button className="context-intent-toggle recipe-summary-row" key={item.definition.id} aria-pressed={selected?.definition.id===item.definition.id} disabled={busy} onClick={()=>choose(item)}><strong>{item.definition.name}</strong><small>{item.origin==='builtin'?'Built-in template':'Tested template'}</small></button>)}
      </div>
      {!matchesSuccessful.length&&!matchesTemplates.length&&<p role="status">No recipes match this search or keyword.</p>}
      {!successful.length&&<small className="recipe-retention-hint">Successful workflows appear automatically after execution and required validation. No registration needed.</small>}
      {retentionFinding&&<p role="status">{retentionFinding}</p>}
      {selectedSuccessful&&<SuccessfulRecipes record={selectedSuccessful} onInspect={onInspectRun} onDiscuss={onDiscuss}/>}
    </section>}
    {view==='recipes'&&unavailable.length>0&&<details className="detail-section"><summary>Recipes requiring migration · {unavailable.length}</summary>{unavailable.map(item=><p key={item.id}><strong>{item.name}</strong> · {item.finding}</p>)}</details>}
    {view==='recipes'&&queue.length>0&&<details className="detail-section"><summary>Advanced composition</summary><h3>Composition order</h3><p>{queue.map(u=>`${u.alias}: ${catalog.find(e=>e.definition.id===u.recipe_id)?.definition.name??u.recipe_id}`).join(" → ")}</p><button disabled={busy} onClick={()=>setQueue([])}>Clear composition</button>{!selected&&<button className="context-intent-toggle" disabled={busy} onClick={()=>void compose()}>Validate composition and open draft</button>}</details>}
    {view==='recipes'&&selected&&<section className="detail-section"><h3>{selected.definition.name}</h3><p>{selected.definition.description}</p><details><summary>More actions</summary><button className="context-intent-toggle" disabled={busy} onClick={()=>onDiscuss(`Use the ${selected.definition.name} recipe for my task. `)}>Discuss this template</button></details><details><summary>Advanced parameter inspector</summary><p className="recipe-operation-chain">{selected.definition.steps.map(s=>s.skill.replaceAll("_"," ")).join(" → ")}</p>{Object.entries(selected.definition.parameters).map(([key,p])=><label key={key}>{key.replaceAll("_"," ")}<small>{p.description}</small>{p.type==="csv_source"&&queue.length>0&&<select aria-label="Connect previous recipe output" value="" onChange={e=>{if(e.target.value)setValues({...values,[key]:JSON.stringify({recipe_output:e.target.value})});}}><option value="">Use original input or connect a CSV output…</option>{queue.filter(u=>catalog.find(e=>e.definition.id===u.recipe_id)?.definition.output_contract==="table/csv-v1").map(u=><option key={u.alias} value={u.alias}>{u.alias} → CSV input</option>)}</select>}{["array","object"].includes(p.type)?<textarea rows={2} value={values[key]??""} disabled={busy} onChange={e=>setValues({...values,[key]:e.target.value})}/>:<input value={values[key]??""} disabled={busy} onChange={e=>setValues({...values,[key]:e.target.value})}/>}</label>)}<button className="context-intent-toggle" disabled={busy} onClick={enqueue}>Add to composition</button><button className="context-intent-toggle" disabled={busy} onClick={()=>void compose()}>Validate composition and open draft</button></details></section>}
    {view==='recipes'&&<details className="detail-section"><summary>Advanced recipe authoring</summary><p>Describe tasks directly in Planner. Successful executions are saved automatically; this optional action generalizes and tests a template.</p><button className="context-intent-toggle" disabled={busy} onClick={()=>onDiscuss(query.trim())}>Describe task in Planner</button><details><summary>Create a reusable recipe from this workflow</summary><p>Planner drafts the JSON and synthetic fixtures; deterministic services run tests; Critic reviews the findings. Model calls run sequentially only when you click Prepare.</p><button className="context-intent-toggle" disabled={busy||!base||!base.plan.steps.some(s=>["vector_attributes_to_csv","select_csv_columns","filter_csv_rows","handle_csv_missing","join_csv","aggregate_csv","export_csv"].includes(s.skill))} onClick={()=>void prepare()}>Prepare recipe</button>{candidate&&<><p>Critic: {candidate.critic.conclusion.replaceAll("_"," ")}</p>{[...candidate.critic.findings,...candidate.critic.limitations].map((f,i)=><p key={i}>{f}</p>)}<details><summary>Definition and fixture evidence</summary><pre>{JSON.stringify(candidate,null,2)}</pre></details><button className="context-intent-toggle" disabled={busy||candidate.critic.conclusion!=="supported"} onClick={()=>void register()}>Register tested recipe</button></>}</details>
    </details>}
    {notice&&<p role="status">{notice}</p>}
  </section></div>;
}
