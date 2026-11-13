# Phase 0 closeout — P0-C1 through P0-C4

Recorded 2026-11-13; [tracking #84](https://github.com/wanggiya/action-charter/issues/84).
This is consolidation and a bug fix, not Phase 1 implementation or a new agent.

## Closeout record

| Task | Result | Evidence and remaining condition |
|---|---|---|
| P0-C1 | Complete | PR #83 merged as `20b7a38`; runtime marker removals and canonical example paths are committed. Read-only workspace verification reports `source_only: true`, no legacy entries, migration status complete. Seven empty legacy folders were removed; no saved record was removed/moved. |
| P0-C2 | Implemented and automatically verified; owner acceptance/merge pending | Mixed valid/invalid recipe and plan inventories return safe partial lists. Invalid records are visible, non-actionable and unchanged. The owner's 74 saved recipe files retain their hashes: 73 valid, one format-policy rejection. |
| P0-C3 | Complete | PR #65 confirms delivery. #60 was already closed; #61–#64 were verified and closed as completed during this task. |
| P0-C4 | Documentation complete; owner merge required | Current status, roadmap and working-method status are reconciled. Phase 0 consolidation exit checks passed. Phase 1 begins after this closeout is accepted and merged; no Phase 1 code is included. |

The owner performed the actual workspace cutover before this task. Verification now
reports `changed_since_migration`, not `exact_copy`: normal use has changed saved
state since the cutover certificate. This does not imply a failed migration. No
cutover/rollback, backup rewrite, ownership change or live database operation ran here.
The previous backup was not recertified. Stable workspace binding is read successfully.

Merged PR #82's owner-authored description says “owner manual acceptance done.”
Treat that as **owner-reported overall acceptance**, not agent-observed real-model
evidence or a source of missing per-step IDs/timings. Earlier acceptance notes remain
historical. Optional live write acceptance was not added by this task.

PA1 source capture and PA2 gold-set labelling remain owner data-collection work as
listed in the Phase 1 plan; no corpus, benchmark or policy-analysis capability is
claimed here. Those owner tasks are distinct from this consolidation/code closeout.

## Inventory behavior and boundaries

Previously, one historical recipe using `inspect_vector` on a CSV caused
`GET /api/v1/recipes` to return 503 for every recipe. Listing now uses per-record
checks through the existing shared task-action service. Valid records retain the
existing response and graph behavior; malformed, unsafe or policy-rejected records
are excluded from the usable list and get bounded diagnostics.

Diagnostics identify the basename, record kind, rejection code and bounded/redacted
reason. `approval_allowed` and `execution_allowed` are always false. Validation errors
do not expose raw payloads. Links, non-regular files and hardlinks are not read as
ordinary records. Corrupt approval/link evidence never becomes verified authority.
An invalid matching Planner artifact blocks that definition link while preserving
the valid recipe's visibility. Diagnostics are deduplicated and capped at 200; total
count and truncation are explicit. Existing directory/file-count/size limits remain.

The same display pattern applies to saved plans and their approval records. Root
ownership, unsafe-root and global-budget failures still fail closed. A wholly
unavailable root is not reported as an empty successful inventory.

Saved records shows labelled unavailable findings immediately below Refresh records,
before either saved list, so a long plan history cannot hide recipe warnings.
Advanced shows findings above recipe cards using the same UI styles.
Unavailable entries have no Open/Approve/Run controls, and graph source options
contain only usable inventory entries. All-invalid lists remain visible with reasons.

Approval preparation, approval verification and execution still load and validate
the exact original artifacts. The CLI's **authority-verification inventory** remains
strict; it serves a different purpose from a tolerant display list. No model text,
historical record, installation or diagnostic grants execution authority. Files are
not repaired, quarantined, rewritten or deleted by listing. No new CLI command or
agent role is required; callers reuse existing services.

The original R8 HTTP snapshot is unchanged. The two intentionally corrected display
coordinators have explicit current AST expectations in the R8 test; all other
coordinators, routes, request schemas and transport contracts still match history.
Valid/empty inventory responses retain their original shape. Diagnostic fields are
additive and appear only when needed; frontend parsing supports older responses.

## Verification

Focused inventory/API/compatibility checks and frontend typecheck/build passed.
After documentation reconciliation, 48 focused inventory/HTTP/compatibility/context
checks passed; 392 local documentation paths resolve. The archived 34,917-byte
overview and all pre-existing status-history text were verified preserved (links rebased).
Seven dedicated cases cover mixed records, strict approval rejection, malformed
JSON, links, size/nesting limits, invalid plans/approvals, bounded diagnostics,
all-invalid lists, immutable bytes and HTTP 200. Existing normal inventory and
authority tests remain in place. Full `make test`: **2,827 passed**, 13 existing
spatial warnings, 769.57 seconds. This ran from an exported source-only tree with
GitHub Actions/frontend-required flags and no owner config, records or private data.
The final seven inventory cases passed again after adding the corrupt matching-plan
assertions. Strict layer checking reports zero debt; compatibility checking reports
zero errors, with 290 retired and 117 explicitly retained boundaries.

The isolated browser/API journey uses stable identity and relocated temporary state.
It verifies Saved records, valid recipe review in Advanced, invalid reason display,
all-invalid plan/recipe handling, long-filename containment, unchanged fixture hashes,
zero approval/execution calls and
zero page errors. It uses a new browser profile and project-local dependencies;
the owner's browser/cache and live services are not used. The real owner inventory
check is read-only and reports aggregate counts, not source data or transcript rows.

Automated results are fixtures/fake-model evidence, not a new local-model benchmark.
No Git commit, push, merge, package install, secret edit or live database change.

## Owner acceptance

1. Restart the usual launcher so its API loads the updated code:
   `bash scripts/start_actioncharter.sh`, retaining your usual launch options.
2. Open **Saved records** in the top toolbar (separate from Reusable recipes).
   Click **Refresh records**. Below it, **Saved recipes · Unavailable records** shows
   rejected recipe findings; expand it if collapsed: the historical CSV/vector mismatch should show a reason and blocked
   approval/execution status. Stored records are not silently repaired.
3. Open a valid recipe. Advanced should still show its steps and exact identity,
   alongside the unavailable-record notice. Viewing needs no write authorization.
4. Refresh: the same invalid file remains blocked, and valid records remain usable.
   An all-invalid fixture should show findings rather than a 503 or empty success.
5. Review and merge this closeout using the owner's Git workflow. Phase 1 follows
   [PHASE_1_PLAN.md](product-direction/PHASE_1_PLAN.md); start with benchmark contracts
   and provider foundations only after closeout acceptance/merge.
