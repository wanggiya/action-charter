# Cross-chat memory — deferred until checkpoint 30 or later

Recorded: 2026-10-14. The operator explicitly deferred this capability for several checkpoints. This is a backlog decision, not permission to implement sharing.

## Current boundary

Each conversation is one task. Saved transcript excerpts and its current workflow can enter that conversation's planning context. Other conversations are not automatically retrieved or pooled. Switching chats opens the selected chat's own state; it does not merge histories. Existing project guidance, operation catalogs and saved workflow artifacts remain separate shared project resources; this is not a multi-user access-control boundary.

Do not add cross-chat retrieval, shared summaries, automatic transcript indexing across conversations, sharing switches, or background promotion to project memory in checkpoints 26–29.

## Later dependency order

| Checkpoint | Priority before sharing | Measurable acceptance |
| --- | --- | --- |
| 26 | Finish single-conversation clarity/memory and orchestration/recovery | History OFF excludes old messages without deleting the transcript; actual request context is inspectable; stale authority cannot resume writes |
| 27 | Output visualization, public-data demo and laptop/PC prototype preparation | Spatial/tabular/combined fixture journeys and supported setup checks pass; no publication implied |
| 28 — proposed | Operational pilot feedback and measured resource budgets | Document actual time/memory/error behavior for representative supported workflows; bounds remain usable on supported laptops |
| 29 — proposed | Single-conversation retention/privacy lifecycle | Source-linked correction, retention/export/deletion and restart behavior are verified; changes to one chat do not change another; no cross-chat retrieval |
| 30 or later — decision gate | Reconsider explicitly selected shared knowledge only | Requires a new operator decision and reviewed design; remains disabled by default until implemented and accepted |

28–30 are proposed later scopes, not delivered capabilities. They do not move existing checkpoint history or authorize live-data changes, Git actions or publication.

## Discussion reserved for the later gate

Prefer explicitly shared decisions, preferences or reviewed method templates over pooling entire transcripts. Any future entry should retain its originating chat/turn, scope, freshness and supersession/revocation state. The destination context should explain why an entry was selected. Revoked, expired, conflicting or unrelated entries must not enter another chat automatically. Historical approvals never become shared execution authority.

No implementation, dependency installation or background agent is part of this decision record.
