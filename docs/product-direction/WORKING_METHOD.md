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

| Step | Goal | Exit criterion | Status |
|---|---|---|---|
| 1 | Phase 0: consolidate the codebase (no new features) | Full `make test` passes; repo root contains source only | In progress |
| 2 | Benchmark suite | 20–30 realistic tasks on synthetic sensitive-style data, runnable with one command against the real local model, baseline recorded | Not started |
| 3 | Hero journey reliable and fast | CSV/Excel → profile/clean → 3–5 plain-language questions → readable report; benchmark success and time targets agreed with owner and met | Not started |
| 4 | Prove one learning loop | Case-based recipe reuse makes a repeated benchmark task measurably faster or more accurate | Not started |
| 5 | Guided mode + Linux Personal package | Non-expert can install and finish the hero journey; tested with real users | Not started |
| 6+ | Server platform Phases 1–5 | See [AUTONOMOUS_PLATFORM_DESIGN.md](AUTONOMOUS_PLATFORM_DESIGN.md#migration-phases) | Not started |

### Step 1 tasks (Phase 0)

Each task is one branch and one PR. Tasks marked "after" depend on another task.

| ID | Task | What it achieves | Status |
|---|---|---|---|
| P0-1 | Move checkpoint docs to `docs/development/checkpoints/`; group `postgis_*`/`geoserver_*` under subpackages | Readable docs tree | Done (PR #59) |
| P0-2 | Move runtime folders (`builder-*`, `recipe-runs`, `traces`, `plans`, `approvals`, …) under one workspace root, configurable by setting | Repo holds only source; prerequisite for packaging and Windows | Not started |
| P0-3 | Merge the PostGIS promotion/rollback packages into one plan → approve → execute → verify → rollback lifecycle | Reusable pattern for L3 production writes | Not started |
| P0-4 | Shared task-actions layer used by `interface_api`, CLI, chat and MCP | One code path; Guided/Studio/Admin/REST become thin adapters | Not started |
| P0-5 | Storage repository interface (SQLite implementation now) — after P0-2 | Editions differ by config, not code | Not started |
| P0-6 | Split `interface/src/App.tsx` by workspace (Planner / Graph / Results / Settings) with a state store | Room to add Guided mode | Not started |
| P0-7 | Trim/archive `context/PRODUCT_ROADMAP.md` below the 128 KB context-load limit | Planner context keeps loading | Not started |

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
  executes, validates and records evidence. Never weaken a safety check to make a
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
