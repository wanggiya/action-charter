# Checkpoint 18 direction — from governed prototype to useful product

## Product test

ActionCharter must become faster and easier for ordinary data work than manually
coordinating scripts, spreadsheets, GIS tools, model prompts, approvals, and
evidence. Governance is the differentiator, but governance cannot require the
operator to manually shepherd every internal artifact.

## Default user journey

1. **Plan** — describe the outcome, select data, and continue the task
   conversation with bounded history.
2. **Review graph** — inspect the generated process, inputs, effects, approval
   gates, and expected outputs; request revisions or edit permitted parameters.
3. **Run** — approve consequential scope once and follow live execution.
4. **Check outcome** — inspect results, validation, maps or tables, failures,
   and recommended next actions.

Recipes, workflow internals, raw SHA-256 values, release components, Snakemake,
skill construction, and infrastructure settings remain available in an
**Advanced** workspace. Hashes are compared automatically in Python and shown
prominently only for mismatch, audit, export, or expert review. Matching
artifacts should appear connected in the graph without manual comparison.

## Planning roles

- **Task history**: stores immutable user requests, clarifications, selections,
  decisions, results, failures, and artifact references. It is authoritative
  project state rather than model-generated memory.
- **Context Curator**: deterministically selects a bounded, redacted context
  package for the current task and records its exact source references.
- **Intent agent**: reads only the reviewed context package, decomposes the
  desired outcome, asks necessary questions, and proposes a goal-level process.
- **Planner agent**: maps that reviewed process onto implemented, uniquely
  identified capabilities and typed arguments. It does not invent functions.
- Existing deterministic policy remains authoritative for execution.

The original task records remain authoritative. Summaries are derived views,
never replacements for source history. Neither context selection nor intent
reasoning grants approval or execution authority.

## Context-and-graph workspace after task history

After Checkpoints 21 and 22 provide task history, bounded context packages,
and reviewed intent, the default interface should place the task conversation
and context on one side and the live process graph on the other. The context
side shows the current goal, relevant source references, clarifications,
assumptions, and proposed revisions. The graph side shows the corresponding
plan, agent roles, data movement, gates, execution, and evidence. Selecting an
item on either side should reveal the linked item on the other side.

The conversation is a place to express intent and inspect context, not an
approval channel. A separate explicit decision remains required for
consequential work. Task history is persisted by the governed application;
model-generated summaries are derived and can be checked against their sources.
This layout should be implemented when those records exist rather than
presenting an empty chat pane that implies memory or agency prematurely.

The completed Checkpoint 19 PostGIS run exposed a product gap: operators still
manually traverse plan storage, recipe storage, separate approvals, previews,
and evidence screens. After task history and context exist, the default path
must offer an optional skill selector, graph-side review, one explicit decision
over exact consequential scope, a deliberate Run action, and a current-task
outcome. Internal artifacts and execution attempts remain accessible on demand.
See `context/POST_HISTORY_INTERFACE.md` for the acceptance boundaries.

## Tabular processing

Add governed CSV/TSV and dataframe operations through typed pandas adapters,
contracts, fixtures, validation, and evidence. Start with common inspect,
select, filter, join, group, aggregate, sort, reshape, clean, and export tasks.
Do not expose arbitrary Python expressions or unrestricted dataframe methods.

## Governed library capability discovery

A capability-discovery/Builder process may inspect an installed library's
public API and documentation and propose candidate operations. User-facing
display names should be fully qualified—for example `pandas.read_csv()` or
`geopandas.GeoDataFrame.to_file()`—so provenance and collisions are clear.

Discovery does not automatically authorize every NumPy, pandas, GeoPandas, or
third-party function. Each candidate must receive:

- a globally unique internal capability ID;
- fully qualified display name and pinned library version;
- typed input/output schema;
- access and side-effect classification;
- bounded path, network, and resource policy;
- deterministic tests and validation contract;
- isolated candidate testing;
- explicit human promotion into the active registry; and
- removal or deprecation support.

## Local product delivery

- Start frontend, backend, and required local services through one supported
  command or desktop launcher.
- Detect Ollama, Docker, PostGIS, and GeoServer availability and explain missing
  optional capabilities.
- Package a laptop/PC prototype with safe local defaults and retain CLI commands
  for automation and recovery.
- Reduce repeated confirmations by grouping non-consequential steps and asking
  once for the exact consequential scope.

## Product roadmap after Checkpoint 17

1. Checkpoint 18: prototype release and reproducible installation/startup;
2. Checkpoint 19: simplified default workspace plus Advanced mode;
3. Checkpoint 20: automatic artifact/digest relationship projection;
4. Checkpoint 21: governed task history and deterministic context assembly;
5. Checkpoint 22: bounded Context Curator and conversational Intent Agent;
6. Checkpoint 23: governed tabular-data vertical slice;
7. Checkpoint 24: governed library capability discovery and candidate testing;
8. Checkpoint 25: real user task benchmark measuring time, intervention count, failures, and
   outcome quality against manual spreadsheet/GIS work.

## Reviewable checkpoint sequence

- **18 — reproducible local startup and alpha-release gate:** one supported
  launcher, bounded service diagnostics, clean shutdown, and release notes.
- **19 — simplified default workspace:** make Plan → Review graph → Run →
  Check outcome the primary navigation and move expert controls to Advanced.
- **20 — automatic authority-chain projection:** compare digests server-side,
  connect matching artifacts visually, and surface hashes mainly for mismatch
  or audit.
- **21 — governed task history:** append immutable task events and construct
  deterministic, bounded, redacted context packages with source references.
- **22 — Context Curator and conversational intent:** use reviewed context
  packages for an Intent Agent above the Planner without granting tool
  authority or treating conversation as approval.
- **23 — governed tabular vertical slice:** inspect CSV/TSV, apply a small
  typed Pandas transformation set, validate output, and record lineage.
- **24 — governed capability discovery:** propose fully qualified installed-
  library operations, isolate tests, and require explicit promotion.
- **25 — comparative product benchmark:** measure operator interventions,
  elapsed time, failure recovery, deterministic correctness, reproducibility,
  and audit comprehension against a manual workflow and a general coding
  agent.

ActionCharter does not attempt to match a general agent runtime feature for
feature. Checkpoint 18 tests whether it can be distinctly better for governed,
reproducible professional data work.
