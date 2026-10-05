import { useEffect, useState } from "react";
import { Bot, X, ChevronDown, Check, Search } from "lucide-react";
import { createPlannerPlan, loadPlannerSkills, saveGeneratedPlannerPlan, type InterfacePlannerResult, type PlannerSkillCatalog, type SavedPlannerResult } from "../lib/interface-api";

import { skillRecommendationScore } from "../lib/skill-recommendations";
import { skillLabel } from "../lib/skill-labels";

type Props = { visible: boolean; onClose: () => void; onPlan: (plan: InterfacePlannerResult) => void; onSaved: (saved: SavedPlannerResult) => void; onInvalidate: () => void };
export function TextPlanner({ visible, onClose, onPlan, onSaved, onInvalidate }: Props) {
  const [skillsOpen, setSkillsOpen] = useState(false);
  const [skillSearch, setSkillSearch] = useState("");
  const [inputFile, setInputFile] = useState("");
  const [context, setContext] = useState("");
  const [catalog, setCatalog] = useState<PlannerSkillCatalog | null>(null);
  const [skills, setSkills] = useState(["inspect_vector"]);
  const [plan, setPlan] = useState<InterfacePlannerResult | null>(null);
  const [saved, setSaved] = useState<SavedPlannerResult | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!visible || catalog) return;
    let active = true;
    void loadPlannerSkills().then((value) => { if (active) setCatalog(value); }).catch((e: unknown) => { if (active) setError(e instanceof Error ? e.message : "Capabilities unavailable"); });
    return () => { active = false; };
  }, [visible, catalog]);
  const store = async (result: InterfacePlannerResult) => {
    setBusy("Saving validated proposal");
    const stored = await saveGeneratedPlannerPlan(result);
    setSaved(stored); onSaved(stored);
  };
  const generate = async () => {
    if (busy || !context.trim() || !skills.length || !catalog) return;
    setBusy("Generating and validating plan"); setError(""); setPlan(null); setSaved(null); onInvalidate();
    try {
      const result = await createPlannerPlan(context, skills, inputFile.trim() ? [inputFile.trim()] : []);
      setPlan(result); onPlan(result);
      await store(result);
    } catch (e) { setError(e instanceof Error ? e.message : "Plan request blocked"); }
    finally { setBusy(""); }
  };
  const recommendations = (catalog?.skills ?? []).map((skill) => ({ skill, score: skillRecommendationScore(skill, context) })).filter(({ score }) => score > 0).sort((a, b) => b.score - a.score || a.skill.id.localeCompare(b.skill.id)).slice(0, 5);
  return <aside hidden={!visible} className="intent-workbench text-planner" aria-label="Text planner agent">
    <header><div><h2><Bot size={20}/> Text planner agent</h2></div><button onClick={onClose} aria-label="Close text planner"><X size={18}/></button></header>
    <p>Describe your goal, inputs, outputs and constraints in ordinary language. Exact skill IDs are optional. The plan appears alongside this context and is saved automatically after validation.</p>
    <fieldset disabled={Boolean(busy)}>
      <label>Input file <small>Optional · defaults to data/input</small><input value={inputFile} maxLength={960} placeholder="sample_points.geojson or data/input/sample_points.geojson" onChange={(event) => { setInputFile(event.target.value); setPlan(null); setSaved(null); setError(""); onInvalidate(); }}/></label>
      <label>Planning context<textarea rows={14} maxLength={8000} value={context} placeholder={'Inspect data/input/sample_points.geojson. Return feature count, fields and CRS only. No writes or database loading.'} onChange={(e) => { setContext(e.target.value); setPlan(null); setSaved(null); setError(""); onInvalidate(); }}/></label>
      {context.trim() && recommendations.length > 0 && <div className="text-skill-suggestions"><small>Suggested skills · add only what this task needs</small><div>{recommendations.map(({ skill }) => <button type="button" className="intent-secondary" key={skill.id} disabled={skills.includes(skill.id) || skills.length >= 20} title={skill.id} onClick={() => { setSkills((items) => [...items, skill.id]); setPlan(null); setSaved(null); onInvalidate(); }}>{skills.includes(skill.id) ? "Selected · " : "+ "}{skillLabel(skill.id)}</button>)}</div></div>}
      <div className="text-skill-picker" onKeyDown={(event) => { if (event.key === "Escape") setSkillsOpen(false); }}>
        <button type="button" className="intent-secondary skill-picker-trigger" aria-expanded={skillsOpen} aria-controls="text-planner-skills" onClick={() => setSkillsOpen((open) => !open)}><span>Skills · {skills.length} selected</span><ChevronDown size={16}/></button>
        <div className="selected-skill-tags">{skills.map((id) => <button type="button" className="selected-skill-tag" key={id} title={id} aria-label={`Remove ${skillLabel(id)}`} onClick={() => { setSkills((items) => items.filter((item) => item !== id)); setPlan(null); setSaved(null); onInvalidate(); }}>{skillLabel(id)}<X size={12}/></button>)}</div>
        {skillsOpen && <div id="text-planner-skills" className="skill-picker-dropdown"><label className="skill-search-label"><Search size={15}/><input autoFocus aria-label="Search skills" placeholder="Search by name or technical ID…" value={skillSearch} onChange={(event) => setSkillSearch(event.target.value)}/></label><div className="skill-picker-options" role="group" aria-label="Available planning skills">{catalog?.skills.filter((skill) => `${skillLabel(skill.id)} ${skill.id} ${skill.access ?? ""}`.toLowerCase().includes(skillSearch.trim().toLowerCase())).sort((a, b) => skillLabel(a.id).localeCompare(skillLabel(b.id))).map((skill) => <button type="button" className="skill-picker-option" key={skill.id} aria-pressed={skills.includes(skill.id)} disabled={!skills.includes(skill.id) && skills.length >= 20} onClick={() => { setSkills((items) => items.includes(skill.id) ? items.filter((id) => id !== skill.id) : [...items, skill.id]); setPlan(null); setSaved(null); onInvalidate(); }}><span className="skill-choice-mark">{skills.includes(skill.id) && <Check size={14}/>}</span><span><strong>{skillLabel(skill.id)}</strong><small>{skill.id} · {skill.approval_required ? "Approval required for action" : "Read-only / no approval requirement"}</small></span></button>)}</div>{catalog && !catalog.skills.some((skill) => `${skillLabel(skill.id)} ${skill.id} ${skill.access ?? ""}`.toLowerCase().includes(skillSearch.trim().toLowerCase())) && <p>No matching skills. Try another name.</p>}<button type="button" className="intent-secondary" onClick={() => setSkillsOpen(false)}>Done</button></div>}
        <small>Select the skills your task needs. Selection allows planning, not execution.</small>
      </div>
      <button className="text-generate-plan" disabled={!context.trim() || !skills.length || !catalog} onClick={() => void generate()}>Generate plan</button>
    </fieldset>
    <div aria-live="polite">{busy && <p className="intent-notice">{busy}…</p>}{error && <div role="alert" className="intent-error"><strong>{plan ? "Plan ready · automatic save failed" : "Planning blocked"}</strong><p>{error}</p><small>Nothing approved or executed.</small>{plan && !saved && <button disabled={Boolean(busy)} onClick={() => { setError(""); void store(plan).catch((e: unknown) => setError(e instanceof Error ? e.message : "Storage blocked")).finally(() => setBusy("")); }}>Retry saving this plan</button>}</div>}
    {plan && <div className="intent-result"><strong>{saved ? "Plan saved automatically · review in graph" : "Validated plan · graph ready"}</strong><p>{plan.plan.summary}</p><p>{plan.plan.steps.length} steps · {plan.plan.steps.filter((step) => step.requires_approval).length} approval gates</p><details><summary>Steps and technical details</summary><pre>{JSON.stringify(plan.plan.steps, null, 2)}</pre>{saved && <code>{saved.plan_filename}</code>}</details></div>}</div>
    <footer>Automatic storage preserves a generated proposal. It does not record human review, approve work or execute tools. Closing keeps this draft; refresh clears it. Stored plans remain available in Saved plans.</footer>
  </aside>;
}
