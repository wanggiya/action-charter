# Statistical methods: implementation and acceptance

2026-10-27. A coherent T05/T09/T10 slice, not completion of the whole expansion plan.

2026-10-28 [agent/report follow-up](T05_ANALYTICAL_ADVICE_AND_REVIEW.md): next-analysis
advice, optional StatisticsSpec.question, definition/computed-finding report sections,
expanded bounded Critic evidence and actual local-model synthetic acceptance. Report
charts/domain interpretation remain separate work; previous contracts stay compatible.

## What is implemented

The existing registered `inspect_csv` operation accepts typed `analysis.statistics`.
Its existing verified CSV scan feeds one statistical accumulator; no second source
engine, arbitrary Python/formula evaluation, or new authorization path is introduced.
The operation catalog advertises the methods, Planner receives their argument schema,
and requested-method coverage rejects proposals that merely promise the numbers.
Ordinary inspections prune unused statistical definitions from the model request.

- Descriptive and grouped statistics: count, mean, minimum, maximum, declared
  percentiles, variance and standard deviation (`ddof` 0 or 1; linear quantiles).
- Pearson and Spearman labeled correlation matrices and unadjusted two-sided P-values.
- Numeric OLS: explicit outcome/predictors/intercept, coefficients, standard errors,
  t statistics, P-values, confidence intervals, R-squared/adjusted R-squared,
  residual standard error, conditioning, leverage and Durbin–Watson diagnostics.
- Nonrobust, HC3 or explicitly selected cluster covariance. Cluster inference records
  cluster count and its inference degrees of freedom; few clusters are warned about.
- Source hash, selected/complete/excluded counts, missing-token policy, runtime versions,
  limitations and a deterministic Markdown report. Critic receives aggregate facts.

The implementation uses [statsmodels OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html)
and its [regression results](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.html).
Runtime versions are recorded rather than inferred from the documentation version.

Agents can use MCP `table_statistics`, `linear_regression` and existing `profile_table`.
The shared workflow operation is still `inspect_csv`, not an unregistered tool name.
[Agent guidance](../skills/table_statistics/SKILL.md) documents selection and assumptions.
CLI `geoagent table-statistics` uses the same service. Terminal `/statistics [RUN_ID]`
and `/analysis-report [RUN_ID]` read stored reports without a model call or execution.
Frontend Outcome → Statistics offers Summary, Descriptive, Matrices, Regression and
Report sections, plus a report download. Changing interactive Groups does not relabel
or replace the immutable statistical result from the recorded run.

## Runtime and interpretation limits

Install `.venv/bin/python -m pip install -e '.[statistics]'` in the launcher environment
if this optional profile is absent (`dev` includes it). This adds SciPy/statsmodels;
installation grants no execution or write authority. Restart the existing launcher
after code/dependency updates. Health should report planner contract `statistics-v2`.
This slice uses the existing bounded table-analysis process, not the separate minimal
Docker dataset-profile worker. That worker has not gained regression support.

Bounds: 200,000 matching records, 24 selected numeric fields, 12 predictors, at most
two descriptive grouping fields/64 groups, plus existing file/process/time/result-byte
budgets. Whole matching rows are processed or an explicit limit error is returned;
there is no silent sample. Narrow filters or an explicitly chosen sample when needed.

Variables must be numeric measurements selected explicitly. Category/identifier codes
are not automatically valid predictors; no implicit categorical encoding or formulas.
Default missing policy is error. Explicit `complete_cases` uses the same complete rows
across all selected statistical fields and reports exclusions; it does not edit data.
Constant outcomes, rank deficiency, poor conditioning and insufficient observations
reject. Perfect/nearly perfect fits suppress misleading coefficient inference.
Nonrobust covariance requires appropriate error assumptions; HC3 does not correct
repeated observations. Cluster covariance requires justified independent groups.
Correlation P-values are not corrected for repeated observations or multiple testing.
Model fit/significance does not establish causation or out-of-sample performance.

Browser download saves the recorded report through the user's browser. It is not a
backend project-file export. Dataset/report writes by workflow operations still require
normal Allow writes, exact authorization and Execute. Nothing in chat authorizes writes.

## Frontend validation

### If the model omits the regression

Contract `statistics-v2` constrains a simple statistical proposal to the requested
methods inside `inspect_csv.analysis.statistics`. It requires actual analysis,
statistics, methods and regression objects rather than permitting null/metadata-only
alternatives. Explicit cluster covariance requires its grouping field. Numerical
variables/parameters remain model output; no backend fallback synthesizes a plan.
A genuine missing-input question remains possible with plan=null. Backend policy
still rejects omitted/invalid methods, including from providers ignoring constraints.
The error guidance no longer recommends calculate_csv_columns for every omission.
Fixed a request-parser bug where unbounded matching interpreted “covariance” as
“variance” and unintentionally required descriptive statistics. Regression-only
decoding omits unused descriptive-field selectors, so the grouping identifier is
not invited into the numeric complete-case population. It remains a cluster key.
Restart the launcher after updating; closing Chrome cannot change the model's output
or the running backend contract. Recorded table-statistics-v1 result files are unchanged.

Real-model follow-up: the loaded local qwen3.5:9b, with reasoning_effort=none and
1024 maximum output tokens, produced a valid clustered regression on the four-row
synthetic fixture and its computed result matched the independent reference
(R-squared 0.9657142857). Approximately 55 seconds including planning and read-only
analysis on this machine; not a general performance benchmark. No workflow was
dispatched or write authorized. Optional launch configuration matching the reasoning
setting tested here:

```bash
MODEL_REASONING_EFFORT=none MODEL_TIMEOUT_SECONDS=240 bash scripts/start_actioncharter.sh
```

The exact user regression request also passed with the same loaded model/settings
and a temporary copy of diabetic_sample_5000.csv: correct outcome, both predictors
and patient_nbr cluster key; 5,000 analyzed rows, 4,260 clusters, R-squared
0.31906296707718984. Approximately 69 seconds including planning and read-only analysis.
No automatic correction was needed. The diagnostic explicitly called the shared
read-only analysis service on the validated model arguments; it did not dispatch a
workflow or create write authority. Full governed dispatch/recovery is separately
covered by the isolated browser journey. No broad model/domain-reliability claim.

Verification follow-up: full suite 2,169 passed before the final covariance-matching
correction; final focused statistics/scope suite 20 passed after that correction.
Interface validation and isolated browser acceptance passed with statistics-v2.

### If planning times out

`planner generation` at 120 seconds means the model did not finish proposing the
workflow; it is not a failed CSV scan. `filenames resolve under data/input` is an
input-path hint, not the cause. Timeout alone does not prove context overflow.
Statistics-only requests now use a focused prompt: shared schema/policy validation
and history remain, while unrelated conversion examples/general instructions are
removed and unrelated recipes are excluded. One schema alone did not previously
imply a small prompt. A comparable fresh fixture fell from 24,861 to 14,638 prompt
bytes (41%); existing chat/history and recipes can change the actual size. Restart
the launcher after this update.

Retry once in a new chat with the regression-only request below before adding other
methods. A fresh chat avoids accumulated conversation context. If the
same model still needs more time, stop the launcher and use:

```bash
MODEL_TIMEOUT_SECONDS=240 bash scripts/start_actioncharter.sh
```

This allows longer model reasoning; it does not accelerate it or authorize writes.
For compatible thinking models, `MODEL_REASONING_EFFORT=none` is another explicit
launch option; do not assume every installed model supports it. No retry happens
automatically. See [Ollama thinking controls](https://docs.ollama.com/capabilities/thinking)
for model-specific support; older server versions may differ. Opening an old workflow
after refresh is not evidence that the timed-out request succeeded. Verify the matching
submission and actual recorded run.

```text
Inspect test/diabetic_sample_5000.csv. Fit linear regression of time_in_hospital
on num_medications and num_lab_procedures, with an intercept and cluster covariance
grouped by patient_nbr. Return coefficients, P-values and R-squared. No writes.
```

The focused-prompt tests verify reduced request size and preserved typed statistics;
they do not establish broad latency/reliability of a particular local Ollama model.

### Standard acceptance journey

1. Restart with your normal `bash scripts/start_actioncharter.sh` command. No
   `--enable-write-tools` is needed for this read-only statistical inspection.
2. Put this small fixture at `data/input/statistical_fixture.csv`:

   ```csv
   x,y
   0,1
   1,3
   2,4
   3,5
   ```

3. Start a new chat and send:

   ```text
   Inspect statistical_fixture.csv. Compute descriptive statistics and Pearson
   correlation for x and y. Fit linear regression of y on x with intercept and
   nonrobust covariance. Return coefficients, standard errors, P-values, 95%
   confidence intervals, R-squared and adjusted R-squared. No writes.
   ```

4. Select the inspection block. Its arguments must include `analysis.statistics`
   with describe, pearson and linear_regression, outcome y and predictor x. A promise
   in the chat alone is not success. Click Execute; no authorization is required.
5. Open Outcome → Statistics → Regression. Intercept and slope should both be 1.3;
   slope P-value about 0.01729237; R-squared about 0.96571429. Descriptive: mean x 1.5,
   sample variance x 1.6666667. Matrices must show labeled x/y axes and four rows.
6. Download the statistical report. Confirm source path/hash, four analyzed rows,
   methods, coefficients, P-values and limitations. Refresh and reopen this chat/run:
   the same values must return without another execution.
7. In terminal, open the same chat and use `/statistics`. It must show the same
   source-linked report. Historical reports are evidence, not fresh source checks.

For the real sample, use a separate chat and request descriptive statistics and OLS
for `test/diabetic_sample_5000.csv`: outcome time_in_hospital, predictors num_medications
and num_lab_procedures, intercept, cluster covariance grouped by patient_nbr. All 5,000
rows should be analyzed with 4,260 clusters for the current sample. This is an exploratory
engineering test, not a medical conclusion. New source bytes can change these figures.

## Verification record

Known-answer tests independently compare simple OLS to hand calculations/SciPy
linregress, multivariate coefficients to an orthogonal fixture, and check covariance
choices, missingness, filters, rank deficiency, perfect fits, budgets, MCP/CLI parity,
planner schema coverage and source immutability. A read-only real 5,000-row sample
calculation matched independent NumPy least squares: coefficients approximately
0.05171443, 0.18765340, 0.03857347; R-squared 0.31906297; 4,260 patient clusters.
Source SHA-256: `55b57c6c552e7b20f40c9dbd1dea98e706e5f214e879fe92407794fcd4e2d01b`.
Browser acceptance replaces the model with a fixture while exercising real services;
it does not establish reliability of the installed Ollama model.

Completed checks: `make test` — 2,168 passed (13 existing warnings); final focused
statistics/Planner/MCP suite — 156 passed, plus the 16-case statistics suite after
the actual registered MCP invocation assertion. `make interface-validate` passed
(existing bundle-size advisory). Isolated browser acceptance passed Statistics
sections, report download, saved-run restoration without replay, CLI continuity and
terminal journeys, with zero page errors. HTTP fixture tests require permission to
bind local loopback ports; the restricted first run was superseded by this passing run.

## Next slices

T01/T03 full lifecycle/contract consolidation and T06 generated-code reuse remain open.
This family partially addresses T05/T09/T10; broader model diagnostics, categorical
encoding, covariance matrices, group comparisons, predictive evaluation and justified
causal designs remain separate work. T11 document frequencies/co-occurrence/word clouds,
XLSX/JSON/document adapters and broader formats are not delivered by this slice.
