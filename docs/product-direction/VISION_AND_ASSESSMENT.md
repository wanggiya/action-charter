# Vision and assessment (snapshot 2026-11-01)

Direction document. The numbers below were measured on 2026-11-01 on branch
`checkpoint/agent-modes-consolidation`, which had a large uncommitted working tree.
Re-measure before relying on them.

## Vision (owner's words, condensed)

- Software that runs on Linux now and Windows later.
- It fills the gap for people who want AI help but whose data is too sensitive for external APIs.
- AI agents maximize, optimize and accelerate data science and data engineering, and make the outputs easy for people without data-science knowledge to use.
- Agents are separated by role and responsibility, and they evolve and learn automatically.
- Later: a fully autonomous agent platform on cloud or on-site servers covering data processing, science, engineering and administration. See [AUTONOMOUS_PLATFORM_DESIGN.md](AUTONOMOUS_PLATFORM_DESIGN.md).

## Current condition

**Size:** about 75k lines of Python in 62 subpackages under `src/geoagent_harness`, about 7.4k lines of TypeScript (`interface/src/App.tsx` alone is 2,683 lines), 2,254 passing tests, 174 tracked docs (about 100 are `CHECKPOINT*.md`), about 55 top-level directories, 187 commits since 2026-07-26.

**Strengths (delivered):**
- Fully local model via Ollama (qwen3.5:9b / qwen3 family); containers are limited to the local model network.
- Strong governance: typed operations, deterministic policy, exact Authorize → Execute, create-only writes, hash-verified lineage, Critic review, Snakemake export.
- Data coverage: CSV/XLSX/JSON(L) inspection, preparation, joins, statistics (descriptive, Pearson/Spearman, OLS), readiness reports (Markdown/PDF), PostgreSQL/PostGIS round trip, vector/raster, GeoServer.
- Roles: Planner, Executor, Critic, Builder, method_memory. Single/Three-agent mode is chosen manually.
- Interfaces: React workflow graph + chat, CLI, terminal chat, MCP server.

**Unproven or open (from the project's own records):**
- Real local-model reliability (F5 partial): 40–120 s per planning call, timeouts, advisory reviews often unavailable.
- Learning: the ranking evaluation showed no benefit (OFF 3/6, ON 2/6). "Self-evolving" is a design ([LEARNING_WITHOUT_RL.md](../LEARNING_WITHOUT_RL.md)), not a demonstrated capability.
- Non-expert usability: never tested. Interface vocabulary (digest, scope, recipe, evidence, Authorize/Execute colours) is aimed at engineers.
- Packaging: not a packaged app. Depends on WSL + Docker + host Ollama; Windows is not addressed.

## Priorities (recommended order)

1. **Freeze features and pick one hero journey.** For example: Excel/CSV in → profile and clean → answer 3–5 plain-language questions → readable report. Treat PostGIS promotion/rollback, GeoServer and Snakemake as secondary until this works end to end on the real local model.
2. **Benchmark suite as the main metric.** 20–30 realistic tasks on synthetic sensitive-style data. Measure success rate, wall time, model calls and user clicks for each model size. Fixture models do not count as evidence.
3. **Reduce model calls per task.** Use deterministic routing and recipes for solved tasks, and the LLM only for intent and interpretation. Make Three-agent mode opt-in until the benchmark shows it helps (on one shared 9B model it multiplies latency).
4. **Prove one learning loop**: case-based recipe reuse that makes a repeat task measurably faster or more accurate. Do this before claiming auto-evolution; Builder code generation and fine-tuning come later.
5. **Guided (non-expert) interface mode.** See [EDITIONS_AND_INTERFACES.md](EDITIONS_AND_INTERFACES.md).
6. **Package the Linux Personal edition** (one installer, first-run model check, no Docker for the basic path). Avoid new hard WSL dependencies so Windows stays possible.

## Structural problems

| Problem | Evidence | Fix |
|---|---|---|
| Runtime state mixed with source | About 30 artifact directories at repo root (`builder-*` ×12, `recipe-runs`, `traces`, `planner-conversations`, `approved-recipes.local.json`…); 1.5 GB working directory | One workspace/data root (e.g. `~/.local/share/actioncharter/<project>` or `./workspace/`). Needed for packaging and Windows. |
| Package sprawl | 11 `postgis_*` packages (promotion/rollback × plan/approval/execution/verification) | One database lifecycle module with a generic plan → approve → execute → verify → rollback pattern |
| Duplicate transports | `interface_api`, `chat`, `mcp_server`, `cli.py` each reach into services | Shared task-actions layer, as already planned in [GENERALIZATION_AND_CONSOLIDATION_PLAN.md](../GENERALIZATION_AND_CONSOLIDATION_PLAN.md) |
| Docs are a diary | Status and resume files are dense logs; about 100 checkpoint docs | Done 2026-11-01: checkpoints moved to `docs/development/checkpoints/` with links rewritten. Keep a short README, architecture doc, user guide and one living status page. |
| Frontend monolith | 2,683-line `App.tsx` | Split by workspace (Planner / Graph / Results / Settings) with a state store |
| Identity drift | Repo `geoagent-skill-harness`, product "ActionCharter", pitch is general data science | Decide whether GIS is the niche or one plugin |
| Mixed storage | SQLite for chats, JSON files for evidence/approvals across many directories | SQLite (desktop) / PostgreSQL (server) behind one repository layer; files only for large artifacts |
| Safety hurts usability | Every gate adds vocabulary and clicks | Keep guarantees in the backend and present them simply (Guided mode) |
| "Agents" are prompt roles | All roles run sequentially on one model; one container per role in compose | Describe them as roles. One process on desktop; containers only for sandboxed workers. |

## Competitive landscape

| Product | Their advantage | Our advantage |
|---|---|---|
| **Impulse AI** (impulselabs.ai) — no-code "autonomous ML engineer": prompt → trained, deployed model with API; claims top 2.5% on a Kaggle competition (self-reported) | Frontier models, speed, polished no-code UX, ML deployment | Fully local/offline; broader engineering, statistics and GIS scope; auditability. They are cloud SaaS as far as we found. |
| ChatGPT data analysis, Julius AI | Best ease of use and model quality | They are cloud-only, which excludes our target users |
| Databricks Genie, Snowflake Cortex, Hex | AI inside the customer's governed warehouse. **Main enterprise competitor for sensitive data.** | No cloud or warehouse required: small organisations, air-gapped sites, individual researchers |
| H2O Driverless AI, DataRobot on-prem | Mature on-prem AutoML | Conversational, cheaper, covers engineering and reporting, not only modelling |
| Open source (PandasAI, Open Interpreter, Open WebUI/AnythingLLM + Jupyter, n8n + Ollama) | Free, flexible, simple | Governance, verification, audit trail, reproducibility. They run arbitrary generated code. |

**Positioning:** "The auditable, offline AI data analyst for regulated data." Likely first market: health research (current tests use diabetes/readmission data) and public-sector GIS.
**Gaps to close to compete:** reliability, speed, simplicity, packaging.
