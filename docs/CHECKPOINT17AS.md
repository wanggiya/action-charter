# Checkpoint 17AS — reviewed adapted-trace persistence

Checkpoint 17AS adds an explicit evidence-persistence boundary to Assurance.
The operator selects one Critic-compatible recipe-run candidate, reviews its
exact adapted-trace SHA-256, confirms that scope, and requests immutable storage.

The loopback service rebuilds the candidate from the current immutable recipe,
approval, recipe evidence, and durable timing records. It compares the rebuilt
digest with the reviewed digest before exclusively creating:

- `traces/<task_id>.json`; and
- `reports/<task_id>.md`.

The stored pair is immediately reopened through the existing deterministic
Critic evidence builder. Existing targets, stale digests, unsafe roots, missing
source evidence, and contradictory identities fail closed.

## Authority boundary

This operation stores evidence only. It does not:

- invoke the Critic model;
- record a Critic result;
- declare release readiness;
- create a release; or
- execute a recipe or tool.

## Interface validation

1. Restart the source-pinned interface API and frontend.
2. Open **Assurance**.
3. Use the **Store adapted trace** drawer.
4. Select a `Critic-compatible preview`.
5. Review the displayed adapted-trace SHA-256.
6. Check the exact-review confirmation.
7. Click **Store trace and report**.
8. Confirm `TRACE AND REPORT STORED` and the explicit no-Critic/no-release
   statement.

The same candidate cannot be stored twice.

The Critic evidence header scrolls with the Assurance content. The persistence
drawer remains available at the lower-right because it is the active review
control, but it does not make the large workspace header sticky. Its minus
button collapses it to a compact **Trace review** handle; the expand button
restores it without losing the selected candidate or review confirmation.

```bash
make test
cd interface && pnpm build
```
