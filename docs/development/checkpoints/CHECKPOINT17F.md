# Checkpoint 17F — Trace-derived workflow topology

Checkpoint 17F makes validated runs look like the work they actually recorded.
The projector creates a node for each governed tool operation rather than
always returning one generic tool-boundary node.

## Behavior

- zero to twenty recorded operations are accepted;
- the union of recorded calls and results determines the visible sequence;
- controlled identifiers become readable titles;
- unsafe identifiers become neutral numbered labels;
- arguments and result payloads never enter the projection;
- graph edges connect Executor through each operation into Validation;
- canvas bounds adapt to real nodes in horizontal and vertical layouts.
- process nodes use action titles and embed the responsible user, agent,
  deterministic service or tool boundary;
- the minimap mirrors node category, status color and shape;
- the mouse wheel zooms, while Shift plus the wheel scrolls horizontally;
- every timeline stage is selectable, with its first and last stages anchored
  to the ends of the timeline.

The sequence records trace order. It does not claim data dependency beyond the
information present in the current trace schema. A future plan projection will
use explicit plan-step and dependency identities.

Failure-stage placement and live running timestamps require the later governed
execution-state contract. The timeline already uses node status classes and is
structured to receive those states without becoming an execution authority.

## Export and view

```bash
.venv/bin/geoagent export-interface-workflows \
  --trace-root traces \
  --output-root interface/public/runtime \
  --pretty

cd interface
pnpm dev
```

Choose runs with different tool histories and compare their nodes, link counts
and canvas lengths. Switch between horizontal and vertical layouts and use Fit.

## Validation

```bash
.venv/bin/pytest tests/test_interface_projection.py -q

cd interface
pnpm install --frozen-lockfile
pnpm build
```
