import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import type { PlannerSkillCatalog } from "../lib/interface-api";
import { skillLabel } from "../lib/skill-labels";

type Skill = PlannerSkillCatalog["skills"][number];
const supported = new Set(["inspect_vector", "inspect_raster", "convert_vector", "convert_raster", "load_vector_to_postgis", "validate_postgis_layer", "generate_report", "export_snakemake_workflow", "verify_snakemake_export"]);
type Props = { x: number; y: number; skills: Skill[]; onAdd: (skill: Skill) => void; onClose: () => void };
export function AddOperationMenu({ x, y, skills, onAdd, onClose }: Props) {
  // Keep keystrokes local so searching does not render the whole graph.
  const [search, setSearch] = useState("");
  const options = useMemo(() => skills.filter((skill) => supported.has(skill.id) && `${skillLabel(skill.id)} ${skill.id}`.toLowerCase().includes(search.trim().toLowerCase().replace(/snake[\s-]+make/g, "snakemake"))), [skills, search]);
  const featured = options.filter((skill) => skill.id.includes("snakemake"));
  const other = options.filter((skill) => !skill.id.includes("snakemake"));
  return <section className="block-add-menu operation-picker" style={{ left: x, top: y }} role="dialog" aria-labelledby="operation-picker-title" onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); onClose(); } }}>
    <header className="operation-picker-header"><div><strong id="operation-picker-title">Add operation</strong><button type="button" className="operation-picker-close" aria-label="Close add operation panel" onClick={onClose}><X size={16}/></button></div><label className="operation-picker-search"><Search size={15}/><input autoFocus aria-label="Search operations" value={search} placeholder="Search operations…" onChange={(event) => setSearch(event.target.value)}/></label></header>
    <div className="operation-picker-results" role="group" aria-label="Available operations">
      {featured.length > 0 && <div className="operation-picker-featured" role="group" aria-label="Snakemake operations"><strong>Snakemake</strong>{featured.sort((a, b) => Number(a.id.startsWith("verify")) - Number(b.id.startsWith("verify"))).map((skill) => <button type="button" className={skill.id.startsWith("verify") ? "snakemake-verify-choice" : "snakemake-export-choice"} key={skill.id} title={skill.id} onClick={() => onAdd(skill)}>{skillLabel(skill.id)}</button>)}</div>}
      {other.map((skill) => <button type="button" key={skill.id} title={skill.id} onClick={() => onAdd(skill)}>{skillLabel(skill.id)}</button>)}
      {!options.length && <p>No matching supported operations.</p>}
    </div>
  </section>;
}
