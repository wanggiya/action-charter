# Checkpoint 17K — Trusted template proposal bridge

Checkpoint 17K exposes the existing CLI recipe-template catalog to the guided
interface without creating a second template authority.

## Existing source of truth

`context/RECIPE_TEMPLATES.yaml` remains the trusted, versioned catalog. The
existing CLI validates it and emits the browser runtime projection:

```bash
mkdir -p interface/public/runtime
.venv/bin/geoagent recipe-template-catalog \
  --project-root . \
  --pretty > interface/public/runtime/recipe-templates.json
```

The generated JSON is ignored by Git. The browser caps its size, validates its
schema and accepts it only when the backend reports that catalog validation
passed and neither file modification nor execution occurred.

## Interface behavior

The top application bar now exposes a dedicated **Templates** button. It opens
a focused workspace above the graph rather than mixing template selection with
the selected-node Inspector. The workspace first distinguishes workflow,
recipe and skill, then lets the operator:

- select one trusted recipe template;
- collect its required parameters and an operator request;
- render the catalog step/dependency graph as an uncommitted proposal;
- download a strictly validated `RecipeProposal` JSON document compatible with
  the existing CLI proposal compiler.

Each selectable recipe card displays its step count, included skills and
required inputs so users do not mistake one skill for the complete workflow.

The current trusted templates cover vector inspection, raster inspection,
raster conversion, vector conversion and vector-to-PostGIS processing.

The interface rejects proposal download when required values are absent. If an
operator structurally edits a template graph, download is also withheld because
the current CLI `RecipeProposal` contract represents a trusted template choice
and parameters—not arbitrary graph topology. This prevents the visible graph
from silently disagreeing with the downloaded proposal.

## CLI compatibility check

Until the authenticated local interface API exists, a downloaded proposal can
be copied under an ignored proposal root and compiled without saving or running:

```bash
mkdir -p recipe-proposals.local
cp ~/Downloads/vector_to_postgis-proposal.json recipe-proposals.local/
.venv/bin/geoagent compile-recipe-proposal \
  recipe-proposals.local/vector_to_postgis-proposal.json \
  --proposal-root recipe-proposals.local \
  --project-root . \
  --pretty
```

Compilation remains deterministic and non-executing. Recipe storage, approval,
execution, evidence and Snakemake export retain their existing separate gates.

## What comes next

The next slice should introduce a loopback-only, typed interface service that
accepts this exact proposal contract and returns deterministic assessment and
compilation results. Later slices can expose explicit save, policy, approval,
execution and evidence operations. The browser must never receive arbitrary
shell, filesystem, SQL, package-installation or network authority.

The CLI/interface equivalence strategy is documented in
`docs/CORE_CONCEPTS.md`: establish a governed CLI case, create a comparable
interface case with different safe identifiers and targets, then compare their
normalized contracts, gates, validation and evidence.

## Validation

```bash
cd interface
corepack pnpm build
cd ..
.venv/bin/pytest -q
git diff --check
```
