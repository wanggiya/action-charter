# T01 audit slice: analytical views and existing Builder execution

Inspected 2026-10-27 while fixing grouped titles/chart percentages. This is a concrete
code-path audit, not completion of the entire T01 ownership/compatibility inventory.
No Builder candidate was generated/installed or server/database activated for this audit.

## Two analytical result paths actually exist

```text
Executed CSV inspection
  ResultsWorkspace -> GroupExplorer / useTableAnalysis
  POST workflow/runs, action=table_analysis
  workflow_runs.run_action -> analytical_service.recorded_analysis
  profile_table -> inspection_policy.bounded_read(action=csv_discover)
  returns table-analysis-v1 + source reference
  validates run/chat/plan/step/source and original codebook identity

Analytical conversation/session
  conversation exploration -> tabular.analyst.run_session
  dataset_service.profile_dataset -> sandbox.manager.run_profile [Docker default]
                                   or bounded process [explicit local setting]
  recorded observation contains dataset-profile-v1
  DatasetOutcome -> DatasetViewExplorer
  POST analysis/view -> dataset_views.dataset_view
  binds saved chat revision + profile/source hashes
  profile_dataset -> saves selected view/history; reopening reads saved result

Direct access already shares services
  MCP profile_table -> tools.profile_table -> analytical_service.profile_table
  MCP comprehensive profile -> dataset_service.profile_dataset
  terminal grouped views -> analysis/view API
```

Execution ownership also inspected: terminal `/review` and frontend preparation use
`workflow.prepare_workflow`; exact authorization uses `authorize_workflow`; terminal
and frontend durable start use `workflow_runs.run_action`, which re-prepares and invokes
`execute_workflow` through its worker. Cancel/read use the same durable-run API. MCP has
its own approved-recipe entry (`mcp_server/approved_recipe.py`), not the full frontend
task lifecycle. Do not claim full task-control MCP parity from shared analytical methods.
Full authority/receipt compatibility tracing remains an audit follow-up below.

Relevant files: `interface/src/components/ResultsWorkspace.tsx`, `TableExplorer.tsx`,
`DatasetOutcome.tsx`, `DatasetViewExplorer.tsx`; `src/geoagent_harness/interface_api/
workflow_runs.py`, `server.py`; `tabular/analytical_service.py`, `dataset_service.py`,
`dataset_views.py`, `analyst.py`; `chat/views.py`; `mcp_server/tools.py`, `server.py`.

The two services are not interchangeable by renaming a function: runtime selection,
result schemas, legacy compatibility and storage/source bindings differ. Do not merge
them blindly or weaken source checks. A later source/result adapter must preserve these
contracts while removing only proven duplication. No full DataFrame cache was found in
the inspected `source_reference` path; its reference describes recorded query/evidence.

## First consolidation performed

Both grouping views previously implemented chart percentages/presentation separately.
Ordinary workflow grouping used a generic chart with a `group` category label; analytical
session grouping supplied percentages through another path. Titles were mostly generic
page names rather than explicit recorded selections. This was insufficient feedback when
the user changed fields, even where the existing cross-tab caption used current fields.

`GroupedChart` now supplies shared record counts, overall/within-primary percentages,
denominator facts, pie applicability and rendering. Counts come from recorded groups;
display changes do not dispatch another read/model call. Percent axes use 0–100% rather
than stretching the largest observed percentage to a visually full bar. Display area is
bounded. Titles use applied result fields, not unsent control drafts; changing draft
fields retains the old result/title until an explicit calculation succeeds.

This is a narrow T03 presentation-contract slice. Typed numeric/distinct summaries
remain available; it is not a backend statistical-service rewrite or T05 completion.

Validation: 2,145 backend tests and frontend validation passed. Browser checks verify
applied grouping titles, 25% overall versus 50% within-primary on a known fixture,
0–100% axes, bounded plot dimensions, and unchanged frontend/terminal/history behavior.
The separate real-sample browser verifies every age/gender cell against 5,000 source
rows. Model replies are fixtures; these checks do not exercise new Builder generation.

## Existing Builder lifecycle: actual owners

| Stage | Actual owner inspected | Decision |
| --- | --- | --- |
| Generation | CLI generation entry -> builder.service.propose_builder_candidate -> load builder manifest -> builder.agent.generate_builder_proposal -> shared model | Reuse model boundary, bounded proposal validation and provenance; optional role rather than mandatory permanent fourth agent |
| Materialization | builder.materialization.materialize_builder_proposal | Audit/reuse candidate storage/identity primitives; do not remove current path constraints to permit arbitrary host files |
| Isolated test execution | Makefile builder-candidate-test/-record -> Compose skill-test-runner -> docker/skill-test-runner/run_candidate_tests.py -> pytest with candidate package paths | Existing executor really runs candidate code/tests; retain compatibility and assess resources before task-oriented generated-code reuse |
| Evidence assessment | builder.testing.assess_builder_candidate_tests + test_evidence | Reuse exact candidate/test binding; assessment itself is not execution |
| Promotion/activation | CLI commands -> builder.promotion.promote_builder_candidate / activation.activate_builder_bundle plus plans/reviews | Retain developer workflow. Never automatically call source activation from ordinary analysis chat |
| Post-activation verification | builder.post_activation_verification.verify_builder_activation | Byte/evidence verification, not analytical result validation |

Compose test runner declares network none, read-only root/candidate mount, temporary
scratch, dropped capabilities, no-new-privileges and PID limit. This inspection is not
proof it already meets all requirements for generated analytical jobs: the inspected
service does not declare the analytical worker's same CPU/memory quotas. Its runner
imports candidate code and executes pytest, so static metadata checks are insufficient.

The analytical Docker launcher has fixed selected-file mounts, no network, unprivileged
user, read-only root, CPU/memory/PID/descriptor limits and bounded temporary storage.
It invokes a fixed profile protocol, not arbitrary Python jobs. Reuse its boundary
primitives only after designing/testing a versioned candidate-execution protocol.

## Next audit work, not done by this slice

### T02 exact-scope recovery delivered — 2026-10-27

Found `use-plan-run` was filtering the last 50 globally recent receipts after list
truncation. Correct evidence could disappear when other chats updated many runs.
`workflow_runs` now has a `latest` read action requiring conversation ID plus plan hash;
frontend and terminal `/run` (when no known/explicit run ID exists) use that shared lookup.
The global inventory remains a bounded display list, not the source of truth for recovery.

Metadata scanning is bounded to 10,000 directory entries/three seconds and per-receipt
size limits. Unreadable/over-budget lookup is reported as unavailable, not missing.
Only the chosen scope uses existing interrupted-run reconciliation; unrelated records
are not rewritten. This is not a new persistent index or an arbitrary-scale guarantee.
Future indexed lookup should reuse existing storage infrastructure with explicit legacy
compatibility rather than create another competing source of truth.

The frontend preserves previously loaded matching evidence across a failed refresh,
shows its unavailable status, and polls restored queued/running/cancelling runs as well
as pending assessments. Reads never restart a worker or restore write authorization.
Fixed an additional audited defect: assistance receipts were assigned a tuple dictionary
key, causing JSON persistence failure; the proper named field now persists and caches.

Acceptance includes exact-scope recovery behind 55 unrelated fixture receipts, a pending
status response followed to real completion, a temporary refresh outage with evidence
retained, controlled model timeout/refresh with saved plan and no authority replay,
cross-chat/plan rejection, corrupt/budget failures and cached assistance without new calls.
The pending status/timeout are controlled simulations around real saved backend records;
this is not a claim to reproduce every installed-model or process-disconnection failure.
Existing chat-history global scan bounds and full Builder lifecycle compatibility audit
remain open; this work does not mark all of T01/T02 complete.

Follow-up T02 presentation/state work: `lib/execution-state.ts` now describes the
existing header Execute gates once, reused by the button tooltip/accessible description
and graph status. No backend permission change. `TextPlanner` clears its restoring
wording after publishing the recovered proposal and explicitly distinguishes results.
Browser acceptance refreshes before execution, verifies no run/Outcome was fabricated,
then executes normally; historical views remain blocked with a readable reason.
This validates those cases, not exhaustive timeout/disconnection recovery or all
execution buttons. Existing `use-plan-run` matches chat plus plan before showing evidence.

- Trace complete prepare/authorize/start/cancel/recovery paths across frontend, CLI and
  MCP, including unavailable capabilities and explicit interface coverage.
- Inventory legacy operation/result hashes and activation/installation tests that must
  remain compatible before extracting shared lifecycle primitives.
- Choose one known-answer candidate and trace all generated files, test receipts,
  review decisions and promoted/activated artifacts without changing live trusted source.
- Reproduce the timeout/refresh/disabled Execute scenario (T02); chart fixes do not
  establish that recovery issue is fixed.
- Define the first task-level candidate adapter and resource policy from this evidence;
  do not introduce another generation/install subsystem before the audit is complete.

## Shared statistical contract slice — 2026-10-27

T05/T09/T10 now reuse AnalysisOptions.statistics and the existing CSV scan through
StatisticsAccumulator. inspect_csv execution, MCP table_statistics/linear_regression
and CLI table-statistics call the same bounded analytical service. Recorded Outcome
and terminal reports consume its versioned result; Critic receives aggregate evidence.
No parallel executor, new write authority or arbitrary Python runtime was introduced.
The separate minimal Docker comprehensive-profile worker is not extended by this slice.
[Acceptance/limits](TABLE_STATISTICS_ACCEPTANCE.md). T01/T03 remain partial.

