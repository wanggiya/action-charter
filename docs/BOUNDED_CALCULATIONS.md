# Bounded table calculations — implemented slice

Implemented 2026-10-17 from the [recorded design](BOUNDED_CALCULATION_DESIGN.md).
This is an additional bounded operation; it does not complete checkpoint 27 or
implement arbitrary code acquisition, RL, domain-knowledge memory or chat-based
authorization. No new agent/subagent, model or MCP server is added.

## Behavior and responsibilities

`calculate_csv_columns` uses the existing source/target contract: original CSV/TSV
under data/input, or a validated CSV-producing ancestor via source_step. Bare
filenames normalize under data/input. Each output is a fresh data/output/*.csv
file, with exact approval and independent validation required. Existing table
bounds apply: 8 MiB files, 10,000 rows, 100 columns and bounded previews.

Planner proposes typed expression data and may repair it once through the normal
correction path. Backend services validate/evaluate it, enforce budgets and retain
actual evidence. Existing graph, authorization, runner, recipe and CLI services
are reused. Critic is not required to validate a calculation.

Expressions have closed, versioned arguments and five node kinds:

- column: a numeric original source column, referenced by name.
- number: a finite numeric constant; booleans and numeric strings are not constants.
- binary: add, subtract, multiply or divide two numeric expressions.
- compare: eq, ne, gt, ge, lt or le on numeric expressions; used as a condition.
- if: a comparison condition with numeric then/otherwise expressions.

Every derived output must be numeric. Numeric classifications can use conditional
codes; text/date/statistical functions are not in this slice. All expressions read
original source columns, not sibling derived columns. Output names must be unique
and cannot replace existing columns. Source columns and string identifiers remain
unchanged. Values are explicitly converted to float64 for calculations: this is
not exact decimal/currency arithmetic and can lose large-integer precision.

`missing_policy` is mandatory: error rejects missing values in any referenced
source column; propagate carries missing values through expressions, including a
missing conditional result. Conditionals evaluate only selected branches.
Division by zero with present operands fails; missing operands propagate under
propagate. Numeric source errors and non-finite/overflow results fail. There are
no imports, eval, arbitrary Python/functions, package installs or network calls.
Optional assumptions record units/domain meaning supplied for review, not proven
facts or independently verified domain knowledge.

## Validation and independent checks

Schema checks enforce at most five derived columns, 100 expression nodes total,
maximum depth eight, and 8,192 UTF-8 bytes for the compact JSON calculations list
(`ensure_ascii=False`, no insignificant whitespace). Semantic checks reject
boolean arithmetic and non-numeric outputs.

Before saving/reviewing a workflow, original input calculations validate referenced
columns and numeric/missing inputs and evaluate at most 100 source rows without
publishing files. Known intermediate schemas are checked where available; joins
and unknown intermediate values are checked against actual validated artifacts at
runtime. These checks are not a guarantee that later rows will succeed.

Execution validates the full bounded input. Before publication and during output
verification, a separate scalar interpreter checks all serialized calculation rows,
source-column preservation and output shape. Numeric comparisons allow 1e-12
relative/absolute tolerance. SHA, source identity, counts and columns also pass
existing checks. Verification does not prove the user's chosen domain formula.
A failure cannot authorize retries or overwrite earlier outputs.

There is no separate agent-callable calculation preview tool. Preflight is an
automatic bounded service; opening saved formulas/results performs no calculation
execution or model call.

## Effort accounting

One conversational turn shares a maximum of four model attempts across generation,
discovery, correction and any explicitly requested recipe preparation/Critic work.
Discovery permits at most two read-only requests (search returns at most five
matches; inspect requests one source). Calculation repair consumes the existing
single correction allowance, not another budget. Failed model attempts count;
transport timeouts are never automatically retried. Ordinary planning needs no
mandatory discovery or Critic call.

Context sent to Planner shows model/discovery attempts, total submitted prompt
bytes, elapsed time and endpoint-provided token usage. Missing or partial usage
is reported as unavailable, not zero. Every full prompt remains capped at 64,000
UTF-8 content bytes. Existing MODEL_MAX_TOKENS is sent to the endpoint; its
interpretation depends on that endpoint. Bytes/tokens are not reasoning quality.

Optional trusted launcher setting `PLANNER_TURN_TIMEOUT_SECONDS` accepts finite
values greater than zero and at most 2400. It starts immediately before Planner
inference, caps subsequent per-call timeouts by remaining time and rejects late
replies before chat/plan commit. No overall deadline is imposed by default pending
laptop measurements; MODEL_TIMEOUT_SECONDS still bounds individual calls. HTTP
transport timeouts are not forceful cancellation of all backend computation.
The opt-in post-turn method helper remains separately accounted in its existing
receipt; it is outside Planner generation and cannot authorize anything.

## Frontend acceptance

Restart the existing launcher, refresh, and send:

> Inspect sample_orders.csv. Add a new numeric column doubled equal to amount
> multiplied by 2. Preserve every original column and propagate missing values.
> Use a fresh output CSV. Do not execute yet.

1. Confirm a Calculate table columns block and the correct source path appear.
   Saving the proposal creates no CSV. Planner may omit target_path for safe backend
   allocation. Actual model planning quality must be tested on the laptop.
2. Select the block. Planning details shows a readable formula and missing policy.
3. Open Block tools -> Parameters. Use formula controls to change 2 to 3; choose
   missing policy from the selector. Validate and save edits before approval.
   The expression editor requires no manual JSON.
4. Authorize the exact output, then Execute. Original sample rows produce doubled
   values 30, 60, missing, 120, 15, 90 after the edit. Original IDs remain strings.
5. Expand outcome/validation: check table rows and calculation_values passing.
6. Refresh/reopen the chat. The edited formula restores without reexecution.
7. Add -> search Calculate discovers the operation. Invalid columns, collisions or
   expressions reject without replacing the saved workflow. A later-row runtime
   failure reports failure rather than claiming preflight guaranteed success.

The [typed example](../examples/calculations/double_amount.json) uses multiplier 2:
expected values 20, 40, missing, 80, 10, 60. Submit through existing workflow-plan,
workflow-review, workflow-authorize and workflow-execute CLI services. CLI and
interface share contracts, scope and execution; CLI execution requires explicit
confirmation and the exact authorization records.

## Verification

New fixture tests cover actual temporary CSV execution, CLI authority, intermediate
artifacts, successful retention, independent tamper detection, lazy conditionals,
missing values, unsafe expressions, bounds, late-row failures, cumulative effort
and late-reply preservation. Browser fixture acceptance covers chat/graph creation,
formula editing without JSON, fresh authorization/execution and refresh restoration.
Model replies are fixtures; no live model, database or service acceptance is implied.
Verified: `make test` passed 1,711 tests; `make interface-validate` passed typecheck/build. Twenty-three browser fixture cases passed across calculations (4), CSV workflows (6), recipe preparation/cancellation/recovery (6), and retention/discovery (7). Calculation editing also checks that an empty numeric draft blocks saving.


## Calculation planning repair follow-up

The supplied acceptance prompt says “multiplied by 2.” Initial schema focusing
recognized “multiply” but missed that inflection and “new numeric column,” omitting
the calculation argument schema on the first request. Recognition now includes
those forms and “divided.” Simple CSV-calculation requests receive focused
inspection/calculation/export schemas; explicitly requested supporting transforms
and existing workflow schemas remain available. This reduces descriptive context,
not the operation allowlist or backend validation.

Planner now receives a complete non-executing reply example, with the actual
inspection/calculation step shape and approval/validation flags. Example filenames,
columns and constants are illustrative; they never become a backend fallback plan.
“Do not execute yet” requests a proposal, not a null-plan schema-repair promise.
A repair receives the complete example and safe findings within the same single
correction allowance. Genuine missing-input questions remain permitted.

Repeated repair promises return planner_repair_deferred with safe diagnostics,
prior concrete schema findings when available and guidance identifying a model-
output failure. They do not tell users to invent approval/validation rules. Saved
workflows remain unchanged; no authorization or execution occurs. No retry budget
was increased. Restart the launcher and retry the same acceptance prompt; local
model reliability still requires operator verification.

Regression coverage includes exact prompt wording, inflections, typed examples,
bounded repair, no canned-plan fallback, saved-workflow preservation and HTTP error
classification. The calculation browser fixture deliberately defers once, then
returns a valid model fixture proposal; it executes only after fresh authorization.

Follow-up verification: `make test` passed 1,726 tests, `make interface-validate`
passed, and 11 targeted browser fixture cases passed (calculation repair/edit/run/
restore: 4; retained-method discovery/reuse/privacy: 7). These use fixture model
replies and temporary CSV data, not a live Ollama acceptance run.


## Decoder schema and malformed-response follow-up

[Transport, compatibility and safe diagnostics](PLANNER_STRUCTURED_OUTPUT.md).
Planner now requests schema-constrained structural JSON, while all existing runtime
checks remain authoritative. Malformed whole responses no longer receive the
misleading plan-field type label; reported output-token truncation is distinct.
No retry or output-token budget is increased automatically. Required proposal gates bind upward from the registry without granting authority. One exact-request planning smoke passed on the configured local qwen3:4b-instruct; broader model acceptance remains open.

## Inspector clarity follow-up — 2026-10-18

The information panel lists every operation in the selected current plan, including
readable calculation formulas before node selection. Selecting a list item focuses
that graph node. Calculation graph subtitles also show the formula. An explicit
calculation request whose saved plan lacks calculate_csv_columns gets a visible
missing-step notice; no operation is invented or added automatically. A one-step
inspection plan cannot calculate columns, even when its inspection succeeds.

Selected-operation planning details retain the formula while Raw arguments is
collapsed. Authorization review uses the same readable formula with explicit
source/target parameters rather than a long JSON expression. Performer appears
once with status. Execution details groups authority and observed facts; Evidence
and Task history remain available below the operation content, collapsed by
default. No execution or authorization behavior changes.

Manual check: reopen the chat and read Workflow operations. For the doubling
example it must list Inspect CSV table and Calculate table columns, with
`doubled = (amount × 2)`. Select the calculation to see its details. Expand Raw
arguments, Execution details, Evidence and Task history individually. If only
inspection is listed, ask Planner to add the calculation and inspect the updated
list before authorizing; do not execute an incomplete plan.

Verified: make test (1,744 passed with local test-server socket access),
make interface-validate (typecheck/build), five calculation browser cases and
six existing CSV browser cases. Browser checks use isolated profiles, temporary
files, the real backend and fixture model replies; they do not establish what
a particular existing chat contains or broader live-model planning quality.

## Missing calculation in saved history — 2026-10-18

Read-only inspection of a local historical conversation and its immutable saved
plan confirmed a model-output omission: the summary and assistant message claimed
`doubled = amount × 2`, while plan.steps contained only inspect_csv. The frontend
correctly displayed that single step; there was no saved expression to render.
Earlier structural/argument/authority checks did not establish request coverage.
The historical records remain unchanged.

Conversational planning now checks a narrow class of explicit calculated-column
requests before accepting a non-null proposal, including expanded recipe steps.
It supplies a coverage hint and rejects a plan missing calculate_csv_columns,
using the existing single correction attempt. Repeated omission returns
planner_scope_incomplete and preserves the prior transcript/workflow; nothing is
saved, authorized or executed by that failed turn. Missing semantic inputs or
unavailable selected capabilities may still receive a genuine null-plan question
or explanation. Negative/removal, metadata-only, selection and join requests
are covered by regressions.

This is a bounded English request-coverage guard, not general natural-language
understanding or proof that every formula matches user intent. It does not invent
formulas, patch old plans, grant authority or bypass argument/path/data validation.
Frontend restoration continues to show the actual saved steps and a missing-step
notice for the affected request. After restarting the API, resubmit the full
calculation task in that chat to obtain a new validated proposal; refreshing alone
cannot add a calculation to the historical record.

The isolated browser check seeds a temporary copy of the historical failure,
restores it, rejects a fresh inspection-only success claim, corrects the actual
step list, shows the formula and executes only after fresh test authorization.
It then checks output values and refresh restoration without repeated execution.
Set ACTIONCHARTER_CALCULATION_FAILURE_MODE=invalid_json when running the existing
calculation browser command to retain the alternate malformed-JSON repair case.

Calculation-focused decoding also binds the three relevant operation argument
shapes and exclusive source choices. The simple calculation instruction set
omits unrelated domain/authoring rules, and the Planner manifest now explicitly
separates proposing approval-required operations from receiving permission to
execute them. All manifest permissions and backend authority checks remain.

The simple, explicit single-column slice also supplies a decoder operation
skeleton (inspection when requested/already present, then calculation). Paths,
column names, expressions and missing policy still come from the model; the
backend does not substitute a canned plan. Complex or negative instructions and
nontrivial existing workflows keep the general path. A final temporary-history
check with the actual qwen3:4b-instruct model returned the correct two steps,
formula and missing policy in one call (34.44 seconds), with no authorization,
execution or CSV creation. Broader model acceptance remains open.

Final verification of this follow-up: make test — 1,764 passed;
make interface-validate — typecheck/build passed (existing bundle-size warning);
six isolated calculation browser cases passed with the real backend and fixture
model replies. The separate actual-model planning check above passed once;
it neither executed the workflow nor replaced the operator's historical record.

Reuse-citation follow-up: ordinary calculation planning does not require a recipe.
The model's optional reuse-ID field is omitted when no source was supplied or
successfully inspected, and otherwise enumerates those eligible sources. The
backend still rejects forged/unrelated claims rather than dropping them. A repeat
failure reports planner_reuse_unverified and preserves the saved workflow. The
default calculation browser fixture covers this error; omission/invalid_json
variants remain available through ACTIONCHARTER_CALCULATION_FAILURE_MODE.
