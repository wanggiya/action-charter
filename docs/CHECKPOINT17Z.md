# Checkpoint 17Z — append-only plan decision

Checkpoint 17Z records one explicit human approve or deny decision for an exact
prepared Planner-result request.

The reviewed-save transition is idempotent for an already stored, exactly equivalent
validated result. It revalidates the existing artifact and returns
`already_stored` without changing its modification time, allowing the browser
to continue to approval preparation after refresh or regeneration. An unsafe,
invalid, or non-equivalent existing artifact still fails closed.

The interface accepts bounded approver and reason text, an optional one-to-1440
minute validity period, and an explicit approved or denied selection. The
server reprepares the request, reloads and rehashes the immutable plan, reruns
deterministic policy, compares the request digest, and derives step scope
server-side before using the existing append-only approval service.

Read-only plans cannot create meaningless approval evidence. Decisions are
available only when the trusted plan contains approval-required steps. A denial
is displayed as denied rather than failed. Both decisions write evidence only;
nothing is executed.

## Manual test request

Select only `convert_vector` and use:

```text
Create exactly one step using convert_vector to convert data/input/sample_points.geojson to data/output/planner_approval_test.gpkg. Set requires_approval to true and validation_required to true. Plan only; do not execute.
```

Generate, review, save, and prepare the request. Enter an approver and reason,
then record either decision. Confirm the interface shows `APPROVED` or `DENIED`
and `Append-only evidence created · nothing executed`.

## Validate

```bash
.venv/bin/pytest -q tests/test_interface_api.py
corepack pnpm@10.17.1 --dir interface build
```

## Next

Independently verify the recorded plan decision before exposing any execution
preview or Executor action.
