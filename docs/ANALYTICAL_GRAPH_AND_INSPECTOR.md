# Recorded analytical graph and information panel

Delivered 2026-10-25. Follows [the bounded analytical loop](BOUNDED_ANALYTICAL_LOOP.md).
The conversation already saved tool evidence, but previously only chat rendered it;
the graph and information panel remained attached to workflow plans/runs. This change
projects the saved analytical session into the existing graph and inspector.

## What the view represents

After analytical exploration completes or stops with partial results, the view selects
**Latest analytical session · recorded**. It contains:

- The request's input folder and the analytical reasoning role with recorded call counts.
- Discovered inputs, distinguishing header/listing evidence from a fully profiled source.
  Candidate samples retain unverified provenance. Up to eight file blocks are rendered;
  the discovery inspector lists the complete bounded inventory.
- Recorded discovery, operation-assessment and profile actions, in journal order.
- Completed/failed action status and an advisory explanation/partial-findings block.

Edges identify recorded call order, tool invocation, data inputs and evidence flow.
Discovery links do not imply that every file was profiled. Only actual recorded actions
appear: no invented authorization, validation or Critic call. The timeline shows the
recorded action sequence and findings; individual action timestamps are not available.

The graph is a read-only evidence projection, with its own source type, not a new
executable workflow. Execute is disabled and authorization is not offered in this view.
Existing saved plans remain available under Graph to view; selecting one restores its
normal controls and existing backend validation/authority checks.

## Information panel

Clicking a block opens the existing information panel, including after it was closed.
The panel displays scoped facts from saved evidence:

- Discovery: folder, filenames, byte sizes, available column metadata and candidate flags.
- Input: full path, discovery scope, sample uncertainty and any recorded full-source profile.
- Assessment: operation, selected strategy, byte/row limits and remaining runtime checks.
- Profile: source and matching rows, distinct counts, recorded numeric/missing profiles,
  source SHA-256, codebook binding, query, checks and retained grouped summaries.
- Findings: computed facts alongside the model's advisory explanation, counts and duration.

Displayed hashes and statistics describe the recorded read. Opening the graph is not
current-source revalidation. Group display is bounded to the retained session evidence
(first 20 groups when truncated); it is not presented as a full interactive group table.
Unrequested numerical statistics remain explicitly unavailable. No raw source rows are
added. Model interpretation is not an independently validated Critic assessment.

## Restore and scope correctness

Opening the saved chat restores this graph without model calls, source reads or replay.
New sessions record their creation revision; older sessions label their loaded chat
revision rather than invent an action timestamp. New chat clears the analytical view.
Changing graph sources does not replace the saved executable plan or grant authority.
A scope generation guard prevents asynchronous startup restoration from overriding the
chat-specific graph or restoring an unrelated plan into a plan-less analytical chat.

The extended journey also exposed an older analytical writer that omitted task/chat IDs
on its final user/assistant pair. New writes include these IDs. A compatibility read
normalizes only the known two-entry shape, corroborated by identical messages and revision
in the same conversation plus recorded analytical evidence. It changes no stored text or
files on read. A later normal conversation write stores the corrected metadata. Foreign
or conflicting provenance is still rejected. No user database was edited during testing.

## Exact manual validation — no regeneration required

1. Stop/restart the existing launcher with `bash scripts/start_actioncharter.sh`, refresh
   the browser, and select the saved analytical chat that already worked.
2. Expect the analytical graph automatically. If viewing another source, choose
   **Graph to view → Latest analytical session · recorded**.
3. Click Discover input files, then Assess processing strategy. Confirm discovered
   candidates are distinguished from the selected full source and that its profile
   strategy is full_stream.
4. Click Profile selected table. In the reported user's saved session, the recorded
   source is data/input/test/diabetic_data.csv, with 101,766 source/matching rows,
   71,518 distinct patient_nbr, time_in_hospital mean approximately 4.395987, min 1,
   max 14 and zero invalid numeric values. These are the saved tool observations,
   not a fresh run or merely the model's reply. Inspect the source hash/query/checks.
5. Close the information panel, then click a graph block or timeline action: it reopens.
   Click Analytical findings to compare the advisory text with computed observations.
6. Refresh: graph and facts return without new analysis. Select a normal saved plan and
   switch back: the saved plan remains intact. A new chat must show no old analytical
   nodes or values. A partial session must not invent a completed profile.

## Verification

The isolated browser journey checks graph rendering, profile/strategy facts, panel
close/reopen, refresh, saved-plan switching, read-only controls, new-chat isolation and
partial-result accuracy. It also exercises the previous quality/group/export journey
using only temporary fixtures and the existing project-local browser profile/assets.
Targeted analytical-session/privacy tests verify new provenance, stable session revision,
read projection without stored mutation, successful later planning, and foreign-record
rejection. Final make test: 2,086 passed with 13 existing Rasterio warnings;
make interface-validate passed (existing large-bundle advisory remains). Browser tests
passed with zero page errors. Final focused provenance/privacy tests: 28 passed.
No model call or live-data mutation was needed for this graph integration.
