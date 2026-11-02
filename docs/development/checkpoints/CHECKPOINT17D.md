# Checkpoint 17D — Evidence-backed node inspector

Checkpoint 17D turns the existing read-only node inspector into a useful view
of validated workflow evidence. Selecting a node shows facts projected by the
trusted Python boundary rather than interpreting raw traces in the browser.

## Export and inspect

```bash
.venv/bin/geoagent export-interface-workflows \
  --trace-root traces \
  --output-root interface/public/runtime \
  --pretty

cd interface
pnpm dev
```

Refresh the page, choose a run, and select each node. Older generated runtime
files do not contain the new detail records, so regenerate them after applying
this checkpoint.

## Projected detail contract

Each node may contain:

- one summary of at most 240 characters;
- at most ten label/value aggregate facts;
- normalized start and finish timestamps plus a non-negative duration;
- at most ten safe findings using bounded stage and code identifiers.

Both Pydantic and Zod reject unknown fields and enforce the collection and
string bounds. The interface also resets stale selection when switching runs,
so the inspector always describes a node in the graph currently displayed.

## Information deliberately excluded

- original request and context text;
- tool arguments, result payloads and unrestricted error messages;
- approval identity and approval rationale;
- absolute or private artifact paths;
- credentials, secret values and private model reasoning.

This checkpoint adds no approval, execution, filesystem, database, network or
package-installation authority to the browser. Artifact navigation, mobile
inspector sheets and proposal-only graph editing remain later interface work.

## Validation

```bash
.venv/bin/pytest tests/test_interface_projection.py -q

cd interface
pnpm install --frozen-lockfile
pnpm build
```
