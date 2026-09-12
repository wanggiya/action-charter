# Guided interface product scope

The ActionCharter interface is intended to become the normal operating surface,
not a read-only companion to the CLI. The CLI remains for automation,
development, recovery and advanced operators.

## Target experience

1. The user describes a desired outcome and selects data.
2. The Planner proposes a typed workflow.
3. The interface renders it as an editable Blueprint-style node graph.
4. The user changes permitted parameters or requests a revision.
5. Deterministic policy highlights effects, risks and approval requirements.
6. Human approval binds to the exact proposal digest.
7. Governed execution reports queued, running, completed, failed and skipped
   nodes with start time, elapsed time and safe progress.
8. Validation, Critic review, evidence and outputs remain attached to the graph.

## Required coverage

| Area | Interface responsibility |
| --- | --- |
| Requests and context | Guided request composer, bounded input selection and contract expectations |
| Planning and policy | Proposed steps, dependencies, parameters, warnings and deterministic policy results |
| Approval | Exact digest, affected resources, required steps, expiry and explicit human decision |
| Vector and raster | Inspection, conversion, validation and safe previews using existing controlled adapters |
| Tabular data | Governed pandas capability after its typed adapter and policy contracts exist |
| PostGIS | Inspect, load, validate, compare, assess, promote, verify and rollback through existing boundaries |
| Recipes | Create, review, approve, execute and inspect reusable recipe evidence |
| Snakemake | Export, validate, dry-run and replay without requiring users to write commands |
| Skills | Browse active skills; propose, test, promote and verify candidate skills through Builder controls |
| Agents | Show Planner, Executor, Critic and Builder ownership, authority and activity |
| Evidence and reports | Safe structured previews, lineage, validation, Critic records and downloadable reports |
| Releases | Candidate/current state, promotion history, authoritative packages and rollback state |
| GeoServer | Existing bounded inspection and approval-gated publication first; broader administration later |
| Operations | Start time, elapsed time, node state, safe diagnostics, cancellation where supported and retry proposals |

## Checkpoint placement

This operating surface belongs to the Checkpoint 17 sequence. It will be built
in reviewable slices rather than one unsafe browser authority expansion.
Checkpoint 18 remains pilot operations and bounded memory after the guided
interface has a credible end-to-end path.

The browser never receives arbitrary shell, SQL, Python-package installation,
filesystem or network authority. User actions call typed backend contracts and
preserve plan, policy, exact approval, execution, validation and evidence
boundaries.
