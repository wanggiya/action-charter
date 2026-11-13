# Phase 1 plan — baseline benchmark and model providers

Recorded 2026-11-12; closeout updated 2026-11-13. **Plan for contributors (humans and AI agents); not implemented.**
Read [AGENTS.md](../../AGENTS.md) and [WORKING_METHOD.md](WORKING_METHOD.md) first. This
file says *what* to build in Phase 1, *where* the code goes, *in which order*, and *how*
agents work on it.

## 0. Before Phase 1: close Phase 0

State on 2026-11-13: R-series merged (PR #82), with owner-reported overall
acceptance. Owner workspace cutover and stable project adoption are complete.
[Closeout evidence and acceptance](../P0_CLOSEOUT.md), tracked by #84:

| ID | Task | Who | Result / final gate |
|---|---|---|---|
| P0-C1 | Runtime-marker removal and canonical example paths | Owner | Done: PR #83 merged as 20b7a38; read-only verification now reports source-only/no legacy entries. Seven empty old folders removed; no saved records deleted. |
| P0-C2 | Resilient display inventories; a rejected stored recipe must not break the list | Agent | Implemented/automatically verified: valid records plus bounded non-actionable findings; no stored-file changes; strict approval/execution retained. Owner acceptance/merge pending. |
| P0-C3 | Close delivered issues #60–#64 | Owner delegated to agent | Done: PR #65 delivery verified; #60 already closed, #61–#64 closed as completed. |
| P0-C4 | Reconcile current status, roadmap, working-method Status and handoff; preserve history | Agent, with P0-C2 | Documentation complete; consolidation exit checks passed. Owner acceptance/merge pending. |

Phase 0 consolidation is recorded Done in the working-method Status column; its
closeout changes still require the owner's Git integration. Phase 1 starts **after
P0-C1 and P0-C2/C4 are accepted and merged**, not automatically during this task.
PA1 source capture and PA2 gold-set labelling remain owner data-only work in parallel;
no policy corpus or analysis capability is claimed as delivered by consolidation.

## 1. Goal and exit criterion

Goal: **measure before improving**, and make the model source configurable and safe.

Phase 1 is done when all hold:
1. One command runs a suite of **20–30 realistic tasks** and writes a result report.
2. A **baseline** is recorded with the real local model (qwen3.5:9b via Ollama),
   labelled *real model*, plus a fixture run labelled *fixture*.
3. **Provider profiles and credentials (M1)** work: local Ollama, a second
   OpenAI-compatible endpoint, and a local LiteLLM proxy with a key.
4. **Egress gate (M2)** passes: a request above a profile's `data_allowed` class is
   refused and the (fake) server receives **zero requests**; no key appears in any log,
   evidence or export.
5. The benchmark runs per provider profile and the comparison is recorded.
6. Full `make test`, strict layer check and compatibility check pass.

Out of scope (later phases — do not build now): Data Card, per-role routing (M3),
efficiency work, hero journey, run workspaces, agent modes, new processing
capabilities (CAD import, document corpus, grid ingest), cloud models with real data
(deferred by owner decision until both editions exist), UI redesign.

## 2. Structure — where the code goes

Layer rule (from [IMPORT_LAYERS.md](../IMPORT_LAYERS.md)): a module may import only
its own layer or lower. `scripts/check_import_layers.py --strict` must stay clean. A
**new top-level package needs an explicit entry** in
`tests/architecture/import_layers_policy.json`. Do not put new code in the retained
compatibility package roots listed by `scripts/check_compatibility.py`.

| Layer | Phase 1 additions | Location |
|---|---|---|
| L0 contracts | Benchmark task spec, result record, metric names; provider profile schema; egress class enum and context-part tags | `contracts/benchmark.py`, `contracts/model_providers.py` |
| L1 platform | Provider interface + `openai_compatible` provider; profile loading; credential references; egress gate; per-call audit fields | `platform/model_gateway/` (`providers/`, `profiles.py`, `credentials.py`, `egress.py`); settings via `platform/configuration.py` |
| L1 core | Nothing new expected; deterministic scorers reuse `core/verification` where possible | `core/verification/` |
| L4 agents | **No new agents, no permission changes.** Only: model calls go through the gateway with a profile id | `agents/roles/*` (call sites only) |
| L5 task actions | Settings actions to list/select/test profiles (no secrets returned) | `task_actions/` |
| L6 apps | Benchmark runner and report; CLI command; HTTP settings endpoints; Settings UI for profiles | `apps/benchmark/` (new, classify as L6), `apps/cli/`, `apps/http/routers/settings.py`, `interface/src/` Settings workspace |

Files outside `src/`:

| What | Where | In git? |
|---|---|---|
| Task definitions + small **synthetic** inputs + expected outputs | `benchmarks/tasks/<task-id>/` (`task.yaml`, `input/`, `expected/`) | Yes |
| Tasks using real local data (diabetes CSV etc.) | `task.yaml` references `data/input/...`; marked `requires_local_data: true`; skipped with a clear message if absent | Definition yes, data **no** |
| Raw run output | Workspace state `benchmark-runs/<run-id>/` | No |
| Summarised results | `benchmarks/results/<date>-<profile>-<model>.json` + `.md` | Yes (no data values, no secrets) |
| Provider profiles | Workspace configuration `model-providers.yaml` (outside the repo); example in `examples/model-providers.example.yaml` | Example only |
| Credentials | Environment variable or `.secrets/` file **referenced by name**; never in profile, logs or evidence | No |

## 3. Benchmark design

### Task format (`benchmarks/tasks/<id>/task.yaml`; values below are illustrative)

```yaml
id: h-csv-profile-001
workload: H            # H health, E engineering, PA policy, G grid, S safety
title: Profile diabetes encounter table and report missingness
request: "Inspect data/input/diabetic_data.csv and report missing values per column."
inputs: [data/input/diabetic_data.csv]
requires_local_data: true
data_class: raw        # highest egress class the task needs
expected:
  kind: deterministic  # deterministic | gold_set | refusal | unsupported
  checks:              # each check is code, never model judgement
    - type: report_contains_columns
      columns: [race, weight, payer_code]
    - type: value_close
      field: missing.weight
      expected: 0.9686
      tolerance: 0.001
limits: { wall_clock_s: 600, model_calls: 20 }
```

### Suite v1 (20–30 tasks)

| Group | Count | Examples | Expected kind |
|---|---|---|---|
| H health | 6–8 | Profile/missingness, codebook decoding, grouping, correlation/OLS (existing diabetes pipeline), synthetic patient table, county join with a small synthetic PLACES-style file | deterministic |
| E engineering | 5–7 | GeoJSON/SHP inspect, vector → GeoPackage, load vector to a **disposable** PostGIS, CSV → PostgreSQL create-only load + round trip | deterministic |
| S safety / governance | 5–6 | Prompt injection inside a CSV cell; request to write without approval; path outside allowed roots; wrong operation for format (`inspect_vector` on CSV); request for unsupported arbitrary shell | refusal (must refuse, nothing executed) |
| PA policy | 2–3 | Stance extraction on gold-set statements (PA2) | `unsupported` now — records the baseline gap; scored in Phase 4 |
| E2 / G | 1–2 | DXF import; one-day grid sample file | `unsupported` now |

Rules: synthetic inputs where possible; tasks needing real data are skipped cleanly
when data is absent; no network access during a run except the model endpoint; no
live (non-disposable) databases.

### Metrics per task and run

Correctness (checks passed), refusal correctness, status, model calls, prompt and
completion tokens (when reported), wall time, process CPU, peak memory, retries,
timeouts, approvals required, provider profile id, model name, egress class used,
code version (git SHA). Reuse `platform/model_gateway/telemetry.py` (content-free).

### Commands (target)

```bash
geoagent benchmark list
geoagent benchmark run --suite v1 --profile local-ollama          # real model
geoagent benchmark run --suite v1 --fixture                        # fake model, CI
geoagent benchmark compare benchmarks/results/A.json benchmarks/results/B.json
```

The fixture mode runs in `make test` (fast subset); real-model runs are manual and
labelled `real model` in results.

## 4. Model providers (M1, M2)

Details: [MODEL_PROVIDERS_PLAN.md](MODEL_PROVIDERS_PLAN.md). Phase 1 specifics:
- **M1:** profile file (`id, kind, base_url, api, credential_ref, location,
  data_allowed, models, capabilities, limits`); `Authorization` header from the
  credential reference; model listing via `/v1/models` with optional Ollama native
  listing; capability detection (json_schema → json_object → text). Existing
  `MODEL_BASE_URL`/`MODEL_NAME` keep working as an implicit `local` profile.
- **M2:** tag context parts by egress class (`none`, `metadata`, `data_card`,
  `aggregates`, `raw`); the gateway refuses before the network call if the request
  exceeds the profile's `data_allowed`; record the highest class per call. Until M2
  passes, non-local profiles are limited to `none`.
- **Cloud models:** owner decision 2026-11-06 defers cloud models for project data.
  In Phase 1 test non-local profiles only with synthetic data, a second local host, or
  a local LiteLLM proxy.
- First secret source: environment variables and `.secrets/` files only (keyring/Vault later).

## 5. Task list

| ID | Task | Depends on | Lane |
|---|---|---|---|
| P1-B1 | Benchmark contracts (L0) and task-file loader with validation | P0-C2 | A |
| P1-B2 | Runner + result recorder + fixture mode; `geoagent benchmark` CLI | B1 | A |
| P1-B3 | Deterministic check types (columns, values with tolerance, file/table exists, row counts, refusal + nothing executed) | B1 | A |
| P1-B4 | Suite v1 task definitions and synthetic inputs (sections 3) | B2, B3 | A |
| P1-B5 | Baseline: fixture run in CI subset; real qwen3.5:9b run recorded in `benchmarks/results/` | B4 | A |
| P1-M1 | Provider interface, profiles, credentials, model listing, capability detection, Settings UI | P0-C2 | B |
| P1-M2 | Egress classes, context tagging, gate, audit fields, leak scan test | M1 | B |
| P1-M3c | Real-provider checks: Ollama, second endpoint, local LiteLLM proxy with key, blocked-network run | M2 | B |
| P1-B6 | Benchmark per profile + comparison report | B5, M1 | A+B |
| P1-X | Phase 1 closeout: update phase table, `CURRENT_STATUS.md`, evidence links | all | — |
| Owner | PA1 capture election sources (data only); PA2 label 50–100 gold statements | — | — |

Lanes A and B can run **in parallel** (different agents, different worktrees). They
meet at B6. Each row is one GitHub issue, one branch, one PR.

## 6. How AI agents work in Phase 1

### Coding agents (working on this repository)

1. **Start:** read AGENTS.md → this file → `context/WORK_RESUME.md` top entry.
   Check `gh issue list`, `gh pr list`, `git worktree list`; do not take a claimed task.
2. **Claim:** one issue per task ID, e.g. `P1-B2: benchmark runner and fixture mode`.
3. **Isolate:** one worktree and branch per task, from up-to-date `main`:
   ```bash
   git fetch origin && git worktree add ../ac-p1-b2 -b feat/p1-b2-benchmark-runner origin/main
   ```
   Two agents never share one working folder.
4. **Commit policy:** per AGENTS.md, no commit/push unless the owner asks. Recommended
   owner instruction for Phase 1: *"commit locally on your task branch; do not push or
   merge"*. The owner pushes, opens the PR and merges.
5. **While working:** stay in scope; no Phase 2+ features; keep the layer check strict;
   no new top-level package without a policy entry; never weaken a safety check.
6. **Done means:** tests for the change; `make test`; strict layer + compatibility
   checks; `make interface-validate` if the UI changed; docs updated (the feature doc
   and Status column only — progress notes go to `context/WORK_RESUME.md`);
   evidence labelled *fixture* or *real model* (model, date, timing).
7. **Hand-off:** a new top entry in `context/WORK_RESUME.md`: what changed, checks run
   with numbers, what is left, exact next command. PR description ends with
   `Closes #<issue>`.
8. **Never:** touch live databases, read or print secrets, move owner workspace data,
   push, merge, or create checkpoint files.

### Product agents (inside ActionCharter)

Current roles: `planner`, `critic`, `executor` (deterministic), `method_memory`,
`builder`; manifests in `agents/<role>/manifest.yaml` (`model_ref`, permissions,
instructions); code in `src/geoagent_harness/agents/roles/` and `agents/runtime/`.

Phase 1 rules for them:
- **No new roles and no permission changes.** The benchmark measures the existing
  roles as they are.
- Every model call goes through `platform/model_gateway` with a provider profile
  id, so the benchmark can attribute calls, tokens and time **per role**.
- `model_ref` (today `shared_ollama_runtime`) resolves to the active provider profile.
  Per-role profiles are M3 (Phase 2) — do not add them now.
- Agents remain workers, not authenticated principals (R12: local actor is `owner`).
  The agent identity registry is Phase 4/7; the experimental model approver is
  Phase 7 (shadow) / 8 — see [SERVER_AUTONOMY_DESIGN.md](SERVER_AUTONOMY_DESIGN.md).
- Safety tasks in the suite (group S) check the core principle: injected text in
  data or model output never causes execution.

## 7. Verification commands

```bash
make test
.venv/bin/python scripts/check_import_layers.py --strict
.venv/bin/python scripts/check_compatibility.py
make interface-validate                 # if interface/ changed
geoagent benchmark run --suite v1 --fixture   # after P1-B2
```

## 8. Risks

| Risk | Mitigation |
|---|---|
| Real-model runs are slow (40–120 s per planning call) | Keep suite at 20–30 tasks; per-task limits; run overnight; record timeouts as results, not failures to hide |
| Benchmark tuned to pass | Expected outputs written before running; checks are code; failures are kept in results |
| Secrets leak through new logging | M2 leak-scan test is mandatory |
| Scope creep into Phase 2 | Feature freeze for new capabilities; Data Card/routing are Phase 2 |
| Parallel agents conflict | Separate worktrees; lane A and B touch different packages; shared files (CLI registry, settings router) changed in small PRs |
