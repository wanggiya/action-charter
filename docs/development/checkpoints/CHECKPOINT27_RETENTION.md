# Checkpoint 27.1: automatic successful-workflow records

Implemented slice of the [checkpoint 27 plan](CHECKPOINT27_PLAN.md). [Planner retrieval/adaptation (27.2)](CHECKPOINT27_REUSE.md) is now delivered. This does not
complete Critic enrichment (27.3), outcome
visualizations, local-model evaluation or prototype/release preparation.

## Behavior and boundaries

Every new durable workflow run captures the registered operation contracts before
dispatch. After execution is final and durable, the backend automatically indexes
successful recorded steps before optional Critic assessment. There is no additional
model call, “make reusable” prompt, synthetic-fixture authoring or registration
ceremony. Closing the interface does not prevent saving.

Reusable recipes now has exclusive **Recipe list** and **Keywords** views. Recorded-success rows are automatic records. These
are historical method records, separate from generalized/registered templates.
Select one to see operation order and Use in Planner. Recorded versions/output
contracts and source runs are under Execution evidence. **Inspect recorded outcome** opens the existing run panel; it neither
changes the current plan nor authorizes/executes an operation. Existing templates,
Advanced recipe authoring and manual composition remain available.

A record is eligible only when the durable run completed, execution occurred,
every expected step has a successful status and recorded result, and every required
deterministic validation passed. Failed, cancelled, interrupted, skipped or
validation-failed work is not labelled successful. Read-only inspection remains
inspection metadata, never an intermediate CSV artifact. Historical success does
not prove that an input/output still exists or has remained unchanged, nor that
the same method works on arbitrary new data.

Baseline names/tags come from operation contracts, not model text or transcripts.
Examples: `csv`, `inspection`, `cleaning`, `aggregation`, `vector`, `raster`,
`geospatial`, `postgis`. A method identity hashes normalized arguments,
dependencies and contract fingerprints. File bindings preserve alias relationships
and suffix/role while ignoring filename differences; literal filters, columns,
keys, strategies and other semantic arguments remain part of that identity.
Repeated identical completion handling is idempotent. Similar successful runs group
under one method but retain distinct run/plan/evidence references. Different
semantic choices or contract versions do not silently inherit the old identity.

## Privacy, storage and failures

The index stores trusted operation metadata and hashes/references, not copied
arguments, file paths, data rows, chat messages, credentials or approval tokens.
Private exact bindings remain in the existing source run. UI discovery includes
only records from the current conversation; requests without a conversation ID
list unlinked CLI records only. No other chat's bindings/history are silently
added to Planner context. The retention service itself adds no Planner prompt retrieval; 27.2 now supplies
bounded examples from the same chat through the shared Planner coordinator.
Cross-chat memory remains deferred to checkpoint 30 or later with a fresh decision.

Index storage is project-local `workflow-state/successful-workflows.sqlite3`,
transactional, owner-created with mode 0600, and excluded from Git and Docker build
contexts. It caps at 200 successful source records (matching the run inventory),
24 KB per metadata record and 16 MB for the database file. Nothing is silently
evicted. General archival/deletion management remains future work.

Contract fingerprints are captured at run preparation and compared on discovery.
Changed/unavailable contracts are shown as historical, not currently applicable.
Older runs without a dispatch-time snapshot are not automatically backfilled;
retrying indexing cannot establish what their original operation versions were.
This automatic path covers durable `workflow/runs`, not legacy synchronous
execution endpoints or synchronous Snakemake export.

An indexing failure cannot turn a completed execution into a failed one or erase
outputs/evidence. The run panel reports unavailable indexing and offers **Retry
indexing only**. This cannot retry an operation, refresh approval or call a model.
If the process stops between completion and indexing, a pending receipt becomes
unavailable after 30 seconds and can be explicitly retried. No workflow or model
request is automatically restarted. A damaged index does not hide existing recipe
templates. Optional Critic failure does not block baseline retention.

## Shared API/CLI

The existing POST `/api/v1/reusable-recipes` `list` action returns
`successful_records` alongside generalized templates. `query` filters safe method
names/tags/operation IDs; optional `conversation_id` selects only that originating
chat. Each group contains operation metadata, contract status and source run/plan/
evidence hashes. These records grant no execution authority.

POST `/api/v1/workflow/runs` with `action: retain` and `run_id` indexes an already
finished eligible run only. Existing CLI commands `reusable-recipes` and
`workflow-runs` invoke exactly these services using `--request-file FILE
--project-root DIR`; no new CLI command or separate registration is required.
Normal frontend users do not need request files or JSON.

## Frontend validation

Use temporary/example inputs with the existing launcher and configured local model.
Do not test against a live database or rerun writes into old targets.

1. Open a new Planner chat; request inspection of `sample_orders.csv` with row
   count and column names, no writes. Before execution, Reusable recipes should
   show no successful record for this new chat. Generating a plan is not success.
2. Review and Execute the read-only inspection. No invented write authorization
   should be needed. Open Reusable recipes: a successful record should appear
   automatically, tagged CSV/inspection, with metadata output and source evidence.
3. In the same chat request cleaning that keeps `region`/`amount`, fills missing
   `region` with `Unknown` and uses fresh CSV targets. Review, authorize exact
   writes and Execute. A second method appears automatically. Do not ask “make
   reusable” and do not click Prepare/Register.
4. Expand the record and inspect its recorded outcome. Refresh and reopen the
   chat: the same records return without inference or execution. Actual file
   contents and prior attempts must remain unchanged.
5. Start a new chat. It must not inherit the first chat's private successful
   records. Return to the original chat to see its records again.
6. For failure/cancellation testing, use temporary fixtures: stopped/failed work
   must not become a successful method. If indexing itself is unavailable, use
   Retry indexing only and verify no operation runs again. Avoid deliberately
   corrupting real project storage; automated tests cover this failure mode.

An actual local model may still time out or propose an invalid plan. Fixture
acceptance proves deterministic retention behavior, not local-model planning
quality. Planner discovery/adaptation is now available through 27.2; optional Advanced
authoring remains separate.

## Verification

Backend tests cover real temporary CSV/vector runs, inspection versus artifact
contracts, zero retention model calls, Critic timeout, missing/failed validations,
semantic deduplication, distinct source evidence, contract changes, scope
isolation, idempotent retry, corrupt/unsafe storage, inventory limits and reopening
through a separate CLI process. New browser acceptance exercises planning without
retention, automatic saving after execution, evidence inspection/index retry,
refresh persistence and chat isolation using real CSV processing and fixture models.
Initial 27.1 acceptance: **1,646 backend tests passed**, frontend typecheck/build passed, and
**17 production-browser fixture groups passed** (5 new retention, 6 existing
Planner/graph, 6 recipe/cancellation/recovery/restart). All browser groups reported
zero page errors and zero live-service calls. Local-model quality remains unverified.
