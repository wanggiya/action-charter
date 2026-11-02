# Checkpoint 17AY — complete PostGIS interface vertical slice

Checkpoint 17AY closes a gap discovered during final operator acceptance. The
Planner could produce and approve the established four-step PostGIS plan, but
the Planner-to-recipe bridge rejected three of its skills because the generic
recipe dispatcher supported only file inspection and conversion.

The governed recipe boundary now allowlists the existing fixed sequence:

1. `inspect_vector`;
2. `load_vector_to_postgis`;
3. `validate_postgis_layer`; and
4. `generate_report`.

The extension accepts only typed arguments and the exact registry entrypoints.
The load remains approval-gated, overwrite remains blocked, the target schema
remains allowlisted, and final success is withheld until the load's independent
PostGIS verifier passes. The explicit validation step performs an additional
read-only inspection. Report materialization remains deferred until the entire
validated run is assembled, when the existing immutable recipe-evidence
persistence boundary writes the authoritative report.

No arbitrary SQL, shell command, dynamic entrypoint, raw request body, or
browser-selected verifier is introduced. A failed execution after a database
write still requires inspection and a fresh target before retry.

Checkpoint 17 is complete only after one fresh operator-run PostGIS workflow
passes from Planner request through recipe compilation, separate recipe
approval, execution, deterministic validation, evidence, Critic review,
release, and Snakemake export.

## Operator acceptance

The fresh `checkpoint17_final_e2e_20260925_02` run completed through the
interface. Independent PostGIS inspection confirmed two rows, EPSG:4326, and
POINT geometry. The same governed run then completed its evidence, Critic,
immutable release, and Snakemake export path. Checkpoint 17 therefore satisfies
its guided-prototype acceptance boundary.
