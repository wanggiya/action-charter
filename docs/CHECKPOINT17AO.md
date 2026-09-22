# Checkpoint 17AO — actionable Planner rejection

Checkpoint 17AO preserves deterministic fail-closed planning while replacing an
opaque policy error with a safe actionable finding.

- Rejected model plans are never returned, saved, approved or executed.
- The loopback API returns a bounded failure code, policy finding, retry guidance
  and explicit negative authority claims.
- The Plan workspace highlights the rejection and offers an explicit retry after
  the operator reviews or clarifies the request.
- Validation policy remains unchanged; retry cannot bypass it.
