# Checkpoint 25 — operation contracts, automatic discovery and extensions

This delivery adds installed-library discovery to the checkpoint 24 registry/execution foundation. It preserves existing skill IDs, registry bytes, plan/recipe formats and historical digests. The existing Builder candidate/test/promotion lifecycle remains available; this checkpoint supplies a small data-only installed-adapter path rather than replacing it with arbitrary module execution.

## Acceptance and delivered behavior

| Area | Measurable acceptance |
| --- | --- |
| Shared contracts | Catalog covers all 24 existing implemented operations plus installed adapters. Stable IDs/names, typed parameter/result schemas, input/output contracts, completion dependencies, runtime requirements, effects/gates and preview/validation contracts are searchable through the same backend service in CLI and Settings. Existing golden workflow digests and legacy execution tests pass. |
| Automatic discovery | One scan enumerates installed Python distributions and statically extracts function/class/method/property declarations from `.py`/`.pyi` manifests, including signatures, annotations and docstrings. Scanned module bodies, decorators, annotations and defaults are never evaluated. Private declarations are optional; native/dynamic/inherited/reexported coverage and limits are reported. |
| Search and evidence | Immutable, hash-bound project-local scan snapshots provide query/distribution/kind filters and paginated candidate results. Candidates have `executable=false`; searching or historical snapshots never grant authority. Changed snapshots and unsafe paths/links reject. |
| Working extension | A tested JSON package binds a fixed CSV column projection to `ext_order_identity`. Fixture tests run only in temporary directories. Explicit installation, exact package digest in proposals, fresh workflow review/authorization, real execution, independent verification and intermediate lineage all pass through shared CLI/interface services. |
| Boundaries | Unknown adapter names, arbitrary entrypoints/code/signature fields, invalid package contracts, bad fixture expectations, conflicting IDs, changed package digests and symlinks reject. Dependency installation, adapter installation and consequential operation approval are separate actions. |

## Shared operation contracts

`operations.registry` wraps the original skill registry and supplies the main workflow argument models. The operation catalog is descriptive, with explicit `workflow_supported` and `parameter_mode` fields: the 17 existing main-workflow operations and installed CSV adapters can be planned/edited/run; other registered spatial/database/GeoServer operations retain their existing service/CLI paths. Their service schemas are described without pretending they are new graph operations or exact CLI flag definitions. Runtime version presence does not prove remote database/service reachability. If an optional runtime cannot expose its result schema, the contract explicitly reports result_schema_available=false rather than importing a candidate or claiming a complete schema.

Planner's optional skill list and Add use backend names/capability metadata. Installing a package refreshes both catalogs. Old/offline presentation labels remain a fallback, not an execution registry. Discovery of an installed callable does not register it with a dispatcher.

## Discovery limits and coverage

Default scope is all installed **Python distributions in the API process**; a selected distribution narrows the scan. This is not operating-system binary discovery, a JavaScript package inventory, or proof that every runtime-exported function is callable. Standard-library/native/dynamic symbol enumeration is not implemented. Use private-declaration inclusion when you want source declarations with underscore names.

The scanner reads declared Python source/stub files through no-follow directory descriptors. Files outside a distribution root, links, oversized files, unavailable manifests and malformed sources are skipped with coverage findings. It never loads discovered entrypoints or evaluates functions, decorators, properties, annotations or default values. The application's existing trusted runtime may already have imported dependencies; discovery itself does not import candidate modules. Secret-named literal defaults are redacted. Signature/doc metadata is untrusted descriptive material, not authority or a runtime type guarantee.

Bounds: up to 1,000 distributions, 2,000 source files, 16 MB total source, 256 KB per file, 10,000 candidates, 8 MB candidate metadata and a cooperative 10-second scan limit. Snapshots cap at 12 MB and 20 project-local records. Candidate signatures show at most 32 parameters; individual text fields are bounded. Results page at 50 by default (UI search uses 25), with a maximum page size of 100. Budget exhaustion reports truncation and unscanned-library count; narrow the scan rather than assume complete coverage. The wall-time limit is checked between files, not a hard process interruption.

Source manifests can be missing for editable installations. C extensions may expose some declarations through Python stubs but native symbols are not introspected. Inherited methods, reexports, monkey patches, runtime-generated functions and decorator-transformed signatures remain unverified. A source-manifest-complete result is not full runtime-library coverage.

Snapshots live under `library-discovery/`; installed packages live under `operation-packages/`. Both are Git/Docker ignored. The paths are metadata storage, not input datasets or execution approval stores. Removing a snapshot explicitly removes search history, not authority. Installed adapters are immutable per ID: updates/uninstallation and general third-party adapter loading are outside this slice.

## Frontend acceptance

1. Use the existing launcher and open Settings → **Operations & libraries**. Expand Registered operations; search `aggregate_csv`. Inspect its parameter/output schemas, effects, dependencies, runtime and authorization/validation requirements.
2. Select `pydantic` or `pandas` under Scan scope, then **Scan installed libraries**. Search `BaseModel` or `read_csv`. Expand a declaration to inspect parameters, annotations and documentation. Confirm it says Candidate only. Open Coverage and limitations. Then try All installed distributions and inspect truncation/unscanned counts.
3. Select [the example package](../examples/checkpoint25/order_identity.operation.json) in Operation package JSON. **Test package** must report successful temporary fixtures while adding no project CSV files or installation.
4. Click **Install tested package**. Confirm registration but no workflow authorization or execution. The package declares the approved `csv_column_projection` adapter; it cannot embed Python, commands, arbitrary module names or custom callable entrypoints.
5. Close Settings. Planner skills and searchable Add must show **Extract order identifiers**. In Planner, ask: “Replace the current proposal with exactly three steps. Inspect sample_orders.csv. Use ext_order_identity on the original file and export its validated CSV using source_step=step_2. Choose fresh output paths data/output/check25_accept/identity.csv and data/output/check25_accept/final.csv. Bind the exact installed package_sha256. Require approval and validation for both writes; do not execute.” The inspection step produces metadata; the adapter reads the original path. The installed adapter's fixed columns are order_id and region.
6. Review the three steps, package digest and displayed fixed adapter configuration (columns, adapter and runtime). Authorize separately, then Execute once. Expect six rows, columns order_id/region, leading `001` preserved and the missing region still empty. CSV hashes/source identity/row count/columns must pass validation; export must consume the verified adapter output and evidence must record lineage.
7. Refresh and reopen the saved plan and history without execution. Installing the package must not have created an execution attempt. The actual successful workflow creates one durable attempt. Changed/expired authority and output replacement remain blocked by the existing execution boundary.

Installation requires pandas 3.0.5, already declared by checkpoint 24. It does not run pip or install any dependency. If runtime requirements are unavailable, install the project dependencies explicitly using the documented setup. Main models propose aliases only from installed contracts, with the exact package digest. No chat, scan or package record grants approval.

## CLI parity

```sh
.venv/bin/geoagent operations --query aggregate_csv
.venv/bin/geoagent library-inventory
.venv/bin/geoagent discover-libraries --distribution pandas --project-root .
.venv/bin/geoagent search-library-functions SCAN_SHA --query read_csv --project-root .
.venv/bin/geoagent test-operation-package examples/checkpoint25/order_identity.operation.json
.venv/bin/geoagent install-operation-package examples/checkpoint25/order_identity.operation.json --package-sha TESTED_PACKAGE_SHA --confirm-install --project-root .
```

The test command returns the normalized typed package SHA; use that returned value, not a raw-file hash. Formatting/default normalization is part of the package identity. CLI discovery saves the same bounded metadata snapshot as the interface; scans/search remain non-executing. `operations` returns the same catalog as `/api/v1/operations/catalog`.

For deterministic execution testing without a model, use [the typed proposal](../examples/checkpoint25/installed_adapter_plan.json) with `inspect_csv`, `ext_order_identity` and `export_csv`. Its package digest matches the normalized public example; choose fresh output paths before repeating. The adapter uses path or source_step, target_path, optional comma/tab delimiter and the exact package_sha256. Its columns are fixed by the package; caller-supplied columns are rejected. Store/review/authorize/execute with checkpoint 24's `workflow-plan`, `workflow-review`, `workflow-authorize` and `workflow-execute` commands. Those commands use the same services as the interface.

## Adding, testing and installing adapters

The example JSON is an operation package, not a pip package. Copy it, give it a new `ext_` ID/name/version, choose unique bounded columns, and provide up to five small CSV input/expected-output fixtures. Test before installation. Installation repeats the fixture tests and creates a new digest-verified record atomically; it cannot replace existing IDs or grant authority. Packages cap at 64 KB and installed packages at 20.

The admitted adapter is intentionally small: CSV column projection through the trusted pandas-backed service. `candidate_function` identifies `pandas.core.indexing.IndexingMixin.loc` and the runtime is fixed to pandas 3.0.5. It is a descriptive mapping to the implemented adapter, not an import target. An arbitrary function discovered in a scan requires a new reviewed adapter implementation, typed arguments/results, effect/dependency contracts, bounded previews and deterministic verification. Extend the trusted adapter allowlist and tests in code (or use the existing Builder candidate lifecycle), then document installation. Never dispatch with `getattr`, `eval`, an unreviewed import string, shell or unrestricted library calls.

## Repeatable browser verification

Playwright 1.63.0 is a pinned frontend development dependency. Install frontend dependencies with the existing pnpm command, then:

```sh
bash scripts/setup_browser_tests.sh
make interface-validate
corepack pnpm@10.17.1 --dir interface browser:test:25
```

Browser scripts always use `interface/.playwright-browsers/` and temporary profiles. They do not use normal browser profiles or the shared Playwright browser cache. The setup command downloads Chromium there. On minimal Debian/Ubuntu Linux, it can download/extract the missing audio runtime under `interface/.browser-system-libs/` without installing system packages; other platform/system dependencies remain explicit. These directories are ignored by Git/Docker and are not runtime application requirements. The shell setup is a Linux/POSIX test workflow, not a claim of native Windows packaging readiness.

The checkpoint 25 browser script uses private ephemeral frontend/API servers and a temporary project. It scans actual installed library metadata, tests/installs the example package, proposes the workflow through a deterministic model fixture, then runs real pandas processing through exact backend authority. No live model, database or GeoServer is contacted. Existing checkpoint 24 browser verification also uses the project-local installation.

## Remaining boundaries

General Python-code extension loading, marketplaces, native-symbol discovery, automatic conversion of every function into an operation, adapter updates/uninstallation and generalized operation composition are not implemented. Checkpoint 26 still owns cancellation/restart-safe scheduling/retry/resume and reusable parameterized workflows; checkpoint 27 owns evaluated laptop/PC packaging and release materials. No release publication or KNIME/Ansible parity claim is made.

Verification at delivery: `make test` passes 1,513 tests and `make interface-validate` passes. The existing large-bundle warning remains. Five checkpoint 25 and six checkpoint 24 actual-temporary-backend browser groups pass without page errors. These are deterministic model-fixture checks; live-model planning quality, native-function completeness and clean native Windows/PC packaging are not established.

Library discovery saves candidate metadata in `library-discovery/`; it does not register executable operations. Tested adapter installation persists in `operation-packages/` across launcher restarts. Reinstallation is unnecessary when reopening the same project. Settings uses the existing sliding ON/OFF switch for private declarations.

Saved scans can now be reopened in Settings under **Saved scanned libraries**, with expandable scan/library/function groups and paginated search. Scanned candidates remain non-executable. Information cards connect input → operation → planned/recorded result with arrows and declared dependencies. See the [functional example index](../examples/README.md) rather than choosing examples by checkpoint number.

Operator follow-up validation: `make test` passed 1,514 tests; `make interface-validate` passed. The five-group temporary-backend browser journey also reopens Settings and queries persisted functions without rescanning, checks the private-declarations switch, and completes installed-adapter execution. CLI inventory uses `saved-library-scans --project-root .`; saved function search uses `search-library-functions HASH --query mean --project-root .`.
