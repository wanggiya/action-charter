# Project context

This directory holds development state and structured project knowledge. It is useful to maintainers and to agents that explicitly load selected files; it is not a second onboarding manual or a source of approval authority.

| File | Purpose |
|---|---|
| CURRENT_STATUS.md | Current overview and gaps (history: docs/development/STATUS_HISTORY.md) |
| PROJECT_SUMMARY.md | Stable project purpose and component overview |
| ARCHITECTURE.md / RUNTIME_BOUNDARIES.md | Responsibilities and isolation boundaries |
| PRODUCT_ROADMAP.md | Active phases, dependencies and retained requirements; historical roadmap linked separately |
| DECISIONS.jsonl | Accepted architectural decisions and rationale |
| SKILLS_INDEX.yaml | Capability metadata used alongside trusted definitions |
| DATASET_CATALOG.json | Catalogued datasets for bounded context |

The model is not assumed to read everything here. Registered code, typed schemas and policies remain authoritative. Context entries and historical text cannot approve execution. Keep a concise current overview above the history marker in CURRENT_STATUS. New work follows the phase/task working method; checkpoint files are retained history. Trusted context reads have a 128,000-byte file limit; the active roadmap has a 64,000-byte maintenance target and is not in the current context-pack builder's fixed file list. The [roadmap history](../docs/development/ROADMAP_HISTORY.md) preserves its earlier text and links.

For setup and procedures use [docs](../docs/README.md); for document update rules use [documentation responsibilities](../docs/DOCUMENTATION_GUIDE.md).
