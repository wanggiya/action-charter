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

- **Intent agent**: maintains bounded task conversation and history, examines
  context and data summaries, decomposes the desired outcome, asks necessary
  questions, and proposes a goal-level process.
- **Planner agent**: maps that reviewed process onto implemented, uniquely
  identified capabilities and typed arguments. It does not invent functions.
- Existing deterministic policy remains authoritative for execution.

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

## Initial Checkpoint 18 order

1. prototype release and reproducible installation/startup;
2. simplified default workspace plus Advanced mode;
3. automatic artifact/digest relationship projection;
4. conversational task history and intent-agent contract;
5. governed tabular-data vertical slice;
6. governed library capability discovery and candidate testing;
7. real user task benchmark measuring time, intervention count, failures, and
   outcome quality against manual spreadsheet/GIS work.
