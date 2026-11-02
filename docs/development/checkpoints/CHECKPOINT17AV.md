# Checkpoint 17AV — governed recipe release

Checkpoint 17AV connects the completed interface recipe lifecycle to the
existing immutable release store without pretending that a recipe-derived run
has planner-plan authority.

## Operator sequence

1. Open **Assurance** and select a stored recipe-derived trace.
2. Run and review the read-only Critic assessment.
3. Confirm and record the exact Critic result.
4. Enter a stable release ID and select **Assess release readiness**.
5. Review component completeness, findings, and the candidate SHA-256.
6. Confirm the exact candidate and select **Create exact release**.

The readiness action explicitly creates deterministic operational history when
it is absent, then reads and verifies the complete evidence chain. It does not
rerun the recipe, invoke a GIS tool, or create a release. Release creation
repeats the assessment and rejects a changed candidate digest before atomically
copying the exact component set into `releases/`.

## Release components

- immutable workflow recipe;
- append-only exact recipe approval;
- durable recipe-run result;
- recipe evidence and artifact lineage;
- adapted WorkflowTrace and deterministic report;
- immutable Critic result record; and
- correlated operational history.

The release assessor checks recipe IDs, recipe digests, approval IDs, run
status, embedded versus independently stored run results, trace/report hashes,
Critic evidence references, approval scope, validation status, and task
identity. Any mismatch fails closed.

## Local validation

```bash
.venv/bin/pytest tests/test_release_assessment.py \
  tests/test_release_storage.py \
  tests/test_operational_history_observers.py \
  tests/test_interface_api.py -q

cd interface
pnpm typecheck
pnpm build
```

For full regression coverage, run `make test` from the repository root.
