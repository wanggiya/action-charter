# Checkpoint 17AW — governed Snakemake export

Checkpoint 17AW adds interface parity for the existing approved-recipe
Snakemake export commands. It deliberately stops before dry-run or replay.

## Interface sequence

1. Open a saved recipe and prepare its exact approval scope.
2. Record and independently verify an approval.
3. Select **Preview approved export** under **Snakemake export**.
4. Review the recipe identity, fixed three-file package, and export-plan digest.
5. Confirm that exact digest and select **Export and validate**.
6. Confirm the result says `EXPORTED · CONTRACT VALID`.

The preview is read-only. The confirmed action creates a directory under
`snakemake-exports/` containing only:

- `Snakefile`;
- `geoagent-replay.json`; and
- `snakemake-export-manifest.json`.

The backend immediately invokes the existing static contract validator. It
checks containment, the exact file set, size limits, canonical workflow
content, configuration and manifest identities, digests, and the trusted replay
entrypoint. Neither action invokes Snakemake or executes a recipe.

## CLI parity

```bash
.venv/bin/geoagent plan-snakemake-export \
  workflow-recipes/<recipe>.json approvals/<approval>.json --pretty

.venv/bin/geoagent export-approved-recipe-snakemake \
  workflow-recipes/<recipe>.json approvals/<approval>.json --pretty

.venv/bin/geoagent validate-snakemake-export \
  snakemake-exports/<export-directory> --pretty
```

## Validation

```bash
.venv/bin/pytest tests/test_interface_api.py \
  tests/test_snakemake_export_planner.py \
  tests/test_snakemake_export_generator.py \
  tests/test_snakemake_export_contracts.py -q

cd interface
pnpm typecheck
pnpm build
```
