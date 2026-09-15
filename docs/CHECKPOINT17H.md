# Checkpoint 17H — Typed graph lanes and connections

Checkpoint 17H distinguishes interaction and governance from data movement.
Agents no longer appear to be interchangeable with the tools they control.

## Edge contract

| Edge | Meaning | Presentation |
| --- | --- | --- |
| Control | User/agent interaction | Solid off-white, arrowed |
| Governance | Policy or approval decision | Dashed amber, arrowed |
| Tool | Bounded Executor-to-tool relationship | Dashed teal, no control arrow |
| Data | Typed tool input/result movement | Solid cyan, no control arrow |
| Evidence | Validated record production | Dotted off-white |

Every projected edge has a bounded label. The browser accepts older runtime
files and derives a deterministic display type, but newly exported projections
must satisfy the strict Python edge contract.

## Lanes and ownership

In horizontal mode, recorded User, Planner, approval and Executor activity
occupies the upper control lane. Referenced Input Data sits beside the request
and enters the Planner through a circular data socket. Executor connects only
to the first recorded operation; operation nodes then follow recorded trace
order and only the last operation connects to validation. Ownership frames
retain their meaning across both orientations.

The lane view contains only components supported by trace fields. Input Data,
Planner, approval, Executor and validation are omitted when their corresponding
context, digest, approval, operation/failure or validation record is absent.
Tool payloads, input paths and input contents remain excluded.

Operation order is the order recorded by the versioned WorkflowTrace mapping,
consistent with the earlier 17F contract. The graph does not attach Executor
to every tool or attach every intermediate tool to validation.

Snakemake is shown only when the trace explicitly records a `snakemake`
runtime version or operation. The current WorkflowTrace schema has no separate
execution-engine field, so an older replay that omits that metadata cannot be
safely inferred from its task name.

## Socket contract

Planner and Executor nodes expose two visibly different connection families:

- hollow, white triangular sockets carry agent/control interaction;
- cyan circular sockets carry bounded data and tool relationships.

Input Data and tool nodes use circular sockets. Tools cannot interrupt the
agent interaction path, and tool/data edges never use control arrows.

Sockets follow the selected layout axis: they sit just inside left/right node sides in
horizontal mode and top/bottom sides in vertical mode. Every connection is
shape-compatible at both ends. Control connects triangle to triangle, tool or
data connects circle to circle, governance connects diamond to diamond, and
evidence connects square to square. All sockets are hollow and render above
their connection lines.

The header exposes run-specific input-reference and tool counts. Runs may
share the same governance skeleton, but their safe tool names, counts, states,
findings, evidence and correlation identity remain trace-derived.

Catalog-selected runs never silently fall back to the demonstration graph. A
missing, stale or invalid runtime projection produces an explicit re-export
notice so two broken selections cannot masquerade as the same workflow.

The minimap uses outline-only nodes and thin connections. The graph viewport
has no decorative rounded frame competing with the workspace. Both the zoom
controls and edge legend have dedicated drag handles so they can be moved away
from graph content.

After installing a new projection contract, regenerate ignored runtime files:

```bash
.venv/bin/geoagent export-interface-workflows \
  --trace-root traces \
  --output-root interface/public/runtime
```

## Interaction boundary

Completed traces remain fixed evidence views. Empty canvas space can be panned,
but nodes cannot be repositioned. Future proposal mode may persist node layout
separately and reconnect only schema-compatible sockets; any semantic edit must
produce a new proposal and digest before approval.

## Validate

```bash
.venv/bin/pytest tests/test_interface_projection.py -q

cd interface
pnpm install --frozen-lockfile
pnpm build
```
