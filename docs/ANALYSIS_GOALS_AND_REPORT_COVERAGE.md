# Inspection-led analysis goals and honest metric coverage

2026-10-30 delivery within T03/T05 and the existing full-data acceptance work.
The user selected: **Let the agent propose analysis goals from the inspection.**
This does not complete the health-data study or the broader local-model reliability gate.

## Problem and implementation

The last reviewed workflow requested numeric profiling and quality checks, without any
`analysis.statistics` methods. Its report could not legitimately contain regression
P-values or prediction precision. Merely promising a report does not perform analysis.

The Planner now has a typed, advice-only reply for analysis goals. It receives bounded
recorded field roles, counts and exact source identity rather than the data rows or a
large workflow prompt. Each goal names a scientific question, candidate fields, method,
rationale and prerequisites. The service validates observed fields and source/hash;
numeric methods reject identifiers, codes and categories as measurements. Numeric
statistics beyond the registered 200,000 matching-row limit require an explicit scope
choice, with no silent sample substitution. The source may have changed since recording;
advice does not certify freshness. Execution still performs normal source checks.

The same conversation API persists goals in `context_usage.analysis_goals`, readable
through CLI clients. This is per-chat advice, not cross-chat memory, domain learning or
an added autonomous agent. Planner role supplies scientific choices; shared deterministic
services validate structure, evidence scope, capabilities and execution boundaries.
No new unrestricted MCP calculation tool is added: existing typed statistics tools and
operation discovery remain the executable surface. The table-statistics skill describes
how to progress from advice to those registered operations.

## Interface and operator validation

1. Restart the existing launcher once to load updated backend code, then refresh the UI.
   Preserve your usual model configuration. Goal advice and read-only inspection do not
   require enabling writes.
2. Open a chat with a completed, source-matching table inspection. Open Outcome → Overview
   and click **Let Planner propose analysis goals**. Alternatively send:
   `Propose analysis goals from the recorded inspection. Suggestions only; preserve the workflow.`
3. The Planner opens and shows **Suggested analysis goals**: question, actual fields,
   method, metrics *when calculated*, availability and expandable prerequisites. The
   current graph and completed run must remain unchanged; no new run should appear.
4. For a supported goal, click **Prepare this goal**. This sends the complete chosen
   goal and recorded source identity to ordinary planning. It prepares a proposal or
   asks for a genuinely missing scientific choice. It does not execute or authorize.
5. Inspect the proposed actual arguments/method, then Execute separately for read-only
   analysis. Review Outcome → Statistics and Report. Do not treat the goal cards as
   measured findings. If the model fails, inspect Request diagnostics; the current
   workflow remains preserved and there is no automatic execution retry.
6. Reopen the chat before preparing a goal to check persistence. A later ordinary turn
   clears the old goal cards; its message still records the chosen goal. Goals for
   unavailable methods have no Prepare action.

## Statistical coverage and limitations

Newly produced readiness reports include a Statistical coverage table. It distinguishes
computed evidence, method diagnostics preventing inference, and metrics not calculated.
Older saved reports are historical evidence and are not rewritten by this change.

| Metric or method | Current behavior |
| --- | --- |
| Descriptive mean, percentiles, variance, standard deviation | Registered typed statistics; requires an actual requested calculation |
| Pearson/Spearman coefficient and conditional P-value | Registered; needs measurement candidates, analysis unit and assumptions |
| OLS coefficients, standard errors, confidence intervals, P-values, R-squared, residual error | Registered numeric regression; requires target/predictors, missing policy and model review |
| Category counts and percentages | Registered grouping; denominator and rows versus entities must be explicit |
| Classification precision/recall/F1, confusion matrix, calibration | No registered training/evaluation operation; proposed goals show a capability gap |
| Categorical association hypothesis tests and causal analysis | Not registered; goals cannot prepare substitute operations |

Standard deviation is not standard error. Residual model error and in-sample R-squared
are not held-out predictive performance. P-values do not demonstrate causality. Health
records can repeat patients; field names alone do not establish the observation unit,
clinical meanings, label definitions or acceptable evaluation split. No agent invents
these choices or metrics. Goals do not create training, installation or write authority.

## Verification record

Focused backend tests cover source/hash binding, observed field roles, rejection of
identifier inference, bounded correction, unavailable capabilities, row limits, durable
chat advice and unchanged workflow/execution state. An isolated browser/API/CLI/terminal
journey checks advice cards, preparation without execution and existing result flows.
The actual local-model evaluation uses saved aggregate metadata plus header-only
stand-ins in a disposable workspace; it never executes a workflow or scans the private
source again. It is an advice-contract test, not full clinical study acceptance.
See WORK_RESUME and the final delivery report for measured outcomes and remaining gates.

Actual qwen3.5:9b advice test passed on saved inspection metadata in one call:
67.6067 seconds, 2,212 prompt / 463 completion tokens, reasoning `none`, output cap
1,200. It returned data-quality and descriptive goals without changing the workflow.
A title was imprecise relative to its fields; these remain unreviewed proposals, not
clinical or scientific endorsement. Earlier failures exposed long rationales and numeric
methods on category codes. Decoding now respects text limits and restricts numeric
method fields to recorded numerical/count candidates; backend checks remain authoritative.
Safe correction findings name trusted goal fields without exposing model values.
Interface validation and isolated browser/API/CLI/PTY journeys pass. The original full
sandbox run had 2,224 passes and 28 HTTP tests blocked by socket permissions; the full
suite then passed with local socket access: **2,254 passed**, 13 existing spatial
warnings, 564.92 seconds. The final role-restricted decoder also passed its focused
tests. No live database, saved model preference or Git action occurred.
