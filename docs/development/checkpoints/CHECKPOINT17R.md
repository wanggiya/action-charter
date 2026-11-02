# Checkpoint 17R — Independent recipe approval verification

Checkpoint 17R makes authority outcomes visually prominent and independently
verifies one append-only recipe approval before any execution control exists.

## Operator flow

1. Record an approve or deny decision through Checkpoint 17Q.
2. Read the large **Append-only evidence recorded** and **Nothing executed**
   outcome cards.
3. Select **Verify recorded decision**.
4. The loopback service reloads the immutable recipe and approval, recomputes
   the recipe digest, reruns deterministic policy, and verifies exact step
   scope, decision and expiry.

An approved verification proves only that the decision currently authorizes
the exact recipe scope. It does not execute a skill, tool, recipe or workflow.

## Boundary

- fixed recipe and approval roots only;
- canonical filenames and SHA-256 identities only;
- no browser-supplied approval scope;
- independent re-read and deterministic policy verification;
- no approval modification and no execution authority.

The next increment may prepare a deterministic execution preview, but actual
execution remains a later, separately reviewed authority boundary.
