# T05: analytical recommendations, review and report evidence

2026-10-29 follow-up: [recorded figures and common table sources](TABLE_FORMATS_AND_STATISTICAL_FIGURES.md)
adds group means/heatmaps/PDF figures and adjacent existing advisory assessment. It
retains the separation of numerical facts, model interpretation and authority below.

Implemented 2026-10-28 as the next slice of IMPLEMENTATION_TODO T03/T04/T05.
This builds on initial field guidance and statistical starters; it does not close
all of T05 or add another permanent agent, unrestricted Python, RL or domain memory.

## Agent skills and shared services

- Initial/comprehensive inspection attaches at most four `analysis_opportunities`:
  field-quality review, measurement distributions, category counts/percentages, and
  key/repeated-entity checks. Each lists actual candidate fields, the existing
  inspect_csv analytical contract, reason and prerequisites. These are bounded
  method-family options, not a selected scientific design or computed findings.
  The standard-library-only profiler and existing response budgets remain intact.
- Existing read-only MCP `recommend_table_fields`, CLI `table-guidance`, and saved
  guidance projections expose the same evidence. The operation catalog makes
  `analysis_recommendations` discoverable under inspect_csv; no fictional operation
  names or unregistered library functions are dispatched.
- Planner runtime guidance and the existing table-statistics skill now cover next
  analysis selection. `What statistical analysis should I do next?` follows the
  recorded advice-only path: at most three relevant suggestions with candidate fields,
  reasons and prerequisites, plus at most one genuinely missing-objective question.
  The count/question limits are model instructions, not semantic guarantees.
  Backend validation requires message + plan=null and rejects action/proposal changes.
  Explicit calculation requests keep the normal planning/Execute route.
- Planner instructions are applied in the request builder; SKILL.md is the maintained
  operator/agent method guide, not a new dynamically installed execution entrypoint.
- Critic manifest and Single/Three-role coordinator instructions now assess question,
  scope, fields, missingness, exclusions, grouping and observation unit. Both use the
  shared statistical-evidence projection. Model review is advisory, not independent
  numerical verification, domain expertise or execution authority.

No new general-purpose agent/tool loop was introduced. The Planner recommends and
proposes; the deterministic analytical service calculates; the Critic assesses the
recorded facts and gaps. Installing a package remains distinct from execution approval.

## Report and review contracts

StatisticsSpec adds optional `question` (1–400 characters). It records an analytical
question as untrusted context; absence is explicit rather than filled with an invented
research objective. Old saved results without it remain readable.

Reports add Analysis definition and Computed findings before the numerical tables.
They show the supplied question, numerical/grouping fields, parsed-row observation
unit and factual counts/ranges/means. They explicitly separate these computations from
agent interpretation. Existing frontend Summary, Report, Markdown/PDF download,
terminal `/statistics`, CLI table-statistics and MCP tools reuse the same recorded
facts. Reports are not silently augmented with a free-form model conclusion.

Critic evidence includes source/hash, specification/question, matching/analysis/excluded
counts, missing/invalid counts, up to eight overall descriptive fields and three group
summaries, up to six measured correlation pairs per method with explicit omitted-pair
counts, matrix applicability/inference limits and regression diagnostics. Descriptive/group omission counts
are explicit. A 6 KB target trims review presentation, never the complete result or report.
If necessary, detailed specification/model evidence is omitted with a clear warning.
Combined run-review budget overflow is also labeled. No raw preview rows are handed over.
Review timeout/unavailability still preserves deterministic outcomes and never retries
workflow operations or grants authority. Actual Critic-model quality remains unverified
by the planning-only model evaluation below.

## Frontend validation

1. Restart the normal launcher; no write flag is needed. Inspect
   `test/diabetic_sample_5000.csv` again so the new recorded advice is available.
2. Outcome → Overview → What to explore next → **Possible next analyses**.
   Expect supported method families with candidate fields and prerequisites, including
   missingness/code review and entity checks where indicated.
3. In the same chat ask: `What statistical analysis should I do next? Suggestions
   only; preserve the current workflow.` Expect a short explanation using recorded
   fields. The graph/run must remain unchanged; advice must not claim computed results.
4. Request an analysis explicitly, for example:

   ```text
   Compute descriptive statistics for time_in_hospital grouped by age in
   test/diabetic_sample_5000.csv. Use missing_policy=error. Replace the inspection
   with one inspect_csv analysis step. Record the question: How does hospital stay
   vary across the recorded age bands? No writes. Prepare only.
   ```

5. Review the actual selected fields/methods, then Execute. Outcome → Statistics →
   Summary should show the supplied question if the model included it. Report should
   include Analysis definition and Computed findings, 5,000 analyzed/zero excluded,
   overall mean 4.6592 and ten age groups. This is encounter-level description of the
   first 5,000 source rows, not clinical or causal evidence about independent patients.
6. Check Markdown/PDF and reopen through Workflow history or terminal `/statistics`.
   Report fields/counts/source binding must agree without another calculation.

## Verification and remaining work

Known-answer tests independently check statistics, question escaping/length, source
binding, grouped evidence, omission accounting, no preview leakage and no mutation of
saved results. Advice tests cover next-analysis wording, strict null-plan responses,
explicit calculation routing and preservation with inspection-on-send enabled.

The isolated analytical browser journey passed with zero page errors, including the
new collapsed method options, question display, report sections, five-page PDF, wide
matrix preservation, terminal history and existing chart/recovery checks. Browser
model replies are fixtures, not evidence of arbitrary local-model quality.

Explicit real-model script:

```bash
.venv/bin/python scripts/statistical_planner_evaluation.py --model qwen3.5:9b
```

It creates a temporary synthetic project, performs one fixed read-only inspection,
then tests actual-model advice, grouped description and Pearson proposals. Verified
model proposals are evaluated by an explicit bounded analysis read, not dispatched
as workflows. No dataset writes, live database calls, downloads or model training.
The script does not change the launcher or operator's saved projects. Diagnostics
report prompt size, correction stage, elapsed time and completion tokens. No automatic
retry after transport timeout; the script continues to distinct named test cases.

Installed qwen3.5:9b with reasoning_effort=none passed all three cases in one call each:
advice 32.7 s / 11,235 prompt bytes / no operation schemas; grouped description 40.1 s /
26,084 bytes / one schema; Pearson 45.2 s / 19,875 bytes / one schema. Advice named only
observed fields and distinguished rows from individuals; numerical values matched
independent known answers. These are three synthetic cases, not a general reliability
or performance benchmark. More compact contexts and broader real-model coverage remain.
These timings/prompt sizes were measured before the final shortening of overlapping
manifest wording to retain the existing 17 KB calculation-planning regression budget.
The focused statistical rules and deterministic validators were not weakened.

Final verification: `make test` **2,186 passed**, with 13 existing spatial warnings;
focused planning/evidence tests passed; `make interface-validate` passed with the
existing bundle-size advisory. The complete isolated browser journey passed with zero
page errors. The real 5,000-row sample retained all four analysis-opportunity families
and produced the expected ten-group, mean-4.6592 report with matching source hashes.
No dependencies installed, live database/service configuration modified, or Git actions
performed. Existing work and user-owned files were preserved.

T05 remains partial: embedded chart figures in exported reports, richer evidence-bound
domain interpretation, broader study designs and comprehensive entry-point consolidation
are open. Broader XLSX/JSON/document adapters, generated-method qualification, agent
routing and memory remain separate dependency-ordered tasks.
