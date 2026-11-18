# Data Cards — recorded facts for planning and inspection

P2-D1, [#98](https://github.com/wanggiya/action-charter/issues/98).

A Data Card projects facts collected by the existing bounded readers. It does not
scan again, infer domain definitions, authorize execution or install capabilities.
Existing CSV/TSV inspection, table profiling (including qualified XLSX/JSON readers)
and bounded spatial discovery return the same `data-card-v1` contract. CLI and MCP
reuse those services. The result Overview renders it without another network call.

Cards include the normalized input source, recorded full-file or package digest
when available, selection/population scope, counts, field storage/observed types,
candidate roles and available quality/numerical facts. Unknown counts remain null.
Identifiers and age bands do not acquire numerical means merely because they contain
digits. Row counts do not establish a patient/entity grain or clinical meaning.

The projection contains at most 32 fields and 8 KB; omitted-field counts remain
explicit. It excludes preview rows and category examples. Explicit selection/filter
and missing-token parameters can contain user-supplied literals; this is not an
anonymization boundary or permission to lower model data-egress classification.
Metadata missingness keeps its empty-cell/native-null semantics; distinct and numeric
counts retain their recorded missing-token and valid-value policies.

| Scope / identity | Meaning |
|---|---|
| Preliminary sample, digest pending | Existing opt-in discovery read a bounded sample/header; full counts and quality are unknown |
| Complete parsed file | Facts cover the complete bounded parsed source, not preview rows |
| Complete selected table | Facts cover the selected workbook sheet/range or record collection; the digest identifies the original file |
| Filtered rows | Profile counts cover matching rows; source and profile denominators remain separate |
| Spatial driver metadata | Driver dimensions/layers/CRS only; a package hash does not validate pixels or every geometry |
| Recorded read | A digest identifies that version; viewing a saved card does not check current file freshness |

The Planner receives same-turn cards only from existing explicit discovery, matched
to the supplied source paths. Recorded result context carries historical cards with
their recorded-freshness label. Source/worksheet/filter matching requires an
independently obtained digest and exact selection; the helper never reads files.
Automatic freshness/cache/reuse scheduling and a card before every planning request
belong to P2-D2. This slice adds no new automatic read-on-Send policy.

The workflow's original evidence is stored once. A normal/latest run response derives
its card from that evidence; the projection does not rewrite the run, reread inputs
or call a model. Existing interrupted-run reconciliation remains separate and never
restarts an operation. Old results without qualified identity/shape remain readable and may
have no card. Supplied card dictionaries never replace the trusted projection.
Comprehensive profile artifacts also store original evidence without the derived
card; the response adds it afterward so the existing artifact budget is preserved.

```text
Existing explicit reader -> original evidence
                                  |
                         shared pure projection
                                  |
                       typed bounded Data Card
                         /        |         \
                   Planner    CLI / MCP    Overview
```

No new agent role, container, arbitrary tool or operation registry entry is added.
`contracts/data_cards.py` owns L0 types; `data/discovery/cards.py` owns the L2 pure
projection. Existing services/adapters share it. Models still propose and interpret;
policy authorizes, Executor performs operations and Critic assesses recorded evidence.

## Validate in the interface

1. In your usual launcher terminal run `.venv/bin/geoagent project-identity --project-root .`.
   Both the coding session and owner terminal currently report **Copied project
   identity**; verified offline remount recovery is still needed. If that error
   remains, stop
   and report it; do not initialize/rebind ownership as part of this test. If identity
   is valid, restart with `bash scripts/start_actioncharter.sh`, then refresh. Writes
   can remain off.
2. In a new chat send `Inspect sample_orders.csv. Return row count and column names. No writes.`
3. Click Execute if inspection-on-send is off. Open Outcome → Overview.
4. Find **Data Card · Recorded inspection**. Expand **Field facts**. Compare source
   rows, field count, missing/distinct values and available numerical summaries
   against Columns and the recorded result. IDs should remain identifier candidates.
5. Expand identity/selection. A completed inspection has a recorded digest; this is
   not a current-file recheck. Close and reopen the chat or historical run: the same
   card should return without another execution. Expanding it makes no analysis call.
6. For an existing comprehensive analytical chat, Outcome → Overview and terminal
   `/overview` show its recorded card. Older stored profiles can omit the UI card;
   a new explicit inspection obtains the current contract without modifying history.

CLI JSON inspection uses the same service:

```bash
.venv/bin/geoagent inspect-csv data/input/sample_orders.csv --project-root .
```

Use the installed CLI's existing help if running from another directory. MCP
`discover_dataset`/`profile_table` return `data_card` through their existing qualified
reader paths; no separate installation is needed. Full-data inference, database
transfer, automatic freshness and efficiency gains are separate acceptance gates.

## Verification record

All3,120 collected offline tests have passing coverage: full source-export run3,114
passed in1209.77s, then80 final affected checks passed22.50s (74 overlaps,0 missing).
The final checks cover narrow legacy/payload/artifact follow-ups; this is not one
uninterrupted final-source invocation. All970 Python source/test files match the
verified export. Interface validation passed12.06s; isolated actual-API/fake-model
browser and CLI/PTY checks passed expansion and refresh/history with no page errors
or authorization calls. Personal browser profiles/caches were not used.
Final context/bounds/redaction checks passed15 tests in0.80s in that isolated copy
with the final documents. Direct checkout checks instead refused the mismatched
ownership marker (6 failed/9 passed); no guard, marker or owner state was changed.

[Real local4B synthetic context observations](../benchmarks/results/2026-11-18-p2d1-card-context.json)
retain a clarification without reader context and a validated inspection proposal
with a preliminary card. No workflow was dispatched. This is not a frozen pre-feature
comparison, statistical reliability result or efficiency win; deterministic follow-ups
were verified afterward. [Current handoff](../context/WORK_RESUME.md).
