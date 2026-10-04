# Documentation responsibilities

## Audiences and ownership

| Document | Primary audience | Purpose | Keep out |
|---|---|---|---|
| Root README | New users, employers and contributors | Explain the product, current scope, setup and workflow; link detailed guides | Incremental checkpoint diary and outdated capability claims |
| docs/ | Operators and developers | Reproducible instructions, examples, troubleshooting, acceptance and design references | Unlabelled historical instructions presented as current |
| context/ | Maintainers and selected agent context consumers | Current state, architecture, catalogs and accepted decisions | Repeated onboarding and long historical narration in CURRENT_STATUS |
| CHANGELOG.md | Users and maintainers comparing changes | Summarize added, changed and fixed behavior over time | Setup manual or current authority definition |
| interface/README.md | Frontend developers | Frontend dependencies, framework and local debugging | Duplicated product overview or contradictory run claims |

These are audiences, not security boundaries. A human can read context files; an agent may consume selected documents. A document's location does not grant trust or permission. Schemas, registry policy and verification code enforce behavior.

## Why keep both docs and context?

A guide answers “How do I do this?” Current context answers “What is implemented, what is limited and what comes next?” They change for different reasons. Keep one authoritative explanation for each subject and link to it rather than maintaining competing copies. The Planner loads selected context files, not every file in these directories. Historical user/task text remains untrusted and cannot supply approval.

## Update rules

- Change user-facing behavior: update its guide, relevant README capability summary and CHANGELOG.
- Change an architectural decision: update architecture/decision records and affected contracts/guides.
- Finish implementation: replace the concise current status; preserve prior history separately.
- Introduce a limitation: state it in current status and the applicable operator guide.
- Add a development checkpoint: put its record in development documentation. Do not add its number to public flow diagrams or an onboarding paragraph.
- When actual behavior differs from a document, investigate the implementation and tests; documentation cannot override policy.

## Historical records

Existing CHECKPOINT*.md files are retained because they explain earlier changes, acceptance commands and decisions. They are development records, not the primary user guide. Some instructions describe a feature before later integration; read current status and current guides first. Avoid bulk renaming them because existing links refer to their names.

The former incremental README and status are preserved under docs/development/ as clearly labelled snapshots. CURRENT_STATUS now contains only current scope and next work. Checkpoint labels can remain in the roadmap, historical records and CHANGELOG for traceability. They should not appear in the public workflow topology.

The CHANGELOG is still development-oriented and checkpoint-labelled. Future release entries should group user-visible changes by release/version; preserve earlier entries rather than rewriting their history. A published release has not been created by this documentation cleanup.
