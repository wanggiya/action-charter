# Shared table-source pipeline — 2026-10-29

This implements one T03/T04/T08 consolidation slice. It does not complete the
generalization plan or add another permanent agent. Existing checkpoint history and
saved runs remain intact. User manual acceptance is pending.

## Structural change

Before, delimited and record readers separately assembled previews, missing counts,
guidance, statistical reports and source references. This made adding a reader repeat
logic and allowed entry points to diverge.

```text
Planner / editable workflow      CLI              MCP
            |                    |                |
            +---------- governed services --------+
                                 |
                   inspect_table (closed dispatch)
                                 |
          +----------------------+--------------------+
          |                                           |
   CSV / TSV parser                 XLSX / JSON / JSONL / NDJSON parsers
          |                                           |
          +---------- TableRow -> bounded TableBatch --+
                                 |
                   shared TableInspection consumer
                   counts / preview / analysis / guidance
                                 |
           reader hash + opened-file/path identity verification
                                 |
              common result + table-source-v1 descriptor
                                 |
           saved evidence -> Critic / frontend / terminal
```

The registry's `inspect_csv` operation ID stays compatible. Its reader metadata comes
from `tabular/source_contracts.py`: suffixes, reader family, selectors, dependencies,
limits and effects. Policy and inspection-on-send checks reuse this catalog. For record
sources, Planner receives the relevant catalog entries instead of a separately maintained
format instruction list. This is narrower than replacing general conversational intent
extraction; those request/repair rules remain.

`TableRow` carries native values, analytical text and storage types. `TableBatch` bounds
retained rows to 256 and analytical UTF-8 payload to 256 KiB; one individually bounded
large row may exceed the batch byte target. Cancellation checkpoints occur between
batches. Readers retain their own parsing, format-specific limits and identity checks.
No result is returned as completed before those checks succeed.

`tabular/inspection.py` now owns counters, previews, guidance, analysis and result
assembly. Entry points select the same trusted reader; they do not implement separate
calculations. This reduces duplicated behavior without merging unrelated execution
protocols or moving model decisions into file parsers.

## Data and compatibility contracts

- New outcomes include validated `table-source-v1`: original path/hash, selected sheet
  or records, selected-table row count, observed storage types and sparse null/empty
  counts, analytical conversion, verification and read-only effects. Sparse count keys
  that are absent mean zero. Storage types use a common default plus field overrides.
- Preview native types are preserved for record formats. The analytical compatibility
  contract remains `table-string-view-v1`: scalars become text, null becomes empty,
  dates become ISO text; empty cells and explicitly declared tokens are missing. This
  is not a new native dataframe type system or automatic domain interpretation.
- Existing fields and the `table-reference-v1` digest formula stay unchanged; the new
  descriptor is excluded from that identity. Old outcomes
  need no descriptor and are not rewritten. All entry points now use float-form default
  percentile labels (`25.0`, etc.); revalidating defaults previously changed their label
  spelling. Stored old labels/IDs remain readable and untouched; numerical answers do
  not change. New reference IDs with previously integer-default percentile queries
  may differ because those defaults now serialize consistently as floats.
- CSV/TSV retain their 1 GiB source cap and independent analysis bounds. XLSX and flat
  record files retain 16 MiB / 200,000 rows and existing ZIP/cell/schema restrictions.
  New formats remain explicit Execute; CSV-only transformations remain CSV-only.

## Skills, discovery and authority

The existing table-statistics skill guides the Planner's use of typed operations.
The registry describes executable contracts; it is not generated executable code.
MCP `list_operation_contracts(query)` exposes that same searchable registry, including
reader contracts and requirements. CLI `operations --query xlsx --project-root .`
discovers the same inspection operation. The built-in Planner receives registry
metadata in-process; this does not add an autonomous MCP discovery loop.

A recipe combines registered operations. A run records their actual execution.
Dependency installation, package scans, a model explanation and any of these discovery
records never authorize execution. All existing path validation, process/worker
boundaries, write gates, exact approvals and outcome checks remain required. No dynamic
import from user-provided format metadata or unrestricted library call is introduced.

To add a trusted reader, a developer must implement parsing/selection and complete
identity verification, register its fixed reader family and catalog entry, and qualify
it with cross-format/entry-point, bounds, unsafe-path, malformed-data and cancellation
tests. Catalog metadata alone cannot dispatch an unknown reader. This is not automatic
installation of arbitrary readers from scanned Python functions.

## Repeatability evidence and manual validation

`tests/test_table_pipeline.py` uses two unrelated temporary datasets and all six suffixes
to reconcile independent means/variance/group means through the shared typed consumer.
It compares direct, CLI and MCP results; checks source hashes and unchanged v1 reference
digests; validates source descriptors, batch bounds, cancellation and discovery parity.
`tests/test_table_sources.py` covers source selection, unsafe/changed files and malformed
formats, and checks that Planner receives the exact relevant catalog entry. Existing
statistics, guidance, workflow and recovery tests remain relevant.

Final automated checks: `make test` **2,209 passed**, with 13 existing spatial-fixture
warnings; `make interface-validate` passed (existing bundle-size advisory). The complete
isolated analytical browser/terminal journey passed with zero page errors. Minimal
worker build-context imports passed with Python site packages disabled. No real-model
evaluation was repeated for this consolidation slice; model behavior with the revised
reader metadata still needs manual validation.

The real 5,000-row diabetic sample was read without writes: time_in_hospital mean 4.6592,
sample variance 9.647384836967394 and ten age groups matched existing results. This is
a numerical regression check, not domain validation or a performance benchmark.
The isolated browser journey additionally checks the saved descriptor's original hash,
columns and lack of authority. No model quality claim follows from fixture tests.

To validate manually, start with the existing launcher, open a new chat and request:

> Inspect records.jsonl. Compute descriptive statistics for x grouped by region.
> No writes. Prepare only.

Use the shipped `examples/table_formats` instructions to copy fixtures into data/input
first. Review the actual source, fields and read-only operation, then Execute. Check
Outcome Statistics, grouped counts and report; reopen the saved chat/run and confirm
the same result without rerunning. Expect four rows, mean x=1.5, sample variance 5/3,
group A mean 0.5 and B mean 2.5. Repeat with records.json. XLSX coverage uses temporary
generated workbooks in automated tests; no workbook binary is shipped. Compare
numerical results, allowing the original source hash to differ. If the small model
fails generation, that is a Planner
quality failure; refreshing is not evidence of successful execution. See the existing
[format acceptance](TABLE_FORMATS_AND_STATISTICAL_FIGURES.md) for exact fixture names
and setup. No write flag or database access is needed for these inspections.

## Deliberately remaining

The comprehensive Docker dataset-profile protocol still has its distinct streaming
profile accumulator/result contract. Its minimal image copies the shared standard-library
catalog, but it does not import the new full result builder. No Docker image was built
or run for this slice. Consolidating that path requires its own compatibility acceptance.
Task-action dispatch, general Planner request interpretation and broader semantic types
remain separate work. Parquet, document extraction/word clouds, arbitrary Python,
new agents and automatic capability installation are not delivered here. This slice
does not complete all T03/T04/T08 items or establish manual user acceptance.
