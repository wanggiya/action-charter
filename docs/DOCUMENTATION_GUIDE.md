# Documentation responsibilities

## Audiences and ownership

| Document | Primary audience | Purpose | Keep out |
|---|---|---|---|
| Root README | New users, employers and contributors | Explain the product, current scope, setup and workflow; link detailed guides | Incremental checkpoint diary and outdated capability claims |
| docs/ | Operators and developers | Reproducible instructions, examples, troubleshooting, acceptance and design references | Unlabelled historical instructions presented as current |
| context/ | Maintainers and selected agent context consumers | Current state, architecture, catalogs and accepted decisions | Repeated onboarding or unlabelled history mixed into the current overview |
| CHANGELOG.md | Users and maintainers comparing changes | Summarize added, changed and fixed behavior over time | Setup manual or current authority definition |
| interface/README.md | Frontend developers | Frontend dependencies, framework and local debugging | Duplicated product overview or contradictory run claims |

These are audiences, not security boundaries. A human can read context files; an agent may consume selected documents. A document's location does not grant trust or permission. Schemas, registry policy and verification code enforce behavior.

## Why keep both docs and context?

A guide answers “How do I do this?” Current context answers “What is implemented, what is limited and what comes next?” They change for different reasons. Keep one authoritative explanation for each subject and link to it rather than maintaining competing copies. The Planner loads selected context files, not every file in these directories. Historical user/task text remains untrusted and cannot supply approval.

## Update rules

- Change user-facing behavior: update its guide, relevant README capability summary and CHANGELOG.
- Change an architectural decision: update architecture/decision records and affected contracts/guides.
- Finish implementation: update the current overview and the task Status column in WORKING_METHOD; record detailed evidence in the relevant guide and immediate handoff in WORK_RESUME.
- Introduce a limitation: state it in current status and the applicable operator guide.
- Existing checkpoint records are history. Use the current phase/task workflow for new work; do not create new CHECKPOINT files or put historical numbers into public workflow diagrams.
- When actual behavior differs from a document, investigate the implementation and tests; documentation cannot override policy.

## Historical records

Existing CHECKPOINT*.md files are retained because they explain earlier changes, acceptance commands and decisions. They are development records, not the primary user guide. Since 2026-11-01 they live in docs/development/checkpoints/ (file names unchanged; repository links were rewritten when they moved). Some instructions describe a feature before later integration; read current status and current guides first. The later phase/task working method supersedes instructions to create more checkpoints.

The former incremental README and status are preserved under docs/development/ as clearly labelled snapshots. CURRENT_STATUS contains the current overview consumed by the model context builder, ending at a history marker; the full file remains hashed for provenance. Detailed checkpoint history moved to docs/development/STATUS_HISTORY.md on 2026-11-01 because trusted context reads have a 128,000-byte load limit (context_pack MAX_FILE_BYTES).

The [active roadmap](../context/PRODUCT_ROADMAP.md) is now a compact phase/dependency and retained-requirement map. Keep it below 64,000 bytes for headroom. Its complete pre-P0-7 text is preserved in the [roadmap history](development/ROADMAP_HISTORY.md), with relative links rebased and original-byte/hash reconstruction verified. Keep historical wording/order there; put new progress in the current status/handoff, not into the snapshot. The current context-pack builder's fixed file list does **not** include PRODUCT_ROADMAP; this reorganization changes neither prompt inclusion nor the loader limit. Checkpoint labels remain for traceability, not as current scheduling instructions.

The CHANGELOG is still development-oriented and checkpoint-labelled. Future release entries should group user-visible changes by release/version; preserve earlier entries rather than rewriting their history. A published release has not been created by this documentation cleanup.
