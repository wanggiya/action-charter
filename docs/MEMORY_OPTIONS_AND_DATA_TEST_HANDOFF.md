# Memory options preserved; controlled data testing next

Recorded 2026-10-23. Latest operator clarification. Documentation only.
This note takes precedence over conflicting claims that a memory architecture or
knowledge-agent separation has already been selected. Keep prior proposals intact.

## Retention clarification

The current shared-memory idea allows current content and priority to change while
keeping older content recoverable by default. It is not a requirement for a physically
immutable file, monotonic byte count or irreversible preservation under every condition.
Do not routinely discard old content because of age, low priority or summarization.
Proposed method: stable IDs, retained revisions, explicit supersession and a readable
current view. Exact pruning, explicit deletion, sensitive-data erasure, archival and
backup retention rules are undecided; no easy/automatic loss of prior versions.
Retrieval may exclude obsolete claims without deleting their history. Versions retain
what was claimed, not proof the claim is correct. JSON schema and update protocol
remain proposals. This refines the earlier shorthand “only grows / never forgets”.

## Preserve two independent design choices

### Memory organization A: separate role memories

    Planner <-> Planner short/mid/long memory
       | selected contributions
       v
    SHARED MEMORY <-> current view + retained revisions + history references
       ^
       | selected contributions
    Critic <-> Critic short/mid/long memory

### Memory organization B: common agent memory

    Planner ---+
               +<-> COMMON short/mid/long memory
    Critic ----+       current view + retained revisions + history references

Both can connect to domain knowledge and graph relationships. The exact shared-memory
retention policy in B remains open; do not silently assume all A-specific details apply.
Separate files versus SQLite is another storage choice, not a substitute for A/B agent
ownership/retrieval behavior. Separate role memories do not inherently require extra
subagents or loaded model instances. Scope/access remains independent from memory tier.

### Knowledge-management role X: combined with Critic

    History + selected memory + documentation + checks
                       |
                    Critic
          assessment + knowledge-curation function
                       |
             knowledge / graph updates

### Knowledge-management role Y: separate logical agent

    History + selected memory + documentation + checks
                       |
       Critic assessment -> Knowledge-management agent
                            extract/qualify/revise/connect
                                      |
                            knowledge / graph updates
                                      |
                          relevant recall into memory

A separate agent may also interpret discussion/documents without waiting for a Critic
assessment. It operates on shared memory through service functions; it does not need
a different container/model process. Its own private-memory policy remains open.

| Role choice | Advantages | Disadvantages |
| --- | --- | --- |
| Combined Critic/curator | Fewer handoffs; reuse loaded evidence; smaller initial implementation; may avoid another model call. | Competing duties, more complicated output, self-review risk, harder to evaluate curation independently. |
| Separate knowledge agent | Focused instructions, independent scheduling/budgets, distinct testing, can combine evidence across completed tasks within permitted scope. | More integration/scheduling, possible extra calls and latency, stale/incomplete handoffs, model disagreement; separate role is not independent proof. |

No assumption that separation automatically improves quality or combining always saves
calls. Compare actual prompts, budgets, correctness and failure handling. Neither role
may verify itself by assertion or grant execution authority. Backend services continue
to own access, versions, source binding and reliable writes in either configuration.

A+Y was the preceding preferred A proposal; it remains recorded, not a final choice.
B+X and earlier A+X also remain recorded. Role choice and memory organization are
separate experimental factors. Do not compare A+Y to B+X and attribute differences
solely to private/common memory. No experiment switch or new agent is implemented.

## Domain knowledge and synchronization retained in all options

History records messages/actions/results. Memory selects useful working experience.
Knowledge curation proposes conditional definitions and methods with exceptions and
per-claim evidence status. Graph edges express supported_by/requires/tested_on/
contradicts/supersedes/applies_to and link to actual sources. They do not establish
scientific correctness or require a separate graph database.

Correction updates a current version while preserving the prior one, flags explicitly
dependent methods/private notes/cached context, and triggers selective reassessment.
No full-history model scan, automatic rerun, silent plan alteration or authority reuse.
Missing dependency links are a known limitation. Packages may later transfer selected
knowledge to compatible installations; this is not model-weight training or automatic
installation of executable capabilities. Privacy, missing evidence and compatibility
remain explicit checks. Cross-chat sharing remains separately gated.

## Immediate priority: prepare controlled data tests

User now wants to preserve memory alternatives and think about them later, then prepare
data tests to establish present functionality and large-data limits. Do not continue
building memory as an assumed prerequisite to this diagnostic evaluation. This changes
the immediate work order, not the claim that broader demo/learning acceptance is done.
No test, download, dependency install or live-service action was performed here.

Proposed next preparation:

1. Identify user-selected datasets, formats, sizes, package companions and intended
   operations; define a reference answer/tool where possible. Do not assume any format
   is supported or choose/download real private/medical data without instruction.
2. Separate discovery, actual processing and visualization tests. Metadata success
   does not demonstrate full-file transformation or complete rendering.
3. Establish laptop RAM/free disk and dataset-size tiers; begin small and increase
   within supported guards. Record wall time, peak worker memory, CPU if available,
   bytes/rows/features, verification state and observable UI responsiveness.
4. Compare metadata/counts/CRS/fields with suitable independent tools or documented
   reference results. Test stopped/failed/reopened runs and output integrity, not just
   a screenshot. Include changed-source and unsupported/over-limit behavior.
5. Use originals read-only and temporary/explicit fresh targets. Writes require normal
   exact review/authorization. No automatic live PostGIS/GeoServer tests or writes.
6. Report passes, failures, safe refusals and capability gaps. Only then propose focused
   scale fixes and determine whether data workflows are suitable for a demo.

Current checkpoint-28 baseline: discovery batches up to four sources / 1 GiB aggregate
under per-reader/time guards; synthetic CSV/TIFF measurements at 16/64 MiB and GPKG/SHP
cases above 8 MiB. These do not prove arbitrary 1 GiB processing. CSV transformations
and full exploration remain 8 MiB / 10,000 rows; geometry/pixel display has separate
bounds. Inspect actual code/configuration when preparing tests rather than raising
limits blindly or describing metadata-only success as huge-data support.

## Next-session instruction

Read this document and WORK_RESUME.md before implementation. Latest request is to
record alternatives and discuss pros/cons, then prepare data testing. All memory
mechanisms remain unimplemented proposals; preserve earlier history and user changes.
User owns Git/publication. No automatic memory deletion, source mutation, new dependency,
training or live-service modification is authorized by this documentation request.
