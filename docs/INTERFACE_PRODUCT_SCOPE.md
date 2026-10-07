# Guided interface product scope

The ActionCharter interface is intended to become the normal operating surface,
not a read-only companion to the CLI. The CLI remains for automation,
development, recovery and advanced operators.

## Target experience

1. The user describes a desired outcome and selects data.
2. The Planner proposes a typed workflow.
3. The interface renders it as an editable Blueprint-style node graph.
4. The user changes permitted parameters or requests a revision.
5. Deterministic policy highlights effects, risks and approval requirements.
6. Human approval binds to the exact proposal digest.
7. Governed execution reports queued, running, completed, failed and skipped
   nodes with start time, elapsed time and safe progress.
8. Validation, Critic review, evidence and outputs remain attached to the graph.

The primary journey is **Planner agent → Flow graph → Authorize (when required) → Execute → Outcome**, with Execution History, Saved records and Settings directly accessible. Execute reviews the current plan; Outcome shows the current result. Technical Plan belongs under Advanced. Recipes, raw digests, detailed evidence, release composition,
Snakemake, skill construction, and infrastructure controls belong in an
expandable advanced workspace. Deterministic digest comparison remains active
even when hashes are not displayed continuously.

The post-history integration must also remove repeated operator bookkeeping:
skill choice becomes optional, exact scope is reviewed once beside the graph,
one explicit decision authorizes the consequential work, and the current
outcome appears before an expandable attempt log. Backend artifact checks and
durable records remain; see `context/POST_HISTORY_INTERFACE.md`.

## Required coverage

| Area | Interface responsibility |
| --- | --- |
| Requests and context | Guided request composer, bounded input selection and contract expectations |
| Planning and policy | Proposed steps, dependencies, parameters, warnings and deterministic policy results |
| Approval | Exact digest, affected resources, required steps, expiry and explicit human decision |
| Vector and raster | Inspection, conversion, validation and safe previews using existing controlled adapters |
| Tabular data | Governed pandas capability after its typed adapter and policy contracts exist |
| PostGIS | Inspect, load, validate, compare, assess, promote, verify and rollback through existing boundaries |
| Recipes | Create, review, approve, execute and inspect reusable recipe evidence |
| Snakemake | Export, validate, dry-run and replay without requiring users to write commands |
| Skills | Browse active skills; propose, test, promote and verify candidate skills through Builder controls |
| Agents | Show Planner, Executor, Critic and Builder ownership, authority and activity |
| Evidence and reports | Safe structured previews, lineage, validation, Critic records and downloadable reports |
| Releases | Candidate/current state, promotion history, authoritative packages and rollback state |
| GeoServer | Existing bounded inspection and approval-gated publication first; broader administration later |
| Operations | Start time, elapsed time, node state, safe diagnostics, cancellation where supported and retry proposals |

## Checkpoint placement

This operating surface belongs to the Checkpoint 17 sequence. It will be built
in reviewable slices rather than one unsafe browser authority expansion.
Checkpoint 18 remains pilot operations and bounded memory after the guided
interface has a credible end-to-end path.

Checkpoint 17 reached that prototype boundary at 17AX. The revised Checkpoint
18 direction is maintained in `context/CHECKPOINT18_DIRECTION.md`.

The browser never receives arbitrary shell, SQL, Python-package installation,
filesystem or network authority. User actions call typed backend contracts and
preserve plan, policy, exact approval, execution, validation and evidence
boundaries.

## Checkpoint 23 composer and view retention

Planner agent opens by default. Files are described in planning context, without a separate Text planner input field. The writing surface fills available left-panel space and keeps keyboard focus visible. Bare model-proposed input filenames are normalized under data/input before policy checks and digest creation. Explicit normalized relative paths remain supported; backend validation rejects unsafe paths. Runtime adapters enforce access boundaries.

View changes and execution-history browsing preserve the generated proposal. Returning to Planner restores its graph without regeneration. Conversation drafts, pending replies, clarification and model failures preserve the proposal. A validated stored revision invalidates downstream approval state. Completed turns are recoverable through the conversation selector, with explicit Open conversation plan after refresh; immutable plans also remain in Saved records. Unvalidated manual graph edits block new planner turns and execution.

Graph editing supports click-and-drag, a searchable right-click add menu, Shift+A, Delete only with canvas focus, and parameters in the inspector. Edited operations must pass backend validation before approval or run. Current-plan dragging, add/delete, searchable add shortcuts and inspector parameter editing are implemented. Validate and save edits is required before Execute. Operation dependency wiring is implemented through matching data ports or inspector selectors and must pass backend DAG/policy validation. Planning/policy scaffold nodes remain explanatory and cannot be rewired into authority. Context text never grants execution authority.

## Docked execution review

Settings has a gear icon. Orange Authorize uses an exclamation icon, highlights required operations and records exact approval without running work. Yellow Play/Execute separately verifies scope and authority before dispatch. Read-only inspection uses the explicit Execute click without a redundant checkbox. History, review and outcomes occupy a right-side workspace column; narrow layouts may stack, but panels do not overlay the graph. Context text remains non-authoritative.

## Operation graph controls

The graph toolbar exposes Add, Delete, Move, Connect, Disconnect and Parameters. Connection edits become optional typed depends_on fields; absent fields keep the legacy sequential recipe and digest. Explicit dependencies are checked for known IDs, uniqueness, self references, cycles and required inspection/validation ancestry, then compiled into the governed recipe. Execution follows its reviewed topological order. Connections express completion prerequisites, not automatic file/output substitution or parallel execution.

Outline uses a subtle top/bottom tint fading to a clear center and opaque content; timeline text retains its separate unboxed presentation. Scrollbars use the timeline theme throughout. Zoom and legend default to the lower-left and remain draggable within the canvas.

## Main-workflow Snakemake blocks

Export to Snakemake and Verify Snakemake package are available in Add and conversational Planner. They reference an immutable original saved plan and independently verified successful governed recipe evidence. Retained operations are displayed as reused; Execute exports and statically verifies the exact package without rerunning source operations or starting Snakemake. A fresh explicit plan approval grants only the current export path; historical source recipe authority is not renewed. Fresh sources must complete successfully before export review. Advanced export remains available for older workflows, but is not required for this block path.
