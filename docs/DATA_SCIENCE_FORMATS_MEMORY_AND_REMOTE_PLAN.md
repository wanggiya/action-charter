# Broader data science, formats, memory and remote operation

User requirements recorded 2026-10-27. Documentation only: no readers, statistical
methods, model roles, dependency installations or remote services are added here.
Preserve existing checkpoint history. This extends the
[consolidation plan](GENERALIZATION_AND_CONSOLIDATION_PLAN.md) and
[Builder reuse plan](BUILDER_REUSE_AND_CAPABILITY_INTEGRATION.md).

The [consolidated TODO](IMPLEMENTATION_TODO.md) turns these requirements into open
tasks with dependencies and acceptance, without marking proposed capabilities delivered.

## Product target

The user wants more than initial inspection or a data-engineering execution summary.
The platform should perform substantial analytical/statistical work, explain methods
and findings, generate useful reports, and transfer verified data to/from configured
PostgreSQL/PostGIS and other explicitly supported services. Use new real/simulated
datasets without binding product behavior to the diabetes example.

Keep composition of tested capabilities as the preferred path; use optional bounded
implementation generation for genuine gaps. Reuse existing Builder machinery, not
another parallel generator. Installed libraries/function discovery supplies candidates
and documentation, not automatic unrestricted execution or evidence of method validity.

## Statistical capabilities and acceptance targets

These are requested targets, not an assertion that each is currently registered.
Audit existing inspection statistics and restricted calculations before adding anything.

| Target | Requirement | Functions/ability to add or generalize | Expected outcome |
| --- | --- | --- | --- |
| Descriptive distributions | Percentiles/quantiles, standard deviation, variance, range and grouped summaries | Shared statistical specifications over supported table sources; explicit sample/population convention, quantile algorithm, missing policy and full-file/sample scope | Reproducible statistics with counts, units, scope and verified reference values |
| Association | Correlations and relationships between suitable variables | Pearson/Spearman and other justified registered methods, applicability checks, pair counts, constant-column handling and labeled correlation/covariance matrices | Correct matrices/plots with missingness and method limits; no treating IDs or codes as continuous by default |
| Matrix analysis | Clearly named matrix operations rather than one undefined matrix feature | Specify correlation, covariance, contingency or design matrix; later numerical algebra methods only as needed, with labeled dimensions and sparse/size limits | Inspectable labeled matrices, associated diagnostics and bounded visualizations |
| Linear regression | Fit and assess a declared outcome/predictor specification | Explicit intercept/encoding, coefficients, standard errors, confidence intervals, appropriate P-values, R-squared/adjusted R-squared and residual diagnostics; missingness and repeated-observation handling | Fitted model evidence and explanatory report; disclose rank deficiency, convergence/applicability failures and evaluation scope |
| Inference and comparisons | Appropriate tests, effect sizes and uncertainty | Named hypotheses, analysis unit, assumptions, sample sizes, multiplicity policy where relevant and qualified uncertainty procedures | Traceable estimates and intervals; P-values do not by themselves establish importance or causation |
| Causal analysis | More than correlation or regression output | Explicit causal question/estimand, treatment/outcome/timing, design, confounder assumptions and identification rationale; supported experimental or observational methods only when justified | Clearly qualified causal estimate or an explicit finding that the data/design cannot identify the requested effect; never automatic causal claims from association |
| General statistical expansion | Additional data-science methods as useful tasks reveal them | Parameterized skills/method families, compatible library adapters and qualified generated-method packages; examples and independent checks | Broader ability without one dataset-specific endpoint per calculation or unrestricted exposure of every package function |
| Analytical reports | Substantive science/engineering findings, not just an execution receipt | Source/scope, method choices, preparation, statistics/model diagnostics, tables/plots, evidence references, assumptions and limitations | Useful report with every measured claim traceable to recorded outputs; agent interpretation distinguished from computed facts |

Models choose and explain methods; tested code computes quantities. A Critic can review
support and assumptions but does not establish validity merely by agreeing. Statistical
methods need compatible data and a defensible question, not only an installed package.
Keep deterministic numerical checks, tolerance/seed conventions and held-out cases.

## Source and format coverage requested

Start with readers/source adapters and bounded inspection, then justified transformations
and writers. Support does not mean every variation of a format or every processing task.
Preserve original files, source identities and extraction/transformation provenance.

| Data family | Requested formats | Reader/adaptation requirements | First useful acceptance |
| --- | --- | --- | --- |
| Tables/workbooks | Existing CSV/TSV; XLSX | Sheets, ranges, headers, types, merged/empty cells, formula versus cached-value policy; compatible shared table analysis | Equivalent fixture values across CSV/XLSX yield reconciled statistics and explicit unsupported workbook cases |
| Structured records | JSON, JSON Lines as a related candidate | Record location, nested objects/arrays, flatten/explode policy, conflicting types, batches and row grain | Nested/flat fixtures become explicit table views without silent row multiplication or coercion |
| Documents | PDF, Markdown, DOC; optionally DOCX through a distinct adapter | Text/table extraction with page/section references, encoding and extraction quality. Treat legacy DOC separately from DOCX. Optional PDF-to-Markdown derived artifact, preserving page/table links and original source | Source-linked text/tables and visible omissions; conversion does not guarantee faithful layout/table extraction |
| Scanned documents | Image PDFs and image text | Optional OCR only when available/configured; retain coordinates/page references and uncertainty; no silent dependency downloads | Distinguish extracted text from OCR output and expose uncertain/missing content |
| Images/non-geospatial rasters | BMP, JPG/JPEG, PNG, TIFF, IMG where its actual driver/content is supported | Dimensions, channels, dtype, color/alpha, metadata, numerical summaries and bounded image previews; explicit method scope beyond simple viewing | Correct metadata/pixel-reference fixtures and previews without inventing geographic coordinates |
| Geospatial rasters | GeoTIFF and supported geospatial IMG/other driver formats | CRS/transform, bands, nodata, units, overviews/windows and full-raster versus sampled statistics; distinguish from ordinary TIFF | Reconcile reference metadata/statistics and preserve spatial identity without loading every pixel into the UI |
| Point clouds | LAS; compressed variants only if explicitly supported | Point schema/count, coordinates, scale/offset, CRS when present, bounds, classifications, chunked reading and bounded/level-of-detail previews | Exact fixture counts/bounds and explicit sampling, followed by justified filters/exports |
| Depth imagery | Depth image formats/encodings to be explicitly selected | Depth scale/units, invalid values, calibration/intrinsics and coordinate frame when applicable; distinguish depth from ordinary image intensity | Correct depth summaries and validated conversions only when required calibration exists |
| Databases/services | Existing PostgreSQL/PostGIS; other services individually qualified | Typed source/destination adapters, identity/snapshot, schema/type mapping, transactional effects, export/import reconciliation and credentials outside model context | Verified staging-table/service round trips, recoverable failures and explicit authority |

An extension alone is not sufficient format detection: IMG, TIFF and depth imagery
have ambiguous content/metadata. No claim of medical image interpretation or general
point-cloud understanding follows from successfully reading a file.

PDF-to-Markdown or OCR output is a derived representation, not replacement truth.
Document text, embedded instructions, macros and external links never grant execution
authority; reading documents must not execute embedded content.

## Architecture and roles, including the previously omitted Builder

The original Builder is a separately defined LLM role/manifest, not automatically a
separate process/model/container. Builder lifecycle modules are backend services;
context-pack builders and deterministic scaffold generators are not extra agents.
Consolidated implementation generation can be performed by the primary agent or an
optional role context. Keep legacy developer source activation separate from task-local
analytical execution and method installation.

```text
Frontend / CLI / MCP
        |
Shared task state + coordinator + capability retrieval
        |
Planner: choose applicable methods and supported source/destination adapters
        |
        +-- Known capability -> compose operations / recipes
        |
        +-- Gap -> optional Builder implementation role
                      -> existing candidate lifecycle primitives
                      -> isolated execution and method qualification [integration planned]
        |
Shared policy, exact authorization, execution services / workers
        |
Files / tables / documents / images / geometry / raster / point-cloud adapters
        |
Deterministic verification + durable evidence
        |
Primary self-review or separate Critic -> statistics / charts / analytical reports
        |
Qualified methods and evidence -> memory / knowledge lifecycle [planned]
        |
Later controlled Linux deployment with data and PostgreSQL/PostGIS [planned]
```

Keep user interaction small: discuss the question, select methods automatically where
well supported, ask only for material missing inputs, and review consequential writes.
Frontend/terminal should expose method/scope, matrix/model outputs and failure reasons
without making the user assemble manifests or code. MCP and CLI must reach the same
backend methods; registry membership alone does not prove all interfaces expose them.

## Memory and learning before autonomous Linux operation

User explicitly orders controlled remote/simulated Linux operation after memory work.
This is a roadmap requirement, not authorization to connect to or mutate a server.

1. First make local processing/reporting/service transfer reliable, and connect Builder
   generation to qualified reusable methods using existing infrastructure.
2. Deliver a scoped memory/knowledge lifecycle before autonomous Linux deployment.
   Preserve the recorded growing shared-history design: corrections/superseding versions
   and retrieval priorities retain earlier evidence rather than casually deleting it.
   Determine final shared-versus-role-private layout from the existing design records;
   do not silently settle the previously open alternatives here.
3. Knowledge-management responsibility can reconcile/qualify domain claims and methods;
   Planner retrieves applicable context, Critic assesses support. A distinct logical
   responsibility does not require a permanently running model/container per role.
4. Acceptance must demonstrate relevant recall, correction of stale/incorrect claims,
   source provenance, scope separation, restart persistence and export/import of qualified
   knowledge/method packages without exporting private rows or stale authority.
5. Then deploy the same governed runtime to an isolated Linux environment with selected
   data and PostgreSQL/PostGIS. Add worker/connection identities, secret isolation,
   job supervision, cancellation, persistent artifacts, restart recovery and consistent
   CLI/API access. No arbitrary server administration or unattended write replay.

Initially self-learning means retaining checked methods, corrections and qualified
domain knowledge, not changing Ollama weights. RL/model training remains a separate
proposal and is not required to demonstrate reusable method acquisition and recall.
Remembered skills need dependency/applicability checks and fresh authority at execution.

## Delivery and acceptance discipline

Extend existing checkpoint plans without renumbering history. Audit current capabilities
first, then deliver coherent slices: shared source/result contracts; common table/document
adapters and descriptive statistics; association/regression and general reporting; broader
image/raster/point-cloud adapters; Builder reuse integration and memory gates as defined
above. Priorities can be adjusted against the first actual analytical tasks; no promise
that every format is a dependency of memory or the first Linux acceptance.

Prefer small dependency profiles appropriate to a laptop, loaded only when required.
Package choices and versions require later evaluation; this record does not authorize
installation. Do not implement one backend service for every statistical function.
Preserve special domain contracts where they matter and reuse shared method families.

Measure correctness against independent references across unrelated datasets, full-file
coverage or explicitly labeled samples, resource limits/cancellation, actual-model
reliability, repeatable parameterized reuse and frontend/CLI/MCP parity. Test remote and
database effects only with authorized isolated fixtures. File readability, fixture model
responses and report fluency are not proof of analytical validity or production readiness.
