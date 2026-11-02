# Checkpoint 17AR — recipe-run trace adaptation preview

Checkpoint 17AR adds a deterministic, non-writing bridge from completed
interface recipe runs to the `WorkflowTrace` contract used by the Critic.

The Assurance workspace now correlates each immutable recipe-evidence artifact
with its exact recipe, approved authority, run result, and durable interface
execution timing. A candidate is shown as Critic-compatible only when all
identities, digests, statuses, steps, and timestamps agree.

## Contract correction

`WorkflowTrace` now carries an optional `recipe_sha256` alongside the existing
optional `plan_sha256`. Recipe authority is therefore represented honestly; a
recipe digest is never placed in a field named `plan_sha256`. Critic approval
completeness accepts either exact authority digest with an approval ID and
approved step scope.

Generic recipe validation is marked with `validation_kind: recipe`. This keeps
the existing PostGIS-specific evidence checks for PostGIS traces while avoiding
false missing-field findings for valid vector or raster recipe runs.

## Authority boundary

- adaptation occurs in memory;
- temporary files are used only to prove compatibility with the existing
  Critic evidence builder and are deleted immediately;
- no trace or report is stored;
- no model is called;
- no Critic result or release is created; and
- older runs without exact durable recipe identity remain not adaptable.

## Validate

```bash
curl -fsS http://127.0.0.1:8765/api/v1/critic-evidence \
  | python3 -m json.tool
make test
cd interface && pnpm build
```

In the interface, open **Assurance** and inspect **Recipe-run trace
candidates**. Recent identity-complete executions should show
`Critic-compatible preview`; incomplete legacy runs should explain why they
cannot be adapted.
