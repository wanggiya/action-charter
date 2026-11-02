# Checkpoint 17E — Safe evidence previews

Checkpoint 17E adds expandable evidence cards to the read-only node inspector.
The cards expose useful reviewed metadata while preserving the projection
boundary established in Checkpoints 17B–17D.

## What appears

- validated trace status and redaction claim;
- plan presence, approved-step count and SHA-256 integrity metadata;
- approval presence without identity or rationale;
- deterministic validation presence and final classification;
- at most four recorded artifacts identified by basename only.

Each node carries at most eight cards and each card carries at most six bounded
facts. Python and browser schemas reject unknown fields and invalid categories,
states or digests. Older projections remain valid and show a prompt to
regenerate evidence previews.

## Export and view

```bash
.venv/bin/geoagent export-interface-workflows \
  --trace-root traces \
  --output-root interface/public/runtime \
  --pretty

cd interface
pnpm dev
```

Choose a run and select Planner, Human approval, Validation or Trace evidence.
Expand the cards in the Evidence section.

## Trust boundary

This is not a generic JSON viewer. It does not expose original requests,
context text, approval identity, tool arguments or results, absolute artifact
paths, unrestricted messages, secrets, credentials or private model reasoning.
Full artifact content requires a future artifact-family-specific sanitizer.
The browser still has no approval, execution, filesystem or arbitrary network
authority.

## Validation

```bash
.venv/bin/pytest tests/test_interface_projection.py -q

cd interface
pnpm install --frozen-lockfile
pnpm build
```
