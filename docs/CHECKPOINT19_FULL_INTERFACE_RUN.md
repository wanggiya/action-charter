# Checkpoint 19 full interface acceptance — PostGIS

This run checks the visible path from a fresh task through a real governed PostGIS load, deterministic validation, durable evidence, Critic assessment, release, and static Snakemake export. Use a **fresh table name**; the example below is `checkpoint19_ui_e2e_20260926_01`. If it already exists, choose a new suffix before planning. Keep overwrite disabled. Record the actual status in the last column.

## Start the local interface

The **one launcher command** starts both the frontend and interface API. It does
not load `.env` or select a model or PostGIS credentials. The exports below are
configuration for this particular PostGIS test, not separate service-start
commands. Set them once in the shell, then run the launcher. If they are
already exported with these values, only the final `bash` command is needed.

Stop the existing launcher with Ctrl+C. In a new terminal at the repository root, run:

```bash
export MODEL_NAME=qwen3:4b-instruct
export MODEL_TIMEOUT_SECONDS=300
export MODEL_MAX_TOKENS=4096
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=geoagent
export POSTGRES_USER=geoagent
export POSTGRES_PASSWORD_FILE="$PWD/.secrets/postgis_password"
export ALLOWED_SCHEMAS=agent_sandbox
bash scripts/start_actioncharter.sh --enable-write-tools
```

For read-only interface use, the usual single command remains
`bash scripts/start_actioncharter.sh`. The `--enable-write-tools` flag is needed
only when deliberately testing an approved write operation. The launcher
defaults Ollama to `http://127.0.0.1:11434/v1` and PostGIS host/port to
`127.0.0.1:5432`; it does **not** supply your database name, user, password
file, allowed schema, model name, timeout, or token limit.

Use your actual local model name if different. The launcher should report `execution authority: ENABLED for bounded, separately approved recipes` and `overwrite authority: DISABLED`. It starts both API and frontend. Open `http://127.0.0.1:5173/`. Do not paste credentials or the password file contents into the interface.

## One fresh run

| # | Interface action | Expected evidence / boundary | Actual |
| --- | --- | --- | --- |
| 1 | Plan: select `data/input/sample_points.geojson` and allow only `inspect_vector`, `load_vector_to_postgis`, `validate_postgis_layer`, `generate_report`. | Four allowed skills; no execution. | |
| 2 | Enter the task request below, then **Generate validated plan**. | Exactly four ordered steps with the requested schema/table; load and report require approval; load and validation steps require validation. If rejected, inspect the finding instead of approving a different plan. | |
| 3 | **Review graph**; inspect the input, four steps, approval gate, and target. Return through **Run**. | The same validated plan reopens; no new plan generated. | |
| 4 | Review exact step arguments and digest, confirm review, **Save reviewed plan**. | Immutable plan stored; nothing approved or executed. | |
| 5 | **Prepare approval request**; inspect exact scope and record an explicit approval with operator name and reason. | Append-only plan decision; nothing executed. | |
| 6 | **Verify recorded decision**, then **Compile governed recipe**. | Independent verification passes; recipe candidate not yet stored or approved. | |
| 7 | Review recipe steps/digest and **Save reviewed recipe**; select **Review recipe approval scope** (or **Run**). | Stored recipe selected by digest; separate recipe approval remains. | |
| 8 | **Prepare approval request**, review steps, record recipe approval and independently verify it. | Recipe approval matches the stored recipe and is still valid. | |
| 9 | Preview exact execution; inspect schema/table and output/evidence destinations. Confirm the preview and click **Execute exact approved preview** once. | Live progress identifies each step; final status `validated_success`; run/evidence/report paths appear. | |
| 10 | **Check outcome**; open the new run. | Durable attempt and step results match the live result; no second execution. | |
| 11 | Advanced → **Assurance**: select this run's adaptable candidate, review digest, **Store trace and report**. | Stored Critic-compatible trace/report; no Critic call yet. | |
| 12 | Select the stored trace, **Run read-only Critic**, inspect assessment, then **Record exact Critic result** after confirming its digest. | Immutable Critic record; no release or new execution. | |
| 13 | Enter a fresh release ID, **Assess release readiness**, review the exact candidate, then **Create exact release**. | Release ready and immutable; no tools rerun. | |
| 14 | Return to the selected approved recipe, **Preview approved export**, review the digest, then **Export and validate**. | Snakefile, replay config, and manifest pass static contract validation; Snakemake and recipe are not run again. | |

Task request for step 2 (replace the table name consistently if needed):

> Create exactly four ordered steps with IDs step_1 through step_4, and no other skills. step_1: inspect_vector with arguments {"path":"data/input/sample_points.geojson"}, requires_approval=false, validation_required=false. step_2: load_vector_to_postgis with arguments {"path":"data/input/sample_points.geojson","target_schema":"agent_sandbox","target_table":"checkpoint19_ui_e2e_20260926_01"}, requires_approval=true, validation_required=true. step_3: validate_postgis_layer with arguments {"target_schema":"agent_sandbox","target_table":"checkpoint19_ui_e2e_20260926_01"}, requires_approval=false, validation_required=true. step_4: generate_report with arguments {"task_id":"checkpoint19_ui_e2e_20260926_01"}, requires_approval=true, validation_required=false. Keep this order and use the exact arguments and flags. Plan only; do not execute.

The Planner's deterministic policy treats `generate_report` as an evidence
write and requires approval, and it requires `validation_required=true` for
`validate_postgis_layer`. Both gates must appear in the reviewed plan. The
current skill index metadata for report approval and validation differs from
these Planner policy flags; this acceptance run follows the enforced policy.

The model may return an invalid or rejected proposal. Do not treat that as a successful plan. Preserve the finding and retry a corrected request. The trusted `vector_to_postgis` template can independently test the governed runner, but using it does not validate the Planner path.

## Independent result check

After the interface reports validated success, confirm the target with the existing PostGIS container:

```bash
docker exec postgis psql -U geoagent -d geoagent -c \
  "SELECT count(*) AS row_count, ST_SRID(geometry) AS srid, GeometryType(geometry) AS geometry_type FROM agent_sandbox.checkpoint19_ui_e2e_20260926_01 GROUP BY 2,3;"
```

For the bundled sample points, expect **2 rows, SRID 4326, POINT**. Compare the table name and counts with the interface outcome. Do not rerun the exact approved execution after a success. If an execution fails after a possible write, inspect the table and durable evidence before choosing a fresh target for another attempt.

Report back the first numbered step that differs from expectation, the displayed status and redacted error text, and whether the independent SQL check matches. Never include secret contents.
