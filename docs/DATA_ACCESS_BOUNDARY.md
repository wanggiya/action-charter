# Shared data access and neutral contracts

R4, [issue #69](https://github.com/wanggiya/action-charter/issues/69), 2026-11-06.
This consolidates existing readers and contracts. Existing launcher options, interface,
CLI commands, operation names, saved records and authorization requirements remain.
Users need no new setting, dependency or storage migration.

## Responsibilities

```text
Frontend / CLI / MCP
         |
    task actions -- eligibility, revisions, exact authority, saved-run scope
         |
    sandbox.inspection <--- discovery / dataset services
         |
    fixed inspection worker -- unchanged resource limits and safe readers
         |
      source data
```

| Owner | Responsibility |
|---|---|
| `sandbox/inspection.py` | Existing bounded read, fixed worker launch, closed inspector limits, source-to-inspector and probe mapping |
| `sandbox/inspection_worker.py` | Existing fixed read actions and resource limits; no generated-code entry point |
| `sandbox/spatial_snapshot.py` | Finite spatial packages, no-follow source reads, sidecar checks and exact content digests |
| `sandbox/spatial_rendering.py` | Existing typed display options and finite vector/raster/pixel rendering |
| `task_actions/inspection_policy.py` | Inspection-on-send eligibility, contract digest, current-chat/plan dispatch checks and internal execution contexts |
| `task_actions/spatial_views.py` | Recorded-run/chat/plan/source binding, completed-step selection and one concurrent view slot |
| `contracts/actions.py` | Unchanged typed immutable-artifact request definitions, with no approval/execution implementation |
| `contracts/table_sources.py`, `contracts/inspection_formats.py` | Unchanged format/batch contracts and inspector/source compatibility checks |
| `contracts/errors.py` | R3's same shared exception identity; no replacement error hierarchy |
| `contracts/context_redaction.py` | Existing context-redaction profile, independent of context-pack construction |
| `platform/project.py`, `platform/outcomes.py` | Existing trusted-root validation and redacted byte-bounded outcome projection |

The sandbox modules no longer need task-action readers/worker/rendering implementations.
Eligibility and authority remain above data access. A registered format, source mapping,
successful read or model message does not approve a workflow. Task actions still check
the exact proposal, revision, operation contract, source binding and human decision.

## Preserved technical boundaries

- The reader uses the same Linux subprocess, fixed first-party code, isolated Python
  startup, narrow environment, resource/deadline/output bounds and cancellation cleanup.
  Progress callbacks and source-change checks remain. This move does not add Docker,
  a MicroVM, a fresh container boundary or an arbitrary-code execution surface.
- CSV discovery/profile/display budgets and spatial package/layer/field/band/cell limits
  are unchanged. Full-file calculations and bounded previews retain their existing scopes.
- `active_inspection` and `planning_discovery` stay in the same policy module. Legacy
  HTTP imports alias that module, preserving context identity. Reader functions/limits
  are re-exported there; its existing subprocess test hooks still use the same standard
  library objects. The spatial view semaphore stays in the task-action service.
- Legacy worker/snapshot, action-request, format and context-redaction modules alias
  their new owners. Classes/functions retain identity across compatibility paths.
  Native import statements use the owners; generated/stored source strings are intact.
- The context and generic result redactors have different existing rules. They remain
  separate, and every caller keeps its previous profile. This is an ownership change,
  not a change to redaction coverage. Result projection still redacts before measuring
  UTF-8 bytes, with the existing 16,384-byte / 128,000-byte analysis limits.
- Action schemas, plan/request bytes, canonical hashes, exception messages/causes and
  API status mapping remain. No database/table/record format or saved authority changes.

## Validation and remaining work

The layer baseline shrinks **65 -> 53 pairs / 68 -> 55 occurrences**. All 12 directly
assigned R4 pairs disappeared; no new/increased upward import or classification change
was accepted. The graph has 434 modules, 35 visible compatibility aliases and the same
single reviewed dynamic import. Strict mode still rejects remaining debt.

Three mixed R4/R6 dependencies concern operational-history observers and Critic/Executor
evidence types. They remain recorded for R6's ownership review; this task does not move
role behavior into core history. Remaining action/orchestration work is R5; specialized
ledger/concurrency contracts are P0-5b. Real workspace cutover and server seams remain
separate. See the [combined inventory](product-direction/RESTRUCTURE_PLAN.md#current-p0r-gap-inventory--2026-11-05).

Verified: **73 focused cases (5.21 s)**, including 26 new boundary cases and
existing layer/storage/redaction cases; **64 existing integration cases (24.97 s)**,
with five expected spatial warnings. They cover default/relocated workspaces, safe
paths, unchanged/different source digests, import/exception/context identity, schema
rejection, redaction profiles, byte bounds and existing discovery/spatial/table/intent
handoff. Unchanged DTO/table/redaction source and worker/snapshot import-only moves
were independently compared with the pre-R4 source.

Frontend validation passed (4.64 s build, existing bundle-size warning). The isolated
relocated-state browser/API/CLI/PTY journey passed with zero page errors, including
statistics, JSON/XLSX/PDF outcomes, history and one exact temporary-write authorization.
Full `make test`: **2,581 passed**, 13 existing spatial warnings, **735.04 s (12:15)**.
Normal layer check and 446 local links (152 Markdown fragments) pass; the active roadmap
remains below 64 KB. Strict mode correctly rejects remaining debt. Automated journeys
use fixture models and temporary data, not live-model/database acceptance. Owner manual validation is deferred
to the combined pass; issue #69 remains open for owner review.

For that combined manual pass, restart the usual launcher with its existing options.
Send `Run a new read-only inspection of sample_orders.csv.` With Inspection on send
OFF, click Execute once; with it ON, the supported metadata request can inspect on send.
Check Outcome, refresh and reopen the same chat/run. The saved result must remain.
In `./actioncharter`, `/chats`, `/open CHAT_ID`, `/history` and `/run RUN_ID` must reopen
the same evidence. Reopening must not repeat execution. Broader analytical requests
retain reviewed Execute; writes retain write policy and exact authorization.
