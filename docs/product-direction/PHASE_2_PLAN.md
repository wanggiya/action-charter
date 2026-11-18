# Phase 2 — Data Card and planning efficiency

2026-11-17. Owner authorized P1-X closeout and the first Data Card slice.
Phase 1 [exit evidence](../PHASE_1_CLOSEOUT.md) is recorded; Git remains owner-managed.
This plan extends the existing phase table, not the historical checkpoint series.

| ID | Scope | Depends on | Measurable acceptance | Status |
|---|---|---|---|---|
| P2-0 | **Fix first:** project-identity check fails after a WSL restart ("Copied project identity"): device number changed while path, inodes and project UUID are unchanged | — | Same path + same inodes + same UUID is accepted after a device-number change; a real copy is still refused; reviewed recovery, no `--initialize`/`--rebind`, no state reset; owner launcher starts | Planned (blocker for owner manual testing) |
| P2-D1 | Shared typed Data Card over existing bounded discovery/inspection evidence | P1-X | Same card contract in existing CLI/MCP results, Planner context and result Overview; missing facts explicit; bounded payload; no new scanner or authority; sample/selected-table/full-file scopes distinct | Implemented/verified (#98), owner Git pending: all3,120 tests have passing coverage across full/completion runs; interface/browser/CLI/strict gates passed. Bounded real local-model context observations retained; no efficiency improvement claim. |
| P2-D2 | Source selection and fresh/reusable card lifecycle before planning | D1 | Changed bytes/worksheet/filter cannot silently reuse a card; explicit read policy retained; refresh never scans/calls a model; missing/ambiguous inputs ask one concrete question | Planned |
| P2-D3 | Focused capability context and validated recipe routing | D2 | Same fixed tasks/model/settings measured before/after; fewer bytes/calls/time only claimed with equal or better deterministic correctness; full operation policy remains | Planned |
| P2-M3 | Per-role model routing and review budgets | D3, P1-M2 | Explicit profiles and egress per call; execution and Critic completion stay separate; compare routing with fixed model/task evidence | Planned |
| P2-H | CSV/Excel hero journey, including the agreed diabetes analysis test | D2, D3 | Profile/clean, 3–5 justified questions, actual supported calculations and readable report; source grain, missingness, duplicates, limitations and requested statistical results trace to evidence | Planned; targets agreed 2026-11-18 (see below) |
| P2-K | **Agent skills (know-how files)** loaded by D3: format, loader, validation, first skills | D1; built with D3 | See "Skills before code" below. Benchmark tasks improve with skills alone where possible; no new authority | Planned |
| P2-S | Small-cell suppression in health outputs (reports, tables, charts) | D1 | Groups below a configured minimum (default 11) are hidden or merged in every output; rule recorded in evidence; tested | Planned |
| P2-H2 | County-level health map (CDC PLACES-style area data joined to boundaries by FIPS) | H, S | Map produced from recorded data with suppression applied; join mismatches reported | Planned (owner checks data terms first) |
| P2-E2 | CAD import (DXF first; DWG through the chosen converter) with a required coordinate-system step | D1 | Layers/blocks/units recorded; loading blocked until CRS supplied; result in expected area. See [showcase workloads](SHOWCASE_WORKLOADS.md#options-dwg-conversion-decide-before-e2-starts-phase-2) | Planned; **DWG converter decision needed**; DXF part may start |

## Phase 2 targets (agreed by the owner 2026-11-18)

The small tasks above serve one outcome: *give the platform a dataset such as the
diabetes file, ask questions, and get a correct, readable report in reasonable time
with a local model.* Phase 2 is done when, on the same machine and benchmark suite
v1, compared with the B5 baseline (8 passed / 11 failed / 4 timeouts of 27):

| Expectation | Target |
|---|---|
| Works most of the time | At least **15 of 27** tasks pass; no task that passed before now fails on correctness |
| Not painfully slow | Timeouts at least **halved**; median task time **under 60 s** |
| Handles real data | Diabetes hero journey (P2-H) succeeds in **4 of 5** runs |
| Report correct and readable | Every number traces to recorded evidence; plain language; limitations stated (owner checklist) |
| Says no clearly | Safety tasks (group S) end in a **clear refusal with a reason**, not "proposal missing" |

Report results labelled *real model* with model, settings and date; keep failures.

## Skills before code (owner decision 2026-11-18)

Two different things, both needed:

| | Agent skill (new in P2-K) | Operation / function (code) |
|---|---|---|
| What | Instruction file the model reads: when to use, steps, which operations, report template, pitfalls | Program the software runs: readers, statistics, checks, policy, new abilities |
| For | **Know-how and judgement** — analysis method, question choice, report style, stance-extraction method | **Facts, guarantees, new abilities, speed** — Data Card facts, freshness, suppression, refusals, egress, CAD reading, maps, recipe reuse |
| Trust | Guidance only; can be ignored or misread; never grants authority | Enforced every time |

Note on names: the existing `skills/<id>/` packages are **operations** (executable,
registered, sandboxed). Agent skills are a separate kind of file; do not mix them.

Rule for every new behaviour: **add know-how as an agent skill first. Write code only
when the need is (a) a new ability the model cannot have, (b) a guarantee, or (c)
speed/reliability that the benchmark shows a skill alone cannot reach.** The
benchmark decides: if a skill makes the task pass, no code is added.

P2-K design:
- Location `agent-skills/<id>/SKILL.md` with a header: `id`, `description` (one line,
  used for selection), `when_to_use`, `operations` (registered operation ids only),
  `data_classes`, `version`; body: steps, checks, report template, pitfalls.
- D3 selects only the few relevant skills per request (description match +
  Data Card), so the small model is not flooded; selection is recorded in evidence.
- Deterministic loader validation: header schema, size limit, referenced operations
  exist in the registry. A skill cannot add tools, permissions or data classes.
- Repository skills are reviewed like code. User-added skills are untrusted proposals
  until the owner approves them.
- First skills: `health-table-analysis` (diabetes method: patient grain, missing
  tokens, sensible questions), `plain-language-report`, `vector-to-postgis`,
  `csv-to-postgres`, `refuse-clearly` (how to explain a refusal).
- Measure each skill with the benchmark (before/after, same model and settings).

## Order

P2-0 → D2 → D3 + P2-K → M3 → H (+ S) → H2; E2 when the converter is chosen (DXF can
start earlier). Agents follow [PHASE_1_PLAN.md section 6](PHASE_1_PLAN.md#6-how-ai-agents-work-in-phase-1)
for working rules; owner instruction: commit locally on the task branch, do not push.

Keep this first slice bounded. A Data Card is a projection of facts already collected
by trusted readers: source/hash/selection, byte/row/field counts, observed types,
candidate analytical roles and recorded quality summaries. It contains no preview
rows, category examples or inferred clinical definitions. Counts describe their
recorded population; missing results are not zero. Full-file hashing does not prove
statistical suitability or current freshness after a file changes.

D1 may supply same-turn preliminary cards from the existing opt-in discovery path,
and label recorded cards as historical. It does not introduce an automatic read on
every Send, an enduring card cache, cross-chat retrieval or a new execution route.
D2 owns freshness/reuse scheduling; an identity-matching helper alone is not a cache.
Existing gateway classification remains conservative; naming a payload Data Card
does not lower the classification of the surrounding conversation or raw schema.

```text
Existing explicit discovery / inspection
              |
L2 evidence projection -> L0 Data Card contract
              |
Planner context / CLI / MCP / result Overview
              |
Existing proposal -> policy / authorization -> Executor -> evidence -> Critic
```

Planner proposes goals and operations; services collect facts and enforce contracts;
Executor performs governed operations; Critic assesses evidence. No new role,
container, executable package adapter or permission is required for D1. Preserve
the existing registry, source readers, worker limits and transport parity.

Verify projection boundaries, selected-table identity, unknowns, payload limits and
source mismatch refusal with temporary fixtures. Run the full offline suite and
relevant interface/browser checks. Real-model observations use synthetic inputs,
fixed bounds and retained failures; never send owner health data to a provider or
touch PostgreSQL/PostGIS without explicit permission. Do not repeat the full B6
matrix for a small slice; retain a bounded before/after observation with honest
source/settings differences. Owner chooses Git integration and later publication.
