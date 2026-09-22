# Interface and CLI parity

The interface must expose governed workflows, not a browser shell. CLI parity
therefore means that the same domain services, policies, approvals, validators
and evidence paths are reachable through typed interface operations.

| Workflow family | Current interface status | Next authority increment |
| --- | --- | --- |
| Recipe templates, compilation and storage | Available | Broader recipe editing |
| Recipe approval, verification and execution | Available | Governed retry |
| Execution progress and history | Available | Full artifact inspection |
| Planner Agent and configured model | Planning through restart-safe verified authority and fixed-slice preview available | Expand typed Executor skill support, then exact execution |
| Plan approval and executor | Not yet available | Digest-bound plan approval |
| Critic and release | Stored evidence inspection, trace adaptation and persistence, and explicit validated in-memory model critique available; result recording and release unavailable | Recorded critique and release authority |
| Vector and raster operations | Available through registered recipe skills | Add remaining format profiles |
| PostGIS load/inspect/change/promotion/rollback | Partially available through recipes | Dedicated governed workspaces |
| GeoServer inspect/publish/verify | Backend and CLI available | Interface workspace later |
| Snakemake export and validation | Not yet available | Approved-recipe export workflow |
| Skill scaffold/contract/candidate/promotion | Not yet available | Builder workspace with offline tests |
| Builder bundle review/promotion/activation | Not yet available | Multi-stage builder governance |
| Schema compatibility and migration | Not yet available | Read-only assessment first |
| Workflow state, resume, history and releases | Runs partially available | Critic/release integration |

## Required sequence

1. Finish Planner → reviewed plan → approval → executor → critic → release.
2. Add Snakemake export and validation for an approved recipe.
3. Add dedicated PostGIS and existing GeoServer governed workspaces.
4. Add skill and builder creation, offline test, review, promotion and activation.
5. Expand data profiles in Checkpoint 18, including tabular CSV/Pandas support.

Every mutation remains disabled by default, requires the same approval as its
CLI equivalent, and must produce deterministic validation and durable evidence.

Planner skill discovery uses a searchable trusted catalog. Request-based
recommendations help discovery as the registry grows, but recommendations do
not grant authority; the backend receives and independently validates only the
operator's explicit selected-skill IDs.
