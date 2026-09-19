# Checkpoint 17AC — restart-safe plan and decision restoration

Checkpoint 17AC adds a bounded validated inventory of immutable Planner results
and their matching append-only decisions. The Plan workspace shows recent saved
plans, their timestamps and decision counts. Selecting one reloads the complete
typed Planner result, reprepares exact approval scope, and restores the latest
recorded decision for independent verification.

The inventory is read-only, capped at 200 plans and 500 decisions, rejects
symlinks and digest/filename mismatch, and performs no execution. Restoration
does not trust an old verification claim: the operator must verify the restored
decision again before an envelope preview.

This prevents model regeneration and duplicate approval records merely to
continue after a browser or API restart.

The inventory is a compact collapsed section by default. It expands into a
vertically scrolling list, supports newest/oldest and A–Z/Z–A ordering, enlarges
timestamp and decision-count metadata, and exposes decision type, step scope,
and time in each card's hover information. Selection is immediate, highlighted,
and collapses the navigator after successful restoration.
