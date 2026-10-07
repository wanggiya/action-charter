# Main-workflow Snakemake export and verification

Export to Snakemake and Verify Snakemake package are now available in the ordinary Add menu and Planner conversation. Advanced is not required. They create and statically verify a replay package; they do not run Snakemake or execute the source recipe again.

## Prerequisite

Start from a saved original operation plan whose governed execution finished with validated_success and independently verified recipe approval, run-result and evidence identities. The current implementation exports completed governed recipe workflows, such as the inspection → PostGIS load → validation/report workflow. A read-only inspection attempt alone is not a completed governed recipe source. Finish the original supported workflow first; a new unsaved/unexecuted workflow cannot export until its source evidence exists.

Historical source authority is checked at the recorded execution time. A new 30-minute plan approval authorizes package creation only; it does not renew the source recipe's execution approval. Replay independently needs valid execution authority and must not target an existing PostGIS table casually.

## Add to your existing workflow

1. Stop and restart the current source launcher with `bash scripts/start_actioncharter.sh --enable-write-tools`, keeping your working configuration. Hard refresh http://127.0.0.1:5173.
2. Open the original completed workflow's saved plan through Planner/Saved records. Keep it as the current generated plan, rather than selecting a history-only graph.
3. Click Add and search Snakemake. Select Export to Snakemake. A Verify Snakemake package block is added automatically after it. The export depends on the retained source operations; verification depends on export.
4. The inspector shows source_plan_filename and source_plan_sha256, populated from the original saved plan. They must continue to identify that exact source. Do not change original operations while adding an export; changing them requires a different reviewed source run.
5. Move the new blocks, inspect their connections and parameters, then click Validate and save edits. Dependencies are validated as an acyclic graph, with export and verification at the end. No files are exported yet.
6. Click Authorize. The right panel identifies the package under snakemake-exports and shows original operations as “Reusing completed evidence · will not rerun.” Only export is highlighted as the new approval gate. Record explicit approval for this exact package scope.
7. Click Execute. Original operations reuse completed evidence, the export block creates the package (or retains the existing exact package), and the verification block checks it. Outcome and Execution History show the export attempt and verification result. The graph marks retained operations as completed evidence and the new operations as completed after actual success.

Expected files: Snakefile, geoagent-replay.json and snakemake-export-manifest.json. Static verification checks the canonical workflow, declared file hashes, trusted replay entrypoint and exact source recipe/approval/configuration scope. A tampered, mismatched or symlinked package is rejected and never silently overwritten.

## Ask Planner instead

With the original saved plan open, leave skills empty or select Export to Snakemake. Its mandatory verification capability remains available. Send:

> Add Snakemake export and static verification after my existing completed workflow. Preserve all original operations and their parameters. Reuse the recorded completed run; do not reload PostGIS or execute Snakemake.

Planner receives the original saved plan reference and may propose the two terminal operations. Backend checks remain mandatory; text never supplies permission or proves source completion. Review the resulting graph, then Authorize and Execute as above.

## Acceptance checks

- Add opens from the toolbar, right-click or Shift+A, with search/× pinned. Searching Snakemake finds both registered operations.
- Export adds its verification block automatically. Both are movable; removing/disconnecting verification makes validation fail. Restoring it allows validation. Cycles and changes to retained source scope are rejected.
- A missing/failed/tampered source run cannot prepare an executable export review.
- Authorization writes only the exact plan decision; it creates neither the package nor a new source recipe-execution approval.
- Execute creates the package and returns static verification evidence, while source output bytes and recipe approval records remain unchanged. No Snakemake process is launched.
- Repeated export validates an existing matching package. Tampered/unexpected files and symlinks fail without replacement. Expired/new-scope approval fails before export.
- Refresh/reopen the export attempt through Execution History; Planner's saved proposal remains recoverable without regenerating or rerunning the source.

Automated tests use temporary local vector conversion artifacts and a fake model. Browser/live-model interaction remains an operator acceptance pass; these tests do not mutate live PostGIS/GeoServer data. Closing checkpoint 23 still requires its remaining graph, view, material and recovery acceptance cases.
