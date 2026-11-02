# Checkpoint 17V — durable execution attempt browser

Checkpoint 17V makes the durable progress introduced in 17U discoverable after
the browser or local interface API has been restarted.

## Implemented

- `GET /api/v1/executions` returns at most 200 durable attempt summaries from
  the fixed `workflow-state/interface-executions/` root.
- The inventory rejects symlink roots, symlink artifacts and malformed artifact
  names.
- New progress records include immutable recipe identity and exact step
  dependencies in addition to live status.
- A top-level **Runs** workspace shows status, start and finish times, step
  count, interruption or failure location, and the execution-preview digest.
- Selecting an eligible attempt reloads its exact progress record and rebuilds
  the run-specific read-only graph.
- Legacy records that lack sufficient recipe identity remain visible but cannot
  create a misleading graph.

## Authority boundary

Inventory and reopening are read-only. They accept no command, recipe mutation,
approval decision, target path or retry request. Reopening an attempt cannot
resume, approve, retry or execute it. An interrupted write remains fail-closed
and requires separate inspection and a future explicitly governed retry flow.

## Validation

Focused interface API tests cover durable inventory projection and existing
restart/interruption behavior. The full Python suite and frontend production
build remain the release checks for the cumulative checkpoint package.
