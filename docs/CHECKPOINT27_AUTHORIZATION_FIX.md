# Checkpoint 27 — conservative report authorization

Fixed 2026-10-19. A saved plan containing CSV inspection, PostGIS validation and
report generation failed Authorize with `recipe has no approval-required steps`.
The plan conservatively required approval, but the recipe compiler lost those
extra gates. The trusted registry classifies report generation as an evidence
write that does not normally require its own approval; the shared runner still
requires exact recipe authority for this workflow path.

Compilation now carries conservative plan gates into recipes that otherwise have
no ordinary writer gate. Recipe-step `additional_approval_required` can only add
a gate; registry requirements always apply. Its false default is omitted from
canonical serialization. Ordinary CSV/vector/raster/PostGIS writer recipes keep
their existing identities. Corrected evidence-only recipes have new digests and
need fresh review/authority; stored plans, historical recipes and approvals are
not rewritten or automatically authorized. Normal writer recipes already bind
the whole definition and still separately verify any stricter plan approval.

The engine rechecks authority before every approved step. Authorize records only
the decisions; it performs no inspection, calculation, database request or report
execution. Session, revision and expiry checks remain active. Turning availability
OFF still blocks later write operations. An explicit report operation needs write
availability on this path; automatic audit/failure record persistence remains
separate from that switch.

## Operator validation

1. Stop the current launcher with Ctrl+C and restart using
   `bash scripts/start_actioncharter.sh`. This loads backend code; refreshing the
   browser alone cannot update the running Python process.
2. Refresh the interface and reopen the saved chat. Inspect the actual operation
   list before authorizing: the reported plan contains PostGIS validation and
   report generation, not just CSV inspection or calculated columns.
3. For that intended report workflow, enable Allow write operations in Settings,
   reopen Authorize and review its exact scope. Submit the decision. The response
   should record plan and recipe approval without execution; Execute remains a
   separate action. Use only synthetic fixtures for acceptance at this stage.
4. If the intended task is CSV inspection only, ask Planner to replace the workflow
   with only `inspect_csv` on `data/input/sample_orders.csv`, returning row count,
   column names and a small preview, without PostGIS validation, report generation
   or writes. Confirm the actual operations; inspection requires no artificial
   approval. This planning-scope correction is separate from the authorization fix.

The reported workflow was not executed against the operator's PostGIS instance.
Tests do not establish whether that table exists or matches the user's intent.

## Verification

- `make test`: 1,787 passed.
- `make interface-validate`: typecheck/build passed.
- `corepack pnpm@10.17.1 --dir interface browser:test:27-report-authorization`:
  two cases passed, including the exact conservative validation/report shape and
  no execution/output during authorization.
- Backend regression executes the complete report workflow with real temporary
  CSV/evidence storage and a mocked PostGIS validator; it checks authority
  invalidation, digest binding and inability to weaken trusted registry gates.
- Browser data/profiles and API are temporary fixtures, separate from the
  operator's launcher and normal browser cache. Model responses are fixtures.
