# Checkpoint 17AH — Planner recipe-save HTTP routing correction

The Planner recipe-save dispatch branch existed, but its path was omitted from
the POST allowlist, so requests returned `endpoint is not available` before
validation. The route is now admitted and covered through the real HTTP handler.

Exact repeated saves also remain idempotent: the server reloads and validates
the canonical recipe and resumes only when its digest matches, without rewrite.
