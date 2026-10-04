# Current implementation status

Updated: 2026-10-04

## Product boundary

ActionCharter is a local, single-operator alpha for governed data workflows. The React interface and CLI use typed backend services. Existing registered recipe workflows support explicit approval, bounded execution, deterministic validation and durable evidence. Vector/raster, PostGIS and limited GeoServer capabilities are implemented; interface coverage is narrower than CLI coverage.

## Context and intent

Implemented: checked task history, bounded retrieval from explicitly selected histories, immutable context review, reasoning-only Intent with clarification, history-free tasks, immutable resolved Intent review, saved-review recovery and exact vector/raster metadata inspection handoff. Reviewed plans can be stored and reopened in the existing Plan workspace with provenance retained. A Planner-added approval requirement is preserved.

Historical denial remains denial. Context review, Intent review and plan storage never infer approval or execute tools. Changed source records block historical review reuse. Fresh tasks require no invented history or citations.

## Known integration gaps

- The new Intent bridge supports one metadata inspection input, not arbitrary write tasks.
- No-approval-required inspection plans cannot yet continue through the legacy approval-dependent plan-to-recipe compiler. Never create artificial approval as a workaround.
- An input path typed in Intent does not automatically select a file picker item.
- Refresh clears unsaved browser drafts. Stored reviews/plans can be recovered; this is not generalized conversation memory.
- Draft graph editing does not change an authoritative executable plan.
- Snakemake static export validation does not run a replay.

## Verification and acceptance

The backend integration matrix covers twelve fresh/history-backed vector/raster and decision combinations with fixture models and real registry/storage services. Offline tests and frontend typecheck/build were checked during implementation. Fixture tests do not establish live-model quality or browser usability. The most recent documentation cleanup changes no execution contract; 27 focused Planner/integration cases passed after the current-context cleanup.

Local operator acceptance and PR review remain separate. See [acceptance and commit instructions](../docs/CHECKPOINT22O.md). Earlier operator PostGIS acceptance observed two rows, EPSG:4326 and POINT geometry; it is historical evidence, not a fresh database check.

## Next work

Integrate a task-centered conversation beside the actual graph, explicit input selection and an understandable decision/run/outcome route. Support read-only continuation without fabricated approval; keep exact approval for writes. Reduce panel hunting and manual digest handling while keeping backend identity checks. Complete a reproducible live demo before making public feature claims.

See [implementation plan](../docs/CHECKPOINT23_PLAN.md). Tabular processing, general package discovery, 3D, end-user packaging and generalized memory remain later work.

## Record navigation

[Architecture](ARCHITECTURE.md), [roadmap](PRODUCT_ROADMAP.md), [documentation responsibilities](../docs/DOCUMENTATION_GUIDE.md). Previous incremental status is preserved in [development history](../docs/development/STATUS_BEFORE_REORGANIZATION.md); it is not the current capability definition.
