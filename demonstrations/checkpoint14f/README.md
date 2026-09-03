# Checkpoint 14F pilot demonstration

This fixed demonstration shows that local-model-assisted GIS work can be
constrained, reviewed, approved, executed, validated, traced and released.
It uses repository-owned inputs and trusted commands; generated run evidence
is intentionally excluded from Git.

## Presentation sequence

1. Run `make checkpoint14f-readiness`. The invalid-geometry fixture must fail
   only `invalid_geometry`, the clean fixture must pass, and the workflow input
   digest must remain stable.
2. Use the request in `DEMO.json` with `plan-task`. Save the validated Planner
   result beneath `plans/`; do not edit it after calculating its canonical
   digest.
3. Review the exact plan and approve only its PostGIS load and report steps.
4. Start `mcp-gis`, wait for its application-startup message, and execute the
   exact plan and approval through the isolated Executor. Restore
   `ENABLE_WRITE_TOOLS=false` immediately after execution.
5. Validate the trace, report and PostGIS checks. Record correlation-scoped
   operational history from those exact files.
6. Persist the separate Critic result. It may assess evidence, but it cannot
   change the deterministic workflow status.
7. Assess, create and independently inspect the six-component authoritative
   release. Pass paths relative to their declared roots. The SHA-256 of
   `RELEASE.json` must equal the digest in the release directory name.
8. Separately compile and approve the fixed vector-conversion recipe. Export
   it to Snakemake, run static validation, and run an isolated dry-run before
   any real replay.
9. For an approved replay, temporarily enable MCP writes, wait for readiness,
   execute the Snakemake DAG, verify its completion marker and output digest,
   and restore the disabled write default.

## Readiness command

```bash
make checkpoint14f-readiness
```

The command assesses the checked-in deterministic dirty-vector fixtures and
performs no regeneration. Its final result must contain:

```text
repository_ready: true
next_action: propose_workflow
model_called: false
approval_created: false
workflow_executed: false
filesystem_modified: false
database_modified: false
release_created: false
snakemake_invoked: false
```

## Safety checkpoints

- A model proposal is never an approval or executable authority.
- Approval binds the exact canonical plan or recipe digest and explicit write
  steps.
- MCP writes remain disabled except during a deliberate execution window.
- The dry-run must create neither GIS output nor a replay-completion marker.
- Workflow status comes from deterministic validation, not the Critic.
- Operational history excludes secrets, prompts and private model reasoning.
- A release is authoritative only after independent exact-file and digest
  verification.
- Generated plans, approvals, outputs, histories, Critic records, releases,
  recipe reviews and Snakemake exports remain outside version control.

## Demonstrated reference result

The presentation run completed with 12 passing PostGIS checks, five validated
operational events, a separate Critic record and a six-component release. The
release digest was
`6e2ee3ead89aa93cb791f07225e010104ed990e585a6c16d812ecfc57f7bf881`.
The separate Snakemake replay produced a validated GeoPackage and durable
digest-bound recipe evidence. These values document the reference run; a new
run is expected to have new timestamps, IDs and package digests.
