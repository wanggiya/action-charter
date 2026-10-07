# Checkpoint 23 commit review

Implementation and automated regression are ready for operator commit review. This is a reviewable change summary, not commit/push authorization. The operator explicitly authorized commit, push, merge with --merge and feature-branch deletion after the sensitive-file audit. This review records the delivered scope and validation; publishing status is reported separately after remote verification.

## What changed and why

| Area | Result and reason |
| --- | --- |
| Planner conversation | Saved dialogue, clarification and complete validated revisions replace the primary one-shot form. Draft/pending/failed turns preserve the current plan. Optional skill selections persist and each turn records skill snapshots. |
| Governed graph edits | Add/delete/parameters and directed dependency edits pass backend argument/path/DAG/policy validation before storage, approval or execution. Blueprint-style pin gestures expose the same typed contracts. Layout changes alone convey no authority. |
| Workflow controls | Orange Authorize records scope-bound decisions; yellow Execute independently checks them. Review, Outcome and History are docked, with clearer information rows and persistent proposals. |
| Local configuration | The host launcher loads allowlisted non-secret .env settings and local secret-file paths, honoring terminal overrides. This fixes the confirmed container-secret-path failure without exporting passwords or enabling writes implicitly. |
| Snakemake | Main-workflow Export and Verify blocks reference a completed saved source and verified historic run. They export/static-verify without reloading PostGIS or launching Snakemake, and require fresh exact export review/approval. |
| Material/layout | Solid/Outline preferences, clearer text, top/bottom edge tint, consistent scrollbars, lower-left zoom/legend and compact expandable controls keep the graph usable. |
| Latest polish | Drag previews update the node/attached curves directly and commit layout once on release, avoiding whole-App rendering per frame and automatic viewport resets on drop. Inspector facts now use the same right-aligned value grid as Outcome. Snakemake choices lead the scrolling options in yellow/orange; only search and close remain pinned. |
| Validation/docs | Automated source/authority/path/edit/recovery/export regression coverage and staged browser walkthroughs document what is proven and what remains pending. |

## Validation and approval gate

- make test passed: 1,460 tests. The backend suite includes temporary vector conversion and governed Snakemake export/static verification, permission failures, changed source/evidence, package integrity and path boundaries.
- make interface-validate and git diff --check passed.
- The production Chromium check passed nine interaction groups: Add ordering/scroll/search, drag/drop viewport retention, edited-plan stability, vertical/cancel behavior, paired review geometry/actions, three materials, Outcome facts, narrow layout and refresh/history recovery. It reproduced the scale-transition drift and 58%-width value defect before their fixes. Every browser API call used a fixture; external requests were blocked and live GIS calls were zero. See [browser regression](CHECKPOINT23_BROWSER_CHECK.md).
- The operator reported the host-configured live workflow working. This is operator-reported evidence, not an agent-run live database test. The manual acceptance CSV remains a template; fixture-only browser tests do not silently convert its live-model/database cases to PASS.
- Configuration, secrets, conversations, attempts, packages and local acceptance outputs remain ignored. No data operations, commits or pushes were performed by this coding turn.

The remaining gate for commit/push is operator review of the final changes and explicit authorization. Keep release/pilot live-model acceptance records distinct from commit readiness; any further observed defect remains a follow-up regression obligation.

No known failing automated check or reported-layout implementation blocker remains for the current checkpoint scope. Performance is implemented, but no browser frame-rate threshold has been measured here. Actual Snakemake engine execution, a single fresh-source execution including export before source completion, arbitrary output substitution and unrelated capability additions are not delivered by these export/static-verification blocks.

No live PostGIS/GeoServer data was modified by the coding agent. Temporary fixture conversion/export tests are separate from operator live-data acceptance.

Automated baseline for this review: make test passed (1,460 tests), interface typecheck/production build and diff checks passed. Ignore checks confirm .env, .secrets, conversations, attempts and exported packages remain excluded. Browser frame rate and manual acceptance are not claimed.
