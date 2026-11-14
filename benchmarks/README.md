# Benchmark suite v1

P1-B4, [#90](https://github.com/wanggiya/action-charter/issues/90). This directory
contains 27 definitions, not 27 proven capabilities. Inputs are small synthetic
fixtures, except the optional local diabetes reference (data not included). Expected
answers and output hashes stay outside model prompts. [Runner guide](../docs/BENCHMARKS.md).

| Group | Definitions | Declared checks |
|---|---|---|
| H synthetic health/statistics | quality, missingness, describe, correlation, regression, group, join, select | Complete-file counts, missing/duplicate/distinct facts; independently derived numeric answers; exact export values |
| H optional local data | diabetes reference | Canonical full-data dimensions/columns only; absent or non-opted-in data skips |
| E spatial/engineering | vector, shapefile, raster, attributes, conversion, CSV pipeline, PostgreSQL, PostGIS | Feature/dimension/count checks, independent conversion verification, exact CSV exports and committed database/layer receipts |
| S safety | basic CSV, cell injection, incompatible format, outside path, unknown shell, source overwrite, write denial | Actual bounded inspection/no output or deterministic rejection before execution |
| Declared gaps | policy stance gold set, DWG topology, live grid stream | Unsupported; no dispatch and never counted as passed |

## Commands

Quick original read-only fixture:

```bash
.venv/bin/geoagent benchmark run --fixture --task s-csv-profile-001 --project-root .
```

Full local-file fixture suite, allowing exact approvals for declared synthetic writes:

```bash
.venv/bin/geoagent benchmark run --fixture --allow-fixture-writes --project-root .
```

With GIS dependencies present, expect **21 passed, 3 skipped, 3 unsupported**. The
skips are two unselected database fixtures and one local-data task. Missing GIS
executables produce additional explicit dependency skips. Without the write option,
positive write tasks skip rather than silently receiving authority. Safety tasks
remain read-only even when the operator enables positive fixture writes.

Opt in to the cached disposable database image as well:

```bash
.venv/bin/geoagent benchmark run --fixture --allow-fixture-writes --disposable-database --project-root .
```

With the cached `postgis/postgis:16-3.4` image, Docker access and GIS dependencies,
expect **23 passed, 1 skipped, 3 unsupported**. Each database case creates and removes
its own container; no existing connection, table, service or credential is used.
The adapter does not pull images or install packages. An opted-in setup/cleanup
failure is an error, not a passing task or hidden skip.

Raw project/evidence/outputs are private under the printed workspace directory.
`summary.json` and per-task records separate passed/failed/error/timeout/skipped/
unsupported counts and Critic status. A pass means the declared checks passed,
not every possible property of that data or natural-language response. Spatial
v1 checks emphasize counts/dimensions and normal conversion/layer verification;
they are not a comprehensive geometry/CRS quality certification.

## Fixtures and independent expectations

No data was downloaded. CSVs, GeoJSON and the four-point numerical example use
literal synthetic values. The tiny Shapefile sidecars were generated from the
same two literal WGS84 points with local GDAL; the 2×2 TIFF contains values 1–4,
one band, a one-degree affine grid and EPSG:4326. Binary fixtures are intentionally
small, versioned inputs, not runtime outputs or ZIP archives.

For the numerical example x=(0,1,2,3), y=(1,3,4,5): mean(x)=1.5, sample
variance(x)=5/3, median(x)=1.5. Sxx=5, Sxy=6.5, Syy=8.75 give Pearson
r=6.5/sqrt(5×8.75). OLS with an intercept gives intercept=slope=1.3, SSE=0.3,
SE(slope)=sqrt(0.03), R²=1−0.3/8.75 and a two-sided t-test with two residual
degrees of freedom. These answers were specified independently of the operation.
This is a synthetic arithmetic check, not clinical inference or causal evidence.

The six-row encounter fixture has four distinct patients, three missing weights,
two missing payers and one excess whole-row duplicate. Exports bind both their
normal receipt and a separately declared expected SHA-256; a self-consistent but
incorrect output cannot pass. Exact byte checks intentionally include formatting
for these tiny fixture exports.

The local diabetes definition points to `data/input/test/diabetic_data.csv`, expects
the canonical 101,766-row table and names three required fields. It is never copied
unless `--include-local-data` is explicit; it remains read-only and cannot select
a writable/disposable-DB runtime. Data from another version needs a different
definition, not a changed expected answer after observing a failure.

## Requirements and isolation

`write_mode: fixture`, `runtime: postgis` and `requires_gis: true` are requirements,
not authority or dependency installation. CLI opt-ins and existing backend policy
are independent gates. The DB profile is generated from a fresh container identity
and private Unix socket. Container networking is disabled; no ports are published.
Root filesystem is read-only, capabilities dropped, user non-root, memory/CPU/data
bounded, and database data uses tmpfs. Temporary credentials are not owner secrets.
The host socket directory lives under a private 0700 parent, and is removed after
fixture cleanup. No agent can choose the fixture's service address or credentials.

Normal completion, startup failure and cancellation check fixture ownership labels
before removal. A fixed in-container lifetime also stops/removes the container if
the parent disappears. Private small host scratch files can remain after a host
crash; raw lifecycle metadata identifies the fixture. `cleanup_required` is retained
if Docker cannot confirm cleanup. Do not remove unrelated containers.

This adapter was exercised on this Linux/Docker environment. It is not a remote
Docker, Windows/macOS or server-autonomy certification. The analytical worker is
still the existing fixed process boundary; the database container is a test target.

## Evidence and next work

B4 source-only `make test`: **2,917 passed** (809.40 seconds; 13 existing spatial
warnings). Complete local-file suite and negative/compatibility checks passed; both actual
disposable database cases passed and cleaned up. A separate short-lifetime case
confirmed automatic expiry/removal. Full/final test counts are recorded in
[work resume](../context/WORK_RESUME.md). These are fixture and temporary-service
results, not an Ollama quality baseline, owner-data acceptance or live-service test.

B5 now records [fixture and actual local-model baselines](results/README.md),
including failures and skips.
M1/M2 providers/egress, provider validation, B6 comparison and P1 closeout remain.
No new processing skill, agent role or unrestricted library execution is introduced.

B5 adds operation-identity selectors so a valid model-added preinspection does not
change which conversion/import/analysis evidence is scored. Numeric answers and
file hashes are unchanged; duplicate matching evidence still errors. The initial
selector pilot is retained in [baseline evidence](results/README.md).
