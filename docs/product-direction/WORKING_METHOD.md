# Working method and delivery plan

Recorded 2026-11-02. This replaces the numbered-checkpoint workflow for new work.
It applies to every contributor, human or AI agent. Read the
[product direction README](README.md) first; this file says **how** we get there and
**in what order**.

## Why the checkpoint system is retired

Checkpoints (CP16 → CP29, about 116 files in `docs/development/checkpoints/`) delivered
strong governance, but a checkpoint could be "accepted" while the questions that matter
stayed open: real local-model reliability, speed, non-expert usability and whether
learning helps. Scope also kept widening (CP17 alone had 51 sub-checkpoints).

| | Old: checkpoints | New: phases + benchmark |
|---|---|---|
| Unit of progress | Numbered checkpoint | Phase with one measurable exit criterion |
| Definition of done | Tests pass + acceptance doc | Exit criterion met; benchmark result where applicable |
| Evidence | Mostly fixture/fake-model tests | Benchmark suite on the real local model |
| Scope | Additive features | Feature freeze + one hero journey |
| Docs | Diary-style logs | One living status page, guides, short decision notes |
| Work tracking | Checkpoint plan docs | GitHub issues + small PRs |

Existing checkpoint files stay as history. **Do not create new `CHECKPOINT*.md` files.**

## Delivery steps (in order)

Do not start a step before the previous one meets its exit criterion, unless the owner
says otherwise. Update the **Status** column when a step changes state.

Workloads and editions: [showcase workloads decision](../decisions/2026-11-06-showcase-workloads-and-editions.md) (2026-11-06).
Order set by the [own-platform decision](../decisions/2026-11-02-own-platform-direction.md) (2026-11-02)
and the [model-provider decision](../decisions/2026-11-03-model-providers.md) (2026-11-03).
Progress notes do not belong in this file: put them in `context/WORK_RESUME.md`, and
only change the Status columns here.

| Phase | Goal | Exit criterion | Status |
|---|---|---|---|
| 0 | Consolidate (no new features): Phase 0 tasks below + [restructure steps R1–R11](RESTRUCTURE_PLAN.md) | Full `make test` passes; repo root contains source only; layer check has no violations. PA1: capture election sources now (data only, see [workloads](SHOWCASE_WORKLOADS.md)). | In progress |
| 1 | Baseline benchmark + model providers ([M1–M2](MODEL_PROVIDERS_PLAN.md)) | Provider profiles, credentials and the data-egress gate pass their tests; 20–30 realistic tasks on synthetic sensitive-style data, one command, real local model; measures correctness **and** efficiency (model calls, tokens, time, resources); baseline recorded. Tasks drawn from the [showcase workloads](SHOWCASE_WORKLOADS.md) H, E1/E3, PA gold set, G1. | Not started |
| 2 | Data Card + efficiency (incl. per-role model routing, M3); hero journey | Data Card shown to agents and users before work; deterministic routing/recipe reuse; hero journey (CSV/Excel → profile/clean → 3–5 plain-language questions → readable report) meets owner-agreed targets; fewer calls and less time at equal or better correctness. Hero journey = health workload H (diabetes + county map); CAD (DXF/DWG) import E2. | Not started |
| 3 | Run workspaces | Per-run process/outcome areas with snapshots; promotion only by verification; governed read access for other agents; sandbox boundary tests pass. **Decide first:** fresh sandbox per job (current plan) vs long-lived MicroVM workspace per agent; Docker on laptops, MicroVM on Linux servers with KVM (not available on macOS; needs nested virtualization on WSL2); measure memory per sandbox against the laptop budget. Document corpus and governed web fetch for PA. | Not started |
| 4 | Agent modes | Single-agent default and multi-agent mode on one runtime; multi mode enabled by default only where the benchmark shows it helps. PA policy-analysis demo is the multi-agent showcase. | Not started |
| 5 | Frontend redesign + Linux Personal package | Guided and Studio modes; non-expert installs and finishes the hero journey without help. Personal edition runs H, E, PA, G1–G2. | Not started |
| 6 | Interop (incl. other model API styles, M4) | External agents (Claude Code, Codex, …) use our governed tools via MCP; optional external models via the gateway; one benchmark task completed this way | Not started |
| 7 | Server profile (incl. shared model gateway, M5) | Headless runs, queue, scheduler, PostgreSQL, login; a scheduled job runs unattended for a week. Platform edition; grid ingest G3 is the unattended-week job. | Not started |
| 8 | Autonomy and evolution | Policy autonomy levels L0–L4; recipe learning promoted only after beating the benchmark; rollback tested. Grid monitoring G4–G5 is the first registered automation. | Not started |

2026-11-02 compatibility fix alongside P0-2: execution versus standalone Critic-review
labels/statuses and explicit review budget verified: 2,275 backend tests, interface
validation and isolated fixture browser/API/CLI/PTY passed. See
[diagnostics](../REQUEST_DIAGNOSTICS.md#execution-and-outcome-review-distinction-2026-11-02).
This does not complete P0-2 or add a processing capability.

Inspection wording follow-up: normalize the user's explicit read-only metadata lead-in
across existing parser/source checks; keep complete-request matching and send policy.
Verified: 2,287 backend tests, interface validation and isolated fixture browser/API/CLI/PTY
passed, including the exact user wording. No new processing operation or checkpoint.

Inspection-source bug fix: bounded follow-ups resolve active inputs or ask a question;
shared format guards cover plan/edit/recipe/runtime boundaries. Decoder focus preserves
capability metadata. [Evidence](../INSPECTION_SOURCE_COMPATIBILITY.md): 2,317 tests,
interface validation and relocated fixture browser/API/CLI/PTY passed. No new processing capability, agent or checkpoint.

### Step 1 tasks (Phase 0)

2026-11-03 bug fix: complete inspection clarification response diagnostics, including
read-only compatibility for older chat/receipt responses; shared equivalent read-only
wording. No new capability or phase. Verified: 2,327 tests (621.88 s), interface
validation and isolated fixture browser/API/CLI/PTY passed. See
[inspection guide](../INSPECTION_SOURCE_COMPATIBILITY.md).

Each task is one branch and one PR. Tasks marked "after" depend on another task.

| ID | Task | What it achieves | Status |
|---|---|---|---|
| P0 bug #81 | Complete recorded inspection quality reports | Existing inspection/report contract coverage | Implemented/automatically verified: 2,816 full-suite tests (785.18 s), final 10 report checks, frontend/strict gates and isolated browser/API/CLI/PTY passed. Owner real-file report acceptance pending. [Scope and validation](../INSPECTION_QUALITY_REPORTS.md); no historical rewrite, inference or authority change. |
| P0-1 | Move checkpoint docs to `docs/development/checkpoints/`; group `postgis_*`/`geoserver_*` under subpackages | Readable docs tree | Done (PR #59) |
| P0-2 | Move runtime folders (`builder-*`, `recipe-runs`, `traces`, `plans`, `approvals`, …) under one workspace root, configurable by setting | Repo holds only source; prerequisite for packaging and Windows | Done: [workspace and offline cutover](../WORKSPACE_STORAGE.md); 2,388 tests (666.49 s), frontend/Compose validation and relocated fixture browser journey passed; source-only exit proved on a disposable migrated project. Owner checkout remains unmigrated. |
| P0-3 | Merge the PostGIS promotion/rollback packages into one plan → approve → execute → verify → rollback lifecycle | Reusable pattern for L3 production writes | Done: [issue #60](https://github.com/wanggiya/action-charter/issues/60), [shared lifecycle](../POSTGIS_LIFECYCLE.md); 2,419 tests (672.35 s), 193 focused checks, frontend/Compose and relocated fixture browser journey passed. Live acceptance remains owner-controlled. |
| P0-4 | Shared task-actions layer used by `interface_api`, CLI, chat and MCP | One code path; Guided/Studio/Admin/REST become thin adapters | Done: [issue #61](https://github.com/wanggiya/action-charter/issues/61), [shared actions](../TASK_ACTIONS.md); 2,447 tests (688.52 s), frontend validation and relocated fixture browser/API/CLI/PTY passed. Import-boundary and compatibility checks pass; no live DB/model acceptance. |
| P0-5 | Storage repository interface (SQLite implementation now) — after P0-2 | Editions differ by config, not code | Done: [issue #62](https://github.com/wanggiya/action-charter/issues/62), [repository contracts](../STORAGE_REPOSITORIES.md); 2,480 tests (732.26 s), frontend validation and relocated fixture browser/API/CLI/PTY passed. Local adapters only; specialized authority/evidence/ranking stores remain separate. |
| P0-6 | Split `interface/src/App.tsx` by workspace (Planner / Graph / Results / Settings) with a state store | Room to add Guided mode | Done: [issue #63](https://github.com/wanggiya/action-charter/issues/63), [implementation](../FRONTEND_WORKSPACES.md); composition shell, workspace controllers/views and provider-scoped store. 2,483 tests passed (938.96 s), frontend validation and four isolated fixture browser journeys passed with zero page errors. |
| P0-7 | Trim/archive `context/PRODUCT_ROADMAP.md` below the 128 KB context-load limit | Planner context keeps loading | Done: [issue #64](https://github.com/wanggiya/action-charter/issues/64); active roadmap below 15 KB, complete linked snapshot with original-byte/hash verification; 545 local links/151 fragments and 12 context checks passed. Full make test: 2,483 passed (682.93 s, 13 existing spatial warnings). Context-pack builder does not currently include the roadmap; no runtime loading change. |
| P0-2b | Workspace follow-up: ownership by **project ID** instead of source-checkout path (servers run installed code with many projects); one layout configuration object replacing the scattered `GEOAGENT_*_ROOT` variables (with R2); migrate the owner's real checkout with the offline migration tool after a backup | Server-ready workspace identity; Phase 0 exit met on the real checkout | Configuration complete with R2. [#79 local stable identity](../PROJECT_IDENTITY.md) implementation/automated gates complete: 2,796 tests (816.47 s; 13 existing spatial warnings), frontend/strict checks and both legacy/stable-ID fixture browser/API/CLI/terminal journeys passed. [Owner cutover preparation ready](../OWNER_WORKSPACE_CUTOVER_PLAN.md): 26.46 MiB runtime, six blocking development links, read-only checks and synthetic preservation/cutover/rollback rehearsal complete. Real backup/cutover pending explicit approval; cross-filesystem source/container mapping provisioning remains future work. No real records moved. |
| P0-5b | Storage follow-up: bring the stores still outside the contracts behind them — approval/authority records, evidence, lifecycle records, write-policy ownership (`write_policy.py`), recipe ranking (`recipe_catalog/successful.py`) — as an **append-only ledger contract** where applicable; add a **concurrency contract** (transactions/row locks, idempotency) that a PostgreSQL implementation must meet | Complete interface, so the server profile is a new implementation, not a redesign | Implementation/automated checks complete: [issue #77](https://github.com/wanggiya/action-charter/issues/77), [specialized contracts](../LEDGER_CONTRACTS.md); 2,736 tests (750.12 s; 13 existing spatial warnings), frontend/strict gate and isolated fixture browser/API/CLI/terminal pass. Host-local leases only; no remote backend. Owner manual acceptance deferred until all R-series work is complete; Git review pending. |
| R-series | Remaining [restructure steps](RESTRUCTURE_PLAN.md): **R1 first** (real layer test), R2 (one platform configuration), R5 completion (CLI through task actions), R7 (`cli.py`), R6 moves, **R12 server seams** | Clean layers; server seams in place | R1–R8 implemented/automatically verified (#66–#76); [R9/R10 reconciled](../LEDGER_CONTRACTS.md#r9-and-r10-reconciliation) against delivered P0-3/P0-6. P0-5b #77 implementation/automated checks complete; R12 [#78 complete](../EXECUTION_CONTEXT.md) for implementation/automated gates: 2,771 tests (793.66 s; 13 existing spatial warnings), frontend/strict gate and final fixture browser/API/CLI/terminal pass; all 27 MCP schemas and existing container permissions preserved; R11 [#80 implementation/automated gates complete](../R11_COMPATIBILITY.md): 290 obsolete adapters retired, 117 explicit public/schema/SDK boundaries retained; historical literal zero-shim target not claimed. 2,808 tests (859.92 s; 13 existing warnings), frontend/source checks and stable-ID fixture browser/API/CLI/terminal passed. [Owner acceptance record](../R_SERIES_ACCEPTANCE.md#acceptance-record): startup/read-only/refresh recovery passed; only Execution History and terminal continuity pending. Fresh-file writing optional, not manually tested. P0-2b local identity #79 automatically verified; real owner cutover remains separate. R-series automated work complete with the documented supported boundary; no new R-series code planned unless a demonstrated regression requires it. Real cutover is separate from R-series manual closure. Git remains owner-controlled. |

Follow [GENERALIZATION_AND_CONSOLIDATION_PLAN.md](../GENERALIZATION_AND_CONSOLIDATION_PLAN.md)
for moves: trace callers first, move one responsibility at a time, keep external
contracts and historical digests compatible.

## Rules for every task

### Before starting
1. Read [AGENTS.md](../../AGENTS.md) and the "Status" columns above.
2. Check for overlapping work: `gh pr list`, `git branch -a`, and open issues. Do not
   start a task another agent has claimed. If tasks touch the same files, coordinate
   through the owner.
3. Claim the task: open or assign a GitHub issue named after the task ID
   (e.g. `P0-2: workspace state root`), or ask the owner to.

### While working
- Branch from up-to-date `main`: `<type>/<task-id>-<short-name>`, e.g.
  `cleanup/p0-2-workspace-root`, `feat/s2-benchmark-suite`.
- Keep the PR small and focused on one task. No unrelated refactors or features.
- **Feature freeze during Step 1:** no new capabilities, operations, agents or UI
  features. Bug fixes are allowed.
- Keep the core principle: models propose; deterministic software authorizes,
  executes, validates and records evidence. (Experimental model approver: only per
  the [design](SERVER_AUTONOMY_DESIGN.md#model-participation-in-authorization), Phase 8.) Never weaken a safety check to make a
  task easier.
- Do not commit, push, touch live databases or edit secrets unless the owner asks.

### Evidence and definition of done
A task is done when:
1. `make test` passes (state the count and duration in the PR).
2. The task's own exit check is shown (e.g. `ls` of the repo root for P0-2).
3. From Step 2 onward: benchmark results before and after, on the real local model,
   for any change that affects planning, execution or results.
4. Evidence is labelled honestly: **fixture/fake-model** vs **real local model**
   (state model name, timing, token counts). Never present fixture results as
   real-model evidence.
5. Docs are updated as below, and the Status column in this file is updated.

### Documentation updates
- `context/CURRENT_STATUS.md`: edit the current overview **in place** so it stays short
  and true. Do not append diary entries.
- `context/WORK_RESUME.md`: a few lines on what is in progress and what is next,
  replacing stale lines rather than stacking new ones on top.
- User-facing change: update the relevant guide and `CHANGELOG.md`.
- Architecture decision: add a short decision note (context, decision, consequences)
  to `docs/decisions/` named `YYYY-MM-DD-<topic>.md` (create the folder with the
  first note).
- Follow [DOCUMENTATION_GUIDE.md](../DOCUMENTATION_GUIDE.md) for where things belong.

### PR description template
```
Task: <ID and name>  (closes #<issue>)
What changed:
Why (link to this plan / decision note):
Evidence:
  make test: <passed/failed count>, <duration>
  Exit check: <command + result>
  Benchmark (Step 2+): <before → after, model, real or fixture>
Not done / limits:
```

## Open decisions for the owner

These block or shape later steps. Record the answer as a decision note when made.
- Accept or change the [editions and interfaces](EDITIONS_AND_INTERFACES.md)
  recommendation (currently "not formally accepted").
- Product identity: repo `geoagent-skill-harness` vs product "ActionCharter";
  GIS as the niche or as one plugin.
- Benchmark success and time targets for Step 3.
- First target market for the pilot (health research or public-sector GIS).
