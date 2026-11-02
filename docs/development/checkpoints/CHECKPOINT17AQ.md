# Checkpoint 17AQ — deterministic Critic evidence workspace

Checkpoint 17AQ exposes the existing deterministic Critic evidence builder in
the guided interface. The **Assurance** workspace inventories bounded
`WorkflowTrace` JSON files and matching Markdown reports, revalidates each pair,
and presents validation state, approval completeness, evidence gaps, warnings,
and SHA-256 references.

## Authority boundary

This checkpoint is deliberately read-only:

- no model is called;
- no Critic assessment or immutable Critic result is created;
- no release is created;
- no tool or recipe is executed; and
- invalid or incomplete evidence is never converted into a success claim.

Recipe-run evidence is not silently treated as a `WorkflowTrace`. A later
checkpoint must add and validate an explicit adapter before newly executed
interface recipes can enter the Critic workflow.

## Validate

Start the source-pinned interface API and frontend, open **Assurance**, and
confirm that known trace/report pairs appear. The workspace must prominently
state `READ-ONLY ASSURANCE`, `no model call`, and `no release`.

```bash
curl -fsS http://127.0.0.1:8765/api/v1/critic-evidence | python3 -m json.tool
make test
cd interface && pnpm build
```
