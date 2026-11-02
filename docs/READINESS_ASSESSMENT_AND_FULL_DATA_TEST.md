# Readiness assessment and full-data acceptance

2026-10-29. T03/T04/T05 real-data readiness slice. The full supplied dataset is the
acceptance target. The 5,000-row file is a preliminary fixture, never a silent substitute.
This delivery does not certify real-model planning, clinical conclusions, database scale
or the complete to-do list. User frontend acceptance remains pending.

## Planner timeout follow-up — 2026-10-29

The reported 22.8 KB / 120.1-second failure occurred during planner generation, before
dispatch. Message bytes are not tokens or CSV bytes; no full-file calculation ran.
The timeout establishes only that the request exceeded its configured deadline. It
does not establish context overflow, model loading, queueing or generation as the cause.

A prompt audit found about 10 KB of generic rules in a single-operation quality request.
The analytical single-inspector path now uses `table-inspection-focused-v1`, replacing
unrelated writer/conversion instructions with concise source/quality/missingness and
authority guidance. Schemas, operation arguments and backend validators are unchanged.
Unused optional arguments and unrequested column lists need not be generated. Existing
statistical, calculation, acquisition and mixed-workflow prompt profiles retain their
separate behavior. This remains model planning, not a model-free workflow template.

The isolated readiness fixture uses **11,218 message bytes** and **3,870 decoder-schema
bytes**; these are distinct measurements, not a token count or a production latency
benchmark. Tests verify actual requested duplicate/key/missing/codebook arguments and
that a timeout makes one model call, retains the saved revision and performs no execution.
Planner diagnostics now include `prompt_profile`; the interface shows it on failure.
No timeout increase, model switch, automatic retry or authority change was introduced.
Actual Ollama latency with this profile still requires manual validation.

Follow-up checks: `make test` **2,219 passed**, 13 existing spatial warnings; focused
planner/schema/timeout tests, `make interface-validate` and the complete isolated
browser/terminal journey passed (zero page errors). No actual model call or data
execution was performed by this debugging slice. The earlier full-data numerical
verification below remains separate evidence.

Stop/restart the existing launcher, refresh the frontend and deliberately resend the
same full-source request once. A new failure should show instructions
`table-inspection-focused-v1` for this quality-only request; a statistical follow-up can
instead use the existing `statistics-focused-v1`. Missing profile diagnostics indicate
an older running backend. If it still times out, retain the complete diagnostics and
inspect the model server's current load/configuration; do not assume a smaller input
CSV fixes a failure that precedes data processing. The contract string statistics-v2
is an API revision, not proof that statistical calculations were running.

## Structure and ownership

```text
Question -> Planner's existing skills -> registered typed inspection
                                        |
                    complete selected-source calculations + verification
                                        |
                    readiness-assessment-v1 (pure evidence projection)
                      /                 |                   \
               frontend Report     CLI/MCP JSON        compact agent evidence
               Markdown/PDF        CLI Markdown        Planner / Critic review
```

`tabular/readiness.py` normalizes the existing table-analysis and comprehensive profile
results. It performs no source reads, model calls, data mutation or approval. It combines
source/hash/selection, filters, denominators, missing policies, field facts, requested
key/duplicate checks, codebook coverage and grouped findings. Readiness evidence is
typed in the operation result schema. Existing calculation and worker paths remain;
the comprehensive worker gains no Pydantic/report dependency or new protocol.

The standard inspection result and comprehensive service attach the same assessment.
Reports use measured facts. Optional Planner interpretation and Critic assessment remain
separate advisory records. Critic and Single/Three-role outcome review receive bounded
scope/check/field evidence, not raw rows or report prose. Larger review packs retain
their existing budgets and report omissions. No new permanent agent is introduced.

The existing statistical skill now describes full-source-first assessment, explicit
missing markers, keys versus repeated entities, codebook coverage and bounded checks.
Planner/Critic manifests reinforce these responsibilities. No operation ID or permission
gate is replaced by a model instruction. Arbitrary Python, dependency installation,
memory learning and auto agent-mode routing are not added here.

The exploration loop now restricts profiling to the explicitly supplied/default full
source candidates for that turn. It may assess an alternative's eligibility, but cannot
profile a neighbouring sample without the user selecting it in a subsequent request.
The permitted list is enforced after model output, independently of prompt compliance.
This is a specific exploration-loop protection, not a claim that all conversational
source-resolution cases have been solved. Sampling itself remains unavailable in that
read-only loop; creating a sample needs a registered writer and normal authorization.

## Scope, limits and meaning

- Complete-file evidence means the entire selected file was processed under its recorded
  filter/selection. It does not prove the file covers the real-world population. A
  sample-looking filename is only a hint; provenance/representativeness remain unverified.
- Missing percentages use matching records. Numeric valid counts and invalid values are
  separate; identifiers and bands are not automatically measurements. Candidate roles
  remain candidates. A check not requested is **unknown**, not passing.
- Key and whole-row duplicate checks come from the specialized exact analysis path.
  The comprehensive profile does not invent those checks; its report marks them unknown.
- A supplied codebook is identified by path/hash. Coverage reports all unmapped values;
  supplied labels are not independent domain verification. No codebook means no verified
  semantic mapping. Unbound sections remain explicit.
- Group reports retain at most 30 rows. Total and within-first-field percentages use
  complete grouped denominators **before** display truncation. Missing-token groups
  remain visible. Original group tables retain all groups within their operation cap.
  The pure percentage helper is shared with existing interactive/terminal views.
- Assessment output is capped at 48,000 bytes and remaining room under the existing
  inspection budget. Field/group omissions are recorded. An oversized assessment is
  omitted with an explicit status; original analysis is never discarded to fit a report.
- Statistical method details are included in the combined Markdown when they fit.
  Otherwise a statistical-report omission is explicit and the original Statistics report
  is retained. Matching-source statistical figures reuse existing interactive SVG/PDF
  projections and their documented caps; Markdown retains tables rather than SVG.
- Opening/exporting a report does not scan the source, call a model or rerun a workflow.
  Browser downloads are local exports. Backend dataset/report-file creation and database
  mutations continue through normal Allow writes -> Authorize -> Execute.

## Interface and CLI/MCP

Outcome **Report** uses existing result tabs, typography, tables and Markdown/PDF export.
It verifies the assessment source/hash against the selected outcome. Statistical figures
require the same matching source/hash. Historical outcomes without a report show an
explicit unavailable state; opening them does not generate new evidence.

Existing MCP `profile_table`/`table_statistics` and CLI `inspect-table` return the same
structured `readiness_assessment`. `inspect-table --report` prints its measured Markdown
instead of JSON and still performs a new explicit read. The terminal `/report`, or
`chat result CHAT_ID --view report`, opens an already saved comprehensive report without
another read. A missing historical report is not silently reconstructed. Existing CLI
workflow history still exposes the same recorded standard-operation outcome and report.

## Manual full-data journey

Restart the existing launcher after updating code. For this read-only phase, write
tools and database access are unnecessary. Start a new chat, use Single or Three roles
explicitly and record the model name. Do not use both modes concurrently on the laptop.

1. Select only **Inspect CSV table** if automatic selection produces oversized requests.
   Send:

   > Inspect test/diabetic_data.csv with test/IDS_mapping.csv. Use the whole supplied
   > file, not diabetic_sample_5000.csv. Treat ? as missing in race, weight, payer_code
   > and medical_specialty. Check encounter_id as the record key and check whole-row
   > duplicates. Count distinct patient_nbr. Prepare only; no writes.

2. Review the actual source/arguments before Execute. A summary alone is not evidence
   that the requested checks are present. Open Outcome -> Report, Columns and Checks.
   Verify 101,766 source/matching rows and 71,518 distinct patient identifiers. Confirm
   missingness, key and duplicate checks against the independent reference; inspect
   coverage for the three supplied codebook sections. Do not interpret source records
   as independent patients or clinically decoded values without supplied definitions.

3. Follow up:

   > Keep the full source, codebook and readiness checks. Add a read-only analysis of
   > time_in_hospital using descriptive statistics. Group encounter counts by age and
   > readmitted. Show percentages within each age band. No writes; prepare only.

   Execute the reviewed proposal. The complete-source mean is approximately
   **4.395986871843248**, not the sample mean 4.6592. There are 30 age/readmission groups;
   their counts sum to 101,766. Use Groups for the complete cross-tab and inspect the
   denominator. Check Report omissions and original Statistics for detailed methods.

4. Request a separate full-source admission_source_id by readmitted comparison with
   the same codebook. Verify supplied labels and all group counts. No clinical or causal
   conclusion follows from a frequency difference alone.

5. Download Markdown and PDF. Reopen the saved chat/run and report after refresh. No
   second execution should occur. Continue the chat from CLI or frontend and verify
   that source, plan/run and recorded results match. Repeat the bounded journey in the
   other role mode; compare correctness, model time, failures and user clarifications.

If generation fails, record the exact error, schema count, bytes and model timing.
Preserve the saved workflow. Refreshing is not proof that execution completed. If an
actual operation limit is exceeded, split the checks or explicitly choose an alternative;
do not relabel a sample's results as the full dataset.

## Acceptance and remaining work

Automated tests use temporary unrelated tables for missing/key/duplicate/mapping facts,
zero denominators, full-group rates before truncation, escaped report text, budget
omissions, CLI/MCP parity, saved terminal reads, Critic evidence and source substitution.
Browser acceptance exercises both Report entry paths, terminal saved reports, local PDF
export and no execution replay. Final `make test`: **2,218 passed**, 13 existing spatial
fixture warnings. `make interface-validate` passed (existing bundle-size advisory).
The complete isolated analytical browser/terminal journey passed with zero page errors;
final focused readiness/source-selection tests also passed. The browser uses project-
local binaries and an ephemeral profile, not the user's browser cache. The final report
wording check was verified separately after the full suite. No dependency installation,
Docker image build, Git/publication action or live database mutation was performed.

The initial full-file calculation check reconciled 101,766 rows, 71,518 distinct patients,
all 30 age/readmission groups, declared missingness, supplied mapping coverage, key and
whole-row duplication, and the hospital-stay mean against independent standard-library
CSV/Decimal calculations. Original data/codebook hashes were unchanged. No model calls,
database connections or writes to source data occurred. This does not establish model
quality or broad performance. The full file is 19,159,383 bytes; record operation limits
separately rather than generalize this to arbitrary massive data.

The final full-file read additionally verified all 50 report fields, all 42 admission-
source/readmission groups, and within-age percentages against complete reference
denominators. Declared missing counts were race 2,273; weight 98,569; payer_code 40,256;
medical_specialty 49,949. In this large combined result the report retained 50 fields
but omitted 16 of the 30 age/readmission display rows and the detailed statistical
appendix to fit its budget. Those omissions are explicit at the top of the UI and in
the report; original Groups retains all 30 rows, and Statistics retains the full method
report. No calculation was sampled to meet a presentation limit. One observed worker
read took about 8.6 seconds and 215 MiB peak RSS; this is not a general benchmark.

Remaining for the first real end-to-end acceptance: user/local-model journey and domain
review, Single/Three-role comparison, then explicitly authorized disposable PostgreSQL
round trip. Existing bounded preparation/transform limits must be checked against the
full file before promising that round trip; sample-scale database tests do not prove
full-scale transformations or transfer. No live database mutation is authorized here.
Workflow-wide synthesis across independent source results, domain narrative validation,
advanced memory/RL, arbitrary generated methods and broader statistical designs remain
separate work. This report composes one inspection's evidence; it does not pretend to
merge unrelated runs or silently choose a clinical cohort.
