# Project context

This directory holds development state and structured project knowledge. It is useful to maintainers and to agents that explicitly load selected files; it is not a second onboarding manual or a source of approval authority.

| File | Purpose |
|---|---|
| CURRENT_STATUS.md | Current overview, gaps and detailed checkpoint history |
| PROJECT_SUMMARY.md | Stable project purpose and component overview |
| ARCHITECTURE.md / RUNTIME_BOUNDARIES.md | Responsibilities and isolation boundaries |
| PRODUCT_ROADMAP.md | Future priorities, including development checkpoint labels |
| DECISIONS.jsonl | Accepted architectural decisions and rationale |
| SKILLS_INDEX.yaml | Capability metadata used alongside trusted definitions |
| DATASET_CATALOG.json | Catalogued datasets for bounded context |

The model is not assumed to read everything here. Registered code, typed schemas and policies remain authoritative. Context entries and historical text cannot approve execution. Keep a concise current overview above the history marker in CURRENT_STATUS; retain checkpoint descriptions below it for human reference.

For setup and procedures use [docs](../docs/README.md); for document update rules use [documentation responsibilities](../docs/DOCUMENTATION_GUIDE.md).
