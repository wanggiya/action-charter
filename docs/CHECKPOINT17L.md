# Checkpoint 17L — CLI/interface parity baseline

Checkpoint 17L freezes one safe, versioned CLI input before the interface gains
backend compilation controls. This gives both surfaces the same proposal and a
normalized result to compare.

## Versioned inputs and generated outputs

The following files belong in Git:

- `context/RECIPE_TEMPLATES.yaml`: the trusted recipe-template source;
- `examples/interface-parity/checkpoint17l-vector-conversion-proposal.json`:
  the non-secret, non-executing parity proposal;
- tests and this runbook.

The following files remain generated and ignored:

- `interface/public/runtime/recipe-templates.json`;
- compilation responses, approvals, run state, evidence and output datasets;
- downloaded browser proposals until deliberately reviewed as fixtures.

## Phase 1: validate and compile through the CLI

Run from the repository root:

```bash
.venv/bin/geoagent recipe-template-catalog --project-root . --pretty \
  > /tmp/actioncharter-checkpoint17l-catalog.json

.venv/bin/geoagent compile-recipe-proposal \
  examples/interface-parity/checkpoint17l-vector-conversion-proposal.json \
  --proposal-root examples/interface-parity \
  --project-root . \
  --pretty > /tmp/actioncharter-checkpoint17l-compiled.json
```

Check the bounded claims without relying on `jq`:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

catalog = json.loads(Path("/tmp/actioncharter-checkpoint17l-catalog.json").read_text())
compiled = json.loads(Path("/tmp/actioncharter-checkpoint17l-compiled.json").read_text())

assert catalog["catalog_validated"] is True
assert catalog["execution_performed"] is False
assert compiled["compilation_performed"] is True
assert compiled["recipe_saved"] is False
assert compiled["approval_performed"] is False
assert compiled["execution_performed"] is False
assert [step["skill_id"] for step in compiled["recipe"]["steps"]] == [
    "inspect_vector",
    "convert_vector",
]
assert compiled["recipe_validation"]["valid"] is True
print("Checkpoint 17L CLI compilation baseline: PASS")
PY
```

This phase intentionally stops before save, approval or execution. Compilation
is deterministic and non-mutating, so it is the correct first backend operation
to expose through the interface.

## Phase 2: repeat through the interface

The next interface service must accept the exact `RecipeProposal` contract and
return the same normalized compilation facts:

- selected template and ordered skill steps;
- dependencies and resolved parameters;
- recipe-policy validity;
- approval-required and validation-required step IDs;
- explicit `recipe_saved=false`, `approval_performed=false` and
  `execution_performed=false` claims.

The interface case may use a different `recipe_id_hint` and output filename,
but it must not silently change the selected template or parameters.

## Later phases

After compilation parity passes, add separate typed controls for save, plan or
policy review, exact approval, execution progress, validation and evidence.
Each control must call the existing domain service rather than shelling out to
the CLI, and each authority increase requires its own tests and visible gate.

## Validation

```bash
cd interface
corepack pnpm build
cd ..
.venv/bin/pytest -q
git diff --check
```
